"""Long-sample n=12 production benchmark. Run from packing/ with thread caps."""

from __future__ import annotations

import argparse
import json
import math
import os
import resource
import time
from fractions import Fraction
from pathlib import Path

from devtools import bench_colgen

ROOT = Path(__file__).resolve().parents[1]


def machine_load() -> dict[str, object]:
    memory = Path("/proc/meminfo").read_text().splitlines()
    return {
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "loadavg": os.getloadavg(),
        "mem_available_kib": next(
            int(line.split()[1]) for line in memory if line.startswith("MemAvailable:")
        ),
        "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
    }


def cpu_usage() -> tuple[float, float, int, int]:
    parent = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return (
        parent.ru_utime + parent.ru_stime,
        children.ru_utime + children.ru_stime,
        parent.ru_minflt,
        children.ru_minflt,
    )


def solve(case: bench_colgen.Case, grids: tuple[int, ...]) -> dict[str, object]:
    report = bench_colgen.bench_rounds(case, grids, price=False)
    run = report["row_run"]
    assert run["rounds"] == 23 and run["rows"] == 5842, run
    assert abs(run["objective"] - 12.217676366606236) < 1e-9, run
    assert run["stopped"] == "converged: every placement covers mass 1", run
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=20)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "raw")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    assert args.workers > 0
    os.environ["PACK_JOBS"] = str(args.workers)
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    warm_start = time.perf_counter()
    solve(case, grids)
    warm_wall = time.perf_counter() - warm_start
    repeats = max(1, math.ceil(args.target_seconds / warm_wall))
    if warm_wall * repeats > 60:
        repeats = max(1, int(60 / warm_wall))
    for sample in range(1, args.samples + 1):
        load_before = machine_load()
        before = cpu_usage()
        start = time.perf_counter()
        reports = [solve(case, grids) for _ in range(repeats)]
        batch_wall = time.perf_counter() - start
        after = cpu_usage()
        assert batch_wall >= 10, (args.workers, sample, batch_wall)
        result = {
            "workers": args.workers,
            "sample": sample,
            "warmup_wall_seconds": warm_wall,
            "repeats": repeats,
            "load_before": load_before,
            "batch_wall_seconds": batch_wall,
            "normalized_batch_wall_seconds": batch_wall / repeats,
            "parent_cpu_seconds": after[0] - before[0],
            "child_cpu_seconds": after[1] - before[1],
            "parent_minor_faults": after[2] - before[2],
            "child_minor_faults": after[3] - before[3],
            "peak_parent_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "solves": [report["row_run"] for report in reports],
            "thread_limits": {
                key: os.environ.get(key)
                for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
            },
        }
        path = args.output_dir / f"baseline-w{args.workers}-s{sample}.json"
        path.write_text(json.dumps(result, indent=2) + "\n")
        print(
            json.dumps({
                "workers": args.workers,
                "sample": sample,
                "batch_wall": round(batch_wall, 3),
                "per_solve": round(batch_wall / repeats, 3),
                "separation": round(
                    sum(run["separation_seconds"] for run in result["solves"]) / repeats, 3
                ),
                "lp": round(sum(run["lp_seconds"] for run in result["solves"]) / repeats, 3),
            }),
            flush=True,
        )


if __name__ == "__main__":
    main()
