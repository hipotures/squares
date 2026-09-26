"""Manual native A/B sessions: build, campaign, sealed replay, and durable reports."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import signal
import subprocess
import sys
import time
import uuid
from fractions import Fraction
from pathlib import Path

from sqpack.fractional import native_ab_metrics as metrics
from sqpack.fractional import native_ab_runtime as runtime

PACKING = Path(__file__).resolve().parents[1]
UNITS = {
    "direction": "site_visits",
    "event-cells": "event_cells",
    "prefix": "grid_values",
    "topk": "scores",
    "scatter": "corner_updates",
    "compact": "copied_values",
    "vertices": "line_pairs",
    "depth-survey": "point_square_queries",
    "exact-at": "point_square_queries",
    "exact-cost": "point_square_queries",
    "lp": "dense_matrix_entries",
    "simplex-iterations": "simplex_iterations",
}


def emit(message: str) -> None:
    print(f"[{int(time.time())}] [native-ab] {message}", flush=True)


def terminal_bell(message: str, *, error: bool = False) -> None:
    """Emit a console BEL plus a visible reason; errors use a double bell."""

    bells = "\a\a" if error else "\a"
    print(f"{bells}[native-ab] {message}", file=sys.stderr, flush=True)


def _state(root: Path) -> dict:
    path = root / "state.json"
    return json.loads(path.read_text()) if path.is_file() else {}


def _completed(state: dict) -> set[str]:
    return {
        stage.get("directory", f"{i}:{j}")
        for i, cycle in enumerate(state.get("cycles", []))
        for j, stage in enumerate(cycle.get("stages", []))
        if stage.get("status") == "complete"
    }


def session_manifest(kind: str, native: str, workers: int, label: str) -> dict:
    os.environ["PACK_NATIVE_KERNELS"] = native
    checked = runtime.preflight()
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=PACKING, capture_output=True, text=True, check=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "diff", "--stat"], cwd=PACKING, capture_output=True, text=True, check=True
    ).stdout
    return {
        "schema": 1,
        "id": uuid.uuid4().hex,
        "kind": kind,
        "label": label,
        "started_epoch": time.time(),
        "commit": commit,
        "tracked_diff": dirty,
        "python": sys.version,
        "platform": platform.platform(),
        "workers": workers,
        "cpu_affinity": sorted(os.sched_getaffinity(0)),
        "libraries": {
            name: importlib.metadata.version(name) for name in ("numpy", "scipy", "highspy")
        },
        "native": checked,
        "rates_are_inclusive": True,
        "units_are_logical_work_not_machine_instructions": True,
    }


def finish_report(
    directory: Path,
    manifest: dict,
    wall: float,
    *,
    exit_code: int,
    drain: float = 0.0,
    campaign_delta: dict | None = None,
    first_window: dict | None = None,
) -> dict:
    counts = metrics.aggregate(directory / "processes")
    rows = {}
    for key, values in counts.items():
        name = key.split("/", 1)[0]
        rows[key] = {
            **values,
            "unit": UNITS.get(name, "items"),
            "calls_per_wall_second": values["calls"] / wall if wall else 0.0,
            "units_per_wall_second": values["units"] / wall if wall else 0.0,
            "units_per_kernel_cpu_second": values["units"] / values["cpu_s"]
            if values["cpu_s"]
            else None,
            "units_per_kernel_worker_second": values["units"] / values["wall_s"]
            if values["wall_s"]
            else None,
        }
    expected = {
        "prefix": ("prefix/c",),
        "topk": ("topk/c",),
        "scatter": ("scatter/c",),
        "compact": ("compact/c",),
        "vertices": ("vertices/c",),
        "exact-depth": ("exact-at/cpp", "exact-cost/cpp"),
    }
    not_exercised = [
        name
        for name in manifest["native"]["kernels"]
        if not any(rows.get(key, {}).get("calls", 0) for key in expected[name])
    ]
    desired = "+".join(manifest["native"]["kernels"]) or "none"
    observed = sorted(key.split("/", 1)[1] for key in rows if key.startswith("direction/"))
    mixed = bool(observed and observed != [desired])
    report = {
        "schema": 1,
        "session": manifest,
        "wall_seconds": wall,
        "drain_seconds": drain,
        "exit_code": exit_code,
        "completed": exit_code == 0,
        "metrics": rows,
        "not_exercised": not_exercised,
        "mixed_direction_profiles": mixed,
        "observed_direction_profiles": observed,
        "campaign_delta": campaign_delta,
        "first_window": first_window,
        "accounting": "completed calls only; snapshots summed once; reused artifacts receive no kernel credit",
        "crash_limit": "abnormal termination may lose approximately the final 1 s of completed work per process",
        "comparison": "live campaign hours are unmatched; use the same sealed replay manifest for causal A/B comparisons",
    }
    runtime.atomic_json(directory / "performance.json", report)
    lines = [
        "NATIVE A/B THROUGHPUT SUMMARY",
        f"kind={manifest['kind']} label={manifest['label']}",
        f"enabled={','.join(manifest['native']['kernels']) or 'none'} workers={manifest['workers']}",
        f"session={wall:.3f}s drain={drain:.3f}s exit={exit_code}",
        "kernel/backend                      calls/s       units/s          units/CPU-s",
    ]
    for key, row in sorted(rows.items()):
        cpu_rate = row["units_per_kernel_cpu_second"]
        cpu_text = "n/a" if cpu_rate is None else f"{cpu_rate:.3f}"
        lines.append(
            f"{key:35s} {row['calls_per_wall_second']:10.3f} "
            f"{row['units_per_wall_second']:13.3f} {cpu_text:>20s} {row['unit']}"
        )
    if not_exercised:
        lines.append("SELECTED BUT NOT EXERCISED: " + ",".join(not_exercised))
    if mixed:
        lines.append(
            "MIXED PROFILE: recovered work retained an older profile; use sealed replay for a clean comparison"
        )
    if campaign_delta:
        lines.append(
            f"new completed stages/hour={campaign_delta['completed_stages'] * 3600 / max(wall, 1e-9):.3f}"
        )
        lines.append(
            f"new verified bound improvements/hour={campaign_delta['bound_improvements'] * 3600 / max(wall, 1e-9):.3f}"
        )
    lines.extend(
        [
            "Inclusive kernel timings overlap; do not sum them.",
            "Compare workload-size bins and sealed replay IDs, not unrelated hourly totals.",
            f"JSON: {directory / 'performance.json'}",
        ]
    )
    text = "\n".join(lines)
    (directory / "performance.txt").write_text(text + "\n")
    print("\n" + text, flush=True)
    return report


def campaign(args: argparse.Namespace, extra: list[str]) -> int:
    if args.workers < 1 or args.workers > 64 or args.minutes < 0:
        raise ValueError("invalid worker count or session duration")
    root = args.root.resolve()
    manifest = session_manifest(
        "live-campaign-unmatched", args.native, args.workers, args.label
    )
    before = _state(root)
    manifest["initial_verified"] = before.get("verified_low")
    manifest["root"] = str(root)
    directory = (
        root.parent / (root.name + "-native-runs") / f"{int(time.time())}-{manifest['id'][:12]}"
    )
    directory.mkdir(parents=True)
    runtime.atomic_json(directory / "session.json", manifest)
    environment = dict(
        os.environ,
        PACK_JOBS=str(args.workers),
        OMP_NUM_THREADS="1",
        OPENBLAS_NUM_THREADS="1",
        MKL_NUM_THREADS="1",
        PACK_NATIVE_SESSION=manifest["id"],
        PACK_NATIVE_STATS=str(directory / "processes"),
        PACK_NATIVE_STARTED_FILE=str(directory / "controller-ready.json"),
    )
    if args.capture is not None:
        environment["PACK_NATIVE_CAPTURE"] = str(args.capture.resolve())
    else:
        environment.pop("PACK_NATIVE_CAPTURE", None)
    command = [
        sys.executable,
        "-m",
        "devtools.run_n12_frontier",
        "--root",
        str(root),
        "--workers",
        str(args.workers),
        "--generation-trials",
        str(args.generation_trials),
    ]
    if args.resume:
        command.append("--resume")
    command.extend(extra[1:] if extra[:1] == ["--"] else extra)
    manifest["command"] = command
    runtime.atomic_json(directory / "session.json", manifest)
    emit(f"profile={args.native} session={directory}; Ctrl-C drains current bounded work")
    started = time.monotonic()
    requested: float | None = None
    first_window = None
    child = None
    old = {}
    stop_pending = False

    def request(_signum, _frame):
        nonlocal stop_pending
        stop_pending = True

    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        old[signum] = signal.signal(signum, request)
    code = 70
    try:
        child = subprocess.Popen(command, cwd=PACKING, env=environment, start_new_session=True)
        next_update = started
        while child.poll() is None:
            now = time.monotonic()
            if args.minutes and now - started >= args.minutes * 60:
                stop_pending = True
            if (
                stop_pending
                and requested is None
                and (directory / "controller-ready.json").exists()
            ):
                requested = now
                first_window = {
                    "wall_seconds": now - started,
                    "metrics": metrics.aggregate(directory / "processes"),
                    "snapshot_lag_seconds_approximately": 1.0,
                }
                runtime.atomic_json(directory / "stop-window.json", first_window)
                child.send_signal(signal.SIGINT)
                emit(
                    "graceful stop requested; waiting for the current bounded work, then reporting throughput"
                )
            if now >= next_update:
                runtime.atomic_json(
                    directory / "progress.json",
                    {
                        "elapsed_seconds": now - started,
                        "draining": requested is not None,
                        "child_pid": child.pid,
                    },
                )
                next_update = now + 5.0
            time.sleep(0.2)
        code = child.wait()
    except Exception as exc:
        code = 70
        runtime.atomic_json(
            directory / "error.json", {"type": type(exc).__name__, "message": str(exc)}
        )
        terminal_bell(
            f"ERROR {type(exc).__name__}: {exc}; draining owned campaign work",
            error=True,
        )
        if child is not None and child.poll() is None:
            child.send_signal(signal.SIGINT)
            child.wait()
    finally:
        for signum, handler in old.items():
            signal.signal(signum, handler)
    wall = time.monotonic() - started
    after = _state(root)
    delta = {
        "completed_stages": len(_completed(after) - _completed(before)),
        "bound_improvements": len(
            {e["id"] for e in after.get("discoveries", [])}
            - {e["id"] for e in before.get("discoveries", [])}
        ),
        "initial_verified": before.get("verified_low"),
        "final_verified": after.get("verified_low"),
    }
    if before.get("verified_low") and after.get("verified_low"):
        delta["exact_bound_gain"] = str(
            Fraction(after["verified_low"]) - Fraction(before["verified_low"])
        )
    try:
        finish_report(
            directory,
            manifest,
            wall,
            exit_code=code,
            drain=0.0 if requested is None else time.monotonic() - requested,
            campaign_delta=delta,
            first_window=first_window,
        )
    except Exception as exc:
        terminal_bell(
            f"ERROR while writing final campaign report: {type(exc).__name__}: {exc}",
            error=True,
        )
        raise
    terminal_bell(
        "campaign finished; final throughput report is ready"
        if code == 0
        else f"campaign finished with exit={code}; inspect error/report artifacts",
        error=code != 0,
    )
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    builder = commands.add_parser(
        "build", help="compile explicit local libraries; never runs a search"
    )
    builder.add_argument("--core-only", action="store_true")
    doctor = commands.add_parser(
        "doctor", help="show selected profile, build identity and native readiness"
    )
    doctor.add_argument("--native", default="none")
    run = commands.add_parser(
        "campaign", help="run real frontier work with an isolated measurement session"
    )
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--resume", action="store_true")
    run.add_argument("--native", default="none")
    run.add_argument("--workers", type=int, default=16)
    run.add_argument("--generation-trials", type=int, default=3)
    run.add_argument("--minutes", type=float, default=60)
    run.add_argument("--label", default="manual")
    run.add_argument("--capture", type=Path)
    seal = commands.add_parser(
        "seal", help="freeze captured inputs and calculate independent reference signatures"
    )
    seal.add_argument("--corpus", type=Path, required=True)
    replay = commands.add_parser(
        "replay", help="bounded replay of exactly the same real captured inputs"
    )
    replay.add_argument("--corpus", type=Path, required=True)
    replay.add_argument("--output", type=Path, required=True)
    replay.add_argument("--native", default="none")
    replay.add_argument("--workers", type=int, default=16)
    replay.add_argument("--minutes", type=float, default=60)
    replay.add_argument("--label", default="replay")
    replay.add_argument(
        "--rounds", type=int, default=0, help="optional finite replay epochs for smoke tests"
    )
    report = commands.add_parser(
        "report", help="read a finished or interrupted measurement without running computation"
    )
    report.add_argument("--session", type=Path, required=True)
    args, extra = parser.parse_known_args(argv)
    if extra and args.command != "campaign":
        parser.error(f"unexpected arguments: {extra}")
    if args.command == "build":
        print(json.dumps(runtime.build(core_only=args.core_only), indent=2))
        return 0
    if args.command == "doctor":
        os.environ["PACK_NATIVE_KERNELS"] = args.native
        print(json.dumps(runtime.preflight(), indent=2))
        return 0
    if args.command == "campaign":
        return campaign(args, extra)
    if args.command in ("seal", "replay"):
        from devtools.native_ab_replay import replay_session, seal_corpus

        if args.command == "seal":
            print(json.dumps(seal_corpus(args.corpus.resolve()), indent=2))
            return 0
        return replay_session(args)
    path = args.session.resolve()
    if (path / "performance.txt").is_file():
        print((path / "performance.txt").read_text())
    else:
        manifest = json.loads((path / "session.json").read_text())
        progress = json.loads((path / "progress.json").read_text())
        print(
            json.dumps(
                {
                    "incomplete_session": manifest,
                    "last_live_elapsed_seconds": progress["elapsed_seconds"],
                    "completed_work_snapshot": metrics.aggregate(path / "processes"),
                },
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    try:
        status = main()
    except BaseException as exc:
        terminal_bell(f"ERROR {type(exc).__name__}: {exc}", error=True)
        raise
    raise SystemExit(status)
