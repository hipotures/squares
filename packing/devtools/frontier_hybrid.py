"""Isolated fixed-target hybrid experiments; never resume a production frontier here."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import signal
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from sqpack.fractional.hybrid_support import load_measure

REPO = Path(__file__).resolve().parents[2]
PACKING = REPO / "packing"
PROFILE = Path(__file__).with_name("hybrid_profile.json")


class Stop:
    def __init__(self, minutes: float):
        self.requested = False
        self.deadline = time.monotonic() + minutes * 60 if minutes > 0 else float("inf")

    def poll(self) -> None:
        self.requested = self.requested or time.monotonic() >= self.deadline

    def signal(self, _number: int, _frame: Any) -> None:
        self.requested = True


def configuration(args: argparse.Namespace) -> dict[str, Any]:
    config = json.loads(PROFILE.read_text(encoding="utf-8"))
    for key in ("workers", "stage_seconds", "verify_seconds", "column_rounds", "row_rounds", "columns_per_round", "seed_map", "direction_steps", "shrink"):
        value = getattr(args, key, None)
        if value is not None:
            config[key] = value
    config["shrink"] = str(Fraction(config["shrink"]))
    if min(config[k] for k in ("workers", "column_rounds", "row_rounds", "columns_per_round", "direction_steps")) < 1:
        raise ValueError("worker, round and net budgets must be positive")
    if not 0 < Fraction(config["shrink"]) < 1:
        raise ValueError("shrink must be strictly between zero and one")
    gap = Fraction(config["angle_limit"]) / config["direction_steps"]
    if Fraction(config["shrink"]) * (1 + gap) >= 1:
        raise ValueError("the fixed-B net does not satisfy strict containment")
    if min(config["stage_seconds"], config["verify_seconds"]) <= 0:
        raise ValueError("wall budgets must be positive")
    return config


def emit(text: str) -> None:
    print(f"[{int(time.time())}] [hybrid] {text}", flush=True)


def campaign(args: argparse.Namespace) -> int:
    from devtools import frontier_runtime as runtime
    from devtools.frontier_io import atomic_json, digest, read_json
    from devtools.frontier_hybrid_external import EXTERNAL

    config = configuration(args)
    root = args.root.resolve()
    if (root / "state.json").exists():
        raise ValueError("this is a production frontier root; choose a new hybrid experiment directory")
    paths = args.seed or [EXTERNAL / "s12/certificates/s12_lower_3.9686.txt"]
    sources = [{"path": str(path.resolve()), "sha256": load_measure(path, pinned_record=(not args.seed)).sha256} for path in paths]
    sides = [str(Fraction(side)) for side in (args.target or config["targets"])]
    if len(set(sides)) != len(sides) or any(not 1 < Fraction(side) < 4 for side in sides):
        raise ValueError("targets must be distinct rational sides between 1 and 4")
    identity = {"config": config, "sources": sources, "targets": sides,
                "code_sha256": runtime.code_fingerprint(PACKING)}
    root.mkdir(parents=True, exist_ok=True)
    with (root / "hybrid.lock").open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state_path = root / "hybrid-state.json"
        if state_path.exists():
            if not args.resume:
                raise ValueError("experiment already exists; use --resume with the same settings")
            state = read_json(state_path)
            if state.get("identity") != identity:
                raise ValueError("code, configuration or seed changed; use a new experiment root")
        else:
            if args.resume:
                raise ValueError("there is no hybrid experiment to resume")
            if any(p.name != "hybrid.lock" for p in root.iterdir()):
                raise ValueError("new experiment root must be empty")
            saved_sources = []
            for i, source in enumerate(sources):
                path = Path(source["path"])
                saved = root / "sources" / f"{i:03d}{path.suffix}"
                saved.parent.mkdir(exist_ok=True)
                saved.write_bytes(path.read_bytes())
                if digest(saved) != source["sha256"]:
                    raise ValueError("seed changed while copying it")
                saved_sources.append({"path": str(saved), "sha256": digest(saved)})
            state = {"schema": "hybrid-campaign/v1", "identity": identity, "sources": saved_sources,
                     "tasks": [{"side": side, "status": "PENDING"} for side in sides]}
            atomic_json(state_path, state)
        for source in state["sources"]:
            if digest(Path(source["path"])) != source["sha256"]:
                raise ValueError("archived source measure changed")
        stop = Stop(args.minutes)
        old_handlers = {sig: signal.signal(sig, stop.signal) for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)}
        environment = dict(os.environ, PACK_JOBS=str(config["workers"]), OMP_NUM_THREADS="1",
                           OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
        try:
            for index, task in enumerate(state["tasks"]):
                if task["status"] in ("VERIFIED", "REJECTED", "UNRESOLVED", "ERROR"):
                    if task.get("verified_candidate") and digest(Path(task["verified_candidate"])) != task["verified_sha256"]:
                        raise ValueError("retained artifact changed after verification")
                    continue
                stop.poll()
                if stop.requested and task["status"] == "PENDING":
                    break
                directory = root / f"target-{index:03d}"
                directory.mkdir(exist_ok=True)
                manifest = directory / "manifest.json"
                body = {"config": config, "sources": state["sources"], "side": task["side"]}
                if not manifest.exists():
                    atomic_json(manifest, body)
                elif read_json(manifest) != body:
                    raise ValueError("job manifest changed")
                result_path = directory / "result.json"
                candidate = directory / "candidate.json"
                task["status"] = "RUNNING"
                atomic_json(state_path, state)
                emit(f"variant={config['variant']} side={task['side']} mode={config['mode']}")
                code = runtime.run(
                    [sys.executable, "-m", "devtools.frontier_hybrid_worker", "--manifest", str(manifest),
                     "--json", str(result_path), "--freeze", str(candidate)], directory / "generation.log",
                    cwd=PACKING, env=environment,
                    limits={"stage_seconds": config["stage_seconds"], "verify_seconds": config["stage_seconds"],
                            "max_rss_mib": config["max_rss_mib"], "heartbeat_seconds": 60},
                    on_poll=stop.poll, heartbeat=lambda elapsed: emit(f"generation running {elapsed:.0f}s"))
                if code:
                    task.update(status="ERROR", returncode=code)
                else:
                    result = read_json(result_path)
                    task["generation"] = result
                    task["status"] = "UNRESOLVED"
                    if result["status"] == "CANDIDATE" and result["mass"] is not None and Fraction(result["mass"]) < 12:
                        if digest(candidate) != result["candidate_sha256"]:
                            raise ValueError("candidate differs from the generation receipt")
                        gate = directory / "gate/verification.json"
                        code = runtime.run(
                            [sys.executable, "-m", "devtools.frontier_verify", "--input", str(candidate),
                             "--side", task["side"], "--report", str(gate)], directory / "gate.log",
                            cwd=PACKING, env=environment,
                            limits={"verify_seconds": config["verify_seconds"], "max_rss_mib": config["max_rss_mib"],
                                    "heartbeat_seconds": 60}, on_poll=stop.poll,
                            heartbeat=lambda elapsed: emit(f"full gate running {elapsed:.0f}s"))
                        if code:
                            task.update(status="ERROR", returncode=code)
                        else:
                            from devtools.frontier_verify import checked_receipt
                            report = checked_receipt(gate, candidate, Fraction(task["side"]))
                            if report is None:
                                raise ValueError("missing or unbound full-gate receipt")
                            task["status"] = report["status"]
                            task["verification"] = report
                            if report["status"] == "VERIFIED":
                                task.update(verified_candidate=report["verified_candidate"], verified_sha256=report["verified_sha256"])
                                emit(f"VERIFIED s(12) >= {task['side']} sha256={report['verified_sha256']}")
                atomic_json(state_path, state)
                emit(f"completed side={task['side']} status={task['status']}")
                if task["status"] == "ERROR":
                    return 70
                stop.poll()
                if stop.requested:
                    break
        finally:
            for sig, handler in old_handlers.items():
                signal.signal(sig, handler)
        emit(f"saved {state_path}; no production frontier state was changed")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--root", type=Path, required=True)
    run.add_argument("--seed", type=Path, action="append")
    run.add_argument("--target", action="append")
    run.add_argument("--resume", action="store_true")
    run.add_argument("--minutes", type=float, default=60)
    for flag in ("workers", "column-rounds", "row-rounds", "columns-per-round", "direction-steps"):
        run.add_argument(f"--{flag}", type=int)
    for flag in ("stage-seconds", "verify-seconds"):
        run.add_argument(f"--{flag}", type=float)
    run.add_argument("--shrink")
    run.add_argument("--seed-map", choices=("scale", "centre"))
    prepare = commands.add_parser("prepare-external")
    prepare.add_argument("--root", type=Path, required=True, help="directory for the build log")
    check = commands.add_parser("check-external")
    check.add_argument("--root", type=Path, required=True)
    check.add_argument("--workers", type=int, default=1)
    check.add_argument("--seconds", type=float, default=7200)
    args = parser.parse_args(argv)
    if args.command == "run":
        return campaign(args)
    from devtools.frontier_hybrid_external import EXTERNAL, check_cover, prepare as build
    if args.command == "prepare-external":
        build(EXTERNAL, args.root.resolve() / "build.log", 1200)
    else:
        source = EXTERNAL / "s12/certificates/s12_lower_3.9686.txt"
        load_measure(source, pinned_record=True)
        report = check_cover(source, EXTERNAL, args.root.resolve(), Fraction(15680, 3951),
                             workers=args.workers, seconds=args.seconds)
        emit(f"external control: {report['status']}")
        return 0 if report["status"] == "VERIFIED" else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
