"""Adjacent long-batch main vs research CPU candidate comparison."""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import time
from fractions import Fraction

from baseline import ROOT, machine_load
from candidate_vectorized import CandidatePool, reachable_values_vectorized

from devtools import bench_colgen
from sqpack.fractional import colgen, generate

ORIGINAL_REACHABLE = generate._reachable_values
ORIGINAL_EVENT_GRID = generate.event_grid
ORIGINAL_POOL = colgen.ProcessPoolExecutor


def configure(mode: str, variant: str) -> None:
    generate._reachable_values = ORIGINAL_REACHABLE
    generate.event_grid = ORIGINAL_EVENT_GRID
    colgen.ProcessPoolExecutor = ORIGINAL_POOL
    if mode == "candidate":
        if variant == "vectorized":
            generate._reachable_values = reachable_values_vectorized
            colgen.ProcessPoolExecutor = CandidatePool
        else:
            from candidate_prefix import CandidatePool as PrefixPool
            from candidate_prefix import candidate_event_grid
            generate.event_grid = candidate_event_grid
            colgen.ProcessPoolExecutor = PrefixPool


def solve(case, grids):
    report = bench_colgen.bench_rounds(case, grids, price=False)
    run = report["row_run"]
    assert run["rounds"] == 23 and run["rows"] == 5842
    assert abs(run["objective"] - 12.217676366606236) < 1e-9
    assert run["stopped"] == "converged: every placement covers mass 1"
    return run


def cpu_usage() -> tuple[float, float]:
    parent = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return parent.ru_utime + parent.ru_stime, children.ru_utime + children.ru_stime


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--variant", choices=("vectorized", "prefix"), required=True)
    parser.add_argument("--target-seconds", type=float, default=20)
    args = parser.parse_args()
    assert args.workers in (1, 16)
    os.environ["PACK_JOBS"] = str(args.workers)
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                                 inset=case.inset)
    repeat_counts = {}
    for mode in ("reference", "candidate"):
        configure(mode, args.variant)
        t = time.perf_counter()
        solve(case, grids)
        warm = time.perf_counter() - t
        repeats = max(1, math.ceil(args.target_seconds / warm))
        if warm * repeats > 60:
            repeats = max(1, int(60 / warm))
        repeat_counts[mode] = (repeats, warm)
    for sample in (1, 2, 3):
        order = ("reference", "candidate") if sample != 2 else ("candidate", "reference")
        for mode in order:
            configure(mode, args.variant)
            repeats, warm = repeat_counts[mode]
            load_before = machine_load()
            before = cpu_usage()
            t = time.perf_counter()
            runs = [solve(case, grids) for _ in range(repeats)]
            batch_wall = time.perf_counter() - t
            after = cpu_usage()
            assert 10 <= batch_wall <= 60, (mode, sample, batch_wall)
            result = {
                "variant": args.variant, "mode": mode,
                "workers": args.workers, "sample": sample,
                "repeats": repeats, "warmup_wall_seconds": warm,
                "load_before": load_before, "batch_wall_seconds": batch_wall,
                "normalized_wall_seconds": batch_wall / repeats,
                "parent_cpu_seconds": after[0] - before[0],
                "child_cpu_seconds": after[1] - before[1],
                "solves": runs,
            }
            (ROOT / "raw" / f"{args.variant}-{mode}-w{args.workers}-s{sample}.json").write_text(
                json.dumps(result, indent=2) + "\n"
            )
            print(json.dumps({
                "mode": mode, "workers": args.workers, "sample": sample,
                "variant": args.variant,
                "batch_wall": round(batch_wall, 3),
                "per_solve": round(batch_wall / repeats, 3),
                "separation": round(sum(r["separation_seconds"] for r in runs) / repeats, 3),
            }), flush=True)
    configure("reference", args.variant)


if __name__ == "__main__":
    main()
