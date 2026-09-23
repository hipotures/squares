"""Compare production chunking with the accepted full solver state."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.sparse import load_npz

from devtools import bench_colgen
from sqpack.fractional import colgen

ROOT = Path(__file__).resolve().parent
PROFILE = ROOT.parent / "cpu-post-integration-profile" / "raw"


def main() -> None:
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side,
                                               inset=case.inset)
    fixture = np.load(PROFILE / "current-states.npz")
    expected_matrix = load_npz(PROFILE / "current-rows-csr.npz").toarray()
    control = json.loads((ROOT / "raw/control-w1/baseline-w1-s1.json").read_text())
    control_rounds = control["solves"][0]["timings"]
    results = []
    for workers in (1, 4, 8, 16):
        os.environ["PACK_JOBS"] = str(workers)
        sites = colgen.site_set_from_grids(case.outer_side, grids, case.inset)
        rows = colgen.Rows()
        timings: list[colgen.RoundTiming] = []
        weights = [np.zeros(len(sites.orbits))]
        original = colgen._PersistentLp.solve

        def capture(self, held):
            result = original(self, held)
            if result is not None:
                weights.append(result[0].copy())
            return result

        colgen._PersistentLp.solve = capture
        try:
            solution = colgen.solve_rows(sites, case.square_side,
                                         case.half_tangents(), rows,
                                         timings=timings, workers=workers)
        finally:
            colgen._PersistentLp.solve = original
        assert solution.converged and solution.rounds == 23 and len(rows) == 5842
        assert solution.objective == 12.217676366606236
        assert solution.least_covered == 0.9999999999998309
        assert np.array_equal(np.asarray(rows.directions), fixture["directions"])
        assert np.array_equal(np.asarray(rows.centres), fixture["centres"])
        matrix = rows.stacked()
        assert np.array_equal(matrix, expected_matrix)
        assert np.array_equal(np.stack(weights), fixture["weights"])
        assert np.array_equal(solution.weights, fixture["weights"][-1])
        observed_rounds = [asdict(t) for t in timings]
        for observed, expected in zip(observed_rounds, control_rounds, strict=True):
            for key in ("index", "rows_held", "rows_added", "violated", "support",
                        "objective"):
                value = round(observed[key], 6) if key == "objective" else observed[key]
                assert value == expected[key], (workers, key, observed, expected)
        results.append({
            "workers": workers, "rounds": solution.rounds, "rows": len(rows),
            "objective": solution.objective, "least_covered": solution.least_covered,
            "stopped": solution.stopped,
            "matrix_sha256": hashlib.sha256(matrix.tobytes()).hexdigest(),
            "directions_sha256": hashlib.sha256(
                np.asarray(rows.directions, dtype=np.int16).tobytes()).hexdigest(),
            "centres_sha256": hashlib.sha256(
                np.asarray(rows.centres, dtype=np.float64).tobytes()).hexdigest(),
            "round_decisions": [{k: t[k] for k in (
                "index", "rows_held", "rows_added", "violated", "support", "objective"
            )} for t in observed_rounds],
            "row_order_matrix_centres_weights_identical": True,
        })
    path = ROOT / "raw/correctness.json"
    path.write_text(json.dumps({"passed": True, "results": results}, indent=2) + "\n")
    print(json.dumps({"passed": True, "workers": [r["workers"] for r in results]}))


if __name__ == "__main__":
    main()
