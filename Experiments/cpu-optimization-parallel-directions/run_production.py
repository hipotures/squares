"""End-to-end production direction-pool benchmark; PACK_JOBS sets workers."""
import argparse
import json
import os
import resource
from fractions import Fraction
from pathlib import Path

from devtools import bench_colgen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    os.environ["PACK_JOBS"] = str(args.workers)
    original = bench_colgen.solve_rows
    captured = {}

    def solve(*positional, **keywords):
        result = original(*positional, **keywords)
        captured["least_covered"] = result.least_covered
        captured["round_timings_exact"] = [{
            "index": t.index, "separation_seconds": t.separation_seconds,
            "lp_seconds": t.lp_seconds, "rows_held": t.rows_held,
            "rows_added": t.rows_added, "violated": t.violated,
            "support": t.support, "objective": t.objective}
            for t in keywords["timings"]]
        return result

    bench_colgen.solve_rows = solve
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
        report = bench_colgen.bench_rounds(case, grids, price=False)
    finally:
        bench_colgen.solve_rows = original
    report.update(captured)
    report["workers"] = args.workers
    report["peak_rss_kib"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"workers": args.workers, "wall": report["row_run"]["seconds"],
                      "separation": report["row_run"]["separation_seconds"],
                      "lp": report["row_run"]["lp_seconds"],
                      "rounds": report["row_run"]["rounds"],
                      "rows": report["row_run"]["rows"],
                      "objective": report["row_run"]["objective"],
                      "least_covered": report["least_covered"]}, indent=2))


if __name__ == "__main__":
    main()
