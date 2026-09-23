"""Standalone 1/16-worker scaling for the archived row-streaming prototype."""
import io
import json
import resource
import subprocess
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from sqpack.fractional.generate import _least_finite_indices

from streaming_probe import streaming


def worker(task):
    path, intervals, method, calls = task
    grid = np.load(path)
    if method == "baseline":
        mask = np.zeros((grid.shape[0] - 1, grid.shape[1] - 1), dtype=bool)
        for i, (first, last) in enumerate(intervals):
            mask[i, first:last] = True
        def call():
            mass = np.cumsum(np.cumsum(grid, axis=1), axis=0)[:-1, :-1]
            scored = np.where(mask, mass, np.inf)
            return _least_finite_indices(scored.ravel(), 13)
    else:
        def call():
            return streaming(grid, intervals)[0]
    for _ in range(2):
        call()
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    for _ in range(calls):
        call()
    return {"wall_s": time.perf_counter() - started_wall,
            "cpu_s": time.process_time() - started_cpu,
            "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main():
    root = Path(__file__).resolve().parents[2]
    archive = root / "Experiments/cpu-parallel-scaling-investigation/workloads/capture-round18-000-017.tar.zst"
    name = "squares-numpy-capture-20260923/r18_d008"
    grid_bytes = subprocess.check_output(["tar", "-I", "zstd", "-xOf", str(archive), name + "_grid.npy"])
    flat_bytes = subprocess.check_output(["tar", "-I", "zstd", "-xOf", str(archive), name + "_flat.npy"])
    grid = np.load(io.BytesIO(grid_bytes))
    flat = np.load(io.BytesIO(flat_bytes))
    mask = np.isfinite(flat).reshape(grid.shape[0] - 1, grid.shape[1] - 1)
    intervals = []
    for row in mask:
        indices = np.flatnonzero(row)
        intervals.append((int(indices[0]), int(indices[-1]) + 1) if indices.size else (0, 0))
    results = {}
    with tempfile.TemporaryDirectory() as directory:
        grid_path = Path(directory) / "grid.npy"
        grid_path.write_bytes(grid_bytes)
        for count in (1, 16):
            for method in ("baseline", "streaming"):
                calls = 20
                with ProcessPoolExecutor(max_workers=count) as pool:
                    runs = list(pool.map(worker, [(grid_path, intervals, method, calls)] * count))
                results[f"{count}_{method}"] = {
                    "per_call_cpu_ms": 1000 * sum(x["cpu_s"] for x in runs) / (count * calls),
                    "max_worker_wall_s": max(x["wall_s"] for x in runs),
                    "aggregate_cpu_s": sum(x["cpu_s"] for x in runs),
                    "peak_worker_rss_kib": max(x["peak_rss_kib"] for x in runs),
                }
    Path(__file__).with_name("parallel.json").write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
