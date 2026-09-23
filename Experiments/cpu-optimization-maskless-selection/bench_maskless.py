"""Compare full-mask scoring and interval compaction on a real site geometry."""
import json
import statistics
import time
import tracemalloc
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.colgen import site_set_from_grids
from sqpack.fractional.generate import (  # noqa: SLF001
    _least_finite_indices, _reachable_values, direction_net, event_grid,
)


def sample(fn, repeats=30):
    for _ in range(3):
        fn()
    times = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        fn()
        times.append((time.perf_counter_ns() - start) / 1e6)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    fn()
    peak = tracemalloc.get_traced_memory()[1] - before
    tracemalloc.stop()
    return {"median_ms": statistics.median(times), "min_ms": min(times),
            "max_ms": max(times), "peak_extra_bytes": peak}


def main():
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(case.outer_side, case.square_side, inset=case.inset)
    sites = site_set_from_grids(case.outer_side, grids, case.inset)
    points = sites.points()
    rng = np.random.default_rng(211)
    weights = np.where(rng.random(points.shape[0]) < .16, rng.random(points.shape[0]), 0)
    direction = direction_net(case.half_tangents())[26]
    cells = event_grid(points, weights, direction, float(case.outer_side), float(case.square_side))

    def baseline():
        scored = np.where(cells.reachable, cells.mass, np.inf).ravel()
        return _least_finite_indices(scored, 13)

    def compact():
        values, row_ids, firsts, offsets = _reachable_values(cells)
        local = _least_finite_indices(values, 13)
        slots = np.searchsorted(offsets, local, side="right") - 1
        return row_ids[slots] * cells.mass.shape[1] + firsts[slots] + local - offsets[slots]

    expected, actual = baseline(), compact()
    if not np.array_equal(expected, actual):
        raise AssertionError("selected candidate order differs")
    result = {"shape": cells.mass.shape, "reachable_cells": int(cells.reachable.sum()),
              "selected_equal": True, "baseline": sample(baseline), "compact": sample(compact)}
    Path(__file__).with_name("operation.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
