"""Adjacent production chunked solve versus the original one-direction mapping."""

from __future__ import annotations

import argparse
import json
import math
import os
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional import colgen

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT.parent / "cpu-post-integration-profile"
CHUNKED = colgen._ordered_direction_chunks


def reference(pool, points, weights, directions, *, outer, side, keep, clip):
    tasks = ((points, weights, direction, outer, side, keep, clip)
             for direction in directions)
    yield from pool.map(colgen._direction_task, tasks)


def configure(mode: str) -> None:
    colgen._ordered_direction_chunks = reference if mode == "reference" else CHUNKED


def solve(case, grids):
    report = bench_colgen.bench_rounds(case, grids, price=False)
    run = report["row_run"]
    assert run["rounds"] == 23 and run["rows"] == 5842
    assert abs(run["objective"] - 12.217676366606236) < 1e-9
    assert run["stopped"] == "converged: every placement covers mass 1"
    return run


def verify_full_state(case, grids) -> None:
    saved = np.load(PROFILE / "raw/current-states.npz")
    expected_matrix = load_npz(PROFILE / "raw/current-rows-csr.npz").toarray()
    sites = colgen.site_set_from_grids(case.outer_side, grids, case.inset)
    rows = colgen.Rows()
    solution = colgen.solve_rows(sites, case.square_side, case.half_tangents(), rows,
                                 workers=16)
    assert solution.converged and solution.rounds == 23 and len(rows) == 5842
    assert np.array_equal(np.asarray(rows.directions), saved["directions"])
    assert np.array_equal(np.asarray(rows.centres), saved["centres"])
    assert np.array_equal(rows.stacked(), expected_matrix)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-seconds", type=float, default=18)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--tag", default="")
    args = parser.parse_args()
    os.environ["PACK_JOBS"] = "16"
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                               inset=case.inset)
    configure("candidate")
    verify_full_state(case, grids)
    repeat_counts = {}
    for mode in ("reference", "candidate"):
        configure(mode)
        start = time.perf_counter()
        solve(case, grids)
        warm = time.perf_counter() - start
        repeat_counts[mode] = max(1, math.ceil(args.target_seconds / warm))
    if args.samples == 0:
        print(json.dumps({"full_state_identical": True, "warmup": repeat_counts}))
        return
    output = ROOT / "raw/paired"
    output.mkdir(parents=True, exist_ok=True)
    for sample in range(1, args.samples + 1):
        order = ("reference", "candidate") if sample != 2 else ("candidate", "reference")
        for mode in order:
            configure(mode)
            load = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "loadavg": os.getloadavg(),
                    "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip()}
            repeats = repeat_counts[mode]
            start = time.perf_counter()
            runs = [solve(case, grids) for _ in range(repeats)]
            batch = time.perf_counter() - start
            assert 10 <= batch <= 60, batch
            data = {"mode": mode, "sample": sample, "repeats": repeats,
                    "load_before": load, "batch_wall_seconds": batch,
                    "wall_per_solve_seconds": batch / repeats,
                    "separation_per_solve_seconds": sum(x["separation_seconds"] for x in runs)/repeats,
                    "lp_per_solve_seconds": sum(x["lp_seconds"] for x in runs)/repeats,
                    "solves": runs, "full_state_identical": True}
            (output / f"{mode}{args.tag}-s{sample}.json").write_text(
                json.dumps(data, indent=2)+"\n"
            )
            print(json.dumps({"mode": mode, "sample": sample,
                              "batch": batch, "wall": batch / repeats,
                              "separation": data["separation_per_solve_seconds"]}), flush=True)
    configure("reference")


if __name__ == "__main__":
    main()
