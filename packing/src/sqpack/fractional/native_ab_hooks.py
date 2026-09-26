"""Small experimental kernel boundaries; unchanged Python bodies remain references."""

from __future__ import annotations

import os
import time
from functools import wraps
from fractions import Fraction
from math import atan2

import numpy as np

from sqpack.fractional import native_ab_metrics as metrics
from sqpack.fractional import native_ab_runtime as runtime


def accumulate_axis0(grid: np.ndarray) -> None:
    native = runtime.enabled("prefix")

    def operation():
        if native:
            runtime.require_float(grid, 2, writable=True)
            runtime.library("core").prefix_axis0_rowmajor(runtime.pointer(grid), *grid.shape)
        else:
            np.add.accumulate(grid, axis=0, out=grid)

    metrics.timed("prefix", "c" if native else "py", grid.size, operation)


def select_lowest_finite(flat: np.ndarray, count: int) -> np.ndarray | None:
    if not runtime.enabled("topk"):
        return None
    runtime.require_float(flat, 1)
    if not 0 < count <= 64:
        raise ValueError("experimental native topk supports 1..64 candidates")
    result = np.empty(min(count, flat.size), dtype=np.uintp)
    length = runtime.library("core").topk_finite(
        runtime.pointer(flat), flat.size, result.size, runtime.pointer(result)
    )
    return result[:length].astype(np.intp, copy=False)


def scatter(grid, left, right, bottom, top, weights) -> None:
    native = runtime.enabled("scatter")

    def operation():
        if not native:
            np.add.at(grid, (left, bottom), weights)
            np.add.at(grid, (right, bottom), -weights)
            np.add.at(grid, (left, top), -weights)
            np.add.at(grid, (right, top), weights)
            return
        runtime.require_float(grid, 2, writable=True)
        runtime.require_float(weights, 1)
        indices = [runtime.int_array(v) for v in (left, right, bottom, top)]
        if any(len(v) != len(weights) for v in indices):
            raise ValueError("scatter index lengths do not match weights")
        status = runtime.library("core").ab_scatter(
            runtime.pointer(grid),
            *grid.shape,
            *(runtime.pointer(v) for v in indices),
            runtime.pointer(weights),
            len(weights),
        )
        if status:
            raise ValueError(f"native scatter rejected input ({status})")

    metrics.timed("scatter", "c" if native else "py", 4 * len(weights), operation)


def compact(mass, row_ids, firsts, widths, offsets, values) -> None:
    native = runtime.enabled("compact")

    def operation():
        if not native:
            for row, first, width, offset in zip(row_ids, firsts, widths, offsets, strict=True):
                values[offset : offset + width] = mass[row, first : first + width]
            return
        runtime.require_float(mass, 2, contiguous=False)
        runtime.require_float(values, 1, writable=True)
        if mass.strides[1] != 8 or mass.strides[0] < 0 or mass.strides[0] % 8:
            raise ValueError("native compaction requires positive row and unit column strides")
        if np.shares_memory(values, mass):
            raise ValueError("compaction output must not alias its input")
        indices = [runtime.int_array(v) for v in (row_ids, firsts, widths, offsets)]
        if len({len(v) for v in indices}) != 1:
            raise ValueError("inconsistent slab lengths")
        status = runtime.library("core").ab_compact(
            runtime.pointer(mass),
            *mass.shape,
            mass.strides[0] // 8,
            *(runtime.pointer(v) for v in indices),
            len(row_ids),
            runtime.pointer(values),
            values.size,
        )
        if status:
            raise ValueError(f"native compaction rejected input ({status})")

    metrics.timed("compact", "c" if native else "py", values.size, operation)


def observe_topk(function):
    @wraps(function)
    def wrapped(flat, count, *, zero_weight_grid=False):
        mode = "py-zero" if zero_weight_grid else ("c" if runtime.enabled("topk") else "py")
        return metrics.timed(
            "topk",
            mode,
            flat.size,
            lambda: function(flat, count, zero_weight_grid=zero_weight_grid),
        )

    return wrapped


def observe_direction(function):
    @wraps(function)
    def wrapped(points, weights, direction, outer_side, square_side, *, keep, clip=None):
        mode = "+".join(runtime.selection()) or "none"
        value = metrics.timed(
            "direction",
            mode,
            len(points),
            lambda: function(
                points, weights, direction, outer_side, square_side, keep=keep, clip=clip
            ),
        )
        if clip is None and os.environ.get("PACK_NATIVE_CAPTURE"):
            live = int(np.count_nonzero(weights))
            if live:
                angle = atan2(float(direction.uy), float(direction.ux))
                bucket = f"support={live.bit_length()};angle={int(angle * 32)};keep={keep}"
                metrics.capture(
                    "direction",
                    bucket,
                    lambda: (
                        {
                            "ux": str(direction.ux),
                            "uy": str(direction.uy),
                            "vx": str(direction.vx),
                            "vy": str(direction.vy),
                            "label": direction.label,
                            "outer_side": outer_side,
                            "square_side": square_side,
                            "keep": keep,
                            "live_support": live,
                            "sites": len(points),
                        },
                        {"points": points, "weights": weights},
                    ),
                )
        return value

    return wrapped


