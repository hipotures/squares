"""Check C row-major prefix arithmetic and final solve against current main."""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np
from candidate_prefix import candidate_event_grid, install_pool
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.colgen import RoundTiming, Rows, site_set_from_grids, solve_rows

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    stored = np.load(ROOT / "raw/current-states.npz")
    points, membership, weights = (
        stored[name] for name in ("points", "membership", "weights")
    )
    expected_matrix = load_npz(ROOT / "raw/current-rows-csr.npz").toarray()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    directions = generate.direction_net(case.half_tangents())
    cases = 0
    cells_compared = 0
    for index in (0, 1, 8, 18, 22):
        site_weights = weights[index][membership]
        for direction in directions:
            args = (points, site_weights, direction,
                    float(case.outer_side), float(case.square_side))
            reference = generate.event_grid(*args, build_reachable=False)
            candidate = candidate_event_grid(*args, build_reachable=False)
            for field in ("u", "v", "u_events", "v_events", "mass", "lows", "highs"):
                left, right = getattr(reference, field), getattr(candidate, field)
                assert np.array_equal(left.view(np.uint64), right.view(np.uint64)), (
                    index, direction.label, field
                )
            assert reference.domain == candidate.domain
            cases += 1
            cells_compared += reference.mass.size
    install_pool()
    results = []
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
        results.append({"workers": workers, "rounds": solution.rounds,
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
    data = {"event_grid_cases": cases, "mass_cells_compared_bitwise": cells_compared,
            "results": results, "passed": True}
    (ROOT / "raw/prefix-equivalence.json").write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps({"event_grid_cases": cases,
                      "mass_cells_compared_bitwise": cells_compared,
                      "results": [{k: v for k, v in item.items() if k != "round_decisions"}
                                  for item in results], "passed": True}, indent=2))


if __name__ == "__main__":
    main()
