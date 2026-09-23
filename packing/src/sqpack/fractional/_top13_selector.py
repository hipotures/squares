"""Optional wheel-built CPU selector for small stable top-k queries.

Linux and macOS wheels may contain the C library beside this module. Source
checkouts without a built library and other platforms use the NumPy reference
path in ``generate._least_finite_indices``. No compilation occurs on import.
"""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np


def _load_native() -> tuple[ctypes.CDLL, Callable[..., int]] | None:
    suffix = {"linux": ".so", "darwin": ".dylib"}.get(sys.platform)
    if suffix is None:
        return None
    path = Path(__file__).with_name(f"_top13{suffix}")
    if not path.is_file():
        return None
    try:
        library = ctypes.CDLL(str(path))
    except OSError:
        return None
    select = library.topk_finite
    select.argtypes = [
        ctypes.POINTER(ctypes.c_double),
        ctypes.c_size_t,
        ctypes.c_size_t,
        ctypes.POINTER(ctypes.c_size_t),
    ]
    select.restype = ctypes.c_size_t
    return library, select


_NATIVE = _load_native()


def native_available() -> bool:
    """Whether this installation loaded its wheel-built selector."""
    return _NATIVE is not None


def select_lowest_finite(flat: np.ndarray, count: int) -> np.ndarray | None:
    """Return stable lowest finite indices, or defer to the reference path.

    The C helper supports at most 64 candidates. It skips NaN and both
    infinities, and sorts by ``(value, original index)``. The return value is
    ``None`` only when the native path is unavailable or inapplicable.
    """

    if _NATIVE is None or flat.ndim != 1 or flat.dtype != np.float64 or not 0 < count <= 64:
        return None
    values = np.ascontiguousarray(flat)
    result = np.empty(min(count, values.size), dtype=np.uintp)
    select = _NATIVE[1]
    length = select(
        values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
        values.size,
        len(result),
        result.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)),
    )
    return result[:length].astype(np.intp, copy=False)
