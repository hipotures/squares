"""Check slab compaction against full reachability and scored selection."""

from __future__ import annotations

import argparse
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.colgen import site_set_from_grids
from sqpack.fractional.corner_clip import CornerClip
from sqpack.fractional.generate import (
    _least_finite_indices,
    _reachable_values,
    direction_net,
    event_grid,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    points = site_set_from_grids(case.outer_side, grids, case.inset).points()
    directions = direction_net(case.half_tangents())[::12]
    rng = np.random.default_rng(42)
    weights = (
        np.zeros(points.shape[0]),
        np.where(rng.random(points.shape[0]) < 0.08, rng.random(points.shape[0]), 0),
        np.where(rng.random(points.shape[0]) < 0.15, rng.random(points.shape[0]), 0),
    )
    clips = (None, CornerClip(case.outer_side, case.square_side, Fraction(1, 4)))
    checked = 0
    reachable_total = 0
    for clip in clips:
        for weight in weights:
            for direction in directions:
                cells = event_grid(
                    points, weight, direction,
                    float(case.outer_side), float(case.square_side), clip=clip,
                )
                assert cells.reachable is not None
                values, row_ids, firsts, offsets = _reachable_values(cells)
                widths = np.diff(np.append(offsets, values.size))
                indices = np.concatenate([
                    row_ids[slot] * cells.mass.shape[1]
                    + np.arange(firsts[slot], firsts[slot] + int(width))
                    for slot, width in enumerate(widths)
                ]) if widths.size else np.empty(0, dtype=np.intp)
                expected_indices = np.flatnonzero(cells.reachable)
                if not np.array_equal(indices, expected_indices):
                    raise AssertionError("reachable cell sets differ")
                if not np.array_equal(values, cells.mass.ravel()[indices]):
                    raise AssertionError("reachable cell masses differ")
                scored = np.where(cells.reachable, cells.mass, np.inf).ravel()
                zero = not np.any(weight)
                expected = _least_finite_indices(scored, 13, zero_weight_grid=zero)
                actual = indices[
                    _least_finite_indices(values, 13, zero_weight_grid=zero)
                ]
                if not np.array_equal(actual, expected):
                    raise AssertionError("ordered candidate indices differ")
                checked += 1
                reachable_total += len(indices)
    report = {
        "direction_weight_clip_cases": checked,
        "directions_per_weight_clip": len(directions),
        "reachable_cells_examined": reachable_total,
        "reachable_cell_sets_equal": True,
        "masses_bitwise_equal": True,
        "ordered_candidates_equal": True,
        "clip_depths": [None, "1/4"],
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))  # noqa: T201 - diagnostic summary
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
