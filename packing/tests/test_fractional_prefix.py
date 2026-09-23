"""The optional row-major CPU pass must match NumPy's column accumulation."""

from __future__ import annotations

import numpy as np
import pytest

from sqpack.fractional import _prefix_rows


@pytest.mark.parametrize("shape", [(0, 0), (1, 9), (7, 1), (31, 37), (979, 979)])
def test_axis0_prefix_is_bitwise_equal_to_numpy(shape: tuple[int, int]) -> None:
    random = np.random.default_rng(260923)
    grid = random.normal(size=shape)
    expected = np.add.accumulate(grid.copy(), axis=0)
    _prefix_rows.accumulate_axis0(grid)
    assert np.array_equal(grid.view(np.uint64), expected.view(np.uint64))


def test_axis0_prefix_fallback_is_bitwise_equal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    random = np.random.default_rng(260924)
    grid = random.normal(size=(43, 51))[:, ::2]
    expected = np.add.accumulate(grid.copy(), axis=0)
    _prefix_rows.accumulate_axis0(grid)
    assert np.array_equal(grid.view(np.uint64), expected.view(np.uint64))
    monkeypatch.setattr(_prefix_rows, "_NATIVE", None)
    grid = random.normal(size=(43, 51))
    expected = np.add.accumulate(grid.copy(), axis=0)
    _prefix_rows.accumulate_axis0(grid)
    assert np.array_equal(grid.view(np.uint64), expected.view(np.uint64))
