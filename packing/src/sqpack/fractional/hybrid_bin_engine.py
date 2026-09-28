"""Variable-bin search with pinned exact separation and our persistent LP/pricing.

Only the external source's search Model and witness reader are reused. Neither
its floating rows nor a successful restricted LP is a certificate acceptance.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
import uuid
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from sqpack.fractional.hybrid_bins import (
    angle_bin, bin_count, bundle, common_denominator, export_integer,
)
from sqpack.fractional.hybrid_lp import AppendOnlyLp
from sqpack.fractional.hybrid_support import parse_measure


def external_search(root: Path) -> Any:
    from devtools.frontier_hybrid_external import checked_binary
    checked_binary(root)
    source = root / "s12/search/tighten.py"
    spec = importlib.util.spec_from_file_location("_hybrid_pinned_tighten", source)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the pinned external search adapter")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def pose_squares(rows: Any, duals: np.ndarray, side: Fraction, net: int) -> tuple[Any, ...]:
    """Full positive dual with each row's own half-side, for search pricing only."""
    from sqpack.fractional.colgen import Square
    result = []
    for (cx, cy, theta, half), value in zip(rows, duals, strict=True):
        if value <= 1e-9:
            continue
        k = round(net * math.tan(theta / 2))
        geom = angle_bin(net, k)
        x = Fraction.from_float(float(cx)) - side / 2
        y = Fraction.from_float(float(cy)) - side / 2
        c, s = geom.cosine, geom.sine
        result.append((Square(c, s, c * x + s * y, -s, c, -s * x + c * y,
                              Fraction.from_float(float(half))),
                       Fraction.from_float(float(value))))
    return tuple(result)


