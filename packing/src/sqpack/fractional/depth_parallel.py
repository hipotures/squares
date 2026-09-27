"""Run large float depth surveys on an explicitly borrowed generation executor.

The numerical oracle remains colgen._depths. Tasks contain consecutive complete
oracle blocks, never subsets of the square reduction. A driver-scoped context
lets both pricing and ceiling screening borrow the broker without modifying the
independent proof gate or creating another pool. Outside that scope execution
is serial, including the differential reference and certificate processes.
"""

from __future__ import annotations

import time
from collections import OrderedDict
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Protocol

import numpy as np

from sqpack.fractional import native_ab_metrics as metrics

# Keep these boundaries identical to the existing serial depth oracle.
BLOCK_CELLS = 4_000_000


class DepthExecutor(Protocol):
    def depth_survey(
        self, query, axes, offsets, weights, half, *, slack
    ) -> np.ndarray: ...


_EXECUTOR: ContextVar[DepthExecutor | None] = ContextVar("depth_executor", default=None)
_CACHE: OrderedDict[str, tuple[np.ndarray, ...]] = OrderedDict()
SUFFIXES = (".query.npy", ".axes.npy", ".offsets.npy", ".weights.npy")


@contextmanager
def using_executor(executor: DepthExecutor | None) -> Iterator[None]:
    """Bind only this driver's scope; reset even when the generator fails."""
    token = _EXECUTOR.set(executor)
    try:
        yield
    finally:
        _EXECUTOR.reset(token)


def block_ranges(rows: int, squares: int) -> list[tuple[int, int]]:
    """Group whole oracle blocks, preserving every GEMM/reduction shape."""
    if rows < 0 or squares < 0:
        raise ValueError("depth dimensions must be non-negative")
    block = max(1, BLOCK_CELLS // max(1, squares))
    blocks = (rows + block - 1) // block
    stride = block * (4 if blocks >= 32 else 1)
    return [(start, min(start + stride, rows)) for start in range(0, rows, stride)]


def evaluate(reference, query, axes, offsets, weights, half, *, slack):
    """Dispatch only substantial surveys; report waiting separately from work."""
    executor = _EXECUTOR.get()
    units = len(query) * len(weights)
    block = max(1, BLOCK_CELLS // max(1, len(axes)))
    if executor is None or not len(weights) or len(query) < 2 * block:
        return metrics.timed(
            "depth-survey", "numpy", units,
            lambda: reference(query, axes, offsets, weights, half, slack=slack),
        )
    began = time.perf_counter()
    result = executor.depth_survey(query, axes, offsets, weights, half, slack=slack)
    # This driver waited, rather than doing the survey. Do not divide the
    # survey's work by its tiny coordination CPU time: that invents throughput.
    # Actual CPU service is recorded as depth-survey/numpy-worker in workers.
    metrics.record("depth-survey", "shared", units, time.perf_counter() - began, 0.0)
    return result


def worker(key: str, tail: tuple) -> tuple[np.ndarray, float, float]:
    """Read one immutable context per worker and evaluate an ordered point slice."""
    from sqpack.fractional.colgen import _depths

    wall, cpu = time.monotonic(), time.process_time()
    if key not in _CACHE:
        _CACHE[key] = tuple(
            np.load(key + suffix, mmap_mode="r", allow_pickle=False)
            for suffix in SUFFIXES
        )
        while len(_CACHE) > 4:
            _CACHE.popitem(last=False)
    _CACHE.move_to_end(key)
    query, axes, offsets, weights = _CACHE[key]
    start, stop, half, slack = tail
    if not 0 <= start < stop <= len(query):
        raise ValueError("invalid depth worker slice")
    value = metrics.timed(
        "depth-survey", "numpy-worker", (stop - start) * len(weights),
        lambda: _depths.__wrapped__(
            query[start:stop], axes, offsets, weights, half, slack=slack
        ),
    )
    metrics.flush()
    return value, time.monotonic() - wall, time.process_time() - cpu
