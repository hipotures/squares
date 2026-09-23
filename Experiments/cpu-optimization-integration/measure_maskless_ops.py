"""Measure mask/score selection against slab compaction on real site geometry."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from collections.abc import Callable
from fractions import Fraction
from pathlib import Path

import numpy as np

from devtools import bench_colgen
from sqpack.fractional.colgen import site_set_from_grids
from sqpack.fractional.generate import (
    _least_finite_indices,
    _reachable_values,
    direction_net,
    event_grid,
)


def sample(fn: Callable[[], np.ndarray], repeats: int = 30) -> dict[str, float | int]:
    for _ in range(3):
        fn()
    times = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        fn()
        times.append((time.perf_counter_ns() - started) / 1e6)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    fn()
    peak = tracemalloc.get_traced_memory()[1] - before
    tracemalloc.stop()
    return {
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "peak_extra_bytes": peak,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    case = bench_colgen.Case(n=12, outer_side=Fraction(99, 25))
    grids = bench_colgen.site_counts_for_side(
        case.outer_side, case.square_side, inset=case.inset
    )
    points = site_set_from_grids(case.outer_side, grids, case.inset).points()
    rng = np.random.default_rng(211)
    weights = np.where(rng.random(points.shape[0]) < 0.16, rng.random(points.shape[0]), 0)
    direction = direction_net(case.half_tangents())[26]
    cells = event_grid(
        points, weights, direction, float(case.outer_side), float(case.square_side)
    )
    assert cells.reachable is not None

    def baseline() -> np.ndarray:
        scored = np.where(cells.reachable, cells.mass, np.inf).ravel()
        return _least_finite_indices(scored, 13)

    def compact() -> np.ndarray:
        values, row_ids, firsts, offsets = _reachable_values(cells)
        local = _least_finite_indices(values, 13)
        slots = np.searchsorted(offsets, local, side="right") - 1
        return row_ids[slots] * cells.mass.shape[1] + firsts[slots] + local - offsets[slots]

    if not np.array_equal(baseline(), compact()):
        raise AssertionError("selected candidate order differs")
    report = {
        "shape": list(cells.mass.shape),
        "reachable_cells": int(cells.reachable.sum()),
        "selected_equal": True,
        "baseline": sample(baseline),
        "compact": sample(compact),
    }
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))  # noqa: T201 - diagnostic summary


if __name__ == "__main__":
    main()
