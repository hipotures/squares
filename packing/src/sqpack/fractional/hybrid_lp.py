"""One append-only HiGHS model, preserving the basis across rows AND columns."""
from __future__ import annotations

import hashlib
from typing import Any

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix, issparse


def matrix_digest(matrix: Any) -> str:
    sparse = csr_matrix(matrix, copy=True)
    sparse.sum_duplicates()
    sparse.sort_indices()
    h = hashlib.sha256()
    h.update(np.asarray(sparse.shape, dtype=np.int64).tobytes())
    for array in (sparse.indptr, sparse.indices, sparse.data):
        h.update(np.asarray(array, dtype=np.float64).tobytes())
    return h.hexdigest()


class AppendOnlyLp:
    def __init__(self, *, rhs: float = 1.0) -> None:
        import highspy
        if not np.isfinite(rhs) or rhs <= 0:
            raise ValueError("the cover RHS must be finite and positive")
        self.api = highspy
        self.highs = highspy.Highs()
        self.rhs = rhs
        self.rows = self.columns = 0
        self.prefix_digest: str | None = None
        self.costs = np.zeros(0)
        for name, value in (("output_flag", False), ("solver", "simplex"),
                            ("threads", 1), ("parallel", "off")):
            self._check(self.highs.setOptionValue(name, value))

    def _check(self, status: Any) -> None:
        if status != self.api.HighsStatus.kOk:
            raise RuntimeError(f"HiGHS rejected append-only model update: {status}")

    def solve(self, matrix: Any, costs: np.ndarray) -> tuple[np.ndarray, np.ndarray, float]:
        if matrix.ndim != 2 or matrix.shape[1] != len(costs):
            raise ValueError("LP dimensions do not match")
        nr, nc = matrix.shape
        data = matrix.data if issparse(matrix) else matrix
        if (nr < self.rows or nc < self.columns or nc == 0 or np.any(costs <= 0)
                or not np.isfinite(data).all() or not np.isfinite(costs).all()):
            raise ValueError("append-only LP cannot shrink or accept invalid coefficients")
        if self.prefix_digest is not None:
            if (matrix_digest(matrix[:self.rows, :self.columns]) != self.prefix_digest
                    or not np.array_equal(costs[:self.columns], self.costs)):
                raise ValueError("previously installed LP coefficients or costs changed")
        if nc > self.columns:
            new = csc_matrix(-matrix[:self.rows, self.columns:])
            count = nc - self.columns
            self._check(self.highs.addCols(
                count, costs[self.columns:], np.zeros(count),
                np.full(count, self.api.kHighsInf), new.nnz,
                new.indptr.astype(np.int32), new.indices.astype(np.int32), new.data,
            ))
            self.columns = nc
        if nr > self.rows:
            new = csr_matrix(-matrix[self.rows:, :])
            count = nr - self.rows
            self._check(self.highs.addRows(
                count, np.full(count, -self.api.kHighsInf),
                np.full(count, -self.rhs), new.nnz,
                new.indptr.astype(np.int32), new.indices.astype(np.int32), new.data,
            ))
            self.rows = nr
        self.prefix_digest = matrix_digest(matrix)
        self.costs = np.asarray(costs).copy()
        self._check(self.highs.run())
        if self.highs.getModelStatus() != self.api.HighsModelStatus.kOptimal:
            raise RuntimeError(f"restricted LP did not finish optimally: {self.highs.getModelStatus()}")
        result = self.highs.getSolution()
        return (np.asarray(result.col_value), np.maximum(-np.asarray(result.row_dual), 0),
                float(self.highs.getObjectiveValue()))
