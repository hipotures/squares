"""Small-k selector study on preserved real late-round scores."""
import json
import ctypes
import argparse
import statistics
import subprocess
import time
import tracemalloc
from pathlib import Path

import numpy as np

from sqpack.fractional.generate import _least_finite_indices


def compact(a, k):
    ix = np.flatnonzero(np.isfinite(a))
    if not len(ix):
        return ix
    return ix[np.lexsort((ix, a[ix]))[:k]]


def blockwise(a, k, block=65536):
    candidates = []
    for start in range(0, a.size, block):
        part = a[start:start + block]
        n = min(k, part.size)
        if not n:
            continue
        picked = np.argpartition(part, n - 1)[:n]
        finite = picked[np.isfinite(part[picked])]
        if not len(finite):
            continue
        if len(finite) == n:
            cutoff = np.max(part[finite])
            below = finite[part[finite] < cutoff]
            ties = np.flatnonzero(part == cutoff)[:n - len(below)]
            finite = np.concatenate((below, ties))
        candidates.append(finite + start)
    if not candidates:
        return np.empty(0, dtype=np.intp)
    ix = np.concatenate(candidates)
    return ix[np.lexsort((ix, a[ix]))[:k]]


def sample(fn, repeats=25):
    for _ in range(3):
        fn()
    results = []
    for _ in range(repeats):
        start = time.perf_counter_ns()
        fn()
        results.append((time.perf_counter_ns() - start) / 1e6)
    return {"median_ms": statistics.median(results), "min_ms": min(results), "max_ms": max(results), "samples_ms": results}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    fixture = args.input or Path(__file__).resolve().parents[2] / "packing/tests/fixtures/late_selector_flat.npz"
    with np.load(fixture) as archive:
        a = archive["flat"]
    k = 13
    expected = compact(a, k)
    methods = {"current": lambda: _least_finite_indices(a, k),
               "finite_compact": lambda: compact(a, k)}
    source = Path(__file__).with_name("heap_select.c")
    library_path = Path("/tmp/libsqpack_top13.so")
    subprocess.run(["cc", "-O3", "-fPIC", "-shared", "-o", str(library_path), str(source)], check=True)
    library = ctypes.CDLL(str(library_path))
    selector = library.topk_finite
    selector.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t,
                         ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
    selector.restype = ctypes.c_size_t

    def heap():
        result = np.empty(k, dtype=np.uintp)
        size = selector(a.ctypes.data_as(ctypes.POINTER(ctypes.c_double)), a.size,
                        k, result.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)))
        return result[:size]

    methods["compiled_heap"] = heap
    for block in (4096, 16384, 65536, 262144):
        methods[f"block_{block}"] = lambda block=block: blockwise(a, k, block)
    report = {"size": a.size, "finite": int(np.isfinite(a).sum()), "methods": {}}
    for name, fn in methods.items():
        result = fn()
        timing = sample(fn)
        tracemalloc.start()
        before = tracemalloc.get_traced_memory()[0]
        fn()
        peak = tracemalloc.get_traced_memory()[1] - before
        tracemalloc.stop()
        report["methods"][name] = {"exact": bool(np.array_equal(result, expected)),
                                   "peak_extra_bytes": peak, **timing}
    # Stable reference includes NaN and both infinities as ineligible.
    checked = 0
    rng = np.random.default_rng(2701)
    for length in (0, 1, 12, 13, 14, 31, 1024, 100001):
        for trial in range(8):
            test = rng.integers(-3, 4, size=length).astype(np.float64)
            if length:
                test[rng.choice(length, size=length // 8, replace=False)] = np.inf
                test[rng.choice(length, size=length // 8, replace=False)] = np.nan
            target = compact(test, k)
            got = np.empty(k, dtype=np.uintp)
            size = selector(test.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                            test.size, k, got.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t)))
            if not np.array_equal(got[:size], target):
                raise AssertionError(f"compiled selector mismatch: length={length}, trial={trial}")
            checked += 1
    report["randomized_reference_cases"] = checked
    path = args.out or Path(__file__).with_name("results.json")
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: (v["median_ms"], v["exact"]) for k, v in report["methods"].items()}, indent=2))


if __name__ == "__main__":
    main()
