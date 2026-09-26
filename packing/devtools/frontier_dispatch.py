"""Bounded, completion-driven dispatch for independent groups of CPU work.

Only small (group, item IDs) descriptors are submitted. Heavy input belongs in a
pool initializer. This module neither interprets mathematical outcomes nor emits
proofs. A callback can close a group without blocking other groups' work.
"""
from __future__ import annotations

import math
import time
from collections import deque
from collections.abc import Callable, Sequence
from concurrent.futures import FIRST_COMPLETED, Executor, Future, wait
from dataclasses import dataclass
from typing import Any


@dataclass
class BatchSizer:
    """Start cautiously, amortise cheap work, keep expensive/tail work divisible."""

    target_seconds: float = 0.5
    maximum: int = 8
    seconds_per_item: float | None = None
    last_size: int = 1

    def observe(self, durations: Sequence[float]) -> None:
        if not durations:
            return
        # Use the maximum within a batch, not only its average: a cheap phase
        # followed by an expensive direction must promptly shrink its batches.
        sample = max(durations)
        if not math.isfinite(sample) or sample < 0:
            raise ValueError("invalid task duration")
        sample = max(sample, 1e-6)
        old = self.seconds_per_item
        self.seconds_per_item = sample if old is None else max(sample, 0.75 * old + 0.25 * sample)

    def size(self, backlog: int, slots: int) -> int:
        estimate = self.seconds_per_item
        desired = 1 if estimate is None else max(1, int(self.target_seconds / estimate))
        # At least two waves of work remain divisible; all tails go back to one.
        fair_share = max(1, backlog // max(1, 2 * slots))
        self.last_size = min(self.maximum, desired, self.last_size * 2, fair_share)
        return self.last_size


def dispatch(
    executor: Executor,
    execute: Callable[[tuple[int, tuple[int, ...]]], dict[str, Any]],
    groups: Sequence[Sequence[int]],
    *,
    slots: int,
    active: Callable[[int], bool],
    accept: Callable[[int, dict[str, Any]], None],
    checkpoint: Callable[[dict[str, Any], bool], None] | None = None,
    target_seconds: float = 0.5,
    max_batch: int = 8,
    checkpoint_seconds: float = 2.0,
) -> dict[str, Any]:
    """Keep at most ``slots`` batches in flight across all active groups.

    Completed batches are consumed without submission-order blocking. Refill is
    performed before optional checkpoint I/O. Group cancellation is cooperative
    in the worker; a cancelled/incomplete item is never sent to ``accept`` as a
    successful result. An exception aborts this job, preserving saved evidence.
    """
    if (type(slots) is not int or slots < 1 or type(max_batch) is not int
            or not 1 <= max_batch <= 64 or not math.isfinite(target_seconds)
            or target_seconds <= 0 or not math.isfinite(checkpoint_seconds)
            or checkpoint_seconds <= 0):
        raise ValueError("invalid dispatcher limits")
    queues = [deque(items) for items in groups]
    if any(len(set(items)) != len(items) for items in groups):
        raise ValueError("duplicate item in a dispatch group")
    sizers = [BatchSizer(target_seconds, max_batch) for _ in queues]
    pending: dict[Future, tuple[int, tuple[int, ...]]] = {}
    cursor = 0
    began, cpu_began = time.monotonic(), time.process_time()
    stats: dict[str, Any] = {
        "slots": slots, "submitted_batches": 0, "completed_batches": 0,
        "completed_items": 0, "cancelled_batches": 0, "peak_in_flight": 0,
        "largest_batch": 0, "worker_wall_seconds": 0.0, "worker_cpu_seconds": 0.0,
        "dispatch_seconds": 0.0, "checkpoint_seconds": 0.0, "checkpoints": 0,
        "refill_events": 0, "max_completion_to_refill_seconds": 0.0,
        "group_batches": [0] * len(queues),
    }
    last_checkpoint = began

    def update() -> None:
        stats.update(wall_seconds=time.monotonic() - began,
                     coordinator_cpu_seconds=time.process_time() - cpu_began,
                     in_flight=len(pending), queued_items=sum(map(len, queues)),
                     batch_sizes=[sizer.last_size for sizer in sizers])

    def save(force: bool) -> None:
        nonlocal last_checkpoint
        update()
        if checkpoint is not None:
            start = time.monotonic()
            checkpoint(dict(stats), force)
            stats["checkpoint_seconds"] += time.monotonic() - start
            stats["checkpoints"] += 1
        last_checkpoint = time.monotonic()

    def refill() -> None:
        nonlocal cursor
        start = time.monotonic()
        # Round robin across groups, never a fixed partition of the CPU budget.
        while len(pending) < slots:
            found = False
            for _ in queues:
                group = cursor
                cursor = (cursor + 1) % len(queues)
                if not active(group):
                    queues[group].clear()
                    continue
                if not queues[group]:
                    continue
                backlog = sum(len(q) for j, q in enumerate(queues) if active(j))
                size = min(len(queues[group]), sizers[group].size(backlog, slots))
                items = tuple(queues[group].popleft() for _ in range(size))
                future = executor.submit(execute, (group, items))
                pending[future] = group, items
                stats["submitted_batches"] += 1
                stats["group_batches"][group] += 1
                stats["largest_batch"] = max(stats["largest_batch"], len(items))
                stats["peak_in_flight"] = max(stats["peak_in_flight"], len(pending))
                found = True
                break
            if not found:
                break
        stats["dispatch_seconds"] += time.monotonic() - start
        stats["refill_events"] += 1

    try:
        refill()
        while pending:
            done, _ = wait(pending, timeout=checkpoint_seconds, return_when=FIRST_COMPLETED)
            observed = time.monotonic()
            for future in done:
                group, items = pending.pop(future)
                if future.cancelled():
                    stats["cancelled_batches"] += 1
                    continue
                result = future.result()  # Worker errors cannot become quick refusals.
                if result.get("group") != group:
                    raise ValueError("worker returned the wrong group")
                records = result["records"]
                ids = [record["index"] for record in records]
                if len(set(ids)) != len(ids) or any(index not in items for index in ids):
                    raise ValueError("worker returned duplicate or unscheduled items")
                if len(ids) != len(items) and not result.get("cancelled", False):
                    raise ValueError("worker silently omitted scheduled items")
                if result.get("cancelled", False) and active(group):
                    raise RuntimeError("an unresolved group lost cancelled work")
                sizers[group].observe([record["seconds"] for record in records])
                stats["completed_batches"] += 1
                stats["completed_items"] += len(records)
                stats["worker_wall_seconds"] += result["wall_seconds"]
                stats["worker_cpu_seconds"] += result["cpu_seconds"]
                if active(group):
                    for record in records:
                        if not active(group):
                            break
                        accept(group, record)
            # Cancel only futures not yet running. Running work polls its own
            # shared flag; we keep accounting for it until it actually completes.
            for future, (group, _) in pending.items():
                if not active(group):
                    future.cancel()
            refill()
            if done:
                stats["max_completion_to_refill_seconds"] = max(
                    stats["max_completion_to_refill_seconds"], time.monotonic() - observed)
            if time.monotonic() - last_checkpoint >= checkpoint_seconds:
                save(False)
        save(True)
    except BaseException:
        for future in pending:
            future.cancel()
        save(True)
        raise
    update()
    return stats
