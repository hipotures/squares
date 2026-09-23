"""The production pool must leave row decisions in direction order."""

from concurrent.futures import ProcessPoolExecutor
from fractions import Fraction
from typing import cast

import numpy as np
import pytest

from sqpack.fractional import colgen
from sqpack.fractional.colgen import Rows, site_set_from_grids, solve_rows
from sqpack.fractional.generate import direction_net, net_half_tangents


def test_direction_pool_preserves_partial_trajectory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PACK_JOBS", raising=False)
    outer, side = Fraction(11, 5), Fraction(24, 25)
    sites = site_set_from_grids(outer, (7,), Fraction(1, 2))
    tangents = net_half_tangents(Fraction(207107, 500000), 12)
    outcomes = []
    for workers in (1, 2):
        rows = Rows()
        result = solve_rows(
            sites, side, tangents, rows, workers=workers, max_rounds=4, rows_per_direction=2
        )
        outcomes.append((result, rows))
    (serial, serial_rows), (parallel, parallel_rows) = outcomes
    assert serial.rounds == parallel.rounds
    assert serial.stopped == parallel.stopped
    assert serial.objective == parallel.objective
    assert serial.least_covered == parallel.least_covered
    assert serial_rows.directions == parallel_rows.directions
    assert serial_rows.centres == parallel_rows.centres
    np.testing.assert_array_equal(serial_rows.stacked(), parallel_rows.stacked())
    np.testing.assert_array_equal(serial.weights, parallel.weights)
    np.testing.assert_array_equal(serial.duals, parallel.duals)


def test_workers_must_be_positive() -> None:
    sites = site_set_from_grids(Fraction(11, 5), (7,), Fraction(1, 2))
    with pytest.raises(ValueError, match="workers must be positive"):
        solve_rows(sites, Fraction(24, 25), (Fraction(0),), Rows(), workers=0)


@pytest.mark.parametrize("count", [0, 1, 3, 4, 5, 9])
def test_ordered_chunks_include_final_partial_chunk(
    count: int,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []

    def fake_placement(_points, _weights, direction, _outer, _side, *, keep, clip):
        assert keep == 3
        assert clip is None
        return [(float(direction.label), 0.0, 0.0, np.empty(0, dtype=int))]

    class FakePool:
        def map(self, fn, tasks):
            for task in tasks:
                calls.append(len(task[2]))
                yield fn(task)

    monkeypatch.setattr(colgen, "placement_cells", fake_placement)
    directions = direction_net(tuple(Fraction(i, 100) for i in range(count)))
    results = list(
        colgen._ordered_direction_chunks(  # noqa: SLF001
            cast(ProcessPoolExecutor, FakePool()),
            np.empty((0, 2)),
            np.empty(0),
            directions,
            outer=2.0,
            side=1.0,
            keep=3,
            clip=None,
        )
    )
    assert [result[0][0] for result in results] == list(map(float, range(count)))
    assert calls == [min(4, count - start) for start in range(0, count, 4)]


def test_chunk_worker_exception_propagates() -> None:
    directions = direction_net((Fraction(0),))
    with ProcessPoolExecutor(max_workers=2) as pool, pytest.raises(IndexError):
        list(
            colgen._ordered_direction_chunks(  # noqa: SLF001
                pool,
                np.empty((1, 0)),
                np.ones(1),
                directions,
                outer=2.0,
                side=1.0,
                keep=3,
                clip=None,
            )
        )
