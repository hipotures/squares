"""One bounded CPU budget for independent generation jobs.

A driver owns one slot while executing LP/pricing/serialization. At a separation
barrier it releases that slot and submits four-direction chunks to ONE long-lived
pool shared by every driver. Results retain production order. Resuming a driver
requires reacquiring a slot; serial owners + running chunks never exceed slots.
The coordinator handles one request per separation round, not one per direction.
This is scheduling, not proof logic. Only the existing full gate can retain a bound.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import os
import time
import traceback
import uuid
from collections import OrderedDict, deque
from concurrent.futures import Executor, ProcessPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from multiprocessing.connection import wait
from pathlib import Path
from typing import Any

from devtools.frontier_io import atomic_json, canonical_digest, digest, read_json

_CACHE: OrderedDict[str, tuple[Any, Any]] = OrderedDict()


class SharedDirections(Executor):
    """Synchronous facade: the caller sleeps while its slot serves other jobs."""

    def __init__(self, connection):
        self.connection = connection
        self.wait_seconds = 0.0

    def map(self, fn, *iterables, timeout=None, chunksize=1, buffersize=None):
        if len(iterables) != 1 or fn.__name__ != "_direction_chunk_task":
            raise ValueError("shared generation accepts production direction chunks only")
        tasks = list(iterables[0])
        if not tasks:
            return iter(())
        began = time.monotonic()
        self.connection.send(("separate", tasks))
        kind, payload = self.connection.recv()
        self.wait_seconds += time.monotonic() - began
        if kind != "resume":
            raise RuntimeError(f"generation broker refused round: {payload}")
        return iter(payload)


def _direction_work(key: str, tail: tuple) -> tuple[Any, float, float]:
    """Cache read-only arrays once per worker/round; dispatch only small handles."""
    import numpy as np
    from sqpack.fractional.colgen import _direction_chunk_task

    wall, cpu = time.monotonic(), time.process_time()
    if key not in _CACHE:
        _CACHE[key] = (np.load(key + ".points.npy", mmap_mode="r", allow_pickle=False),
                       np.load(key + ".weights.npy", mmap_mode="r", allow_pickle=False))
        while len(_CACHE) > 4:
            _CACHE.popitem(last=False)
    points, weights = _CACHE[key]
    _CACHE.move_to_end(key)
    value = _direction_chunk_task((points, weights, *tail))
    return value, time.monotonic() - wall, time.process_time() - cpu


def _drive(connection, command: list[str], output: str) -> None:
    """Run the real CLI in an isolated process; no nested direction pool."""
    code = 70
    started, cpu = time.monotonic(), time.process_time()
    proxy = SharedDirections(connection)
    try:
        # Imports/setup count as driver work too, rather than extra free CPUs.
        kind, _ = connection.recv()
        if kind != "resume":
            raise RuntimeError("missing initial CPU lease")
        os.environ.update(PACK_JOBS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1",
                          MKL_NUM_THREADS="1", PACK_GENERATION_MANAGED="1")
        from devtools.run_fractional_colgen import main
        with Path(output).open("a", encoding="utf-8", buffering=1) as log:
            with redirect_stdout(log), redirect_stderr(log):
                print(f"[{int(time.time())}] generation driver pid={os.getpid()}", flush=True)
                try:
                    code = main(command[3:], direction_executor=proxy)
                except SystemExit as exc:
                    code = int(exc.code or 0)
                except BaseException:
                    traceback.print_exc()
                    code = 70
        connection.send(("finished", {"returncode": code, "driver_cpu_seconds": time.process_time() - cpu,
                         "wall_seconds": time.monotonic() - started,
                         "separation_wait_seconds": proxy.wait_seconds}))
    except BaseException:
        try:
            connection.send(("finished", {"returncode": 70, "error": traceback.format_exc()}))
        except (EOFError, OSError):
            pass
    finally:
        connection.close()


def _flag(command: list[str], flag: str) -> Path | None:
    return Path(command[command.index(flag) + 1]).resolve() if flag in command else None


def _identity(job: dict, code_sha: str) -> str:
    seed = _flag(job["command"], "--seed-certificate")
    return canonical_digest({"command": job["command"], "seed": digest(seed) if seed else None,
                             "code": code_sha})


def _outputs(job: dict) -> dict[str, str | None]:
    paths = [_flag(job["command"], flag) for flag in
             ("--json", "--freeze", "--raw-weights", "--log", "--row-log", "--phase-log")]
    return {str(p): digest(p) if p.is_file() else None for p in paths if p is not None}


def _cached(job: dict, identity: str) -> dict | None:
    path = Path(job["output"]).parent / "generation-receipt.json"
    if not path.exists():
        return None
    record = read_json(path)
    if record.get("identity") != identity or record.get("finished") is not True:
        raise ValueError(f"generation receipt identity changed: {path}")
    if record.get("outputs") != _outputs(job):
        raise ValueError(f"completed generation artifacts changed: {path}")
    return record


def _preserve_partial(job: dict) -> None:
    directory = Path(job["output"]).parent
    names = [Path(p) for p in _outputs(job)] + [Path(job["output"])]
    present = [p for p in names if p.exists()]
    if present:
        backup = directory / ("interrupted-" + uuid.uuid4().hex[:12])
        backup.mkdir()
        for path in present:
            if path.parent != directory:
                raise ValueError("generation outputs must stay in their stage directory")
            path.replace(backup / path.name)


def validate_jobs(jobs: list[dict]) -> None:
    identities, outputs = set(), set()
    for job in jobs:
        if job["id"] in identities:
            raise ValueError("duplicate generation job id")
        identities.add(job["id"])
        command = job["command"]
        if command[1:3] != ["-m", "devtools.run_fractional_colgen"]:
            raise ValueError("generation queue supports only the fractional generator")
        paths = set(_outputs(job)) | {str(Path(job["output"]).resolve())}
        if outputs & paths:
            raise ValueError("generation jobs must not share output paths")
        outputs.update(paths)
        directory = Path(job["output"]).resolve().parent
        if any(Path(p).parent != directory for p in paths):
            raise ValueError("generation outputs must stay in their stage directory")
        if _flag(command, "--json") is None:
            raise ValueError("generation job must write a result")
    for job in jobs:
        seed = _flag(job["command"], "--seed-certificate")
        if seed is not None and str(seed) in outputs:
            raise ValueError("a generation input cannot be another live job's output")


def run_jobs(jobs: list[dict], root: Path, *, slots: int, stage_seconds: float = 3600,
             no_progress_seconds: float = 1200, code_sha: str = "", on_progress=None) -> dict:
    """Execute a durable, bounded wave. Driver failures do not become search failures.

    Completed stages have immutable receipts and are skipped on recovery. A reboot
    may lose an unfinished stage; its partial files are preserved before a fresh
    attempt. All descendants remain in the enclosing frontier supervisor's group.
    """
    if not 1 <= slots <= 64 or not 0 < stage_seconds < float("inf") or no_progress_seconds < 0:
        raise ValueError("invalid generation resource budget")
    validate_jobs(jobs)
    root.mkdir(parents=True, exist_ok=True)
    if not code_sha:
        from devtools.frontier_runtime import code_fingerprint
        code_sha = code_fingerprint(Path.cwd())
    ctx = mp.get_context("spawn")
    serial: set[str] = set()
    pending: dict[str, deque] = {}
    awaiting: deque[str] = deque()
    rounds: dict[str, dict] = {}
    futures: dict[Any, tuple[str, int, str]] = {}
    drivers: dict[str, dict] = {}
    results: dict[str, dict] = {}
    identities = {job["id"]: _identity(job, code_sha) for job in jobs}
    metrics = {"slots": slots, "max_busy": 0, "chunks_completed": 0,
               "worker_cpu_seconds": 0.0, "worker_wall_seconds": 0.0,
               "round_requests": 0, "context_bytes": 0, "overlap_samples": 0,
               "driver_cpu_seconds": 0.0, "coordinator_cpu_seconds": 0.0}
    began, cpu = time.monotonic(), time.process_time()
    next_notice = began
    dispatch_turn = 0
    pool = ProcessPoolExecutor(max_workers=slots, mp_context=ctx)

    def complete(key: str, info: dict) -> None:
        driver = drivers[key]
        serial.discard(key)
        pending.pop(key, None)
        for future, (owner, _index, _context) in list(futures.items()):
            if owner == key:
                future.cancel()  # Running work continues to count until completion.
        code = int(info.get("returncode", 70))
        if code == 0 and _identity(driver["job"], code_sha) != identities[key]:
            code = 78
            info = {**info, "error": "generation inputs changed during execution"}
        result_path = _flag(driver["job"]["command"], "--json")
        if code == 0 and (result_path is None or not result_path.is_file()):
            code = 70
        record = {**info, "returncode": code, "identity": identities[key],
                  "finished": True, "finished_epoch": int(time.time()),
                  "outputs": _outputs(driver["job"])}
        atomic_json(Path(driver["job"]["output"]).parent / "generation-receipt.json", record)
        results[key] = record
        metrics["driver_cpu_seconds"] += float(info.get("driver_cpu_seconds", 0))
        driver["connection"].close()
        driver["done"] = True

    try:
        # Start at most slots drivers. More jobs are admitted when one finishes.
        unstarted = deque(jobs)
        while unstarted or len(results) < len(jobs) or futures:
            while unstarted and sum(not d["done"] for d in drivers.values()) < slots:
                job = unstarted.popleft()
                key = job["id"]
                cached = _cached(job, identities[key])
                if cached is not None:
                    results[key] = {**cached, "reused": True}
                    continue
                Path(job["output"]).parent.mkdir(parents=True, exist_ok=True)
                _preserve_partial(job)
                parent, child = ctx.Pipe()
                process = ctx.Process(target=_drive, args=(child, job["command"], job["output"]))
                process.start()
                child.close()
                drivers[key] = {"process": process, "connection": parent, "job": job,
                                "done": False, "born": time.monotonic(), "progress": None,
                                "progress_at": time.monotonic()}
                awaiting.append(key)
            # Drain completed chunks independently of submission order.
            for future in [f for f in futures if f.done()]:
                key, index, context = futures.pop(future)
                if drivers[key]["done"]:
                    continue
                try:
                    value, wall, used_cpu = future.result()
                except BaseException as exc:
                    drivers[key]["connection"].send(("error", str(exc)))
                    pending.pop(key, None)
                    continue
                metrics["chunks_completed"] += 1
                metrics["worker_wall_seconds"] += wall
                metrics["worker_cpu_seconds"] += used_cpu
                group = rounds[key]
                group["results"][index] = value
                group["remaining"] -= 1
                if group["remaining"] == 0:
                    awaiting.append(key)
            # Resume serial owners first: completed dependencies never deadlock.
            while awaiting and len(serial) + len(futures) < slots:
                key = awaiting.popleft()
                if drivers[key]["done"]:
                    continue
                serial.add(key)
                group = rounds.pop(key, None)
                drivers[key]["connection"].send(("resume", group["results"] if group else None))
                if group:
                    for suffix in (".points.npy", ".weights.npy"):
                        Path(group["context"] + suffix).unlink(missing_ok=True)
            # Round-robin dispatch with no fixed strategy partitions.
            while len(serial) + len(futures) < slots and any(pending.values()):
                ready = [key for key in pending if pending[key]]
                key = ready[dispatch_turn % len(ready)]
                dispatch_turn += 1
                index, context, tail = pending[key].popleft()
                future = pool.submit(_direction_work, context, tail)
                futures[future] = (key, index, context)
            metrics["max_busy"] = max(metrics["max_busy"], len(serial) + len(futures))
            if serial and futures:
                metrics["overlap_samples"] += 1
            live = {d["connection"]: key for key, d in drivers.items() if not d["done"]}
            for connection in wait(list(live), timeout=0.005) if live else ():
                key = live[connection]
                try:
                    kind, payload = connection.recv()
                except (EOFError, OSError):
                    complete(key, {"returncode": 70, "error": "driver exited without completion"})
                    continue
                if kind == "finished":
                    complete(key, payload)
                elif kind == "separate":
                    if key not in serial or key in rounds:
                        raise RuntimeError("driver requested work without its serial lease")
                    serial.remove(key)
                    import numpy as np
                    first = payload[0]
                    context = str(root / ("context-" + uuid.uuid4().hex))
                    np.save(context + ".points.npy", first[0], allow_pickle=False)
                    np.save(context + ".weights.npy", first[1], allow_pickle=False)
                    metrics["round_requests"] += 1
                    metrics["context_bytes"] += first[0].nbytes + first[1].nbytes
                    rounds[key] = {"remaining": len(payload), "results": [None] * len(payload),
                                   "context": context}
                    pending[key] = deque((i, context, task[2:]) for i, task in enumerate(payload))
                else:
                    raise RuntimeError(f"unsupported generation message: {kind}")
            if not live:
                time.sleep(0.005)
            now = time.monotonic()
            for key, driver in drivers.items():
                if driver["done"]:
                    continue
                directory = Path(driver["job"]["output"]).parent
                progress = tuple((p.stat().st_size, p.stat().st_mtime_ns) if p.exists() else (0, 0)
                                 for p in (directory / "rows.log", directory / "column.log", directory / "phase.log"))
                if progress != driver["progress"]:
                    driver.update(progress=progress, progress_at=now)
                if now - driver["born"] > stage_seconds or (
                    no_progress_seconds and key in serial and now - driver["progress_at"] > no_progress_seconds
                ):
                    driver["process"].terminate()
                    driver["process"].join(2)
                    if driver["process"].is_alive():
                        driver["process"].kill()
                    complete(key, {"returncode": 124, "error": "generation stage deadline/no-progress budget"})
                elif not driver["process"].is_alive() and not driver["connection"].poll():
                    complete(key, {"returncode": 70, "error": "generation driver crashed"})
            if len(results) == len(jobs) and futures:
                # All useful owners ended (possibly a deadline). Do not wait for
                # discarded work before reaching the bounded cleanup in finally.
                break
            if now >= next_notice:
                current = {**metrics, "serial_owners": len(serial), "direction_tasks": len(futures),
                           "completed_jobs": len(results), "jobs": len(jobs),
                           "elapsed_seconds": now - began,
                           "coordinator_cpu_seconds": time.process_time() - cpu}
                atomic_json(root / "generation-progress.json", current)
                if on_progress:
                    on_progress(current)
                next_notice = now + 1.0
        metrics.update(wall_seconds=time.monotonic() - began,
                       coordinator_cpu_seconds=time.process_time() - cpu)
        return {"schema": 1, "finished": True, "jobs": results, "metrics": metrics}
    finally:
        for driver in drivers.values():
            process = driver["process"]
            if process.is_alive():
                process.terminate()
            process.join(2)
            if process.is_alive():
                process.kill()
                process.join()
        for future in futures:
            future.cancel()
        # Python 3.14 supports bounded termination of owned executor children.
        if futures and hasattr(pool, "terminate_workers"):
            pool.terminate_workers()
        else:
            pool.shutdown(wait=True, cancel_futures=True)
        for path in root.glob("context-*.npy"):
            path.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--workers", type=int, required=True)
    parser.add_argument("--stage-seconds", type=float, default=3600)
    parser.add_argument("--no-progress-seconds", type=float, default=1200)
    args = parser.parse_args(argv)
    manifest = read_json(args.manifest)
    fingerprint = digest(args.manifest)
    last = [0.0]
    def progress(metrics):
        if time.monotonic() - last[0] >= 60:
            print(f"[{int(time.time())}] [generation-queue] serial={metrics['serial_owners']} "
                  f"directions={metrics['direction_tasks']} slots={metrics['slots']} "
                  f"jobs={metrics['completed_jobs']}/{metrics['jobs']}", flush=True)
            last[0] = time.monotonic()
    report = run_jobs(manifest["jobs"], args.report.parent, slots=min(args.workers, int(os.environ.get("PACK_JOBS", args.workers))),
                      stage_seconds=args.stage_seconds, no_progress_seconds=args.no_progress_seconds,
                      on_progress=progress)
    if digest(args.manifest) != fingerprint:
        raise ValueError("generation manifest changed during execution")
    report["manifest_sha256"] = fingerprint
    atomic_json(args.report, report)
    print(f"[{int(time.time())}] [generation-queue] complete wall={report['metrics']['wall_seconds']:.3f}s "
          f"coordinator_cpu={report['metrics']['coordinator_cpu_seconds']:.3f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
