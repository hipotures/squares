#!/usr/bin/env python3
"""Replay all 181 preserved round-18 NumPy inputs with the merged selector."""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
EXP = ROOT / "Experiments/cpu-parallel-scaling-investigation"
sys.path.insert(0, str(ROOT / "packing"))
from sqpack.fractional.generate import _least_finite_indices  # noqa: E402

INPUTS = None


def restore(target: Path):
    target.mkdir(parents=True, exist_ok=True)
    capture = target / "squares-numpy-capture-20260923"
    if (capture / "r18_d180_grid.npy").exists():
        return capture
    for archive in sorted((EXP / "workloads").glob("capture-round18-*.tar.zst")):
        subprocess.run(["tar", "-I", "zstd", "-xf", str(archive), "-C", str(target)], check=True)
    return capture


def work(arg):
    op, index = arg
    array = INPUTS[index]
    start_wall = time.perf_counter_ns()
    start_cpu = time.thread_time_ns()
    if op == "selector":
        result = _least_finite_indices(array, 13, zero_weight_grid=False)
        check = int(result[0])
    elif op == "double_cumsum":
        result = np.cumsum(np.cumsum(array, axis=1), axis=0)
        check = float(result[-1, -1])
    else:
        raise ValueError(op)
    return dict(index=index, pid=os.getpid(), wall_ns=time.perf_counter_ns() - start_wall,
                cpu_ns=time.thread_time_ns() - start_cpu, check=check)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--restore-to", type=Path, default=Path("/tmp/post-round0-round18"))
    args = p.parse_args()
    capture = restore(args.restore_to)
    rows = []
    sizes = {}
    for op, suffix in (("selector", "flat"), ("double_cumsum", "grid")):
        global INPUTS
        INPUTS = [np.load(capture / f"r18_d{i:03d}_{suffix}.npy", mmap_mode="r") for i in range(181)]
        sizes[op] = dict(shapes=[list(a.shape) for a in INPUTS], dtypes=sorted(set(str(a.dtype) for a in INPUTS)),
                         input_bytes=sum(a.nbytes for a in INPUTS))
        for workers in (1, 16):
            with ProcessPoolExecutor(max_workers=workers, mp_context=mp.get_context("fork")) as pool:
                arguments = [(op, i) for i in range(181)]
                # First pass populates file cache and starts all worker processes.
                list(pool.map(work, arguments))
                for repeat in range(3):
                    started = time.perf_counter_ns()
                    details = list(pool.map(work, arguments))
                    wall_ns = time.perf_counter_ns() - started
                    row = dict(op=op, workers=workers, repeat=repeat, wall_ns=wall_ns,
                               worker_cpu_ns=sum(d["cpu_ns"] for d in details),
                               worker_wall_ns=sum(d["wall_ns"] for d in details),
                               details=details)
                    rows.append(row)
                    print(op, workers, repeat, f"{wall_ns/1e9:.4f}s", flush=True)
    args.out.write_text(json.dumps(dict(source=str(EXP / "workloads"), sizes=sizes, runs=rows)) + "\n")


if __name__ == "__main__":
    main()
