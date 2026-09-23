"""Research-only full solver with compiled stable top-k selector."""
import ctypes
import os
import subprocess
import sys
from pathlib import Path

import numpy as np

from sqpack.fractional import generate

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packing/benchmarks/round0_selector"))
import solver_benchmark  # noqa: E402

source = Path(__file__).with_name("heap_select.c")
library_path = Path("/tmp/libsqpack_top13.so")
selector = None
selection_calls = 0
original = generate._least_finite_indices  # noqa: SLF001


def heap_select(flat, count, *, zero_weight_grid=False):
    global selection_calls
    capture = os.environ.get("SQUARES_TOP13_CAPTURE")
    if capture and selection_calls == 18 * 181 + 26:
        np.savez_compressed(capture, flat=flat)
    selection_calls += 1
    if zero_weight_grid:
        return original(flat, count, zero_weight_grid=True)
    if flat.dtype != np.float64 or not flat.flags.c_contiguous:
        flat = np.ascontiguousarray(flat, dtype=np.float64)
    take = min(count, flat.size)
    result = np.empty(take, dtype=np.uintp)
    size = selector(flat.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), flat.size,
                    take, result.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)))
    return result[:size].astype(np.intp, copy=False)


def _install_heap():
    global selector
    library = ctypes.CDLL(str(library_path))
    selector = library.topk_finite
    selector.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    selector.restype = ctypes.c_size_t
    generate._least_finite_indices = heap_select  # noqa: SLF001


if __name__ == "__main__":
    subprocess.run(["cc", "-O3", "-fPIC", "-shared", "-o", str(library_path), str(source)], check=True)
    solver_benchmark._install_baseline_selector = _install_heap
    raise SystemExit(solver_benchmark.main())
