"""Matched real-input replay; never advances a frontier or creates a proof."""

from __future__ import annotations

import hashlib
import json
import multiprocessing as mp
import os
import signal
import struct
import time
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

import numpy as np

from sqpack.fractional import native_ab_metrics as metrics
from sqpack.fractional import native_ab_runtime as runtime


def signature(value) -> str:
    h = hashlib.sha256()

    def visit(item):
        if isinstance(item, np.ndarray):
            h.update(str((item.dtype.str, item.shape)).encode())
            h.update(np.ascontiguousarray(item).tobytes())
        elif isinstance(item, Fraction):
            h.update(f"q:{item.numerator}/{item.denominator};".encode())
        elif isinstance(item, (float, np.floating)):
            h.update(b"f:" + struct.pack("!d", float(item)))
        elif isinstance(item, (int, np.integer)):
            h.update(f"i:{int(item)};".encode())
        elif isinstance(item, (list, tuple)):
            h.update(f"seq:{len(item)}[".encode())
            for entry in item:
                visit(entry)
            h.update(b"]")
        elif item is None:
            h.update(b"none;")
        else:
            raise TypeError(f"unsupported replay result type: {type(item).__name__}")

    visit(value)
    return h.hexdigest()


def _path(root: Path, name: str) -> Path:
    result = (root / name).resolve()
    if result.parent != root.resolve():
        raise ValueError("corpus paths must be direct children of the corpus root")
    return result


@lru_cache(maxsize=128)
def _loaded(path_text: str):
    path = Path(path_text)
    record = json.loads(path.read_text())
    data = record["input"]
    if record["kind"] == "direction":
        from sqpack.fractional.model import Direction

        arrays_path = _path(path.parent, record["arrays"])
        if hashlib.sha256(arrays_path.read_bytes()).hexdigest() != record["arrays_sha256"]:
            raise ValueError("captured array checksum changed")
        with np.load(arrays_path, allow_pickle=False) as arrays:
            points, weights = arrays["points"].copy(), arrays["weights"].copy()
        points.flags.writeable = False
        weights.flags.writeable = False
        ux, uy = Fraction(data["ux"]), Fraction(data["uy"])
        direction = Direction(
            data["label"],
            ux,
            uy,
            Fraction(data.get("vx", str(-uy))),
            Fraction(data.get("vy", str(ux))),
        )
        return record, (points, weights, direction)
    if record["kind"] == "vertices":
        lines = [tuple(Fraction(v) for v in line) for line in data["lines"]]
        return record, (lines, Fraction(data["outer_side"]))
    if record["kind"] == "exact":
        from sqpack.fractional.exact_slabs import PreparedDepth

        value = PreparedDepth.__new__(PreparedDepth)
        value._weighted = tuple(
            (tuple(map(int, first)), tuple(map(int, second)), Fraction(weight))
            for first, second, weight in data["weighted"]
        )
        return record, value
    raise ValueError("unsupported corpus kind")


def evaluate(path: Path):
    record, prepared = _loaded(str(path.resolve()))
    data = record["input"]
    if record["kind"] == "direction":
        from sqpack.fractional.generate import placement_cells

        return placement_cells(
            *prepared, data["outer_side"], data["square_side"], keep=data["keep"]
        )
    if record["kind"] == "vertices":
        from sqpack.fractional.colgen import _vertices

        return _vertices(*prepared)
    if data["operation"] == "at":
        return prepared.at(Fraction(data["x"]), Fraction(data["y"]))
    if data["operation"] == "cost":
        return prepared.reduced_cost(
            tuple((Fraction(x), Fraction(y)) for x, y in data["orbit"]),
            Fraction(data["outer_side"]),
        )
    raise ValueError("unsupported exact operation")


