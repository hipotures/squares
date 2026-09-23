"""Capture the current compact score array at n=12 round 18, direction 26."""

from __future__ import annotations

import argparse
import json
import os
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.generate import direction_net


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--metadata", type=Path, required=True)
    args = parser.parse_args()
    os.environ["PACK_JOBS"] = "1"
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    directions = direction_net(case.half_tangents())
    target = 18 * len(directions) + 26
    original = generate._least_finite_indices  # noqa: SLF001 - capture seam
    calls = 0
    captured: np.ndarray | None = None

    def capture(
        flat: np.ndarray, count: int, *, zero_weight_grid: bool = False
    ) -> np.ndarray:
        nonlocal calls, captured
        if calls == target:
            captured = flat.copy()
        calls += 1
        return original(flat, count, zero_weight_grid=zero_weight_grid)

    generate._least_finite_indices = capture  # noqa: SLF001 - capture seam
    try:
        run, _sites, _rows, solution = bench_colgen._row_run(  # noqa: SLF001
            case, grids, max_rounds=60, rows_per_direction=3
        )
    finally:
        generate._least_finite_indices = original  # noqa: SLF001 - capture seam
    if captured is None:
        raise RuntimeError(f"selection call {target} was not reached")
    np.savez_compressed(args.out, flat=captured)
    metadata = {
        "selection_call": target,
        "total_selection_calls": calls,
        "round": 18,
        "direction": 26,
        "direction_count": len(directions),
        "flat_size": int(captured.size),
        "finite_count": int(np.isfinite(captured).sum()),
        "dtype": str(captured.dtype),
        "rounds": run.rounds,
        "rows": run.rows,
        "objective": solution.objective,
        "least_covered": solution.least_covered,
        "stopped": solution.stopped,
    }
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata, indent=2))  # noqa: T201 - capture summary
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
