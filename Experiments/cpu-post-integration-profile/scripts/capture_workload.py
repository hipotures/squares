"""Capture current-main LP and separation states for repeated in-memory replays."""

from __future__ import annotations

import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix, save_npz

from devtools import bench_colgen
from sqpack.fractional import colgen

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    os.environ["PACK_JOBS"] = "1"
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    counts = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    sites = colgen.site_set_from_grids(case.outer_side, counts, case.inset)
    rows = colgen.Rows()
    timings: list[colgen.RoundTiming] = []
    weights = [np.zeros(len(sites.orbits), dtype=float)]
    row_counts: list[int] = []
    original = colgen._PersistentLp.solve

    def capture(self: colgen._PersistentLp, held: colgen.Rows):
        result = original(self, held)
        assert result is not None
        weights.append(result[0].copy())
        row_counts.append(len(held))
        return result

    colgen._PersistentLp.solve = capture
    try:
        solved = colgen.solve_rows(
            sites, case.square_side, case.half_tangents(), rows, timings=timings,
            workers=1,
        )
    finally:
        colgen._PersistentLp.solve = original
    assert solved.converged and solved.rounds == 23 and len(rows) == 5842
    assert len(weights) == solved.rounds and len(row_counts) == solved.rounds - 1
    assert abs(solved.objective - 12.217676366606236) < 1e-9
    np.savez_compressed(
        ROOT / "raw/current-states.npz",
        weights=np.stack(weights), row_counts=np.array(row_counts, dtype=np.int32),
        points=sites.points(), membership=sites.membership(), costs=sites.sizes(),
        directions=np.array(rows.directions, dtype=np.int16),
        centres=np.array(rows.centres, dtype=float),
    )
    matrix = csr_matrix(rows.stacked())
    save_npz(ROOT / "raw/current-rows-csr.npz", matrix, compressed=True)
    metadata = {
        "case": case.label(), "grids": counts, "rounds": solved.rounds,
        "rows": len(rows), "objective": solved.objective,
        "least_covered": solved.least_covered, "stop_reason": solved.stopped,
        "site_count": sites.size, "orbits": len(sites.orbits),
        "matrix_shape": matrix.shape, "matrix_nnz": matrix.nnz,
        "rounds_trace": [
            {"round": t.index, "rows_held": t.rows_held, "support": t.support,
             "separation_seconds": t.separation_seconds, "lp_seconds": t.lp_seconds}
            for t in timings
        ],
    }
    (ROOT / "raw/current-states.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({key: metadata[key] for key in (
        "rounds", "rows", "objective", "least_covered", "matrix_shape", "matrix_nnz"
    )}, indent=2))


if __name__ == "__main__":
    main()
