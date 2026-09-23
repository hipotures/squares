"""The production LP owner appends constraints and retains the HiGHS basis."""

import highspy
import numpy as np

from sqpack.fractional.colgen import Rows, _PersistentLp


def test_persistent_lp_appends_rows_and_reoptimizes() -> None:
    rows = Rows(matrix=np.zeros((0, 2)))
    model = _PersistentLp(np.array([1.0, 1.0]))
    assert rows.add(0, (0.0, 0.0), np.array([1.0, 0.0]))
    first = model.solve(rows)
    assert first is not None
    weights, duals, objective = first
    np.testing.assert_allclose(weights, [1.0, 0.0])
    np.testing.assert_allclose(duals, [1.0])
    assert objective == 1.0
    assert model.held == 1
    assert model.highs.getBasis().valid

    assert rows.add(0, (1.0, 0.0), np.array([0.0, 1.0]))
    second = model.solve(rows)
    assert second is not None
    weights, duals, objective = second
    np.testing.assert_allclose(weights, [1.0, 1.0])
    np.testing.assert_allclose(duals, [1.0, 1.0])
    assert objective == 2.0
    assert model.held == 2
    assert model.highs.getBasis().valid
    assert model.highs.getModelStatus() == highspy.HighsModelStatus.kOptimal
