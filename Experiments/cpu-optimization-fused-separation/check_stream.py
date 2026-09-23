"""Compare streamed mass and candidate order with the base materialized path."""
import json
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.colgen import site_set_from_grids
from sqpack.fractional.generate import _least_finite_indices, direction_net, event_grid  # noqa: SLF001


def main():
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
    sites = site_set_from_grids(case.outer_side, grids, case.inset)
    points = sites.points()
    rng = np.random.default_rng(42)
    weights = [np.zeros(points.shape[0]),
               np.where(rng.random(points.shape[0]) < .08, rng.random(points.shape[0]), 0),
               np.where(rng.random(points.shape[0]) < .15, rng.random(points.shape[0]), 0)]
    directions = direction_net(case.half_tangents())[::12]
    checked = 0
    for w in weights:
        for direction in directions:
            base = event_grid(points, w, direction, float(case.outer_side), float(case.square_side))
            streamed = event_grid(points, w, direction, float(case.outer_side),
                                  float(case.square_side), stream_keep=13)
            if not np.array_equal(base.mass, streamed.mass):
                raise AssertionError("prefix masses differ")
            scored = np.where(base.reachable, base.mass, np.inf).ravel()
            expected = _least_finite_indices(scored, 13, zero_weight_grid=not np.any(w))
            if not np.array_equal(expected, streamed.candidate_order):
                raise AssertionError("ordered candidates differ")
            checked += 1
    report = {"directions_checked": checked, "mass_bitwise_equal": True,
              "candidate_order_equal": True}
    Path(__file__).with_name("stream_check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(report)


if __name__ == "__main__":
    main()
