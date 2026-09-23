"""Research-only native-selector hook for the current production solver.

Build the library separately, then pass its path. This script never compiles
at runtime; production integration, if accepted, must package the native code.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import multiprocessing as mp
import sys
from pathlib import Path

import numpy as np
from bench import main as bench_main

from sqpack.fractional import colgen, generate

_NATIVE_LIBRARIES: list[ctypes.CDLL] = []


def _install_heap(library_path: str) -> None:
    """Install the research selector in the parent or a spawn-style worker."""
    library = ctypes.CDLL(library_path)
    _NATIVE_LIBRARIES.append(library)
    select = library.topk_finite
    select.argtypes = [
        ctypes.POINTER(ctypes.c_double), ctypes.c_size_t,
        ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t),
    ]
    select.restype = ctypes.c_size_t
    original = generate._least_finite_indices  # noqa: SLF001 - research hook

    def heap(
        flat: np.ndarray, count: int, *, zero_weight_grid: bool = False
    ) -> np.ndarray:
        if zero_weight_grid or count > 64 or count <= 0:
            return original(flat, count, zero_weight_grid=zero_weight_grid)
        values = np.ascontiguousarray(flat, dtype=np.float64)
        result = np.empty(min(count, values.size), dtype=np.uintp)
        size = select(
            values.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
            values.size,
            len(result),
            result.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)),
        )
        return result[:size].astype(np.intp, copy=False)

    generate._least_finite_indices = heap  # noqa: SLF001 - research hook


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    args = parser.parse_args()
    library_path = str(args.library.resolve())
    original_selector = generate._least_finite_indices  # noqa: SLF001 - research hook
    original_pool = colgen.ProcessPoolExecutor
    _install_heap(library_path)
    if args.workers > 1:
        def pool_with_selector(*, max_workers: int) -> object:
            return original_pool(
                max_workers=max_workers,
                initializer=_install_heap,
                initargs=(library_path,),
            )

        colgen.ProcessPoolExecutor = pool_with_selector
    old_argv = sys.argv
    try:
        sys.argv = [str(Path(__file__).with_name("bench.py")), "--workers", str(args.workers),
                    "--out", str(args.out)]
        bench_main()
    finally:
        sys.argv = old_argv
        generate._least_finite_indices = original_selector  # noqa: SLF001 - research hook
        colgen.ProcessPoolExecutor = original_pool
    report = json.loads(args.out.read_text())
    report["selector_prototype"] = "native fixed-size heap, injected into production solver"
    report["native_library_sha256"] = hashlib.sha256(args.library.read_bytes()).hexdigest()
    report["worker_start_method"] = mp.get_start_method()
    args.out.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
