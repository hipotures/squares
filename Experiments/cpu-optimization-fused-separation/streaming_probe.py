"""Research-only row-streamed prefix/reachability/top-k probe on archived grids.

The archived flat score supplies exact reachability for this diagnostic. It
does not alter the production solver or claim a complete fused implementation.
"""
import argparse
import json
import statistics
import time
import tracemalloc
from pathlib import Path

import numpy as np

from sqpack.fractional.generate import _least_finite_indices


def row_candidates(row, first, last, offset, k):
    if first >= last:
        return np.empty(0, dtype=np.intp)
    values = row[first:last]
    count = min(k, values.size)
    chosen = _least_finite_indices(values, count)
    return chosen + first + offset


def streaming(grid, intervals, k=13):
    grid = grid.copy()
    running = np.zeros(grid.shape[1], dtype=grid.dtype)
    candidates = []
    columns = grid.shape[1] - 1
    for i, row in enumerate(grid):
        np.cumsum(row, out=row)
        row += running
        running[:] = row
        if i < grid.shape[0] - 1:
            first, last = intervals[i]
            candidates.append(row_candidates(row[:-1], first, last, i * columns, k))
    chosen = np.concatenate(candidates)
    chosen_mass = grid[chosen // columns, chosen % columns]
    result = chosen[np.lexsort((chosen, chosen_mass))[:k]]
    return result, grid


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repeats", type=int, default=5)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    archive = root / "Experiments/cpu-parallel-scaling-investigation/workloads/capture-round18-000-017.tar.zst"
    results = []
    # tarfile does not decode zstd in the project Python; use the system tar.
    import subprocess
    for direction in (0, 8, 17):
        prefix = f"squares-numpy-capture-20260923/r18_d{direction:03d}"
        def read(suffix):
            raw = subprocess.check_output(["tar", "-I", "zstd", "-xOf", str(archive), f"{prefix}_{suffix}.npy"])
            import io
            return np.load(io.BytesIO(raw))
        grid = read("grid")
        flat = read("flat")
        reachable = np.isfinite(flat).reshape(grid.shape[0] - 1, grid.shape[1] - 1)
        intervals = []
        for mask in reachable:
            indices = np.flatnonzero(mask)
            first, last = (int(indices[0]), int(indices[-1]) + 1) if indices.size else (0, 0)
            if indices.size and not np.all(mask[first:last]):
                raise AssertionError("archived reachability is not a row interval")
            intervals.append((first, last))
        reference = _least_finite_indices(flat, 13)
        def baseline():
            mass = np.cumsum(np.cumsum(grid, axis=1), axis=0)[:-1, :-1]
            scored = np.where(reachable, mass, np.inf)
            return _least_finite_indices(scored.ravel(), 13)

        base_times, stream_times = [], []
        for _ in range(args.repeats):
            start = time.perf_counter()
            base = baseline()
            base_times.append(time.perf_counter() - start)
            start = time.perf_counter()
            got, streamed = streaming(grid, intervals)
            stream_times.append(time.perf_counter() - start)
        allocations = {}
        for name, fn in (("baseline", baseline), ("streaming", lambda: streaming(grid, intervals))):
            tracemalloc.start()
            before = tracemalloc.get_traced_memory()[0]
            fn()
            allocations[name] = tracemalloc.get_traced_memory()[1] - before
            tracemalloc.stop()
        results.append({"direction": direction, "shape": grid.shape,
                        "baseline_median_s": statistics.median(base_times),
                        "streaming_median_s": statistics.median(stream_times),
                        "peak_extra_bytes": allocations,
                        "mass_bitwise_equal": bool(np.array_equal(streamed, np.cumsum(np.cumsum(grid, axis=1), axis=0))),
                        "selected_equal": bool(np.array_equal(got, base)),
                        "archived_selected_equal": bool(np.array_equal(got, reference))})
    args.out.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
