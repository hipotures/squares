"""Interleave native row separation and full-dual column batches in one LP."""
from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np


def generate_interleaved(side: Fraction, config: dict[str, Any], seeds: Any, directory: Path,
                         deadline: float, phases: Any, capture: Any) -> tuple[Any, dict[str, Any]]:
    from sqpack.fractional.certificate import Certificate
    from sqpack.fractional.colgen import (
        Rows, SiteSet, _ordered_direction_chunks, dual_squares, orbit_column,
        rationalise_sites, site_set_from_grids, site_set_from_points,
    )
    from sqpack.fractional.generate import LP_FEASIBILITY, direction_net, net_half_tangents, placement_cells
    from sqpack.fractional.hybrid_lp import AppendOnlyLp
    from sqpack.fractional.hybrid_pricing import price_full
    from devtools.frontier_io import atomic_json

    shrink = Fraction(config["shrink"])
    tangents = net_half_tangents(Fraction(config["angle_limit"]), config["direction_steps"])
    directions = direction_net(tangents)
    grid = site_set_from_grids(side, tuple(config["grid_counts"]), Fraction(1, 2))
    sites = site_set_from_points(side, set(grid.positions()) | set(seeds))
    rows = Rows(matrix=np.zeros((0, len(sites.orbits))))
    owner = AppendOnlyLp()
    details: dict[str, Any] = {"converged": False, "objective": None, "rounds": 0, "stopped": "budget"}
    candidate = None
    context = ProcessPoolExecutor(max_workers=config["workers"] - 1) if config["workers"] > 1 else nullcontext(None)
    with context as pool:
        for iteration in range(config["column_rounds"]):
            if time.perf_counter() >= deadline:
                break
            candidate = None
            phases("lp", "start")
            weights, duals, objective = owner.solve(rows.stacked(), sites.sizes())
            phases("lp", "end")
            capture(sites, weights)
            details.update(rounds=iteration + 1, objective=objective)
            weighted = dual_squares(rows, duals, tangents, side, shrink,
                                    support_cap=None, denominator=10**12)
            phases("separation", "start")
            points, membership = sites.points(), sites.membership()
            mass = weights[membership]
            if pool is None:
                answers = (placement_cells(points, mass, direction, float(side), float(shrink),
                                           keep=config["rows_per_direction"]) for direction in directions)
            else:
                answers = _ordered_direction_chunks(pool, points, mass, directions, outer=float(side),
                    side=float(shrink), keep=config["rows_per_direction"], clip=None)
            least, violated, added = float("inf"), 0, 0
            for direction_index, found in enumerate(answers):
                for covered, cu, cv, indices in found:
                    least = min(least, covered)
                    if covered >= 1 - 1e-9:
                        break
                    row = np.zeros(len(sites.orbits))
                    np.add.at(row, membership[indices], 1.)
                    if not row.any():
                        raise RuntimeError("current support cannot cover a separated placement")
                    violated += 1
                    added += int(rows.add(direction_index, (cu, cv), row))
            phases("separation", "end")
            closed = violated == 0 or (added == 0 and least >= 1 - LP_FEASIBILITY)
            details["converged"] = closed
            if closed:
                atoms = rationalise_sites(sites, weights, scale=config["scale"])
                candidate = Certificate(12, side, shrink, atoms, tangents) if atoms else None
                if candidate is not None and candidate.total_mass < 12:
                    details["stopped"] = "rows closed; candidate awaits the full gate"
                    break
            elif added == 0:
                details["stopped"] = "held row exceeds LP tolerance"
                break
            telemetry: dict[str, Any] = {"iteration": iteration, "objective": objective,
                "least_covered": least, "added_rows": added, "inserted": 0,
                "full_dual_mass": float(duals.sum()), "positive_dual_rows": len(weighted)}
            tail = max(4, config["column_rounds"] // 4)
            if (iteration % config["pricing_every"] == 0 and iteration + tail < config["column_rounds"]
                    and weighted and time.perf_counter() < deadline):
                phases("pricing", "start")
                found, priced = price_full(sites, weighted, wanted=config["columns_per_round"],
                    deadline=min(deadline, time.perf_counter() + config["pricing_seconds"]),
                    grid_steps=config["pricing_grid_steps"], arrangement_rows=config["arrangement_rows"])
                phases("pricing", "end")
                telemetry.update(priced)
                additions = []
                for point in found:
                    column = orbit_column(rows, point.orbit, tangents, shrink)
                    actual_cost = len(point.orbit) - float(duals @ column[:len(duals)])
                    if actual_cost < -1e-8:
                        additions.append((point, column))
                for _, column in additions:
                    rows.add_column(column)
                if additions:
                    sites = SiteSet(side, (*sites.orbits, *(point.orbit for point, _ in additions)))
                    candidate = None
                telemetry["inserted"] = len(additions)
            with (directory / "pricing.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(telemetry, allow_nan=False) + "\n")
    atomic_json(directory / "search-support.json", {
        "schema": "hybrid-support/v1", "status": "SEED_ONLY", "outer_side": str(side),
        "atoms": [[str(x), str(y), "0"] for x, y in sites.positions()],
    })
    details.update(rows=len(rows), candidate_points=sites.size, candidate_orbits=len(sites.orbits),
                   lp_models_created=1)
    return candidate, details
