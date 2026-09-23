"""Audit every production HiGHS point against its currently held rows."""

from __future__ import annotations

import argparse
import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import colgen


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    os.environ["PACK_JOBS"] = "1"
    records: list[dict[str, float | int | bool]] = []
    original = colgen._PersistentLp.solve  # noqa: SLF001 - diagnostic seam

    def audited(model: object, rows: colgen.Rows) -> tuple | None:
        solved = original(model, rows)
        if solved is None:
            return None
        weights, duals, value = solved
        matrix = rows.stacked()
        records.append({
            "rows": len(rows),
            "minimum_held_row_coverage": float(np.min(matrix @ weights)),
            "objective": value,
            "objective_from_weights": float(np.dot(model.highs.getLp().col_cost_, weights)),
            "dual_count": len(duals),
            "basis_valid": bool(model.highs.getBasis().valid),
        })
        return solved

    colgen._PersistentLp.solve = audited  # noqa: SLF001 - diagnostic seam
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(
            case.outer_side, case.square_side, inset=case.inset
        )
        run, _sites, rows, solution = bench_colgen._row_run(  # noqa: SLF001 - diagnostic seam
            case, grids, max_rounds=60, rows_per_direction=3
        )
    finally:
        colgen._PersistentLp.solve = original  # noqa: SLF001 - diagnostic seam
    report = {
        "lp_rounds": records,
        "minimum_held_row_coverage": min(
            record["minimum_held_row_coverage"] for record in records
        ),
        "all_bases_valid": all(record["basis_valid"] for record in records),
        "all_dual_lengths_match": all(
            record["rows"] == record["dual_count"] for record in records
        ),
        "maximum_objective_residual": max(
            abs(record["objective"] - record["objective_from_weights"])
            for record in records
        ),
        "rounds": run.rounds,
        "rows": len(rows),
        "objective": solution.objective,
        "least_covered": solution.least_covered,
        "stopped": solution.stopped,
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    summary = {key: value for key, value in report.items() if key != "lp_rounds"}
    print(json.dumps(summary, indent=2))  # noqa: T201
    return 0 if (
        report["minimum_held_row_coverage"] >= 1 - 1e-7
        and report["all_bases_valid"]
        and report["all_dual_lengths_match"]
        and report["maximum_objective_residual"] < 1e-7
        and solution.converged
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
