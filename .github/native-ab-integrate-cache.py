"""Keep filesystem hashing out of hot calls and attribute measured profiles."""
from pathlib import Path


def edit(path, old, new):
    p = Path(path)
    s = p.read_text()
    if s.count(old) != 1:
        raise RuntimeError(f"missing or duplicated anchor: {path}: {old[:60]}")
    p.write_text(s.replace(old, new, 1))


root = "packing/src/sqpack/fractional/"
edit(root + "native_ab_runtime.py", "\ndef source_digest() -> str:\n",
     "\n@lru_cache(maxsize=1)\ndef source_digest() -> str:\n")
edit(root + "native_ab_runtime.py", 'def build(*, core_only: bool = False) -> dict:\n',
     'def build(*, core_only: bool = False) -> dict:\n    source_digest.cache_clear()\n')
edit("packing/tests/test_native_ab_sessions.py", "import os\n", "")
# Fix an inherited test fixture, not the original branch or production policy.
edit("packing/tests/test_frontier_strategy_frontiers.py",
     'def test_status_labels_legacy_globals_and_shows_strategy_local_frontiers():\n    state = campaign()\n',
     'def test_status_labels_legacy_globals_and_shows_strategy_local_frontiers():\n    state = campaign()\n    state["unresolved"] = []\n')
# A selected-but-unused kernel is not a speedup result. Recovered work may retain
# an earlier native choice; expose that rather than presenting a mixed hour as A/B.
edit("packing/devtools/native_ab.py", '    report = {"schema": 1, "session": manifest,',
     '''    expected = {
        "prefix": ("prefix/c",), "topk": ("topk/c",),
        "scatter": ("scatter/c",), "compact": ("compact/c",),
        "vertices": ("vertices/c",), "exact-depth": ("exact-at/cpp", "exact-cost/cpp"),
    }
    not_exercised = [name for name in manifest["native"]["kernels"]
                     if not any(rows.get(key, {}).get("calls", 0) for key in expected[name])]
    desired = "+".join(manifest["native"]["kernels"]) or "none"
    observed = sorted(key.split("/", 1)[1] for key in rows if key.startswith("direction/"))
    mixed = bool(observed and observed != [desired])
    report = {"schema": 1, "session": manifest,''')
edit("packing/devtools/native_ab.py", '        "metrics": rows, "campaign_delta": campaign_delta,',
     '        "metrics": rows, "not_exercised": not_exercised, "mixed_direction_profiles": mixed,\n        "observed_direction_profiles": observed, "campaign_delta": campaign_delta,')
edit("packing/devtools/native_ab.py", '    if campaign_delta:\n',
     '    if not_exercised:\n        lines.append("SELECTED BUT NOT EXERCISED: " + ",".join(not_exercised))\n    if mixed:\n        lines.append("MIXED PROFILE: recovered work retained an older profile; use sealed replay for a clean comparison")\n    if campaign_delta:\n')
edit("packing/devtools/native_ab.py",
     '    commands.add_parser("doctor", help="show selected profile, build identity and native readiness")',
     '    doctor = commands.add_parser("doctor", help="show selected profile, build identity and native readiness")\n    doctor.add_argument("--native", default="none")')
edit("packing/devtools/native_ab.py", '    if args.command == "doctor":\n        print',
     '    if args.command == "doctor":\n        os.environ["PACK_NATIVE_KERNELS"] = args.native\n        print')
# No fsync after every tiny replay task. Multiprocessing finalizers perform the
# full final flush; completed-work snapshots remain throttled to once per second.
edit(root + "native_ab_hooks.py", '            metrics.flush(force=True)\n',
     '            metrics.flush()\n')
edit("packing/devtools/native_ab_replay.py", 'def _batch(root: str, items: list[dict]) -> int:\n    completed = 0\n',
     'def _batch(root: str, items: list[dict]) -> tuple[int, float]:\n    completed = 0\n    began = time.monotonic()\n')
edit("packing/devtools/native_ab_replay.py", '        return completed\n    finally:\n        metrics.flush(force=True)\n',
     '        return completed, time.monotonic() - began\n    finally:\n        metrics.flush()\n')
edit("packing/devtools/native_ab_replay.py", '    cursor = completed = 0\n    started = time.monotonic()\n',
     '    cursor = completed = 0\n    batch_size = 4\n    submitted_batches = peak_in_flight = peak_batch_size = 0\n    service_per_item = None\n    started = time.monotonic()\n    coordinator_started = time.process_time()\n    next_progress = started\n    next_notice = started + 60\n')
edit("packing/devtools/native_ab_replay.py", '                emit("draining at most one four-input batch per worker")',
     '                emit("draining at most one bounded batch per worker; no new tasks will be admitted")')
edit("packing/devtools/native_ab_replay.py", '                count = 4 if limit is None else min(4, limit - cursor)',
     '                count = batch_size if limit is None else min(batch_size, limit - cursor)')
edit("packing/devtools/native_ab_replay.py", '                futures.add(pool.submit(_batch, str(corpus), batch))\n',
     '                futures.add(pool.submit(_batch, str(corpus), batch))\n                submitted_batches += 1\n                peak_in_flight = max(peak_in_flight, len(futures))\n                peak_batch_size = max(peak_batch_size, count)\n')
edit("packing/devtools/native_ab_replay.py", '            for future in done:\n                completed += future.result()\n            runtime.atomic_json(directory / "progress.json", {"elapsed_seconds": time.monotonic() - started,\n                "completed_replays": completed, "in_flight_batches": len(futures), "draining": stop})',
     '''            for future in done:
                count, service = future.result()
                completed += count
                per_item = service / max(count, 1)
                service_per_item = (per_item if service_per_item is None
                                    else 0.8 * service_per_item + 0.2 * per_item)
                # Aim at 50 ms worker service for tiny inputs, bounded at 64.
                # Long directions get one input per task. Fixed work/signatures
                # are unchanged; only transport granularity is adapted.
                batch_size = max(1, min(64, int(0.05 / max(service_per_item, 1e-9))))
            now = time.monotonic()
            if now >= next_progress:
                runtime.atomic_json(directory / "progress.json", {
                    "elapsed_seconds": now - started, "completed_replays": completed,
                    "in_flight_batches": len(futures), "batch_size": batch_size,
                    "coordinator_cpu_seconds": time.process_time() - coordinator_started,
                    "draining": stop})
                next_progress = now + 1.0
            if now >= next_notice:
                emit(f"replay completed={completed} rate={completed / max(now-started, 1e-9):.3f}/s "
                     f"in-flight={len(futures)} batch={batch_size}")
                next_notice = now + 60''')
edit("packing/devtools/native_ab_replay.py", '    session["completed_replays"] = completed\n',
     '    session["coordinator_cpu_seconds"] = time.process_time() - coordinator_started\n    session["submitted_batches"] = submitted_batches\n    session["peak_in_flight"] = peak_in_flight\n    session["peak_batch_size"] = peak_batch_size\n    session["completed_replays"] = completed\n')
# Pin BLAS environment before spawn imports NumPy, not only in its initializer.
edit("packing/devtools/native_ab_replay.py", '    pool = ProcessPoolExecutor(max_workers=args.workers,',
     '    os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")\n    pool = ProcessPoolExecutor(max_workers=args.workers,')
