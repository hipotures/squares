"""Optional wheel-built row-major CPU prefix pass with a NumPy fallback."""

from __future__ import annotations

import ctypes
import sys
from collections.abc import Callable
from pathlib import Path

import numpy as np


def _load_native() -> tuple[ctypes.CDLL, Callable[..., None]] | None:
    suffix = {"linux": ".so", "darwin": ".dylib"}.get(sys.platform)
    if suffix is None:
        return None
    path = Path(__file__).with_name(f"_prefix_rows_native{suffix}")
    if not path.is_file():
        return None
    try:
        library = ctypes.CDLL(str(path))
    except OSError:
        return None
    native = library.prefix_axis0_rowmajor
    native.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_size_t]
    native.restype = None
    return library, native


_NATIVE = _load_native()


def native_available() -> bool:
    """Whether this installation loaded the wheel-built prefix helper."""
    return _NATIVE is not None


def accumulate_axis0(grid: np.ndarray) -> None:
    """Accumulate a float64 grid in place, preserving per-column addition order."""
    if (
        _NATIVE is None
        or grid.dtype != np.float64
        or grid.ndim != 2
        or not grid.flags.c_contiguous
    ):
        np.add.accumulate(grid, axis=0, out=grid)
        return
    _NATIVE[1](
        grid.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), grid.shape[0], grid.shape[1]
    )
