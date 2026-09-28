"""Experimental batched fixed-B search with the original native separation kernels."""
from __future__ import annotations

import json
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import nullcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np


def generate_hybrid(side: Fraction, config: dict[str, Any], seeds: Any, directory: Path,
                    deadline: float, phases: Any, capture: Any) -> tuple[Any, dict[str, Any]]:
    from sqpack.fractional.certificate import Certificate
    from sqpack.fractional.colgen import (
        Rows, SiteSet, dual_squares, orbit_column, rationalise_sites,
        site_set_from_grids, site_set_from_points, solve_rows,
    )
    from sqpack.fractional.generate import net_half_tangents
    from sqpack.fractional.hybrid_pricing import price_full

    if config["mode"] == "interleaved":
        from sqpack.fractional.hybrid_interleaved import generate_interleaved
        return generate_interleaved(side, config, seeds, directory, deadline, phases, capture)
    if config["mode"] != "batched":
        raise ValueError("unknown hybrid engine mode")
    shrink = Fraction(config["shrink"])
    tangents = net_half_tangents(Fraction(config["angle_limit"]), config["direction_steps"])
    grid = site_set_from_grids(side, tuple(config["grid_counts"]), Fraction(1, 2))
    sites = site_set_from_points(side, set(grid.positions()) | set(seeds))
    rows = Rows()
    details: dict[str, Any] = {"converged": False, "objective": None, "rounds": 0, "stopped": "budget", "telemetry": []}
    candidate = None
    context = ProcessPoolExecutor(max_workers=config["workers"] - 1) if config["workers"] > 1 else nullcontext(None)
    with context as pool:
        for iteration in range(config["column_rounds"]):
            if time.perf_counter() >= deadline:
                break
            solution = solve_rows(sites, shrink, tangents, rows, max_rounds=config["row_rounds"],
                rows_per_direction=config["rows_per_direction"], deadline=deadline,
                direction_executor=pool, phase_callback=phases)
            details.update(rounds=iteration + 1, objective=solution.objective,
                           converged=solution.converged, stopped=solution.stopped)
            capture(sites, solution.weights)
            if not solution.converged:
                break
            atoms = rationalise_sites(sites, solution.weights, scale=config["scale"])
            candidate = Certificate(12, side, shrink, atoms, tangents) if atoms else None
            if (candidate is not None and candidate.total_mass < 12) or iteration + 1 == config["column_rounds"] or time.perf_counter() >= deadline:
                break
            weighted = dual_squares(rows, solution.duals, tangents, side, shrink,
                                    support_cap=None, denominator=10**12)
            phases("pricing", "start")
            found, telemetry = price_full(sites, weighted, wanted=config["columns_per_round"],
                deadline=min(deadline, time.perf_counter() + config["pricing_seconds"]),
                grid_steps=config["pricing_grid_steps"], arrangement_rows=config["arrangement_rows"])
            phases("pricing", "end")
            telemetry.update(iteration=iteration, positive_dual_rows=int(np.count_nonzero(solution.duals > 1e-9)),
                             full_dual_mass=float(solution.duals.sum()), inserted=0)
            added = []
            for point in found:
                column = orbit_column(rows, point.orbit, tangents, shrink)
                actual_cost = len(point.orbit) - float(solution.duals @ column)
                if actual_cost < -1e-8:
                    added.append((point, column))
            telemetry["inserted"] = len(added)
            details["telemetry"].append(telemetry)
            with (directory / "pricing.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps(telemetry, allow_nan=False) + "\n")
            if not added:
                details["stopped"] = "bounded pricing found no useful candidate; not a method ceiling"
                break
            sites = SiteSet(side, (*sites.orbits, *(point.orbit for point, _ in added)))
            for _, column in added:
                rows.add_column(column)
            candidate = None
    details.update(rows=len(rows), candidate_orbits=len(sites.orbits), candidate_points=sites.size)
    return candidate, details
