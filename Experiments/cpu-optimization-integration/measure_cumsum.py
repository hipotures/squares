"""Captured-grid bitwise, allocation, and one/16-worker cumsum measurements."""
import argparse
import json
import subprocess
import tempfile
import time
import tracemalloc
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np


def operation(grid, mode):
    if mode == "nested":
        return np.cumsum(np.cumsum(grid, axis=1), axis=0)
    out = grid.copy()
    np.add.accumulate(out, axis=1, out=out)
    np.add.accumulate(out, axis=0, out=out)
    return out


def worker(task):
    path, mode, calls = task
    grid = np.load(path)
    for _ in range(2):
        operation(grid, mode)
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    for _ in range(calls):
        operation(grid, mode)
    return {"wall_s": time.perf_counter() - start_wall,
            "cpu_s": time.process_time() - start_cpu}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    archive = (
        root
        / "Experiments/cpu-parallel-scaling-investigation/workloads/"
        "capture-round18-018-035.tar.zst"
    )
    prefix = "squares-numpy-capture-20260923/r18_d026_grid.npy"
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "grid.npy"
        path.write_bytes(
            subprocess.check_output(["tar", "-I", "zstd", "-xOf", str(archive), prefix])
        )
        grid = np.load(path)
        equal = bool(np.array_equal(operation(grid, "nested"), operation(grid, "inplace")))
        allocation = {}
        for mode in ("nested", "inplace"):
            tracemalloc.start()
            before = tracemalloc.get_traced_memory()[0]
            operation(grid, mode)
            allocation[mode] = tracemalloc.get_traced_memory()[1] - before
            tracemalloc.stop()
        results = {}
        for workers in (1, 16):
            for mode in ("nested", "inplace"):
                if workers == 1:
                    runs = [worker((path, mode, 40))]
                else:
                    with ProcessPoolExecutor(max_workers=16) as pool:
                        runs = list(pool.map(worker, [(path, mode, 40)] * 16))
                results[f"{workers}_{mode}"] = {
                    "ms_per_call_cpu": 1000 * sum(x["cpu_s"] for x in runs) / (workers * 40),
                    "max_wall_s": max(x["wall_s"] for x in runs),
                    "aggregate_cpu_s": sum(x["cpu_s"] for x in runs),
                }
    report = {"shape": grid.shape, "bitwise_equal": equal,
              "peak_extra_allocated_bytes": allocation, "measurements": results}
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))  # noqa: T201 - diagnostic summary


if __name__ == "__main__":
    main()
