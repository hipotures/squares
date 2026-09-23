"""Direct parent CPU accounting for the captured incremental LP sequence."""

from __future__ import annotations

import json
import math
import os
import time
from pathlib import Path

import numpy as np
from profile_lp import one_sequence
from scipy.sparse import load_npz

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    saved = np.load(ROOT / "raw/current-states.npz")
    counts = saved["row_counts"]
    matrix = load_npz(ROOT / "raw/current-rows-csr.npz").toarray()
    blocks = [matrix[first:last] for first, last in zip(
        np.concatenate(([0], counts[:-1])), counts, strict=True
    )]
    params = (saved["costs"], blocks, matrix)
    warm = one_sequence(*params, profile=False)
    repeats = max(1, math.ceil(20 / warm["wall_seconds"]))
    for sample in (1, 2, 3):
        load = {
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "loadavg": os.getloadavg(),
            "cpu_pressure": Path("/proc/pressure/cpu").read_text().strip(),
        }
        cpu_before = time.process_time()
        start = time.perf_counter()
        sequences = [one_sequence(*params, profile=False) for _ in range(repeats)]
        wall = time.perf_counter() - start
        cpu = time.process_time() - cpu_before
        assert 10 <= wall <= 60
        data = {
            "sample": sample, "repeats": repeats, "load_before": load,
            "batch_wall_seconds": wall, "batch_parent_cpu_seconds": cpu,
            "wall_per_sequence_seconds": wall / repeats,
            "parent_cpu_per_sequence_seconds": cpu / repeats,
            "last_objective": sequences[-1]["objectives"][-1],
        }
        (ROOT / "raw" / f"lp-cpu-s{sample}.json").write_text(json.dumps(data, indent=2) + "\n")
        print(json.dumps({"sample": sample, "batch_wall": round(wall, 3),
                          "parent_cpu_per_sequence": round(cpu / repeats, 3)}), flush=True)


if __name__ == "__main__":
    main()
