"""The production pool must leave row decisions in direction order."""
from fractions import Fraction

import numpy as np
import pytest

from sqpack.fractional.colgen import Rows, site_set_from_grids, solve_rows
from sqpack.fractional.generate import net_half_tangents


def test_direction_pool_preserves_partial_trajectory(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PACK_JOBS", raising=False)
    outer, side = Fraction(11, 5), Fraction(24, 25)
    sites = site_set_from_grids(outer, (7,), Fraction(1, 2))
    tangents = net_half_tangents(Fraction(207107, 500000), 12)
    outcomes = []
    for workers in (1, 2):
        rows = Rows()
        result = solve_rows(sites, side, tangents, rows, workers=workers,
                            max_rounds=4, rows_per_direction=2)
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
