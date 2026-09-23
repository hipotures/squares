"""Compare complete production row trajectories at one and sixteen workers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    states = []
    for workers in (1, 16):
        os.environ["PACK_JOBS"] = str(workers)
        run, _sites, rows, solution = bench_colgen._row_run(  # noqa: SLF001 - validation seam
            case, grids, max_rounds=60, rows_per_direction=3
        )
        states.append((run, rows, solution))
    (serial_run, serial_rows, serial), (parallel_run, parallel_rows, parallel) = states
    matrix_a, matrix_b = serial_rows.stacked(), parallel_rows.stacked()
    checks = {
        "rows": len(serial_rows) == len(parallel_rows),
        "direction_order": serial_rows.directions == parallel_rows.directions,
        "centre_order": serial_rows.centres == parallel_rows.centres,
        "coefficient_matrix": np.array_equal(matrix_a, matrix_b),
        "weights": np.array_equal(serial.weights, parallel.weights),
        "duals": np.array_equal(serial.duals, parallel.duals),
        "objective": serial.objective == parallel.objective,
        "least_covered": serial.least_covered == parallel.least_covered,
        "stop_reason": serial.stopped == parallel.stopped,
        "rounded_round_trajectory": serial_run.timings == parallel_run.timings,
    }
    # Timings themselves naturally differ. Compare only decisions in each round.
    checks["round_decisions"] = [
        {key: value for key, value in timing.items() if key not in ("separation_s", "lp_s")}
        for timing in serial_run.timings
    ] == [
        {key: value for key, value in timing.items() if key not in ("separation_s", "lp_s")}
        for timing in parallel_run.timings
    ]
    del checks["rounded_round_trajectory"]
    report = {
        "checks": checks,
        "serial_matrix_sha256": digest(matrix_a.tobytes()),
        "parallel_matrix_sha256": digest(matrix_b.tobytes()),
        "serial_rounds": serial_run.rounds,
        "parallel_rounds": parallel_run.rounds,
        "serial_rows": serial_run.rows,
        "parallel_rows": parallel_run.rows,
        "objective": serial.objective,
        "least_covered": serial.least_covered,
        "stopped": serial.stopped,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))  # noqa: T201 - command-line diagnostic
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
