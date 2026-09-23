#!/usr/bin/env python3
"""Temporary n=12 direction-process benchmark; changes no repository files."""

from __future__ import annotations

import argparse
import inspect
import json
import multiprocessing as mp
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

PACKING_ROOT = Path("/home/user/DEV/squares/packing")
sys.path.insert(0, str(PACKING_ROOT))

from devtools import bench_colgen  # noqa: E402
from sqpack.fractional import colgen  # noqa: E402
from sqpack.fractional.generate import placement_cells  # noqa: E402


def _direction_task(args):
    points, site_weights, direction, outer, side, keep, clip = args
    return placement_cells(
        points, site_weights, direction, outer, side, keep=keep, clip=clip
    )


def _parallel_solve_rows():
    source = inspect.getsource(colgen.solve_rows)
    old = """        for index, direction in enumerate(directions):
            for mass, cu, cv, covers in placement_cells(
                points,
                site_weights,
                direction,
                outer,
                side,
                keep=rows_per_direction,
                clip=clip,
            ):
"""
    new = """        tasks = (
            (points, site_weights, direction, outer, side, rows_per_direction, clip)
            for direction in directions
        )
        for index, found in enumerate(_DIRECTION_POOL.map(_direction_task, tasks)):
            for mass, cu, cv, covers in found:
"""
    if source.count(old) != 1:
        raise RuntimeError("solve_rows direction loop no longer matches this benchmark")
    namespace = {}
    exec(source.replace(old, new), colgen.__dict__, namespace)
    return namespace["solve_rows"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pid-file", type=Path)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("--workers must be positive")
    if args.pid_file:
        args.pid_file.write_text(f"{os.getpid()}\n")

    original = bench_colgen.solve_rows
    parallel = _parallel_solve_rows()
    captured = {}

    def timed_parallel_solve(*positional, **keywords):
        # The benchmark's _row_run timer surrounds this whole function. The
        # pool is created once, reused across rounds, and joined before return.
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            colgen.__dict__["_DIRECTION_POOL"] = pool
            colgen.__dict__["_direction_task"] = _direction_task
            try:
                solution = parallel(*positional, **keywords)
            finally:
                del colgen.__dict__["_DIRECTION_POOL"]
                del colgen.__dict__["_direction_task"]
        captured["least_covered"] = solution.least_covered
        captured["round_timings_exact"] = [
            {
                "index": t.index,
                "separation_seconds": t.separation_seconds,
                "lp_seconds": t.lp_seconds,
                "rows_held": t.rows_held,
                "rows_added": t.rows_added,
                "violated": t.violated,
                "support": t.support,
                "objective": t.objective,
            }
            for t in keywords["timings"]
        ]
        return solution

    bench_colgen.solve_rows = timed_parallel_solve
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(
            case.outer_side, case.square_side, inset=case.inset
        )
        report = bench_colgen.bench_rounds(case, grids)
    finally:
        bench_colgen.solve_rows = original
    report.update(captured)
    report["workers"] = args.workers
    report["worker_model"] = "ProcessPoolExecutor over directions"
    report["start_method"] = mp.get_start_method()
    report["parent_pid"] = os.getpid()
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
