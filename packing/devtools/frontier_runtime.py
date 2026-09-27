"""Restart-safe subprocess jobs with independent watchdogs, not a proof checker.

Each job has an immutable specification, an advisory lock held by its supervisor,
boot/start-time process identities, and a durable completion receipt. A restarted
controller attaches to a live job instead of submitting duplicate computation.
Only a process group bearing this job's unguessable ownership token may be killed.
"""
from __future__ import annotations

import argparse
import errno
import fcntl
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from devtools.frontier_io import atomic_json, canonical_digest, digest, read_json

TIMEOUT = 124
RESOURCE_LIMIT = 125
INFRASTRUCTURE = 70
PERMANENT_ERROR = 78
DEFAULTS: dict[str, Any] = {
    "stage_seconds": 3600.0,
    "verify_seconds": 7200.0,
    "no_progress_seconds": 1200.0,
    "heartbeat_seconds": 300.0,
    "poll_seconds": 1.0,
    "retries": 2,
    "backoff_seconds": 5.0,
    "terminate_seconds": 10.0,
    "max_rss_mib": 0,
    "min_free_mib": 512,
}


class JobConflict(RuntimeError):
    """A job path cannot be reused for a different command or input."""


class LiveJob(RuntimeError):
    """A legacy child is alive but cannot safely be adopted as a new job."""


def boot_id() -> str:
    return Path("/proc/sys/kernel/random/boot_id").read_text().strip()


def process_info(pid: int) -> dict[str, Any] | None:
    try:
        text = Path(f"/proc/{pid}/stat").read_text()
        parts = text.rsplit(") ", 1)[1].split()
        return {
            "pid": pid, "state": parts[0], "ppid": int(parts[1]),
            "pgid": int(parts[2]), "ticks": parts[19],
            "rss": max(0, int(parts[21])) * os.sysconf("SC_PAGE_SIZE"),
        }
    except (OSError, ValueError, IndexError):
        return None


def identity(pid: int) -> dict[str, Any]:
    info = process_info(pid)
    return {
        "pid": pid, "start_ticks": None if info is None else info["ticks"],
        "boot_id": boot_id(), "host": socket.gethostname(),
    }


def is_alive(record: dict[str, Any]) -> bool:
    if record.get("boot_id") != boot_id() or record.get("host") != socket.gethostname():
        return False
    info = process_info(int(record.get("pid", -1)))
    return bool(info and info["state"] != "Z" and info["ticks"] == record.get("start_ticks"))


def owned_members(pgid: int | None, token: str) -> list[dict[str, Any]]:
    result = []
    needle = f"SQUARES_FRONTIER_JOB_TOKEN={token}".encode()
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        info = process_info(int(entry.name))
        if not info or (pgid is not None and info["pgid"] != pgid) or info["state"] == "Z":
            continue
        try:
            environment = (entry / "environ").read_bytes().split(b"\0")
        except (OSError, PermissionError):
            continue
        if needle in environment:
            result.append(info)
    return result


def terminate_owned(pgid: int, token: str, grace: float) -> None:
    # This must never operate on an arbitrary PID from an old machine/boot.
    if pgid <= 1 or pgid == os.getpgrp() or not owned_members(pgid, token):
        return
    try:
        os.killpg(pgid, signal.SIGTERM)
    except ProcessLookupError:
        return
    end = time.monotonic() + grace
    while time.monotonic() < end and owned_members(pgid, token):
        time.sleep(min(0.1, max(0.0, end - time.monotonic())))
    if owned_members(pgid, token):
        try:
            os.killpg(pgid, signal.SIGKILL)
        except ProcessLookupError:
            pass


def lock_busy(path: Path) -> bool:
    with path.open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


