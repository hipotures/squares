"""Compare interval compaction against the original full reachable matrix."""
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.generate import (  # noqa: SLF001
    _least_finite_indices, _reachable_values, direction_net, event_grid,
)
from sqpack.fractional.colgen import site_set_from_grids


def main():
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
    sites = site_set_from_grids(case.outer_side, grids, case.inset)
    points = sites.points()
    directions = direction_net(case.half_tangents())[::12]
    rng = np.random.default_rng(42)
    weights = [np.zeros(points.shape[0]),
               np.where(rng.random(points.shape[0]) < .08, rng.random(points.shape[0]), 0),
               np.where(rng.random(points.shape[0]) < .15, rng.random(points.shape[0]), 0)]
    checked = 0
    for w in weights:
        for direction in directions:
            cells = event_grid(points, w, direction, float(case.outer_side),
                               float(case.square_side))
            values, row_ids, firsts, offsets = _reachable_values(cells)
            length = np.diff(np.append(offsets, values.size))
            indices = np.concatenate([
                row_ids[slot] * cells.mass.shape[1] + np.arange(firsts[slot], firsts[slot] + int(width))
                for slot, width in enumerate(length)
            ]) if length.size else np.empty(0, dtype=np.intp)
            expected_indices = np.flatnonzero(cells.reachable)
            if not np.array_equal(indices, expected_indices):
                raise AssertionError("reachability differs")
            if not np.array_equal(values, cells.mass.ravel()[indices]):
                raise AssertionError("masses differ")
            scored = np.where(cells.reachable, cells.mass, np.inf).ravel()
            zero = not np.any(w)
            expected = _least_finite_indices(scored, 13, zero_weight_grid=zero)
            actual = indices[_least_finite_indices(values, 13, zero_weight_grid=zero)]
            if not np.array_equal(actual, expected):
                raise AssertionError("candidate order differs")
            checked += 1
    result = {"directions_checked": checked, "reachability_exact": True,
              "candidate_order_exact": True}
    Path(__file__).with_name("interval_check.json").write_text(json.dumps(result, indent=2) + "\n")
    print(result)


if __name__ == "__main__":
    main()