def observe_event_grid(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        if not os.environ.get("PACK_NATIVE_STATS"):
            return function(*args, **kwargs)
        wall, cpu = time.perf_counter(), time.process_time()
        result = function(*args, **kwargs)
        metrics.record(
            "event-cells",
            "+".join(runtime.selection()) or "none",
            result.mass.size,
            time.perf_counter() - wall,
            time.process_time() - cpu,
        )
        return result

    return wrapped


def observe_vertices(function):
    @wraps(function)
    def wrapped(lines, outer_side):
        native = runtime.enabled("vertices")

        def operation():
            if not native:
                return function(lines, outer_side)
            data = np.asarray(
                [[float(a), float(b), float(c)] for a, b, c in lines], dtype=np.float64
            )
            data = data.reshape((-1, 3))
            half = float(outer_side) / 2 + 1e-12
            lib = runtime.library("core")
            count = lib.ab_vertices(runtime.pointer(data), len(data), half, None, None, 0)
            if count > np.iinfo(np.intp).max // 16:
                raise MemoryError("native vertex allocation exceeds addressable size")
            points = np.empty((count, 2), dtype=np.float64)
            sources = np.empty((count, 2), dtype=np.int64)
            filled = lib.ab_vertices(
                runtime.pointer(data),
                len(data),
                half,
                runtime.pointer(points),
                runtime.pointer(sources),
                count,
            )
            if filled != count:
                raise RuntimeError("vertex sizing/fill disagreement")
            # Keep the private reference function's return shape/type, not just values.
            return points, [tuple(row) for row in sources.tolist()]

        value = metrics.timed(
            "vertices", "c" if native else "py", len(lines) * (len(lines) - 1) // 2, operation
        )
        if os.environ.get("PACK_NATIVE_CAPTURE"):
            metrics.capture(
                "vertices",
                f"lines={len(lines).bit_length()};side={float(outer_side):.3f}",
                lambda: (
                    {
                        "lines": [[str(v) for v in line] for line in lines],
                        "outer_side": str(outer_side),
                    },
                    None,
                ),
            )
        return value

    return wrapped


def observe_depths(function):
    @wraps(function)
    def wrapped(query, axes, offsets, weights, half, *, slack):
        return metrics.timed(
            "depth-survey",
            "numpy",
            len(query) * len(weights),
            lambda: function(query, axes, offsets, weights, half, slack=slack),
        )

    return wrapped


def observe_lp(function):
    @wraps(function)
    def wrapped(self, rows):
        # A solve and the matrix size are both recorded; row-count is a workload
        # descriptor, not a claim that all LPs with this shape cost the same.
        result = metrics.timed(
            "lp", "highs", len(rows) * self.columns, lambda: function(self, rows)
        )
        if os.environ.get("PACK_NATIVE_STATS"):
            info = self.highs.getInfo()
            count = max(0, int(info.simplex_iteration_count))
            metrics.record("simplex-iterations", "highs", count, 0.0, 0.0)
        return result

    return wrapped


def _depth_handle(self):
    if not hasattr(self, "_ab_native_handle"):
        self._ab_native_handle = runtime.ExactDepth(self._weighted)
    return self._ab_native_handle


def _depth_payload(self, operation, **kwargs):
    return (
        {
            "operation": operation,
            "weighted": [
                [list(map(str, first)), list(map(str, second)), str(weight)]
                for first, second, weight in self._weighted
            ],
            **kwargs,
        },
        None,
    )


def exact_at(function):
    @wraps(function)
    def wrapped(self, x, y):
        native = runtime.enabled("exact-depth")

        def operation():
            if not native:
                return function(self, x, y)
            from sqpack.fractional.exact_slabs import _point

            return _depth_handle(self).query((_point(x, y),))

        value = metrics.timed(
            "exact-at", "cpp" if native else "py", len(self._weighted), operation
        )
        if os.environ.get("PACK_NATIVE_CAPTURE"):
            metrics.capture(
                "exact",
                f"at:{len(self._weighted)}:{x.denominator.bit_length()}",
                lambda: _depth_payload(self, "at", x=str(x), y=str(y)),
            )
        return value

    return wrapped


def exact_cost(function):
    @wraps(function)
    def wrapped(self, orbit, outer_side):
        native = runtime.enabled("exact-depth")

        def operation():
            if not native:
                return function(self, orbit, outer_side)
            from sqpack.fractional.exact_slabs import _point

            half = outer_side / 2
            points = tuple(_point(x - half, y - half) for x, y in orbit)
            return Fraction(len(orbit)) - _depth_handle(self).query(points)

        value = metrics.timed(
            "exact-cost", "cpp" if native else "py", len(orbit) * len(self._weighted), operation
        )
        if os.environ.get("PACK_NATIVE_CAPTURE"):
            metrics.capture(
                "exact",
                f"cost:{len(self._weighted)}:{len(orbit)}",
                lambda: _depth_payload(
                    self,
                    "cost",
                    outer_side=str(outer_side),
                    orbit=[[str(x), str(y)] for x, y in orbit],
                ),
            )
        return value

    return wrapped


def flush_after(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        finally:
            metrics.flush()

    return wrapped