def _paths(args: list[str], cwd: Path) -> tuple[list[Path], list[Path]]:
    inputs: list[Path] = []
    outputs: list[Path] = []
    for flag, collection in (
        ("--seed-certificate", inputs), ("--snapshot", inputs),
        ("--source-result", inputs), ("--input", inputs), ("--manifest", inputs),
        ("--json", outputs), ("--freeze", outputs), ("--raw-weights", outputs),
        ("--report", outputs), ("--log", outputs), ("--row-log", outputs), ("--phase-log", outputs),
    ):
        if flag in args:
            path = Path(args[args.index(flag) + 1])
            collection.append((cwd / path).resolve())
    if "-m" in args:
        module = args[args.index("-m") + 1]
        if module in ("devtools.decide_certificate", "devtools.declare_least_cell_mass"):
            inputs.append((cwd / args[-1]).resolve())
    return inputs, outputs


def _checksums(paths: list[Path]) -> dict[str, str | None]:
    return {str(path): digest(path) if path.is_file() else None for path in paths}


def _receipt_valid(receipt: dict[str, Any], fingerprint: str) -> bool:
    if receipt.get("fingerprint") != fingerprint or receipt.get("state") != "DONE":
        return False
    for name, expected in receipt.get("outputs", {}).items():
        path = Path(name)
        actual = digest(path) if path.is_file() else None
        if actual != expected:
            return False
    return True


def code_fingerprint(cwd: Path) -> str:
    """Fingerprint executable search/verification code, not changing research data."""
    paths = sorted(p for p in (cwd / "src/sqpack/fractional").iterdir()
                   if p.suffix in (".py", ".c", ".cpp"))
    paths += sorted((cwd / "devtools").glob("frontier*.py"))
    paths += [cwd / "devtools/run_fractional_colgen.py", cwd / "devtools/decide_certificate.py",
              cwd / "src/sqpack/workers.py", cwd / "uv.lock"]
    return canonical_digest({str(p.relative_to(cwd)): digest(p) for p in paths if p.is_file()})


def _spawn_supervisor(spec_path: Path, output: Path, cwd: Path, environment: dict[str, str]) -> subprocess.Popen:
    with output.with_name(output.name + ".supervisor.log").open("a") as log:
        return subprocess.Popen(
            [sys.executable, "-m", "devtools.frontier_runtime", "--job", str(spec_path)],
            cwd=cwd, env=environment, stdin=subprocess.DEVNULL,
            stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
        )


def run(
    args: list[str], output: Path, *, cwd: Path,
    env: dict[str, str] | None = None, limits: dict[str, Any] | None = None,
    heartbeat: Callable[[float], None] | None = None,
    on_poll: Callable[[], None] | None = None,
) -> int:
    """Launch or reattach to one durable job; completed unchanged jobs are reused."""
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    inputs, outputs = _paths(args, cwd)
    settings = {**DEFAULTS, **(limits or {})}
    environment = dict(os.environ if env is None else env)
    overrides = {key: environment[key] for key in (
        "PACK_JOBS", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
        "PACK_NATIVE_KERNELS", "PACK_NATIVE_BUILD_ROOT"
    ) if key in environment}
    spec_path = output.with_name(output.name + ".job.json")
    receipt_path = output.with_name(output.name + ".receipt.json")
    lock_path = output.with_name(output.name + ".job.lock")
    spec = read_json(spec_path) if spec_path.exists() else None
    if spec is not None:
        # CLI changes on resume apply to future jobs, not an already-running job.
        # In-flight work keeps its original resource budget and environment.
        overrides = dict(spec["overrides"])
        settings = {**DEFAULTS, **spec["limits"]}
        environment.update(overrides)
    fingerprint = canonical_digest({"command": args, "inputs": _checksums(inputs),
                                    "environment": overrides, "cwd": str(cwd.resolve())})
    if spec is not None:
        if spec["fingerprint"] != fingerprint:
            raise JobConflict(f"job input or command changed: {spec_path}")
    else:
        spec = {"version": 1, "fingerprint": fingerprint, "command": args,
                "cwd": str(cwd.resolve()), "output": str(output),
                "outputs": [str(p) for p in outputs], "overrides": overrides,
                "token": uuid.uuid4().hex, "limits": settings, "attempts": [],
                "code_sha256": code_fingerprint(cwd.resolve()),
                "created_at": time.time(), "state": "PENDING"}
        atomic_json(spec_path, spec)
    if receipt_path.exists():
        receipt = read_json(receipt_path)
        if _receipt_valid(receipt, fingerprint):
            return int(receipt["returncode"])
        raise JobConflict(f"completed job artifacts changed: {receipt_path}")
    supervisor = None
    # An advisory lock, not just a PID, also closes the spawn-before-PID-save race.
    if not lock_busy(lock_path):
        supervisor = _spawn_supervisor(spec_path, output, cwd, environment)
    start = time.monotonic()
    next_heartbeat = start + settings["heartbeat_seconds"]
    supervisor_restarts = 0
    while True:
        if on_poll is not None:
            on_poll()
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            if not _receipt_valid(receipt, fingerprint):
                raise JobConflict(f"invalid job completion receipt: {receipt_path}")
            if supervisor is not None:
                supervisor.wait(timeout=30)
            return int(receipt["returncode"])
        if supervisor is not None and supervisor.poll() is not None:
            if supervisor_restarts >= int(settings["retries"]):
                raise RuntimeError(f"job supervisor repeatedly exited without a receipt: {spec_path}")
            supervisor_restarts += 1
            supervisor = None
            # Recovery reconciles job-owned descendants under the original
            # deadline; a crashed supervisor never authorizes overlapping work.
        if supervisor is None and not lock_busy(lock_path):
            # The old supervisor died. Its replacement reconciles the original
            # owned child before launching any new computation.
            supervisor = _spawn_supervisor(spec_path, output, cwd, environment)
        now = time.monotonic()
        if heartbeat is not None and now >= next_heartbeat:
            heartbeat(now - start)
            next_heartbeat = now + settings["heartbeat_seconds"]
        time.sleep(max(0.01, settings["poll_seconds"]))


