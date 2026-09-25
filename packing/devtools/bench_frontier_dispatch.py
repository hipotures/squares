"""Synthetic queue service-rate/long-tail controls, NOT solver benchmarks.

Workers sleep for specified intervals. This isolates scheduling and IPC overhead
without pretending a four-core CI machine is a sixteen-core arithmetic server.
The same item durations are used for the barrier and shared-queue comparisons.
"""
from __future__ import annotations

import argparse
import json
import math
import multiprocessing as mp
import statistics
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any

from devtools.frontier_dispatch import dispatch

_DURATION = 1.0
_LONG_TAIL = False


def initialise(duration: float, long_tail: bool) -> None:
    global _DURATION, _LONG_TAIL
    _DURATION, _LONG_TAIL = duration, long_tail


def work(task: tuple[int, tuple[int, ...]]) -> dict[str, Any]:
    group, indices = task
    start, cpu = time.monotonic(), time.process_time()
    records = []
    for index in indices:
        duration = _DURATION
        if _LONG_TAIL:
            duration = _DURATION * 16 if index == 0 else _DURATION / 4
        began = time.monotonic()
        time.sleep(duration)
        records.append({"index": index, "seconds": time.monotonic() - began})
    return {"group": group, "records": records, "cancelled": False,
            "wall_seconds": time.monotonic() - start, "cpu_seconds": time.process_time() - cpu}


def one(pool, groups, slots):
    return dispatch(pool, work, groups, slots=slots, active=lambda _: True,
                    accept=lambda *_: None, target_seconds=0.5, max_batch=8)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workers", type=int, default=16)
    parser.add_argument("--samples", type=int, default=3)
    parser.add_argument("--target-seconds", type=float, default=12)
    parser.add_argument("--task-seconds", type=float, default=1)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--service-only", action="store_true")
    args = parser.parse_args(argv)
    if (not 1 <= args.workers <= 32 or not 1 <= args.samples <= 10
            or not 10 <= args.target_seconds <= 30 or not 0.01 <= args.task_seconds <= 1):
        parser.error("use workers 1..32, samples 1..10, target 10..30s, task 0.01..1s")
    multiple = math.lcm(6, args.workers)
    total = math.ceil(args.target_seconds * args.workers / (args.task_seconds * multiple)) * multiple
    per_group = total // 6
    samples = []
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn"),
                             initializer=initialise, initargs=(args.task_seconds, False)) as pool:
        # Start the workers before measuring sustained scheduler service rate.
        list(pool.map(work, [(0, (0,))] * args.workers))
        for sample in range(args.samples):
            result = one(pool, [range(per_group)] * 6, args.workers)
            result["sample"] = sample + 1
            samples.append(result)
            print(json.dumps({k: result[k] for k in ("sample", "wall_seconds", "completed_items",
                 "submitted_batches", "coordinator_cpu_seconds", "dispatch_seconds", "peak_in_flight")}), flush=True)
    # Same synthetic work, measured with and without a boost barrier. Aggregate
    # repetitions into >10-second samples; never report millisecond micro-runs
    # as evidence about long VM experiments.
    pairs = []
    if not args.service_only:
        with ProcessPoolExecutor(max_workers=args.workers, mp_context=mp.get_context("spawn"),
                                 initializer=initialise, initargs=(0.03, True)) as pool:
            list(pool.map(work, [(0, (0,))] * args.workers))
            # Four groups allow both paired batches to stay roughly within 10..60s.
            # A pilot can be inflated by cold imports; use the known sleep lower bound.
            repeats = max(1, math.ceil(args.target_seconds / 0.48))
            for sample in range(args.samples):
                pair = {"sample": sample + 1, "repeats": repeats}
                order = ("barrier", "shared") if sample % 2 == 0 else ("shared", "barrier")
                for mode in order:
                    started = time.monotonic()
                    for _ in range(repeats):
                        if mode == "shared":
                            one(pool, [range(32)] * 4, args.workers)
                        else:
                            for _ in range(4):
                                one(pool, [range(32)], args.workers)
                    pair[mode + "_batch_seconds"] = time.monotonic() - started
                pair["ratio"] = pair["barrier_batch_seconds"] / pair["shared_batch_seconds"]
                pairs.append(pair)
                print(json.dumps(pair), flush=True)
    report = {"purpose": "synthetic scheduler service-rate and barrier control; NOT solver speedup",
              "workers": args.workers, "task_seconds": args.task_seconds,
              "samples": samples, "long_tail_pairs": pairs,
              "median_items_per_second": statistics.median(r["completed_items"] / r["wall_seconds"] for r in samples),
              "median_coordinator_cpu_fraction": statistics.median(r["coordinator_cpu_seconds"] / r["wall_seconds"] for r in samples),
              "median_tail_ratio": statistics.median(p["ratio"] for p in pairs) if pairs else None}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