def generate_bins(side: Fraction, config: dict[str, Any], seeds: Any,
                  directory: Path, deadline: float, phases: Any) -> tuple[Any, dict[str, Any]]:
    from devtools.frontier_hybrid_external import EXTERNAL, checked_binary, minimum, run_logged
    from devtools.frontier_io import atomic_json
    from sqpack.fractional.colgen import SiteSet, site_set_from_points
    from sqpack.fractional.hybrid_pricing import price_full

    external = external_search(EXTERNAL)
    binary = checked_binary(EXTERNAL)
    net = config["bin_net"]
    count = bin_count(net)
    sites = site_set_from_points(side, set(seeds))
    if not sites.orbits:
        raise ValueError("bin search needs at least one exact source measure")
    denominator = common_denominator(side, sites.positions())
    width = int(side * denominator)
    model = external.Model(width, denominator, [
        np.asarray([[int(x * denominator), int(y * denominator)] for x, y in orbit],
                   dtype=np.int64) for orbit in sites.orbits
    ])
    warm = []
    for k in sorted({round(i * (count - 1) / 12) for i in range(13)}):
        geom = angle_bin(net, k)
        low, high = geom.centre_range(side)
        for cx in np.linspace(float(low), float(high), 13):
            for cy in np.linspace(float(low), float(high), 13):
                warm.append((cx, cy, 2 * math.atan(k / net), float(geom.square_side / 2)))
    model.add_rows(warm)
    owner = AppendOnlyLp(rhs=1.000002)
    details: dict[str, Any] = {"converged": False, "objective": None, "rounds": 0,
                               "stopped": "budget", "geometry": "variable-bin"}
    attempt = directory / ("bin-attempt-" + uuid.uuid4().hex)
    attempt.mkdir()
    details["attempt_directory"] = str(attempt)
    accepted_candidate = None
    for iteration in range(config["column_rounds"]):
        if time.perf_counter() >= deadline:
            break
        phases("lp", "start")
        weights, duals, objective = owner.solve(model.matrix(), model.sizes)
        phases("lp", "end")
        probe = attempt / f"probe-{iteration:04d}.txt"
        probe.write_text(export_integer(sites, weights, weight_scale=10**12,
                                       factor=Fraction(1_000_000, 1_000_001), up=False))
        witness = attempt / f"witness-{iteration:04d}.txt"
        if witness.exists():
            raise ValueError("probe path already exists; do not overwrite an earlier attempt")
        phases("separation", "start")
        code, text = run_logged(
            [str(binary), str(probe), "12", str(net), str(config["workers"]),
             str(config["rows_per_direction"]), str(witness)],
            attempt / f"probe-{iteration:04d}.log", deadline - time.perf_counter(),
        )
        phases("separation", "end")
        if code != 0:
            raise RuntimeError("exact separator failed operationally; inspect the probe log")
        covered = minimum(text)
        details.update(rounds=iteration + 1, objective=objective, converged=covered >= 1)
        atomic_json(directory / "search-support.json", {
            "schema": "hybrid-support/v1", "status": "SEED_ONLY", "outer_side": str(side),
            "atoms": [[str(x), str(y), "0"] for x, y in sites.positions()],
        })
        if covered >= 1:
            final_text = export_integer(sites, weights, weight_scale=config["scale"])
            measure = parse_measure(final_text.encode())
            if measure.mass < 12:
                accepted_candidate = bundle(final_text, net)
                details["stopped"] = "probe closed; candidate awaits the full independent gate"
                break
        if not witness.is_file():
            raise RuntimeError("exact separator did not produce its requested witness file")
        old_rows = len(model.rows)
        weighted = pose_squares(model.rows, duals, side, net)
        cut_rows = external.read_witnesses(str(witness), net)
        added = model.add_rows(cut_rows)
        row_info: dict[str, Any] = {"iteration": iteration, "objective": objective,
            "minimum_probe": str(covered), "added_rows": added, "inserted": 0,
            "dual_rows": len(weighted), "full_dual_mass": float(duals.sum())}
        tail = max(4, config["column_rounds"] // 4)
        if iteration + tail < config["column_rounds"] and time.perf_counter() < deadline:
            phases("pricing", "start")
            found, telemetry = price_full(
                sites, weighted, wanted=config["columns_per_round"],
                deadline=min(deadline, time.perf_counter() + config["pricing_seconds"]),
                grid_steps=config["pricing_grid_steps"], arrangement_rows=0,
                coordinate_denominator=denominator,
            )
            phases("pricing", "end")
            row_info.update(telemetry)
            for point in found:
                q = np.asarray(model.rows[:old_rows])
                c, s = np.cos(q[:, 2]), np.sin(q[:, 2])
                column = np.zeros(old_rows)
                for x, y in point.orbit:
                    first = np.abs((float(x) - q[:, 0]) * c + (float(y) - q[:, 1]) * s)
                    second = np.abs(-(float(x) - q[:, 0]) * s + (float(y) - q[:, 1]) * c)
                    column += np.maximum(first, second) <= q[:, 3] - external.TOL
                if len(point.orbit) - float(duals @ column) < -1e-8:
                    row_info["inserted"] += int(model.add_orbit(
                        int(point.point[0] * denominator), int(point.point[1] * denominator)))
            sites = SiteSet(side, tuple(tuple((Fraction(int(x), denominator),
                         Fraction(int(y), denominator)) for x, y in orbit)
                         for orbit in model.orb_int))
        with (directory / "pricing.jsonl").open("a", encoding="utf-8") as log:
            log.write(json.dumps(row_info, allow_nan=False) + "\n")
        if not added and not row_info["inserted"]:
            details["stopped"] = "no new row/column; not a proof of a method ceiling"
            break
    atomic_json(directory / "search-support.json", {
        "schema": "hybrid-support/v1", "status": "SEED_ONLY", "outer_side": str(side),
        "atoms": [[str(x), str(y), "0"] for x, y in sites.positions()],
    })
    details.update(rows=len(model.rows), candidate_points=sites.size,
                   candidate_orbits=len(sites.orbits), lp_models_created=1)
    return accepted_candidate, details
