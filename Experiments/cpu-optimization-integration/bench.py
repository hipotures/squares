"""Controlled n=12 production row-generator benchmark.

Run from packing/ with PYTHONPATH=. and the three BLAS/OpenMP limits set to 1.
The row-run timer excludes the optional dual-pricing phase.
"""

from __future__ import annotations

import argparse
import json
import os
import resource
from fractions import Fraction
from pathlib import Path

from devtools import bench_colgen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    os.environ["PACK_JOBS"] = str(args.workers)
    captured: dict[str, object] = {}
    original = bench_colgen.solve_rows

    def record_solve(*positional: object, **keywords: object) -> object:
        solution = original(*positional, **keywords)
        captured["least_covered"] = solution.least_covered
        captured["round_timings_exact"] = [
            {
                "index": entry.index,
                "separation_seconds": entry.separation_seconds,
                "lp_seconds": entry.lp_seconds,
                "rows_held": entry.rows_held,
                "rows_added": entry.rows_added,
                "violated": entry.violated,
                "support": entry.support,
                "objective": entry.objective,
            }
            for entry in keywords["timings"]
        ]
        return solution

    bench_colgen.solve_rows = record_solve
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(
            case.outer_side, case.square_side, inset=case.inset
        )
        report = bench_colgen.bench_rounds(case, grids, price=False)
    finally:
        bench_colgen.solve_rows = original
    report.update(captured)
    report["workers_requested"] = args.workers
    report["peak_parent_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["thread_limits"] = {
        name: os.environ.get(name)
        for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    row_run = report["row_run"]
    print(json.dumps({  # noqa: T201 - command-line benchmark summary
        "workers": args.workers,
        "wall": row_run["seconds"],
        "separation": row_run["separation_seconds"],
        "lp": row_run["lp_seconds"],
        "rounds": row_run["rounds"],
        "rows": row_run["rows"],
        "objective": row_run["objective"],
        "least_covered": report["least_covered"],
        "stopped": row_run["stopped"],
    }, indent=2))


if __name__ == "__main__":
    main()
