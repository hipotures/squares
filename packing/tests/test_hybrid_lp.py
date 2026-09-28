"""Append-only updates are compared against fresh restricted LP solves."""
import numpy as np
import pytest
from scipy.optimize import linprog
from scipy.sparse import csr_matrix

from sqpack.fractional.hybrid_lp import AppendOnlyLp


@pytest.mark.parametrize("sparse", [False, True])
def test_rows_and_columns_share_one_model(sparse):
    owner = AppendOnlyLp(rhs=1.000002)
    identity = id(owner.highs)
    matrices = [
        np.zeros((0, 2)),
        np.array([[1., 0.], [0., 1.]]),
        np.array([[1., 0., 1.], [0., 1., 1.]]),
        np.array([[1., 0., 1.], [0., 1., 1.], [1., 1., 0.]]),
        np.array([[1., 0., 1., 1.], [0., 1., 1., 0.],
                  [1., 1., 0., 1.], [1., 0., 0., 1.]]),
    ]
    for matrix in matrices:
        costs = np.ones(matrix.shape[1])
        weights, dual, objective = owner.solve(csr_matrix(matrix) if sparse else matrix, costs)
        assert id(owner.highs) == identity
        if len(matrix):
            reference = linprog(costs, A_ub=-matrix,
                                b_ub=np.full(len(matrix), -owner.rhs), bounds=(0, None))
            assert reference.success
            assert objective == pytest.approx(reference.fun, abs=1e-8)
            assert np.min(matrix @ weights) >= owner.rhs - 1e-7
            assert np.max(matrix.T @ dual - costs) <= 1e-7
        else:
            assert objective == 0


def test_changed_previous_coefficients_are_refused():
    owner = AppendOnlyLp()
    owner.solve(np.eye(2), np.ones(2))
    with pytest.raises(ValueError, match="coefficients or costs changed"):
        owner.solve(np.ones((2, 2)), np.ones(2))
    with pytest.raises(ValueError, match="coefficients or costs changed"):
        owner.solve(np.eye(2), np.array([1., 2.]))
    with pytest.raises(ValueError, match="cannot shrink"):
        owner.solve(np.ones((1, 2)), np.ones(2))


@pytest.mark.parametrize("rhs", [0, -1, float("nan"), float("inf")])
def test_invalid_rhs(rhs):
    with pytest.raises(ValueError, match="RHS"):
        AppendOnlyLp(rhs=rhs)
