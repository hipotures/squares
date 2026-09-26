"""Durable strategy cohorts around the unchanged single-cycle decision policy.

Only generation stages run concurrently. Full proof gates run after a wave has
drained. Cheap rationalisation results are interpreted immediately, and eligible
independent strategies refill the next wave. Admission is bounded: each strategy
is admitted at most once per portfolio invocation, so repairs and the outer
controller cannot be starved by an endless chain of speculative replacements.
"""
from __future__ import annotations

import sys
import time
from collections import deque
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


def refill_resumed_cohort(root: Path, state: dict[str, Any], frontier, *, exclude=()) -> list[int]:
    """Fill a partial cohort only at a safe, non-stopping pre-wave boundary.

    The historical name remains for callers. This now runs between waves as
    well as after resume. Never mutate an unadopted wave or bypass a proof gate.
    """
    if state.get("generation_wave") or getattr(frontier, "stop_requested", lambda: False)():
        return []
    active = [index for index in state.get("active_generation", [])
              if state["cycles"][index].get("status") in ("RUNNING", "INTERRUPTED")]
    if not active:
        return []
    cycles = [state["cycles"][index] for index in active]
    if any(stage.get("status") == "generated"
           for cycle in cycles for stage in cycle.get("stages", [])):
        return []
    # A precision-only attempt must run to its cheap result before speculation.
    # If it has already advanced to queued generation it no longer needs this
    # protection and must not permanently reserve an idle portfolio slot.
    if any(cycle.get("plan_reason", "").startswith("untried same-side rationalisation")
           and not any(stage.get("status") == "queued" and stage.get("work_kind") == "generation"
                       for stage in cycle.get("stages", [])) for cycle in cycles):
        return []
    maximum = min(int(state["config"].get("generation_trials", 3)),
                  int(state["config"]["workers"]))
    room = maximum - len(active)
    limit = state["config"].get("max_cycles")
    if limit is not None:
        room = min(room, max(0, int(limit) - len(state["cycles"])))
    if room <= 0:
        return []
    occupied = {cycle.get("strategy", "baseline") for cycle in cycles} | set(exclude)
    plans = []
    for name in state["config"]["strategies"]:
        if len(plans) >= room:
            break
        if name in occupied:
            continue
        choice = frontier_policy.strategy_proposal(state, name)
        if choice is not None:
            plans.append(choice)
            occupied.add(name)
    added = []
    for plan in plans:
        cycle = {"side": plan["side"], "strategy": plan["strategy"],
                 "search_revision": state.get("search_revision", 0),
                 "plan_reason": plan["reason"], "status": "RUNNING",
                 "started_at": frontier.stamp(), "seed_verified_low": state["verified_low"],
                 "stages": []}
        index = len(state["cycles"])
        state["cycles"].append(cycle)
        state["active_generation"].append(index)
        added.append(index)
    if added:
        frontier.save_state(root, state)
        frontier.emit(root, f"[portfolio] resumed-refill={len(added)} "
                      f"active={len(state['active_generation'])}/{maximum} boundary=pre-wave "
                      f"strategies={','.join(state['cycles'][i].get('strategy', 'baseline') for i in state['active_generation'])}")
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
            continue
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
                  f"depth_cpu={metrics.get('depth_worker_cpu_seconds', 0):.3f}s "
                  f"max_busy={metrics['max_busy']}/{metrics['slots']} "
                  f"mean_leased={metrics.get('mean_leased_slots', 0):.2f} "
                  f"solo_serial={metrics.get('solo_serial_seconds', 0):.3f}s")


def retire_superseded(root: Path, state: dict[str, Any], frontier) -> None:
    """Retire redundant generation after adoption, never alter a live wave."""
    if state.get("generation_wave"):
        return
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


def _prepare_cycle(root: Path, state: dict[str, Any], index: int, frontier):
    """Interpret results and finish cheap scale work before queueing generation."""
    stop_requested = getattr(frontier, "stop_requested", lambda: False)
    while index in state["active_generation"]:
        cycle = state["cycles"][index]
        if cycle["status"] not in ("RUNNING", "INTERRUPTED"):
            state["active_generation"].remove(index)
            return None
        retire_superseded(root, state, frontier)
        if index not in state["active_generation"]:
            return None
        has_generated = any(s.get("status") == "generated" for s in cycle.get("stages", []))
        if stop_requested() and not has_generated:
            if cycle["status"] == "RUNNING":
                cycle.update(status="INTERRUPTED",
                             reason="operator stop between stages; continuation deferred for resume",
                             interrupted_at=frontier.stamp())
                frontier.save_state(root, state)
            return None
        state["active"] = index
        stage = frontier.run_cycle(root, state, defer_generation=True)
        state["active"] = None
        if stage is None:
            if cycle["status"] not in ("RUNNING", "INTERRUPTED"):
                state["active_generation"].remove(index)
            return None
        if stop_requested():
            cycle.update(status="INTERRUPTED",
                         reason="operator stop before queued continuation; stage preserved for resume",
                         interrupted_at=frontier.stamp())
            frontier.save_state(root, state)
            return None
        if stage.get("work_kind") != "rerationalisation":
            return stage
        code = frontier.run_child(stage["command"], Path(stage["directory"]) / "stdout.log",
                                  frontier.controlled_env(state))
        if code:
            frontier.record_job_failure(root, state, cycle, stage, code)
            return None
        stage.update(status="generated", result=read_json(Path(stage["directory"]) / "result.json"))
        frontier.save_state(root, state)
        # Interpret immediately (including any required full gate), not after
        # an unrelated 500/1000-second generation wave. A stop still defers the
        # next scale/stage; run_cycle owns that decision.
    return None


def run_portfolio(root: Path, state: dict[str, Any], frontier=None) -> None:
    if frontier is None:
        from devtools import run_n12_frontier as frontier
    stop_requested = getattr(frontier, "stop_requested", lambda: False)
    if not state.get("active_generation"):
        if state.get("active") is not None:
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
    admitted = {state["cycles"][i].get("strategy", "baseline") for i in state["active_generation"]}
    while state.get("active_generation"):
        if state.get("generation_wave"):
            _finish_wave(root, state, frontier)
        retire_superseded(root, state, frontier)
        queued = []
        todo = deque(state["active_generation"])
        while True:
            while todo:
                index = todo.popleft()
                if index not in state["active_generation"]:
                    continue
                stage = _prepare_cycle(root, state, index, frontier)
                if stage is not None:
                    queued.append((index, state["cycles"][index]["stages"].index(stage), stage))
                frontier.save_state(root, state)
            retire_superseded(root, state, frontier)
            state["active_generation"] = [i for i in state["active_generation"]
                                          if state["cycles"][i]["status"] in ("RUNNING", "INTERRUPTED")]
            queued = [entry for entry in queued if entry[0] in state["active_generation"]]
            if stop_requested() or not queued:
                break
            added = refill_resumed_cohort(root, state, frontier, exclude=admitted)
            if not added:
                break
            admitted.update(state["cycles"][i].get("strategy", "baseline") for i in added)
            todo.extend(added)
        if stop_requested():
            for index in state.get("active_generation", []):
                cycle = state["cycles"][index]
                if cycle["status"] == "RUNNING":
                    cycle.update(status="INTERRUPTED",
                                 reason="operator stop after current generation wave; continuation deferred for resume",
                                 interrupted_at=frontier.stamp())
            state["active"] = None
            frontier.save_state(root, state)
            frontier.write_views(root, state)
            frontier.emit(root, "[stop] current generation wave adopted; no later stage was started; "
                          "remaining cohort is resumable")
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