def seal_corpus(root: Path) -> dict:
    target = root / "manifest.json"
    if target.exists():
        return validate_corpus(root)
    names = ("PACK_NATIVE_KERNELS", "PACK_NATIVE_STATS", "PACK_NATIVE_CAPTURE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ["PACK_NATIVE_KERNELS"] = "none"
    os.environ.pop("PACK_NATIVE_STATS", None)
    os.environ.pop("PACK_NATIVE_CAPTURE", None)
    items = []
    try:
        for path in sorted(root.glob("*.json")):
            record = json.loads(path.read_text())
            if record.get("kind") not in ("direction", "vertices", "exact"):
                continue
            value = evaluate(path)
            items.append(
                {
                    "file": path.name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "kind": record["kind"],
                    "bucket": record["bucket"],
                    "reference_signature": signature(value),
                }
            )
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value
        _loaded.cache_clear()
    if not items:
        raise ValueError("no complete captured inputs; first run a campaign with --capture")
    body = {
        "schema": 1,
        "items": items,
        "reference": "all experimental switches off",
        "note": "bounded real-input sample; kernel replay, not full-solver throughput",
    }
    body["id"] = hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()
    runtime.atomic_json(target, body)
    return body


def validate_corpus(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    content = {key: value for key, value in manifest.items() if key != "id"}
    if (
        hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()
        != manifest["id"]
    ):
        raise ValueError("sealed corpus manifest was changed")
    if not manifest["items"] or len(manifest["items"]) > 96:
        raise ValueError("invalid corpus size")
    for item in manifest["items"]:
        path = _path(root, item["file"])
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError(f"sealed input changed: {path.name}")
        record = json.loads(path.read_text())
        if "arrays" in record:
            array_path = _path(root, record["arrays"])
            if hashlib.sha256(array_path.read_bytes()).hexdigest() != record["arrays_sha256"]:
                raise ValueError(f"sealed arrays changed: {array_path.name}")
    return manifest


def _initialize(native: str, session: str, directory: str) -> None:
    os.environ.update(
        PACK_NATIVE_KERNELS=native,
        PACK_NATIVE_SESSION=session,
        PACK_NATIVE_STATS=directory,
        PACK_JOBS="1",
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
    )
    os.environ.pop("PACK_NATIVE_CAPTURE", None)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    runtime.preflight()


def _batch(root: str, items: list[dict]) -> tuple[int, float]:
    completed = 0
    began = time.monotonic()
    try:
        for item in items:
            actual = signature(evaluate(_path(Path(root), item["file"])))
            if actual != item["reference_signature"]:
                raise RuntimeError(f"native/reference mismatch in {item['file']}")
            completed += 1
        return completed, time.monotonic() - began
    finally:
        metrics.flush()


def replay_session(args) -> int:
    from devtools.native_ab import emit, finish_report, session_manifest, terminal_bell

    if not 1 <= args.workers <= 64 or args.minutes < 0 or args.rounds < 0:
        raise ValueError("invalid replay budget")
    corpus = args.corpus.resolve()
    manifest = validate_corpus(corpus)
    session = session_manifest("sealed-kernel-replay", args.native, args.workers, args.label)
    session["corpus_id"] = manifest["id"]
    session["corpus"] = str(corpus)
    session["items_per_epoch"] = len(manifest["items"])
    directory = args.output.resolve() / f"{int(time.time())}-{session['id'][:12]}"
    directory.mkdir(parents=True)
    runtime.atomic_json(directory / "session.json", session)
    stop = False

    def request(_signum, _frame):
        nonlocal stop
        stop = True

    old = {
        sig: signal.signal(sig, request)
        for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)
    }
    os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
    pool = ProcessPoolExecutor(
        max_workers=args.workers,
        mp_context=mp.get_context("spawn"),
        initializer=_initialize,
        initargs=(args.native, session["id"], str(directory / "processes")),
    )
    futures = set()
    cursor = completed = 0
    batch_size = 4
    submitted_batches = peak_in_flight = peak_batch_size = 0
    service_per_item = None
    started = time.monotonic()
    coordinator_started = time.process_time()
    next_progress = started
    next_notice = started + 60
    requested = None
    code = 0
    first_window = None
    limit = args.rounds * len(manifest["items"]) if args.rounds else None
    emit(
        f"replay corpus={manifest['id']} inputs={len(manifest['items'])} profile={args.native}"
    )
    try:
        while True:
            now = time.monotonic()
            if args.minutes and now - started >= args.minutes * 60:
                stop = True
            if stop and requested is None:
                requested = now
                first_window = {
                    "wall_seconds": now - started,
                    "metrics": metrics.aggregate(directory / "processes"),
                }
                runtime.atomic_json(directory / "stop-window.json", first_window)
                emit(
                    "draining at most one bounded batch per worker; no new tasks will be admitted"
                )
            while (
                not stop and len(futures) < args.workers and (limit is None or cursor < limit)
            ):
                count = batch_size if limit is None else min(batch_size, limit - cursor)
                batch = [
                    manifest["items"][(cursor + i) % len(manifest["items"])]
                    for i in range(count)
                ]
                cursor += count
                futures.add(pool.submit(_batch, str(corpus), batch))
                submitted_batches += 1
                peak_in_flight = max(peak_in_flight, len(futures))
                peak_batch_size = max(peak_batch_size, count)
            if not futures:
                break
            done, futures = wait(futures, timeout=0.2, return_when=FIRST_COMPLETED)
            for future in done:
                count, service = future.result()
                completed += count
                per_item = service / max(count, 1)
                service_per_item = (
                    per_item
                    if service_per_item is None
                    else 0.8 * service_per_item + 0.2 * per_item
                )
                # Aim at 50 ms worker service for tiny inputs, bounded at 64.
                # Long directions get one input per task. Fixed work/signatures
                # are unchanged; only transport granularity is adapted.
                batch_size = max(1, min(64, int(0.05 / max(service_per_item, 1e-9))))
            now = time.monotonic()
            if now >= next_progress:
                runtime.atomic_json(
                    directory / "progress.json",
                    {
                        "elapsed_seconds": now - started,
                        "completed_replays": completed,
                        "in_flight_batches": len(futures),
                        "batch_size": batch_size,
                        "coordinator_cpu_seconds": time.process_time() - coordinator_started,
                        "draining": stop,
                    },
                )
                next_progress = now + 1.0
            if now >= next_notice:
                emit(
                    f"replay completed={completed} rate={completed / max(now - started, 1e-9):.3f}/s "
                    f"in-flight={len(futures)} batch={batch_size}"
                )
                next_notice = now + 60
    except BaseException as exc:
        code = 1
        runtime.atomic_json(
            directory / "error.json", {"type": type(exc).__name__, "message": str(exc)}
        )
        terminal_bell(f"ERROR during replay: {type(exc).__name__}: {exc}", error=True)
        for future in futures:
            future.cancel()
        pool.terminate_workers()
        emit(f"FAILED: {exc}; results must not be used as an accepted speedup")
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        for sig, handler in old.items():
            signal.signal(sig, handler)
    session["coordinator_cpu_seconds"] = time.process_time() - coordinator_started
    session["submitted_batches"] = submitted_batches
    session["peak_in_flight"] = peak_in_flight
    session["peak_batch_size"] = peak_batch_size
    session["completed_replays"] = completed
    session["matched_output_checks"] = completed
    session["fully_completed_epochs"] = completed // len(manifest["items"])
    try:
        finish_report(
            directory,
            session,
            time.monotonic() - started,
            exit_code=code,
            drain=0.0 if requested is None else time.monotonic() - requested,
            first_window=first_window,
        )
    except Exception as exc:
        terminal_bell(
            f"ERROR while writing final replay report: {type(exc).__name__}: {exc}",
            error=True,
        )
        raise
    terminal_bell(
        "replay finished; final throughput report is ready"
        if code == 0
        else f"replay finished with exit={code}; inspect error/report artifacts",
        error=code != 0,
    )
    return code
