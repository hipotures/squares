"""Check exact current-main solve outcomes at every baseline worker count."""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional.colgen import RoundTiming, Rows, site_set_from_grids, solve_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                                 inset=case.inset)
    captured = np.load(ROOT / "raw/current-states.npz")
    expected_matrix = load_npz(ROOT / "raw/current-rows-csr.npz").toarray()
    results = []
    for workers in (1, 4, 8, 16):
        os.environ["PACK_JOBS"] = str(workers)
        sites = site_set_from_grids(case.outer_side, grids, case.inset)
        rows = Rows()
        timings: list[RoundTiming] = []
        solution = solve_rows(sites, case.square_side, case.half_tangents(),
                              rows, timings=timings, workers=workers)
        matrix = rows.stacked()
        assert solution.converged and solution.rounds == 23 and len(rows) == 5842
        assert abs(solution.objective - 12.217676366606236) < 1e-9
        assert solution.least_covered >= 1 - 1e-9
        assert np.array_equal(np.asarray(rows.directions), captured["directions"])
        assert np.array_equal(np.asarray(rows.centres), captured["centres"])
        assert np.array_equal(matrix, expected_matrix)
        results.append({
            "workers": workers, "rounds": solution.rounds, "rows": len(rows),
            "objective": solution.objective, "least_covered": solution.least_covered,
            "stop_reason": solution.stopped, "row_order_identical": True,
            "centres_identical": True, "coefficient_matrix_identical": True,
            "round_decisions": [
                {"index": x.index, "rows_held": x.rows_held,
                 "rows_added": x.rows_added, "violated": x.violated,
                 "support": x.support, "objective": x.objective}
                for x in timings
            ],
        })
    data = {"results": results, "passed": True}
    (ROOT / "raw/baseline-correctness.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"passed": True, "results": [
        {key: value for key, value in result.items() if key != "round_decisions"}
        for result in results
    ]}, indent=2))


if __name__ == "__main__":
    main()
