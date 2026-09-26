"""Durable strategy cohorts around the unchanged single-cycle decision policy.

Only generation stages run concurrently. Completed stages are interpreted in
cohort order and full proof gates run after a generation wave has drained, so
verification cannot multiply the global CPU budget. Every cycle has its own
artifacts; a speculative sibling never overwrites an earlier verified result.
"""
from __future__ import annotations

import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools import frontier_policy
from devtools.frontier_io import atomic_json, digest, read_json


def select_plans(state: dict[str, Any], first: dict[str, Any]) -> list[dict[str, Any]]:
    maximum = min(int(state["config"].get("generation_trials", 3)),
                  int(state["config"]["workers"]))
    limit = state["config"].get("max_cycles")
    if limit is not None:
        maximum = min(maximum, max(1, int(limit) - len(state["cycles"])))
    # Do not let speculative generation delay an already useful precision fix.
    if first.get("reason", "").startswith("untried same-side rationalisation"):
        maximum = 1
    plans = [first]
    for name in state["config"]["strategies"]:
        if len(plans) >= maximum:
            break
        if name == first["strategy"]:
            continue
        choice = frontier_policy.strategy_proposal(state, name)
        if choice is not None:
            plans.append(choice)
    return plans


def refill_resumed_cohort(root: Path, state: dict[str, Any], frontier) -> list[int]:
    """Restore generation parallelism after a graceful stop left a partial cohort."""
    active = [
        index for index in state.get("active_generation", [])
        if state["cycles"][index].get("status") in ("RUNNING", "INTERRUPTED")
    ]
    if not active:
        return []
    cycles = [state["cycles"][index] for index in active]
    # Interpret already-generated results before speculating on fresh work: one
    # of them may move the verified bound and make a new sibling redundant.
    if any(
        stage.get("status") == "generated"
        for cycle in cycles
        for stage in cycle.get("stages", [])
    ):
        return []
    # Same-side precision repair deliberately owns the cohort by itself.
    if any(
        cycle.get("plan_reason", "").startswith("untried same-side rationalisation")
        for cycle in cycles
    ):
        return []

    maximum = min(
        int(state["config"].get("generation_trials", 3)),
        int(state["config"]["workers"]),
    )
    room = maximum - len(active)
    limit = state["config"].get("max_cycles")
    if limit is not None:
        room = min(room, max(0, int(limit) - len(state["cycles"])))
    if room <= 0:
        return []

    occupied = {cycle.get("strategy", "baseline") for cycle in cycles}
    plans = []
    for name in state["config"]["strategies"]:
        if len(plans) >= room:
            break
        if name in occupied:
            continue
        choice = frontier_policy.strategy_proposal(state, name)
        if choice is None:
            continue
        plans.append(choice)
        occupied.add(name)
    if not plans:
        return []

    added = []
    for plan in plans:
        cycle = {
            "side": plan["side"],
            "strategy": plan["strategy"],
            "search_revision": state.get("search_revision", 0),
            "plan_reason": plan["reason"],
            "status": "RUNNING",
            "started_at": frontier.stamp(),
            "seed_verified_low": state["verified_low"],
            "stages": [],
        }
        index = len(state["cycles"])
        state["cycles"].append(cycle)
        state["active_generation"].append(index)
        added.append(index)
    frontier.save_state(root, state)
    frontier.emit(
        root,
        f"[portfolio] resumed-refill={len(added)} "
        f"active={len(state['active_generation'])}/{maximum} "
        f"strategies={','.join(state['cycles'][i].get('strategy', 'baseline') for i in state['active_generation'])}",
    )
    return added


