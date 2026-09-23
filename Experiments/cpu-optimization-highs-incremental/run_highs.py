"""Research-only full n=12 solver using one incremental HiGHS model."""
import argparse
import json
import sys
import resource
from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import colgen

from bench_lp import Incremental

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "packing/benchmarks/round0_selector"))
from solver_benchmark import _direction_task, _parallel_solve_rows  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()
    original = colgen.solve_lp
    models = {}
    lp_rounds = []
    captured = {}

    def incremental(sites, rows):
        matrix = rows.stacked()
        if "model" not in models:
            models["model"] = Incremental(sites.sizes())
        update, solve, weights, duals, value, status = models["model"].solve(matrix)
        lp_rounds.append({"rows": len(rows), "update_seconds": update,
                          "solve_seconds": solve, "objective": value,
                          "minimum_coverage": float(np.min(matrix @ weights)),
                          "status": status})
        if status != "HighsModelStatus.kOptimal":
            return None
        return weights, np.maximum(duals, 0), value

    def timed_solve(*positional, **keywords):
        if args.workers == 1:
            result = original_rows(*positional, **keywords)
        else:
            with ProcessPoolExecutor(max_workers=args.workers) as pool:
                colgen.__dict__["_DIRECTION_POOL"] = pool
                colgen.__dict__["_direction_task"] = _direction_task
                try:
                    result = parallel_rows(*positional, **keywords)
                finally:
                    del colgen.__dict__["_DIRECTION_POOL"]
                    del colgen.__dict__["_direction_task"]
        captured["least_covered"] = result.least_covered
        captured["round_timings_exact"] = [vars(t) if hasattr(t, "__dict__") else {
            "index": t.index, "separation_seconds": t.separation_seconds,
            "lp_seconds": t.lp_seconds, "rows_held": t.rows_held,
            "rows_added": t.rows_added, "violated": t.violated,
            "support": t.support, "objective": t.objective}
            for t in keywords["timings"]]
        return result

    original_rows = bench_colgen.solve_rows
    parallel_rows = _parallel_solve_rows() if args.workers > 1 else None
    colgen.solve_lp = incremental
    bench_colgen.solve_rows = timed_solve
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
        report = bench_colgen.bench_rounds(case, grids, price=False)
    finally:
        colgen.solve_lp = original
        bench_colgen.solve_rows = original_rows
    report.update(captured)
    report["lp_rounds"] = lp_rounds
    report["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["workers"] = args.workers
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"wall": report["row_run"]["seconds"],
                      "rounds": report["row_run"]["rounds"],
                      "rows": report["row_run"]["rows"],
                      "objective": report["row_run"]["objective"],
                      "least_covered": report["least_covered"]}, indent=2))


if __name__ == "__main__":
    main()
