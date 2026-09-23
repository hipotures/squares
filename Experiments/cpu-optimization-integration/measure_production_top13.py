"""Compare packaged native and NumPy fallback on the captured M4 score array."""

from __future__ import annotations

import argparse
import json
import statistics
import time
import tracemalloc
from collections.abc import Callable
from pathlib import Path

import numpy as np

from sqpack.fractional import _top13_selector
from sqpack.fractional.generate import _least_finite_indices


def sample(fn: Callable[[], np.ndarray], repeats: int = 30) -> dict[str, float | int]:
    for _ in range(3):
        fn()
    times = []
    for _ in range(repeats):
        started = time.perf_counter_ns()
        fn()
        times.append((time.perf_counter_ns() - started) / 1e6)
    tracemalloc.start()
    before = tracemalloc.get_traced_memory()[0]
    fn()
    peak = tracemalloc.get_traced_memory()[1] - before
    tracemalloc.stop()
    return {
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "peak_extra_bytes": peak,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    with np.load(args.input) as archive:
        flat = archive["flat"]
    if not _top13_selector.native_available():
        raise RuntimeError("the editable installation did not load the native selector")
    finite = np.flatnonzero(np.isfinite(flat))
    expected = finite[np.lexsort((finite, flat[finite]))][:13]
    native = sample(lambda: _least_finite_indices(flat, 13))
    native_order = _least_finite_indices(flat, 13)
    original = _top13_selector._NATIVE  # noqa: SLF001 - diagnostic fallback seam
    try:
        _top13_selector._NATIVE = None  # noqa: SLF001 - diagnostic fallback seam
        fallback = sample(lambda: _least_finite_indices(flat, 13))
        fallback_order = _least_finite_indices(flat, 13)
    finally:
        _top13_selector._NATIVE = original  # noqa: SLF001 - diagnostic fallback seam
    report = {
        "input": str(args.input),
        "size": int(flat.size),
        "finite": int(finite.size),
        "native_exact": bool(np.array_equal(native_order, expected)),
        "fallback_exact": bool(np.array_equal(fallback_order, expected)),
        "native": native,
        "fallback": fallback,
    }
    if not report["native_exact"] or not report["fallback_exact"]:
        raise AssertionError("top-13 selection differs from the stable reference")
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))  # noqa: T201 - benchmark summary


if __name__ == "__main__":
    main()