def _finish_wave(root: Path, state: dict[str, Any], frontier) -> None:
    wave = state["generation_wave"]
    directory = Path(wave["directory"])
    manifest_path = directory / "manifest.json"
    if digest(manifest_path) != wave["manifest_sha256"]:
        raise ValueError("generation wave manifest changed after scheduling")
    code = frontier.run_child(wave["command"], directory / "stdout.log", frontier.controlled_env(state))
    report_path = directory / "report.json"
    if code or not report_path.exists():
        for index, stage_index in wave["stages"]:
            cycle = state["cycles"][index]
            stage = cycle["stages"][stage_index]
            if stage["status"] == "queued":
                frontier.record_job_failure(root, state, cycle, stage, code or 70)
        state["generation_wave"] = None
        frontier.save_state(root, state)
        return
    report = read_json(report_path)
    if report.get("manifest_sha256") != wave["manifest_sha256"] or report.get("finished") is not True:
        raise ValueError("generation wave lacks a bound completion report")
    for index, stage_index in wave["stages"]:
        cycle = state["cycles"][index]
        stage = cycle["stages"][stage_index]
        record = report["jobs"][f"cycle-{index}"]
        if stage["status"] != "queued":
            continue  # Crash after adoption: never apply a completed result twice.
        for path, expected in record["outputs"].items():
            current = digest(Path(path)) if Path(path).is_file() else None
            if current != expected:
                raise ValueError(f"generation output changed after completion: {path}")
        stage["generation_scheduler"] = record
        stage["wave_metrics"] = report["metrics"]
        if record["returncode"]:
            frontier.record_job_failure(root, state, cycle, stage, int(record["returncode"]))
            continue
        result = read_json(Path(stage["directory"]) / "result.json")
        if result["settings"].get("n") != 12 or Fraction(result["settings"]["outer_side"]) != Fraction(cycle["side"]):
            raise ValueError("generation output belongs to another problem")
        stage.update(status="generated", result=result)
    state["generation_wave"] = None
    frontier.save_state(root, state)
    metrics = report["metrics"]
    frontier.emit(root, f"[generation-wave] completed wall={metrics['wall_seconds']:.3f}s "
                  f"coordinator_cpu={metrics['coordinator_cpu_seconds']:.3f}s "
                  f"driver_cpu={metrics['driver_cpu_seconds']:.3f}s "
                  f"direction_cpu={metrics['worker_cpu_seconds']:.3f}s "
                  f"max_busy={metrics['max_busy']}/{metrics['slots']}")



def retire_superseded(root: Path, state: dict[str, Any], frontier) -> None:
    """Do not start further generation at/below an already certified side.

    Called only after a wave drains, never while its children are running. A
    generated result already on disk remains auditable; no verifier verdict is
    invented. On crash/resume the terminal status makes retirement idempotent.
    """
    if state.get("generation_wave"):
        return  # Its completion has not yet been adopted; never retire live work.
    low = Fraction(state["verified_low"])
    for index in list(state.get("active_generation", [])):
        cycle = state["cycles"][index]
        if cycle["status"] not in ("RUNNING", "INTERRUPTED") or Fraction(cycle["side"]) > low:
            continue
        cycle.update(status="UNRESOLVED", superseded_by=str(low),
                     reason="superseded by a verified bound at or above this target; no further generation",
                     finished_at=frontier.stamp())
        for stage in cycle.get("stages", []):
            if stage.get("status") == "queued":
                stage.update(status="superseded", reason=cycle["reason"])
                atomic_json(Path(stage["directory"]) / "metadata.json", stage)
        state["active_generation"].remove(index)
        if state.get("active") == index:
            state["active"] = None
        frontier.save_state(root, state)
        frontier.emit(root, f"[superseded] cycle={index + 1} strategy={cycle.get('strategy', 'baseline')} "
                      f"L={frontier.display(cycle['side'])} verified-through={frontier.display(low)}; no new stage")


