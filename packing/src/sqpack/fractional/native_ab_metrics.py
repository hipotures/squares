"""Low-overhead completed-work accounting and bounded real-input sampling.

Each process owns a cumulative snapshot. Normal boundaries/finalization flush it;
periodic flushes bound crash loss to approximately one second of completed work.
Snapshots are summed once, never accumulated repeatedly by the reader. Kernel
wall/CPU times are inclusive and must NOT be added across nested kernels.
"""

from __future__ import annotations

import atexit
import hashlib
import json
import os
import time
import uuid
from pathlib import Path
from typing import Callable, TypeVar

from sqpack.fractional.native_ab_runtime import atomic_json

T = TypeVar("T")
_pid = 0
_context = None
_token = ""
_stats: dict[str, dict] = {}
_last_flush = 0.0
_seen_capture: set[tuple[str, int]] = set()


def _reset() -> None:
    global _pid, _token, _stats, _last_flush, _seen_capture, _context
    context = (
        os.getpid(),
        os.environ.get("PACK_NATIVE_SESSION"),
        os.environ.get("PACK_NATIVE_STATS"),
        os.environ.get("PACK_NATIVE_CAPTURE"),
    )
    if _context == context:
        return
    _context = context
    _pid = os.getpid()
    _token = f"{_pid}-{uuid.uuid4().hex}"
    _stats, _seen_capture, _last_flush = {}, set(), 0.0
    # multiprocessing's normal exit bypasses ordinary atexit handlers.
    from multiprocessing.util import Finalize

    Finalize(None, flush, kwargs={"force": True}, exitpriority=10)


def record(name: str, backend: str, units: int, wall: float, cpu: float) -> None:
    if not os.environ.get("PACK_NATIVE_STATS"):
        return
    _reset()
    if units < 0 or wall < 0 or cpu < 0:
        raise ValueError("negative completed-work metric")
    key = f"{name}/{backend}"
    value = _stats.setdefault(
        key,
        {
            "calls": 0,
            "units": 0,
            "wall_s": 0.0,
            "cpu_s": 0.0,
            "min_units": units,
            "max_units": units,
            "bins": {},
        },
    )
    value["calls"] += 1
    value["units"] += int(units)
    value["wall_s"] += float(wall)
    value["cpu_s"] += float(cpu)
    value["min_units"] = min(value["min_units"], units)
    value["max_units"] = max(value["max_units"], units)
    bucket = str(int(units).bit_length())
    group = value["bins"].setdefault(
        bucket, {"calls": 0, "units": 0, "wall_s": 0.0, "cpu_s": 0.0}
    )
    for field, increment in (("calls", 1), ("units", units), ("wall_s", wall), ("cpu_s", cpu)):
        group[field] += increment
    flush()


def timed(name: str, backend: str, units: int, operation: Callable[[], T]) -> T:
    if not os.environ.get("PACK_NATIVE_STATS"):
        return operation()
    wall, cpu = time.perf_counter(), time.process_time()
    try:
        result = operation()
    except BaseException:
        record(
            name + "-error", backend, 0, time.perf_counter() - wall, time.process_time() - cpu
        )
        raise
    record(name, backend, units, time.perf_counter() - wall, time.process_time() - cpu)
    return result


def flush(*, force: bool = False) -> None:
    global _last_flush
    directory = os.environ.get("PACK_NATIVE_STATS")
    context = (
        os.getpid(),
        os.environ.get("PACK_NATIVE_SESSION"),
        directory,
        os.environ.get("PACK_NATIVE_CAPTURE"),
    )
    if not directory or _context != context or not _stats:
        return
    now = time.monotonic()
    if not force and now - _last_flush < 1.0:
        return
    atomic_json(
        Path(directory) / f"{_token}.json",
        {
            "schema": 1,
            "session": os.environ.get("PACK_NATIVE_SESSION", ""),
            "pid": _pid,
            "process_token": _token,
            "epoch": time.time(),
            "stats": _stats,
        },
    )
    _last_flush = now


def aggregate(directory: Path) -> dict:
    result: dict[str, dict] = {}
    for path in sorted(directory.glob("*.json")):
        snapshot = json.loads(path.read_text())
        for key, value in snapshot["stats"].items():
            current = result.setdefault(
                key,
                {
                    "calls": 0,
                    "units": 0,
                    "wall_s": 0.0,
                    "cpu_s": 0.0,
                    "min_units": value["min_units"],
                    "max_units": 0,
                    "bins": {},
                },
            )
            for field in ("calls", "units", "wall_s", "cpu_s"):
                current[field] += value[field]
            current["min_units"] = min(current["min_units"], value["min_units"])
            current["max_units"] = max(current["max_units"], value["max_units"])
            for bucket, counts in value["bins"].items():
                group = current["bins"].setdefault(
                    bucket, {"calls": 0, "units": 0, "wall_s": 0.0, "cpu_s": 0.0}
                )
                for field in group:
                    group[field] += counts[field]
    return result


def capture(kind: str, bucket: str, payload: dict, arrays: dict | None = None) -> None:
    """Capture at most 64 directions, 16 vertex sets and 16 exact-query inputs.

    Exclusive per-slot reservations bound files across ALL worker processes.
    Capturing stops once a replay manifest seals the corpus. Nothing is uploaded.
    The sampled inputs are a workload sample, not a representative census.
    """
    root_text = os.environ.get("PACK_NATIVE_CAPTURE")
    if not root_text:
        return
    _reset()
    root = Path(root_text)
    if (root / "manifest.json").exists():
        return
    limit = 64 if kind == "direction" else 16
    slot = int(hashlib.sha256(bucket.encode()).hexdigest()[:8], 16) % limit
    identity = (kind, slot)
    if identity in _seen_capture:
        return
    _seen_capture.add(identity)
    root.mkdir(parents=True, exist_ok=True)
    stem = f"{kind}-{slot:03d}"
    try:
        fd = os.open(root / f"{stem}.lock", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        return
    os.close(fd)
    if callable(payload):
        payload, arrays = payload()
    value = {"schema": 1, "kind": kind, "bucket": bucket, "input": payload}
    if arrays is not None:
        import numpy as np

        temporary = root / f"{stem}.{os.getpid()}.tmp.npz"
        np.savez(temporary, **arrays)
        target = root / f"{stem}.npz"
        temporary.replace(target)
        value["arrays"] = target.name
        value["arrays_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    atomic_json(root / f"{stem}.json", value)


atexit.register(flush, force=True)