def _progress(paths: list[Path]) -> tuple[tuple[int, int], ...]:
    values = []
    for path in paths:
        try:
            stat = path.stat()
            values.append((stat.st_size, stat.st_mtime_ns))
        except FileNotFoundError:
            values.append((0, 0))
    return tuple(values)


def _permanent(output: Path) -> bool:
    with output.open("rb") as handle:
        handle.seek(max(0, output.stat().st_size - 32768))
        text = handle.read().decode(errors="replace")
    return any(token in text for token in (
        "ModuleNotFoundError:", "SyntaxError:", "unrecognized arguments:",
        "error while loading shared libraries", "No module named",
    ))


def supervise(spec_path: Path) -> int:
    spec = read_json(spec_path)
    output = Path(spec["output"])
    receipt_path = output.with_name(output.name + ".receipt.json")
    lock_path = output.with_name(output.name + ".job.lock")
    with lock_path.open("a+") as locker:
        fcntl.flock(locker, fcntl.LOCK_EX)
        spec = read_json(spec_path)
        if receipt_path.exists():
            receipt = read_json(receipt_path)
            return 0 if _receipt_valid(receipt, spec["fingerprint"]) else 1
        if spec.get("state") == "DONE" and "completion" in spec:
            receipt = spec["completion"]
            if not _receipt_valid(receipt, spec["fingerprint"]):
                raise JobConflict(f"completed artifacts changed before receipt recovery: {spec_path}")
            atomic_json(receipt_path, receipt)
            return 0
        limits = {**DEFAULTS, **spec["limits"]}
        args = list(spec["command"])
        kind = "search" if any(module in args for module in (
            "devtools.run_fractional_colgen", "devtools.frontier_generation_queue"
        )) else "verification"
        if "devtools.frontier_rationalise" in args:
            kind = "rationalisation"
        max_seconds = limits["stage_seconds"] if kind == "search" else limits["verify_seconds"]
        progress_seconds = limits["no_progress_seconds"] if kind == "search" else 0
        token = spec["token"]
        spec["supervisor"] = identity(os.getpid())
        spec.setdefault("deadline", time.time() + max_seconds)
        spec["state"] = "RUNNING"
        atomic_json(spec_path, spec)
        # The ownership token also closes the child-spawn/PID-save crash window:
        # a replacement supervisor finds unrecorded descendants without guessing PIDs.
        members = owned_members(None, token)
        if members:
            groups = {member["pgid"] for member in members}
            deadline = min(float(spec["deadline"]), float(spec.get("child_deadline", spec["deadline"])))
            watched = [output, output.parent / "rows.log", output.parent / "column.log"]
            previous = _progress(watched)
            last_progress = time.monotonic()
            recovery_reason = "owned descendants finished; exit status unavailable"
            while members:
                groups.update(member["pgid"] for member in members)
                now = time.monotonic()
                progress = _progress(watched)
                if progress != previous:
                    previous, last_progress = progress, now
                rss = sum(member["rss"] for member in members)
                if (int(limits["max_rss_mib"]) > 0 and rss > int(limits["max_rss_mib"]) * 1024**2
                        or shutil.disk_usage(output.parent).free < int(limits["min_free_mib"]) * 1024**2):
                    recovery_reason = "orphan resource guard"
                    break
                if time.time() >= deadline:
                    recovery_reason = "orphan wall-time budget"
                    break
                if progress_seconds and now - last_progress >= progress_seconds:
                    recovery_reason = "orphan no-progress watchdog"
                    break
                time.sleep(max(0.01, limits["poll_seconds"]))
                members = owned_members(None, token)
            for pgid in groups:
                terminate_owned(pgid, token, limits["terminate_seconds"])
            spec["attempts"].append({"kind": "orphan-reconciled", "at": time.time(),
                                     "reason": recovery_reason})
            spec.pop("child", None)
            atomic_json(spec_path, spec)
        returncode = INFRASTRUCTURE
        reason = "retry budget exhausted"
        consumed = sum(a.get("kind") == "execution" for a in spec["attempts"])
        for attempt in range(consumed, int(limits["retries"]) + 1):
            # Never execute updated files under a job spec stamped with old code.
            # Completed immutable receipts remain reusable as historical evidence.
            if spec.get("code_sha256") != code_fingerprint(Path(spec["cwd"])):
                returncode, reason = PERMANENT_ERROR, "executable source changed; schedule a fresh job"
                break
            input_paths, _ = _paths(args, Path(spec["cwd"]))
            current_inputs = canonical_digest({
                "command": args, "inputs": _checksums(input_paths),
                "environment": spec["overrides"], "cwd": spec["cwd"],
            })
            if current_inputs != spec["fingerprint"]:
                returncode, reason = PERMANENT_ERROR, "job inputs changed before execution"
                break
            if time.time() >= float(spec["deadline"]):
                returncode, reason = TIMEOUT, "total job budget including retries"
                break
            if shutil.disk_usage(output.parent).free < int(limits["min_free_mib"]) * 1024**2:
                returncode, reason = RESOURCE_LIMIT, "insufficient free disk for evidence"
                break
            if attempt:
                # A prior attempt is never silently overwritten.
                archive = output.parent / f"{output.name}.attempt-{attempt:02d}"
                archive.mkdir(exist_ok=True)
                for path in [output, *(Path(p) for p in spec["outputs"])]:
                    if path.exists() and path.parent == output.parent:
                        destination = archive / path.name
                        if not destination.exists():
                            shutil.copy2(path, destination)
                        if path != output:
                            path.unlink()
                delay = min(60.0, limits["backoff_seconds"] * 2 ** (attempt - 1))
                time.sleep(max(0.0, min(delay, float(spec["deadline"]) - time.time())))
                if time.time() >= float(spec["deadline"]):
                    returncode, reason = TIMEOUT, "total job budget exhausted during backoff"
                    break
            environment = {**os.environ, **spec["overrides"],
                           "SQUARES_FRONTIER_JOB_TOKEN": token}
            prior_limits = sum(a.get("returncode") == RESOURCE_LIMIT for a in spec["attempts"])
            if prior_limits:
                environment["PACK_JOBS"] = str(max(1, int(environment.get("PACK_JOBS", 1)) // (2 ** prior_limits)))
            began = time.monotonic()
            with output.open("a", encoding="utf-8") as handle:
                handle.write(f"\n[supervisor] attempt={attempt + 1} kind={kind}\n")
                handle.flush()
                try:
                    child = subprocess.Popen(
                        args, cwd=spec["cwd"], env=environment, stdin=subprocess.DEVNULL,
                        stdout=handle, stderr=subprocess.STDOUT, start_new_session=True,
                    )
                except OSError as error:
                    returncode = (PERMANENT_ERROR if error.errno in (
                        errno.ENOENT, errno.EACCES, errno.ENOEXEC, errno.ENOTDIR
                    ) else INFRASTRUCTURE)
                    reason = f"child could not start: {error}"
                    handle.write(reason + "\n")
                    handle.flush()
                    spec["attempts"].append({"kind": "execution", "attempt": attempt + 1,
                        "returncode": returncode, "reason": reason, "spawn_error": True,
                        "elapsed": time.monotonic() - began, "finished_at": time.time()})
                    atomic_json(spec_path, spec)
                    if returncode == PERMANENT_ERROR:
                        break
                    continue
                try:
                    spec["child"] = identity(child.pid)
                    spec["child_deadline"] = float(spec["deadline"])
                    execution = {"kind": "execution", "attempt": attempt + 1,
                                 "started_at": time.time(), "child": spec["child"],
                                 "workers": environment.get("PACK_JOBS")}
                    spec["attempts"].append(execution)
                    atomic_json(spec_path, spec)
                    atomic_json(output.with_name(output.name + ".child.json"), spec["child"])
                    previous = _progress([output, output.parent / "rows.log", output.parent / "column.log"])
                    last_progress = began
                    reason = "child completed"
                    while child.poll() is None:
                        time.sleep(max(0.01, limits["poll_seconds"]))
                        now = time.monotonic()
                        progress = _progress([output, output.parent / "rows.log", output.parent / "column.log"])
                        if progress != previous:
                            last_progress, previous = now, progress
                        rss = sum(member["rss"] for member in owned_members(child.pid, token))
                        exceeded = int(limits["max_rss_mib"]) > 0 and rss > int(limits["max_rss_mib"]) * 1024**2
                        if exceeded or shutil.disk_usage(output.parent).free < int(limits["min_free_mib"]) * 1024**2:
                            returncode, reason = RESOURCE_LIMIT, "memory or evidence-disk guard"
                            break
                        if time.time() >= float(spec["deadline"]):
                            returncode, reason = TIMEOUT, "wall-time budget"
                            break
                        if progress_seconds and now - last_progress >= progress_seconds:
                            returncode, reason = TIMEOUT, "no solver log progress"
                            break
                    else:
                        returncode = int(child.returncode)
                    if child.poll() is None:
                        terminate_owned(child.pid, token, limits["terminate_seconds"])
                    child.wait(timeout=30)
                finally:
                    # Also clean up surviving pool descendants after a failed leader.
                    terminate_owned(child.pid, token, limits["terminate_seconds"])
                    if child.poll() is None:
                        child.wait(timeout=30)
                execution.update({"returncode": returncode, "reason": reason,
                                  "elapsed": time.monotonic() - began, "finished_at": time.time()})
                spec.pop("child", None)
                atomic_json(spec_path, spec)
            if returncode == 0:
                break
            if _permanent(output):
                returncode, reason = PERMANENT_ERROR, "environment/command error; retry suppressed"
                break
            # Mathematical rejection uses a successful structured report. Legacy
            # verifier exit 1 is a verdict, not an infrastructure retry request.
            if kind == "verification" and returncode == 1:
                break
        spec["state"] = "DONE"
        spec["returncode"] = returncode
        spec["reason"] = reason
        completion = {
            "version": 1, "state": "DONE", "fingerprint": spec["fingerprint"],
            "returncode": returncode, "reason": reason,
            "outputs": _checksums([Path(p) for p in spec["outputs"]]),
            "attempts": spec["attempts"], "finished_at": time.time(),
        }
        spec["completion"] = completion
        atomic_json(spec_path, spec)
        atomic_json(receipt_path, completion)
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job", type=Path, required=True)
    args = parser.parse_args()
    return supervise(args.job)


if __name__ == "__main__":
    raise SystemExit(main())
