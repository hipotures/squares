"""Compare fresh SciPy LP with persistent HiGHS on the same n=12 row trajectory.

Run from packing/: uv run --frozen --no-dev --with highspy python ../Experiments/
cpu-optimization-highs-incremental/bench_lp.py --out /tmp/highs.json
"""
import argparse
import json
import time
from fractions import Fraction
from pathlib import Path

import highspy
import numpy as np
from scipy.sparse import csr_matrix

from devtools import bench_colgen
from sqpack.fractional import colgen


class Incremental:
    def __init__(self, costs, *, solver="simplex", presolve="on"):
        self.highs = highspy.Highs()
        self.highs.setOptionValue("output_flag", False)
        self.highs.setOptionValue("solver", solver)
        self.highs.setOptionValue("presolve", presolve)
        n = len(costs)
        self.highs.addCols(n, np.asarray(costs, dtype=float),
                           np.zeros(n), np.full(n, highspy.kHighsInf),
                           0, np.zeros(n + 1, dtype=np.int32),
                           np.empty(0, dtype=np.int32), np.empty(0))
        self.held = 0

    def solve(self, matrix):
        start = time.perf_counter()
        new = csr_matrix(-matrix[self.held:])
        count = new.shape[0]
        self.highs.addRows(count, np.full(count, -highspy.kHighsInf),
                           -np.ones(count),
                           new.nnz, new.indptr.astype(np.int32),
                           new.indices.astype(np.int32), new.data)
        self.held += count
        update = time.perf_counter() - start
        start = time.perf_counter()
        self.highs.run()
        solve = time.perf_counter() - start
        solution = self.highs.getSolution()
        return update, solve, np.asarray(solution.col_value), -np.asarray(solution.row_dual), self.highs.getObjectiveValue(), str(self.highs.getModelStatus())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = colgen.solve_lp
    models = {}
    rounds = []

    def compare(sites, rows):
        matrix = rows.stacked()
        if not models:
            costs = sites.sizes()
            models["simplex"] = Incremental(costs)
            models["ipm"] = Incremental(costs, solver="ipm")
            models["simplex_no_presolve"] = Incremental(costs, presolve="off")
        start = time.perf_counter()
        scipy_result = original(sites, rows)
        scipy_seconds = time.perf_counter() - start
        row = {"rows": len(rows), "scipy_seconds": scipy_seconds, "options": {}}
        for name, model in models.items():
            update, solve, weights, duals, objective, status = model.solve(matrix)
            row["options"][name] = {
                "update_seconds": update, "solve_seconds": solve,
                "objective": objective, "status": status,
                "objective_difference": objective - scipy_result[2],
                "weight_max_difference": float(np.max(np.abs(weights - scipy_result[0]))),
                "dual_max_difference": float(np.max(np.abs(duals - scipy_result[1]))),
                "minimum_coverage": float(np.min(matrix @ weights)),
            }
        rounds.append(row)
        return scipy_result

    colgen.solve_lp = compare
    bench_colgen.solve_rows.__globals__["solve_lp"] = compare
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
        report = bench_colgen.bench_rounds(case, grids, price=False)
    finally:
        colgen.solve_lp = original
    result = {"rounds": rounds, "row_run": report["row_run"],
              "highspy_version": highspy.HIGHS_VERSION_MAJOR if hasattr(highspy, "HIGHS_VERSION_MAJOR") else "unknown"}
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"lp_rounds": len(rounds), "scipy_total": sum(r["scipy_seconds"] for r in rounds),
                      "model_totals": {k: sum(r["options"][k]["update_seconds"] + r["options"][k]["solve_seconds"] for r in rounds) for k in models},
                      "solver_wall": report["row_run"]["seconds"]}, indent=2))


if __name__ == "__main__":
    main()