def run_portfolio(root: Path, state: dict[str, Any], frontier=None) -> None:
    if frontier is None:
        from devtools import run_n12_frontier as frontier

    stop_requested = getattr(frontier, "stop_requested", lambda: False)
    resumed_generation = bool(state.get("active_generation"))

    if not state.get("active_generation"):
        if state.get("active") is not None:
            # Finish an existing pre-upgrade cycle before admitting new siblings.
            state["active_generation"] = [state["active"]]
        else:
            first = state.pop("scheduled_work")
            plans = select_plans(state, first)
            indices = []
            for plan in plans:
                cycle = {"side": plan["side"], "strategy": plan["strategy"],
                         "search_revision": state.get("search_revision", 0),
                         "plan_reason": plan["reason"], "status": "RUNNING",
                         "started_at": frontier.stamp(), "seed_verified_low": state["verified_low"],
                         "stages": []}
                indices.append(len(state["cycles"]))
                state["cycles"].append(cycle)
            state["active_generation"] = indices
            frontier.emit(root, f"[portfolio] admitted={len(indices)} slots={state['config']['workers']} "
                          f"strategies={','.join(p['strategy'] for p in plans)} "
                          f"targets={','.join(p['strategy'] + '@' + frontier.display(p['side']) for p in plans)}")
        state["active"] = None
        frontier.save_state(root, state)
    if resumed_generation and not stop_requested():
        refill_resumed_cohort(root, state, frontier)
    while state.get("active_generation"):
        if state.get("generation_wave"):
            _finish_wave(root, state, frontier)
        retire_superseded(root, state, frontier)
        queued = []
        for index in list(state["active_generation"]):
            if index not in state["active_generation"]:
                continue  # A preceding proof may have retired this sibling.
            cycle = state["cycles"][index]
            if cycle["status"] not in ("RUNNING", "INTERRUPTED"):
                state["active_generation"].remove(index)
                continue
            retire_superseded(root, state, frontier)
            if index not in state["active_generation"]:
                continue
            has_generated = any(
                stage.get("status") == "generated" for stage in cycle.get("stages", [])
            )
            if stop_requested() and not has_generated:
                if cycle["status"] == "RUNNING":
                    cycle.update(
                        status="INTERRUPTED",
                        reason="operator stop between stages; continuation deferred for resume",
                        interrupted_at=frontier.stamp(),
                    )
                    frontier.save_state(root, state)
                continue
            state["active"] = index
            stage = frontier.run_cycle(root, state, defer_generation=True)
            state["active"] = None
            if stage is None:
                if cycle["status"] not in ("RUNNING", "INTERRUPTED"):
                    state["active_generation"].remove(index)
            elif stop_requested():
                cycle.update(
                    status="INTERRUPTED",
                    reason="operator stop before queued continuation; stage preserved for resume",
                    interrupted_at=frontier.stamp(),
                )
                frontier.save_state(root, state)
                continue
            elif stage.get("work_kind") == "rerationalisation":
                # Cheap snapshot work does not require a generation pool.
                code = frontier.run_child(stage["command"], Path(stage["directory"]) / "stdout.log",
                                          frontier.controlled_env(state))
                if code:
                    frontier.record_job_failure(root, state, cycle, stage, code)
                else:
                    stage.update(status="generated", result=read_json(Path(stage["directory"]) / "result.json"))
            else:
                queued.append((index, cycle["stages"].index(stage), stage))
            frontier.save_state(root, state)
        retire_superseded(root, state, frontier)
        queued = [entry for entry in queued if entry[0] in state["active_generation"]]
        if stop_requested():
            for index in state.get("active_generation", []):
                cycle = state["cycles"][index]
                if cycle["status"] == "RUNNING":
                    cycle.update(
                        status="INTERRUPTED",
                        reason="operator stop after current generation wave; continuation deferred for resume",
                        interrupted_at=frontier.stamp(),
                    )
            state["active"] = None
            frontier.save_state(root, state)
            frontier.write_views(root, state)
            frontier.emit(
                root,
                "[stop] current generation wave adopted; no later stage was started; "
                "remaining cohort is resumable",
            )
            return
        if not queued:
            continue
        number = int(state.get("generation_wave_count", 0)) + 1
        directory = root / "generation-waves" / f"wave-{number:06d}"
        while directory.exists():
            number += 1
            directory = directory.with_name(f"wave-{number:06d}")
        directory.mkdir(parents=True)
        jobs = [{"id": f"cycle-{index}", "command": stage["command"],
                 "output": str(Path(stage["directory"]) / "stdout.log")}
                for index, _, stage in queued]
        manifest_path = directory / "manifest.json"
        atomic_json(manifest_path, {"schema": 1, "jobs": jobs})
        runtime = state["config"]["runtime"]
        command = [sys.executable, "-m", "devtools.frontier_generation_queue",
                   "--manifest", str(manifest_path), "--report", str(directory / "report.json"),
                   "--workers", str(state["config"]["workers"]),
                   "--stage-seconds", str(runtime["stage_seconds"]),
                   "--no-progress-seconds", str(runtime["no_progress_seconds"])]
        state["generation_wave_count"] = number
        state["generation_wave"] = {"directory": str(directory), "command": command,
                                    "manifest_sha256": digest(manifest_path),
                                    "stages": [(i, j) for i, j, _ in queued],
                                    "started_epoch": int(time.time())}
        frontier.save_state(root, state)
        _finish_wave(root, state, frontier)
    state["active"] = None
    frontier.save_state(root, state)
    frontier.write_views(root, state)
