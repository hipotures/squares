"""Verify vectorized interval results and complete solver state against main."""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np
from candidate_vectorized import install_pool, reachable_values_vectorized
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.colgen import RoundTiming, Rows, site_set_from_grids, solve_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    stored = np.load(ROOT / "raw/current-states.npz")
    weights, points, membership = (
        stored[name] for name in ("weights", "points", "membership")
    )
    expected_matrix = load_npz(ROOT / "raw/current-rows-csr.npz").toarray()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = generate.direction_net(case.half_tangents())
    compared = 0
    values = 0
    for orbit_weights in weights:
        site_weights = orbit_weights[membership]
        for direction in directions:
            cells = generate.event_grid(points, site_weights, direction,
                                        float(case.outer_side), float(case.square_side),
                                        build_reachable=False)
            reference = generate._reachable_values(cells)
            candidate = reachable_values_vectorized(cells)
            for a, b in zip(reference, candidate, strict=True):
                assert np.array_equal(a, b)
            compared += 1
            values += reference[0].size
    install_pool()
    outcomes = []
    counts = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                                 inset=case.inset)
    for workers in (1, 16):
        os.environ["PACK_JOBS"] = str(workers)
        sites = site_set_from_grids(case.outer_side, counts, case.inset)
        rows = Rows()
        timings: list[RoundTiming] = []
        solution = solve_rows(sites, case.square_side, case.half_tangents(),
                              rows, workers=workers, timings=timings)
        assert solution.converged and solution.rounds == 23 and len(rows) == 5842
        assert abs(solution.objective - 12.217676366606236) < 1e-9
        assert solution.least_covered >= 1 - 1e-9
        assert np.array_equal(np.asarray(rows.directions), stored["directions"])
        assert np.array_equal(np.asarray(rows.centres), stored["centres"])
        assert np.array_equal(rows.stacked(), expected_matrix)
        outcomes.append({"workers": workers, "rounds": solution.rounds,
                         "rows": len(rows), "objective": solution.objective,
                         "least_covered": solution.least_covered,
                         "stop_reason": solution.stopped,
                         "full_state_identical": True,
                         "round_decisions": [
                             {"index": x.index, "rows_held": x.rows_held,
                              "rows_added": x.rows_added, "violated": x.violated,
                              "support": x.support, "objective": x.objective}
                             for x in timings
                         ]})
    data = {"grid_cases": compared, "compact_values_compared": values,
            "all_arrays_bitwise_equal": True, "outcomes": outcomes,
            "passed": True}
    (ROOT / "raw/vectorized-equivalence.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"grid_cases": compared, "compact_values_compared": values,
                      "outcomes": [{k: v for k, v in item.items() if k != "round_decisions"}
                                   for item in outcomes],
                      "passed": True}, indent=2))


if __name__ == "__main__":
    main()
