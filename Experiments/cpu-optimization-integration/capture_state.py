"""Hash a complete n=12 solver state for cross-checkpoint trajectory checks."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import colgen, generate


def digest(value: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(value).tobytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--label", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    os.environ["PACK_JOBS"] = str(args.workers)
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    run, _sites, rows, solution = bench_colgen._row_run(  # noqa: SLF001 - diagnostic seam
        case, grids, max_rounds=60, rows_per_direction=3
    )
    report = {
        "label": args.label,
        "workers": args.workers,
        "colgen_module": str(Path(colgen.__file__).resolve()),
        "generate_module": str(Path(generate.__file__).resolve()),
        "rounds": run.rounds,
        "rows": len(rows),
        "objective": solution.objective,
        "least_covered": solution.least_covered,
        "stopped": solution.stopped,
        "directions_sha256": digest(np.asarray(rows.directions, dtype=np.int32)),
        "centres_sha256": digest(np.asarray(rows.centres, dtype=np.float64)),
        "matrix_sha256": digest(rows.stacked()),
        "weights_sha256": digest(solution.weights),
        "duals_sha256": digest(solution.duals),
        "round_decisions": [
            {key: value for key, value in timing.items() if key not in ("separation_s", "lp_s")}
            for timing in run.timings
        ],
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    summary = {key: value for key, value in report.items() if key != "round_decisions"}
    print(json.dumps(summary, indent=2))  # noqa: T201


if __name__ == "__main__":
    main()
