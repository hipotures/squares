"""Compare deterministic zero-mass tie surveys in only the first solver round."""

from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from devtools import bench_colgen
from sqpack.fractional import generate


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy", choices=("first", "spread", "hash"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    original = generate._least_finite_indices  # noqa: SLF001 - measured seam

    def select(flat: np.ndarray, count: int, *, zero_weight_grid: bool = False) -> np.ndarray:
        if not zero_weight_grid:
            return original(flat, count)
        finite = np.flatnonzero(flat == 0)
        count = min(count, finite.size)
        if args.policy == "first" or count == 0:
            return finite[:count]
        if args.policy == "spread":
            return finite[np.linspace(0, finite.size - 1, count, dtype=np.intp)]
        # A fixed multiplicative permutation of the index bits. This selects
        # spatially dispersed ties without a random seed or a full value sort.
        keys = finite.astype(np.uint64) * np.uint64(0x9E3779B97F4A7C15)
        chosen = np.argpartition(keys, count - 1)[:count]
        chosen = chosen[np.argsort(keys[chosen])]
        return finite[chosen]

    generate._least_finite_indices = select  # noqa: SLF001 - measured seam
    try:
        case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
        grids = bench_colgen.site_counts_for_side(
            case.outer_side, case.square_side, inset=case.inset
        )
        run, _sites, _rows, _solution = bench_colgen._row_run(  # noqa: SLF001
            case, grids, max_rounds=1, rows_per_direction=3
        )
    finally:
        generate._least_finite_indices = original  # noqa: SLF001 - restore seam
    report = {"policy": args.policy, "row_run": bench_colgen.asdict(run)}
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(report["row_run"])


if __name__ == "__main__":
    main()
