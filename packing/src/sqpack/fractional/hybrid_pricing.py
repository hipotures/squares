"""Bounded broad candidate discovery and full rationalized-dual rechecks.

No candidate found is budget exhaustion, never an exhaustive pricing certificate.
The optional integer lattice applies only to NEW candidates, not imported sites.
"""
from __future__ import annotations

import time
from fractions import Fraction
from typing import Any

import numpy as np


def scores(query: np.ndarray, weighted: Any, *, deadline: float) -> np.ndarray:
    """D4-averaged float depth; supports a different half-side for every row."""
    from sqpack.fractional.colgen import symmetrise
    family = symmetrise(weighted)
    answer = np.full(len(query), -np.inf)
    if not family:
        return np.zeros(len(query))
    data = np.asarray([[float(s.ax), float(s.ay), float(s.u), float(s.bx), float(s.by),
                        float(s.v), float(s.half), float(w)] for s, w in family])
    query_chunk = max(1, min(256, 1_000_000 // min(len(data), 2048)))
    for first in range(0, len(query), query_chunk):
        if time.perf_counter() >= deadline:
            break
        block = query[first:first + query_chunk]
        depth = np.zeros(len(block))
        for start in range(0, len(data), 2048):
            if time.perf_counter() >= deadline:
                return answer
            rows = data[start:start + 2048]
            a = np.abs(block[:, 0, None] * rows[:, 0] + block[:, 1, None] * rows[:, 1] - rows[:, 2]) <= rows[:, 6] + 1e-9
            b = np.abs(block[:, 0, None] * rows[:, 3] + block[:, 1, None] * rows[:, 4] - rows[:, 5]) <= rows[:, 6] + 1e-9
            depth += (a & b) @ rows[:, 7]
        answer[first:first + len(block)] = depth
    return answer


def price_full(sites: Any, weighted: Any, *, wanted: int, deadline: float,
               grid_steps: int = 400, refinement_centres: int = 16,
               arrangement_rows: int = 16, coordinate_denominator: int | None = None) -> tuple[list[Any], dict[str, Any]]:
    from sqpack.fractional.colgen import Candidate, d4_orbit, rank_candidates
    from sqpack.fractional.exact_slabs import PreparedDepth

    if wanted < 1 or not 2 <= grid_steps <= 1000:
        raise ValueError("invalid bounded pricing configuration")
    side = sites.outer_side
    centre = side / 2
    step = side / grid_steps
    grid = [(step * i, step * j) for j in range(grid_steps // 2 + 1) for i in range(j + 1)]
    query = np.asarray([[float(x - centre), float(y - centre)] for x, y in grid])
    depth = scores(query, weighted, deadline=deadline)
    order = np.argsort(-depth, kind="stable")
    candidates = [grid[int(i)] for i in order[:max(96, wanted * 4)] if depth[i] > 1 + 1e-8]
    for index in order[:refinement_centres]:
        if depth[index] <= 1 + 1e-8 or time.perf_counter() >= deadline:
            break
        x, y = grid[int(index)]
        pitch = step
        for _ in range(2):
            pitch /= 4
            local = [(x + pitch * a, y + pitch * b) for a in range(-4, 5) for b in range(-4, 5)
                     if 0 <= x + pitch * a <= side and 0 <= y + pitch * b <= side]
            values = scores(np.asarray([[float(a - centre), float(b - centre)] for a, b in local]), weighted, deadline=deadline)
            if not np.isfinite(values).any():
                break
            best = int(np.argmax(values))
            x, y = local[best]
            candidates.append((x, y))
    # Never construct the all-pairs arrangement of the entire dual.
    if (arrangement_rows and len({square.half for square, _ in weighted}) <= 1
            and time.perf_counter() < deadline):
        bounded = tuple(sorted(weighted, key=lambda item: -item[1])[:arrangement_rows])
        candidates += [c.point for c in rank_candidates(sites, bounded, survey=96, wanted=min(16, wanted))]
    exact = PreparedDepth(weighted)
    held = set(sites.positions())
    checked: dict[Any, Any] = {}
    for x, y in candidates:
        if time.perf_counter() >= deadline:
            break
        if coordinate_denominator is not None:
            x = Fraction(round(x * coordinate_denominator), coordinate_denominator)
            y = Fraction(round(y * coordinate_denominator), coordinate_denominator)
        if not (0 <= x <= side and 0 <= y <= side) or (x, y) in held:
            continue
        orbit = d4_orbit(x, y, side)
        key = orbit[0]
        if key in checked:
            continue
        cost = exact.reduced_cost(orbit, side)
        if cost < 0:
            checked[key] = Candidate((x, y), orbit, 1 - cost / len(orbit), cost)
    result = sorted(checked.values(), key=lambda c: (-c.averaged_depth, c.orbit[0]))[:wanted]
    return result, {
        "pricing_rows": len(weighted), "pricing_mass": str(sum((w for _, w in weighted), Fraction())),
        "grid_points": len(grid), "grid_points_scored": int(np.isfinite(depth).sum()),
        "candidate_proposals": len(candidates), "negative_unique_orbits": len(checked),
        "best_exact_cost": str(result[0].cost) if result else None,
        "pricing_exhaustive": False,
        "pricing_budget_exhausted": time.perf_counter() >= deadline,
    }
