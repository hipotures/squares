"""Worker CPU and wall scaling on the current captured round-18 direction."""
import ctypes
import json
import statistics
import subprocess
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from sqpack.fractional.generate import _least_finite_indices


def worker(args):
    path, method, calls = args
    with np.load(path) as archive:
        a = archive["flat"]
    if method == "heap":
        lib = ctypes.CDLL("/tmp/libsqpack_top13.so")
        select = lib.topk_finite
        select.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t,
                           ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)]
        select.restype = ctypes.c_size_t
        out = np.empty(13, dtype=np.uintp)
        pointer = a.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
        out_pointer = out.ctypes.data_as(ctypes.POINTER(ctypes.c_size_t))
        def call():
            select(pointer, a.size, 13, out_pointer)
    else:
        def call():
            _least_finite_indices(a, 13)
    for _ in range(3):
        call()
    wall = time.perf_counter()
    cpu = time.process_time()
    for _ in range(calls):
        call()
    return {"wall_s": time.perf_counter() - wall,
            "cpu_s": time.process_time() - cpu}


def main():
    root = Path(__file__).resolve().parent
    subprocess.run(["cc", "-O3", "-fPIC", "-shared", "-o", "/tmp/libsqpack_top13.so",
                    str(root / "heap_select.c")], check=True)
    path = root / "current-round18-direction26.npz"
    results = {}
    for count in (1, 16):
        for method in ("current", "heap"):
            calls = 25
            with ProcessPoolExecutor(max_workers=count) as pool:
                runs = list(pool.map(worker, [(path, method, calls)] * count))
            results[f"{count}_{method}"] = {
                "per_call_cpu_ms": 1000 * sum(x["cpu_s"] for x in runs) / (count * calls),
                "max_worker_wall_s": max(x["wall_s"] for x in runs),
                "aggregate_cpu_s": sum(x["cpu_s"] for x in runs),
            }
    (root / "parallel-selector.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
