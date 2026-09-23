"""Minimum-cell survey semantics, independent of NumPy's equal-key ordering."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from sqpack.fractional.generate import _least_finite_indices, placement_cells
from sqpack.fractional.model import rotation_from_half_tangent


def _reference(flat: np.ndarray, count: int) -> np.ndarray:
    finite = np.flatnonzero(np.isfinite(flat))
    return finite[np.lexsort((finite, flat[finite]))][:count]


def _policy_reference(
    flat: np.ndarray, count: int, *, zero_weight_grid: bool = False
) -> np.ndarray:
    if count <= 0:
        return np.empty(0, dtype=np.intp)
    if zero_weight_grid:
        zeros = np.flatnonzero(flat == 0)
        count = min(count, zeros.size)
        if count == 0:
            return zeros
        if count == 1:
            return zeros[:1]
        positions = [(index * (zeros.size - 1)) // (count - 1) for index in range(count)]
        return zeros[positions]
    return _reference(flat, count)


def test_captured_round_zero_ordered_zero_inf_pattern() -> None:
    # Losslessly copied from the preserved n=12 direction-26 capture. Its
    # ordered zero/+inf regions trigger the pathological SIMD argpartition.
    fixture = Path(__file__).with_name("fixtures") / "round0_selector_flat.npz"
    with np.load(fixture) as archive:
        flat = archive["flat"]
    assert flat.size == 1_555_009
    assert np.count_nonzero(flat == 0) == 1_013_715
    assert np.all((flat == 0) | np.isposinf(flat))
    selected = _least_finite_indices(flat, 13, zero_weight_grid=True)
    assert np.array_equal(selected, _policy_reference(flat, 13, zero_weight_grid=True))
    assert np.array_equal(selected, _least_finite_indices(flat, 13, zero_weight_grid=True))
    assert np.array_equal(flat[selected], np.zeros(13))

    shuffled = np.random.default_rng(20260923).permutation(flat)
    assert np.array_equal(
        _least_finite_indices(shuffled, 13, zero_weight_grid=True),
        _policy_reference(shuffled, 13, zero_weight_grid=True),
    )


def test_captured_late_round_floating_masses() -> None:
    # Direction 90 of the preserved round-18 n=12 capture, including its ties
    # and unreachable cells. This exercises the partition plus cutoff path.
    fixture = Path(__file__).with_name("fixtures") / "late_selector_flat.npz"
    with np.load(fixture) as archive:
        flat = archive["flat"]
    assert flat.size == 958_441
    assert np.count_nonzero(np.isfinite(flat)) == 723_917
    expected = _reference(flat, 13)
    assert np.array_equal(_least_finite_indices(flat, 13), expected)


def test_zero_weight_placements_do_not_call_argpartition(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("argpartition entered on a zero-weight grid")

    monkeypatch.setattr(np, "argpartition", forbidden)
    points = np.array([[x, y] for x in (1.0, 2.0, 3.0) for y in (1.0, 2.0, 3.0)])
    found = placement_cells(
        points,
        np.zeros(len(points)),
        rotation_from_half_tangent("0", Fraction(0)),
        4.0,
        1.0,
        keep=3,
    )
    assert len(found) == 3
    assert all(mass == 0 for mass, _, _, _ in found)


def test_cutoff_ties_use_ascending_flat_index() -> None:
    flat = np.array([4.0, 2.0, 1.0, 2.0, 0.0, 2.0, 1.0, np.inf])
    assert _least_finite_indices(flat, 4).tolist() == [4, 2, 6, 1]
    assert _least_finite_indices(flat, 6).tolist() == [4, 2, 6, 1, 3, 5]


def test_finite_infinite_all_equal_and_tiny_inputs() -> None:
    cases = (
        np.array([], dtype=float),
        np.array([np.inf]),
        np.array([np.nan, np.inf]),
        np.array([-np.inf, 2.0, 1.0, np.inf]),
        np.array([5.0]),
        np.array([np.inf, -2.0, np.inf, 1.0]),
        np.array([3.0, 3.0, 3.0, 3.0]),
        np.array([0.0, np.inf, 0.0, np.inf]),
        np.array([-0.0, 0.0, np.inf]),
    )
    for flat in cases:
        for count in (0, 1, 2, 3, 12):
            expected = _policy_reference(flat, count)
            assert np.array_equal(_least_finite_indices(flat, count), expected)
            assert np.array_equal(_least_finite_indices(flat, count), expected)
            assert np.array_equal(flat[expected], flat[_reference(flat, count)])
            if np.all((flat == 0) | np.isposinf(flat)):
                expected_zero = _policy_reference(flat, count, zero_weight_grid=True)
                assert np.array_equal(
                    _least_finite_indices(flat, count, zero_weight_grid=True), expected_zero
                )

    with pytest.raises(ValueError, match="zero-weight grid"):
        _least_finite_indices(np.array([0.0, 1.0]), 1, zero_weight_grid=True)


def test_randomized_minimum_selection_matches_stable_reference() -> None:
    rng = np.random.default_rng(20260923)
    for size in range(1, 41):
        for _ in range(30):
            flat = rng.normal(size=size)
            # Exercise exact ties, cutoff ties, unreachable cells and NaNs.
            for index in range(size):
                draw = rng.integers(0, 8)
                if draw < 3:
                    flat[index] = float(rng.integers(-2, 4))
                elif draw == 3:
                    flat[index] = np.inf
                elif draw == 4:
                    flat[index] = np.nan
            count = int(rng.integers(0, size + 4))
            selected = _least_finite_indices(flat, count)
            expected = _reference(flat, count)
            assert np.array_equal(flat[selected], flat[expected])
            assert np.array_equal(selected, _policy_reference(flat, count))
            assert selected.size == min(count, np.count_nonzero(np.isfinite(flat)))
            omitted = np.setdiff1d(np.flatnonzero(np.isfinite(flat)), selected)
            if selected.size and omitted.size:
                assert np.min(flat[omitted]) >= np.max(flat[selected])
