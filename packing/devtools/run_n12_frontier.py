"""Persistent, adaptive search for an n=12 fractional certificate frontier.

Search failure describes this instrument, not a mathematical upper bound.  Only
``devtools.decide_certificate`` can make a new VERIFIED endpoint.
"""

from __future__ import annotations

import argparse
import csv
import fcntl
import json
import math
import hashlib
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools import frontier_policy, frontier_runtime
from devtools.frontier_io import atomic_json as durable_json, atomic_text, digest, read_json

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SEED = REPO / "packing/cases/n12_fractional_certificate/certificate.json"
SCHEMA = 3
LEGACY_RATIONALISATION_SCALE = 200_000
DEFAULT_RATIONALISATION_SCALE = 1_600_000
DEFAULT_MAX_RATIONALISATION_SCALE = 25_600_000
REPAIR_SLACK_FRACTIONS = (
    Fraction(1, 2),
    Fraction(3, 4),
    Fraction(7, 8),
    Fraction(15, 16),
    Fraction(31, 32),
    Fraction(63, 64),
)
REPAIRABLE_VERIFIERS = ("quick-rejected", "full-rejected", "declaration-rejected")
_RUNTIME_LIMITS = dict(frontier_runtime.DEFAULTS)
_ACTIVE_STOP = None

BLUE = "\033[94m"
RESET = "\033[0m"
STAGES = ("screen", "normal", "deep", "maximum")
CSV_FIELDS = (
    "timestamp",
    "side",
    "side_float",
    "cycle",
    "stage",
    "budget",
    "scale",
    "seed",
    "objective",
    "total_mass",
    "atoms",
    "rounds",
    "cumulative_rounds",
    "elapsed",
    "late_gain",
    "averaged_depth",
    "added",
    "classification",
    "verifier",
    "reason",
)


def stamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def git_sha() -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


def side_name(side: Fraction) -> str:
    return f"L-{side.numerator}-{side.denominator}"


def display(side: Fraction | str | None) -> str:
    """Readable exact-rational decimal, with detail near a narrow frontier."""

    if side is None:
        return "none"
    value = Fraction(side)
    with localcontext() as context:
        context.prec = 50
        text = format(Decimal(value.numerator) / Decimal(value.denominator), ".18f")
    whole, _, fractional = text.partition(".")
    fractional = fractional.rstrip("0")
    fractional = fractional.ljust(9, "0")
    return f"{whole}.{fractional}"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    durable_json(path, value)


def load_state(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    state_path = root / "state.json"
    try:
        state = read_json(state_path)
    except (ValueError, OSError):
        backup = root / "state.previous.json"
        if not backup.exists():
            raise
        state = read_json(backup)
        if state_path.exists():
            damaged = root / f"state.damaged-{time.time_ns()}.json"
            shutil.copyfile(state_path, damaged)
        atomic_json(state_path, state)
    if state.get("schema") not in (2, SCHEMA) or state.get("n") != 12:
        raise ValueError("incompatible frontier state schema or n")
    old_schema = state["schema"]
    if old_schema != SCHEMA:
        backup = root / f"state.schema-{old_schema}-{digest(state_path)[:12]}.json"
        if not backup.exists():
            shutil.copyfile(state_path, backup)
        state["schema"] = SCHEMA
        state.setdefault("migrations", []).append({"at": stamp(), "from_schema": old_schema,
                                                  "to_schema": SCHEMA})
    stored_config = state.get("config")
    if not isinstance(stored_config, dict):
        raise ValueError("invalid frontier state config")
    if config is not None:
        if any(stored_config.get(key) != config.get(key) for key in (
            "verified_low", "search_high", "seed_certificate", "workers", "budgets", "row_rounds"
        )):
            raise ValueError("resume settings differ from the saved experiment")
        for key, legacy in (("scale", LEGACY_RATIONALISATION_SCALE), ("max_scale", None)):
            requested = config.get(key)
            if key not in stored_config and requested is not None:
                stored_config[key] = requested
                state.setdefault("migrations", []).append({
                    "at": stamp(), "kind": "rationalisation-scale" if key == "scale" else "max-rationalisation-scale", "from": legacy, "to": requested,
                })
            elif stored_config.get(key) != requested:
                raise ValueError("resume rationalisation scale differs from the saved experiment")
    stored_config.setdefault("scale", DEFAULT_RATIONALISATION_SCALE)
    stored_config.setdefault("max_scale", DEFAULT_MAX_RATIONALISATION_SCALE)
    stored_config.setdefault("row_rounds", 60)
    stored_config.setdefault("max_row_rounds", max(60, stored_config["row_rounds"] * 2))
    stored_config.setdefault("strategies", [item["name"] for item in frontier_policy.PROFILES])
    stored_config.setdefault("strategy_width", "1/100000")
    if not isinstance(state.get("cycles"), list):
        raise ValueError("invalid frontier state")
    active = state.get("active")
    if active is not None and (type(active) is not int or not 0 <= active < len(state["cycles"])):
        raise ValueError("active cycle is missing")
    certificate = Path(state["verified_certificate"])
    if not certificate.exists():
        raise ValueError("verified certificate is missing")
    record = read_json(certificate)
    if record.get("n") != 12 or Fraction(record["outer_side"]) != Fraction(state["verified_low"]):
        raise ValueError("verified certificate no longer matches the saved lower bound")
    if state.get("verified_sha256") is not None and digest(certificate) != state["verified_sha256"]:
        raise ValueError("verified certificate changed after acceptance")
    # Legacy states are retained intact; their best artifact is checked by the
    # full gate once before scheduling new work if no digest was recorded.
    if "verified_sha256" not in state:
        state["anchor_needs_verification"] = True
        state["verified_sha256"] = digest(certificate)
    if not 0 < Fraction(state["verified_low"]) < 4:
        raise ValueError("verified endpoint is outside the supported n=12 campaign range")
    if not isinstance(state.get("unresolved"), list):
        raise ValueError("invalid unresolved history")
    frontier_policy.reconcile(state)
    state.setdefault("mode", "FRONTIER")
    state.setdefault("repair_attempts", [])
    state.setdefault("discoveries", [])
    state.setdefault("operational_errors", [])
    state.setdefault("policy_version", frontier_policy.POLICY_VERSION)
    state.setdefault("search_revision", 0)
    # Do not mark a repair INTERRUPTED merely because the controller restarted:
    # its supervisor may still be running and must be reattached to first.
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    # Raw results remain immutable per-stage evidence. Avoid copying a large LP
    # trace into every state backup and every cheap precision-refinement stage.
    for cycle in state.get("cycles", []):
        for stage in cycle.get("stages", []):
            result = stage.get("result")
            if isinstance(result, dict) and "lp_log" in result and stage.get("directory"):
                source = Path(stage["directory"]) / "result.json"
                if source.is_file():
                    stage["result_file"] = str(source)
                    stage["result_sha256"] = digest(source)
                    stage["state_omitted_fields"] = ["lp_log"]
                    result.pop("lp_log")
    state["updated_at"] = stamp()
    current = root / "state.json"
    if current.exists():
        try:
            previous = read_json(current)
        except (ValueError, OSError):
            previous = None
        if previous is not None:
            atomic_json(root / "state.previous.json", previous)
    atomic_json(current, state)


@contextmanager
def locked(root: Path) -> Iterator[None]:
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".runner.lock").open("a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(f"another frontier runner owns {root}") from error
        yield


def active_unresolved(state: dict[str, Any]) -> list[Fraction]:
    low, high = Fraction(state["verified_low"]), Fraction(state["search_high"])
    return sorted(Fraction(x) for x in state["unresolved"] if low < Fraction(x) <= high)


def soft_high(state: dict[str, Any]) -> Fraction:
    return min(active_unresolved(state), default=Fraction(state["search_high"]))


def stage_scale(stage: dict[str, Any]) -> int | None:
    """Rationalisation scale used by a stage, including legacy stage records."""

    result = stage.get("result") or {}
    settings = result.get("settings") if isinstance(result, dict) else None
    if isinstance(settings, dict) and type(settings.get("scale")) is int:
        return int(settings["scale"])
    if type(stage.get("scale")) is int:
        return int(stage["scale"])
    command = stage.get("command")
    if isinstance(command, list) and "--scale" in command:
        try:
            return int(command[command.index("--scale") + 1])
        except (IndexError, TypeError, ValueError):
            return None
    return None


def scale_limited_unresolved(cycle: dict[str, Any], target_scale: int) -> bool:
    """Whether the finest attempted grid still leaves rationalisation as the blocker."""

    if cycle.get("status") != "UNRESOLVED":
        return False
    finest_scale = -1
    finest_result: dict[str, Any] | None = None
    for stage in reversed(cycle.get("stages") or []):
        used_scale = stage_scale(stage)
        result = stage.get("result") or {}
        if (
            used_scale is not None
            and used_scale > finest_scale
            and isinstance(result, dict)
        ):
            finest_scale = used_scale
            finest_result = result
    return (
        finest_result is not None
        and finest_scale < target_scale
        and scale_limited_result(finest_result)
    )


def next_side(state: dict[str, Any]) -> Fraction | None:
    low = Fraction(state["verified_low"])
    ceiling = soft_high(state)
    if ceiling <= low:
        return None

    # Revisit an unresolved ceiling only when the search instrument actually
    # became stronger. A better VERIFIED seed alone is not enough: the old
    # policy repeatedly reran deterministic unresolved ceilings after every
    # tiny lower-bound improvement and reproduced identical results.
    target_scale = int(
        state.get("config", {}).get(
            "max_scale",
            state.get("config", {}).get("scale", LEGACY_RATIONALISATION_SCALE),
        )
    )
    for cycle in reversed(state["cycles"]):
        if Fraction(cycle["side"]) == ceiling:
            if scale_limited_unresolved(cycle, target_scale):
                return ceiling
            break

    # Return the exact midpoint proposal. The policy layer must still reject
    # duplicate float-backend work and select precision, repair, or another
    # instrument before idle exhaustion; a Fraction alone is not a useful trial.
    return (low + ceiling) / 2


def numeric_search_saturated(state: dict[str, Any]) -> bool:
    """Whether exact bisection has moved below the float64 search resolution."""

    low = Fraction(state["verified_low"])
    ceiling = soft_high(state)
    if ceiling <= low:
        return False
    midpoint = (low + ceiling) / 2
    return float(midpoint) in (float(low), float(ceiling))


def scale_limited_result(result: dict[str, Any]) -> bool:
    """The LP is below 12 but upward rationalisation still misses the theorem."""

    objective = result.get("objective")
    mass = result.get("total_mass")
    return (
        result.get("converged") is True
        and isinstance(objective, int | float)
        and math.isfinite(objective)
        and objective < 12
        and mass is not None
        and Fraction(mass) >= 12
    )


def next_refinement_scale(
    result: dict[str, Any], current_scale: int, max_scale: int
) -> int | None:
    """Double the nested rationalisation grid when rounding is the blocker."""

    if not scale_limited_result(result) or current_scale >= max_scale:
        return None
    return min(current_scale * 2, max_scale)


def starting_scale(state: dict[str, Any], side: Fraction) -> int:
    """Start a retried side above the finest scale already tried there."""

    base = int(state["config"]["scale"])
    maximum = int(state["config"]["max_scale"])
    finest = 0
    for cycle in state["cycles"]:
        if Fraction(cycle["side"]) != side:
            continue
        for stage in cycle.get("stages") or []:
            result = stage.get("result") or {}
            used = stage_scale(stage)
            if used is not None and scale_limited_result(result):
                finest = max(finest, used)
    if finest >= base and finest < maximum:
        return min(finest * 2, maximum)
    return base


def significant_result(decision: str, result: dict[str, Any]) -> bool:
    """Results worth making visually obvious in an occasional terminal glance."""

    return decision in ("VERIFIED", "REFINE_SCALE") or (
        decision == "UNRESOLVED" and scale_limited_result(result)
    )


def apply_result(state: dict[str, Any], cycle: dict[str, Any]) -> None:
    side = Fraction(cycle["side"])
    status = cycle["status"]
    if status == "VERIFIED":
        if cycle.get("verifier") != "full-retainable" or not cycle.get("verified_candidate"):
            raise ValueError("VERIFIED requires a successful full exact gate")
        promote_verified(state, side, Path(cycle["verified_candidate"]), "search")
        state["preferred_strategy"] = cycle.get("strategy", "baseline")
    elif status == "SEARCH_FAILED":
        if Fraction(state["verified_low"]) < side <= Fraction(state["search_high"]):
            state["search_high"] = str(side)
            state["search_high_kind"] = "SEARCH_FAILED"
    elif status == "UNRESOLVED":
        if str(side) not in state["unresolved"]:
            state["unresolved"].append(str(side))
            state["unresolved"].sort(key=Fraction)
    elif status != "ERROR":
        raise ValueError(f"invalid cycle result {status!r}")
    state["active"] = None


def signals(result: dict[str, Any]) -> dict[str, float | int | None]:
    rounds = result.get("rounds") or []
    objectives = [
        float(r["objective"])
        for r in rounds
        if isinstance(r.get("objective"), int | float) and math.isfinite(r["objective"])
    ]
    late = (
        max(0.0, objectives[-min(4, len(objectives))] - objectives[-1])
        if len(objectives) > 1
        else 0.0
    )
    overall = max(0.0, objectives[0] - objectives[-1]) if len(objectives) > 1 else 0.0
    last = rounds[-1] if rounds else {}
    return {
        "late_gain": late,
        "overall_gain": overall,
        "averaged_depth": last.get("averaged_depth"),
        "added": sum(int(r.get("added") or 0) for r in rounds[-3:]),
        "rounds": len(rounds),
    }


def decide_stage(
    result: dict[str, Any], stage_index: int, budgets: list[int], *, nearby: bool
) -> tuple[str, str]:
    """Require inner row convergence; do not treat it as column exhaustion."""
    if result.get("converged") is not True:
        return "UNRESOLVED", (
            "inner row generation did not converge; "
            f"stopped={result.get('stopped', 'unknown')}; "
            "no search-failure inference"
        )
    if result.get("total_mass") is None:
        return "UNRESOLVED", "row solution produced no rationalized candidate"
    signal_values = signals(result)
    objective = result.get("objective")
    mass = result.get("total_mass")
    distance = min(
        abs(float(objective) - 12) if isinstance(objective, int | float) else math.inf,
        abs(float(Fraction(mass)) - 12) if mass is not None else math.inf,
    )
    late = float(signal_values["late_gain"] or 0)
    overall = float(signal_values["overall_gain"] or 0)
    depth = signal_values["averaged_depth"]
    adding = int(signal_values["added"] or 0) > 0
    priced = isinstance(depth, int | float) and depth > 1.002
    improving = late > 0.0002 or (overall > 0.002 and adding)
    close = distance < (0.03 if nearby else 0.015)
    promising = close or (improving and (adding or priced)) or (priced and distance < 0.08)
    if stage_index < len(budgets) - 1 and promising:
        return (
            "ESCALATE",
            (
                f"close={close}, late_gain={late:.6g}, added={adding}, priced={priced}; "
                f"next={budgets[stage_index + 1]}"
            ),
        )
    if promising:
        return (
            "UNRESOLVED",
            (
                f"budget exhausted while close/improving: distance={distance:.6g}, "
                f"late_gain={late:.6g}, added={adding}, priced={priced}"
            ),
        )
    return (
        "SEARCH_FAILED",
        (
            f"search stalled at budget {budgets[stage_index]}: distance={distance:.6g}, "
            f"late_gain={late:.6g}, added={adding}, priced={priced}"
        ),
    )


def emit(root: Path, message: str, *, significant: bool = False) -> None:
    colour = significant and "NO_COLOR" not in os.environ and (
        sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1"
    )
    code = "\033[1;32m" if "VERIFIED LOWER BOUND" in message else BLUE
    try:
        print(f"{code}{message}{RESET}" if colour else message, flush=True)
    except (BrokenPipeError, OSError):
        # A closed SSH terminal must not destroy the current result/checkpoint.
        pass
    with (root / "runner.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{stamp()} {message}\n")
        handle.flush()


def seed_for(state: dict[str, Any], side: Fraction) -> tuple[Path, str]:
    verified = Path(state["verified_certificate"])
    target_scale = int(
        state.get("config", {}).get(
            "max_scale",
            state.get("config", {}).get("scale", LEGACY_RATIONALISATION_SCALE),
        )
    )
    best_path, best_label, best_distance = (
        verified,
        f"verified@{state['verified_low']}",
        abs(side - Fraction(state["verified_low"])),
    )
    for cycle in state["cycles"]:
        for stage in cycle["stages"]:
            path_text = stage.get("candidate_unverified")
            if not path_text or not Path(path_text).exists():
                continue
            candidate_side = Fraction(cycle["side"])
            distance = abs(side - candidate_side)
            used_scale = stage_scale(stage) or LEGACY_RATIONALISATION_SCALE
            if distance == 0:
                if used_scale >= target_scale:
                    continue
            elif distance >= best_distance:
                continue
            best_path, best_label, best_distance = (
                Path(path_text),
                f"search-seed-only@{candidate_side}:scale{used_scale}",
                distance,
            )
    return best_path, best_label


def command(
    side: Fraction,
    budget: int,
    seed: Path,
    directory: Path,
    row_rounds: int,
    scale: int = DEFAULT_RATIONALISATION_SCALE,
    strategy: str = "baseline",
) -> list[str]:
    args = [
        sys.executable,
        "-m",
        "devtools.run_fractional_colgen",
        "--n",
        "12",
        "--side",
        str(side),
        "--shrink",
        "9977/10000",
        "--angle-limit",
        "207107/500000",
        "--direction-steps",
        "180",
        "--grid-counts",
        "auto",
        "--scale",
        str(scale),
        "--support-cap",
        "32",
        "--column-rounds",
        str(budget),
        "--max-rounds",
        str(row_rounds),
        "--rows-per-direction",
        "3",
        "--seed-map",
        "scale",
        "--seed-certificate",
        str(seed),
        "--freeze",
        str(directory / "candidate.unverified.json"),
        "--json",
        str(directory / "result.json"),
        "--log",
        str(directory / "column.log"),
        "--row-log",
        str(directory / "rows.log"),
    ]
    options = frontier_policy.profile(strategy)["options"]
    for key, value in options.items():
        flag = f"--{key}"
        if flag in args:
            args[args.index(flag) + 1] = value
        else:
            args.extend([flag, value])
    args.extend(["--raw-weights", str(directory / "raw-lp.json")])
    return args


def process_start_ticks(pid: int) -> str | None:
    info = frontier_runtime.process_info(pid)
    return None if info is None else info["ticks"]


def active_child(directory: Path) -> int | None:
    """Legacy-child protection is recursive and boot-aware for repair substeps."""
    for record_path in directory.rglob("*.child.json"):
        try:
            record = read_json(record_path)
            if "boot_id" in record:
                if frontier_runtime.is_alive(record):
                    return int(record["pid"])
            else:
                # Pre-upgrade records cannot safely authorize a signal. They
                # can only block a duplicate when the live identity still matches.
                pid = int(record["pid"])
                if record.get("start_ticks") is not None and process_start_ticks(pid) == record["start_ticks"]:
                    return pid
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return None


def latest_progress(directory: Path) -> tuple[str, str, str]:
    """Read flushed logs for the latest column, LP round, and finite objective."""
    column_round = "none"
    lp_round = "none"
    objective = "unknown"
    column_log = directory / "column.log"
    if column_log.exists():
        for line in reversed(tail_text(column_log).splitlines()):
            parts = line.split()
            if len(parts) < 3 or parts[0] != "round" or not parts[1].endswith(":"):
                continue
            index = parts[1][:-1]
            if not index.isdigit():
                continue
            column_round = index
            for part in parts:
                if part.startswith("objective="):
                    objective = part.removeprefix("objective=")
                    break
            break
    row_log = directory / "rows.log"
    if row_log.exists():
        for line in reversed(tail_text(row_log).splitlines()):
            parts = line.split()
            if len(parts) < 6 or not parts[0].lstrip("-").isdigit():
                continue
            lp_round = parts[0]
            objective = parts[5]
            break
    try:
        objective_float = float(objective)
    except ValueError:
        objective = "unknown"
    else:
        objective = f"{objective_float:.5f}" if math.isfinite(objective_float) else "unknown"
    return column_round, lp_round, objective


def heartbeat_message(args: list[str], output: Path, elapsed: float) -> str:
    """One concise progress line for a long-running real subprocess."""
    minutes = max(1, round(elapsed / 60))
    if "--side" not in args or "--column-rounds" not in args:
        return f"[running] {output.name} elapsed={minutes}m"
    side = display(Fraction(args[args.index("--side") + 1]))
    budget = args[args.index("--column-rounds") + 1]
    stage = output.parent.name.split("-", 1)[0]
    column_round, lp_round, objective = latest_progress(output.parent)
    return (
        f"[running] L={side} stage={stage}({budget}) elapsed={minutes}m "
        f"last-round={column_round} lp-round={lp_round} objective={objective}"
    )


def run_child(args: list[str], output: Path, env: dict[str, str] | None = None) -> int:
    root = next((parent for parent in output.parents if (parent / "state.json").exists()), output.parent)
    return frontier_runtime.run(
        args, output, cwd=REPO / "packing", env=env, limits=_RUNTIME_LIMITS,
        heartbeat=lambda elapsed: emit(root, heartbeat_message(args, output, elapsed)),
        on_poll=poll_stop,
    )


def verify_candidate(directory: Path, candidate: Path, expected_side: Fraction) -> tuple[str, str | None]:
    """One durable structured verification job, sharing the normal job watchdog."""
    try:
        record = read_json(candidate, 8 * 1024 * 1024)
        if record.get("n") != 12 or Fraction(record["outer_side"]) != expected_side:
            return "candidate-side-mismatch", None
        if Fraction(record["total_mass"]) >= 12:
            return "mass-not-below-12", None
    except (OSError, ValueError, KeyError, TypeError):
        return "candidate-invalid", None
    from devtools.frontier_verify import verifier_fingerprint
    tool_sha = verifier_fingerprint()
    gate_dir = directory / f"gate-{digest(candidate)[:16]}-{tool_sha[:12]}"
    gate_dir.mkdir(parents=True, exist_ok=True)
    report_path = gate_dir / "verification.json"
    code = run_child([
        sys.executable, "-m", "devtools.frontier_verify", "--input", str(candidate),
        "--side", str(expected_side), "--report", str(report_path),
    ], gate_dir / "stdout.log")
    if code or not report_path.exists():
        return f"verification-error-{code}", None
    report = read_json(report_path)
    if (report.get("source_sha256") != digest(candidate)
            or report.get("verifier_sha256") != tool_sha
            or Fraction(report.get("side", "0")) != expected_side):
        return "candidate-invalid", None
    atomic_json(directory / "verification.json", report)
    if report.get("status") == "VERIFIED" and report.get("category") == "full-retainable":
        verified = Path(report["verified_candidate"])
        if not verified.is_file() or digest(verified) != report.get("verified_sha256"):
            return "candidate-invalid", None
        return "full-retainable", str(verified)
    category = report.get("category")
    if category == "coverage_deficit":
        return "declaration-rejected", None
    if category == "interval_stall":
        return "quick-rejected", None
    if category == "gate_refusal":
        return "full-rejected", None
    return "candidate-invalid", None


def repair_candidate_key(candidate: dict[str, Any]) -> tuple[Fraction, Fraction, int]:
    """Prefer the strongest exact side, then the candidate with more mass slack."""

    return (
        Fraction(candidate["side"]),
        Fraction(12) - Fraction(candidate["total_mass"]),
        int(candidate["cycle_index"]),
    )


def select_repair_candidate(state: dict[str, Any]) -> dict[str, Any] | None:
    """Choose the best untried below-12 candidate rejected by an exact gate."""

    low = Fraction(state["verified_low"])
    finished = [a for a in state.get("repair_attempts", [])
                if a.get("status") in ("VERIFIED", "REJECTED")
                or (a.get("status") == "ERROR"
                    and a.get("error_epoch", 0) >= state.get("error_epoch", 0))]
    completed = {attempt.get("candidate") for attempt in finished}
    completed_digests = {attempt.get("candidate_sha256") for attempt in finished}
    candidates: list[dict[str, Any]] = []
    for cycle_index, cycle in enumerate(state["cycles"], 1):
        side = Fraction(cycle["side"])
        if side <= low:
            continue
        for stage_index, stage in enumerate(cycle.get("stages") or [], 1):
            if stage.get("verifier") not in REPAIRABLE_VERIFIERS:
                continue
            result = stage.get("result") or {}
            mass_text = result.get("total_mass")
            path_text = stage.get("candidate_unverified")
            if mass_text is None or path_text is None:
                continue
            try:
                mass = Fraction(mass_text)
            except (ValueError, ZeroDivisionError):
                continue
            path = Path(path_text)
            if mass >= 12 or not path.exists() or str(path) in completed:
                continue
            if digest(path) in completed_digests:
                continue
            candidates.append(
                {
                    "side": str(side),
                    "total_mass": str(mass),
                    "candidate": str(path),
                    "verifier": stage.get("verifier"),
                    "cycle_index": cycle_index,
                    "stage_index": stage_index,
                    "stage": stage.get("name"),
                    "scale": stage_scale(stage),
                }
            )
    return max(candidates, key=repair_candidate_key) if candidates else None


def diagnosis_from_log(log: Path, stalls: Path) -> dict[str, Any]:
    refusals: list[str] = []
    if log.exists():
        for line in log.read_text(encoding="utf-8").splitlines():
            if "REFUSED:" in line:
                refusals.append(line.split("REFUSED:", 1)[1].strip())
    stalled = None
    if stalls.exists():
        try:
            stalled = json.loads(stalls.read_text(encoding="utf-8")).get("stalled")
        except (OSError, ValueError, TypeError):
            stalled = None
    return {"refusals": refusals, "stalled_boxes": stalled}


def diagnose_repair_candidate(
    directory: Path, candidate: Path
) -> tuple[dict[str, Any], Path | None]:
    """Re-run the exact declaration and quick interval gate with stall evidence."""

    directory.mkdir(parents=True, exist_ok=True)
    declared = directory / "candidate.diagnosed.json"
    shutil.copyfile(candidate, declared)
    declare_log = directory / "declare.log"
    declaration = run_child(
        [sys.executable, "-m", "devtools.declare_least_cell_mass", str(declared)],
        declare_log,
    )
    report: dict[str, Any] = {
        "candidate": str(candidate),
        "declaration_exit": declaration,
        "quick_exit": None,
        "refusals": [],
        "stalled_boxes": None,
    }
    if declaration:
        report["status"] = "declaration-rejected"
        atomic_json(directory / "diagnosis.json", report)
        return report, None

    stalls = directory / "interval-stalls.json"
    quick_log = directory / "quick.log"
    quick = run_child(
        [
            sys.executable,
            "-m",
            "devtools.decide_certificate",
            "--quick",
            "--dump-stalls",
            str(stalls),
            str(declared),
        ],
        quick_log,
    )
    report["quick_exit"] = quick
    report.update(diagnosis_from_log(quick_log, stalls))
    report["status"] = "quick-accepted" if quick == 0 else "quick-rejected"
    atomic_json(directory / "diagnosis.json", report)
    return report, declared


def write_boosted_candidate(
    source: Path, destination: Path, slack_fraction: Fraction
) -> Fraction:
    """Uniformly increase every atom weight while keeping total mass strictly below 12."""

    record = json.loads(source.read_text(encoding="utf-8"))
    atoms = record.get("atoms")
    if not isinstance(atoms, list):
        raise ValueError("repair candidate has no atom list")
    mass = sum((Fraction(atom[2]) for atom in atoms), start=Fraction(0))
    if not 0 < mass < 12:
        raise ValueError(f"repair candidate mass {mass} is not in (0, 12)")
    if not 0 < slack_fraction < 1:
        raise ValueError("repair slack fraction must be strictly between zero and one")
    target = mass + (Fraction(12) - mass) * slack_fraction
    factor = target / mass
    repaired_atoms: list[list[object]] = []
    total = Fraction(0)
    for atom in atoms:
        if not isinstance(atom, list) or len(atom) != 3:
            raise ValueError("repair candidate contains a malformed atom")
        if Fraction(atom[2]) < 0:
            raise ValueError("repair candidate contains negative weights")
        weight = Fraction(atom[2]) * factor
        repaired_atoms.append([atom[0], atom[1], str(weight)])
        total += weight
    if not total < 12:
        raise ValueError("repair would violate the strict mass condition")
    record["atoms"] = repaired_atoms
    record["total_mass"] = str(total)
    record["least_cell_mass"] = None
    destination.parent.mkdir(parents=True, exist_ok=True)
    atomic_json(destination, record)
    return total


def full_gate_on_declared(directory: Path, declared: Path) -> str | None:
    full_log = directory / "full.log"
    full = run_child(
        [sys.executable, "-m", "devtools.decide_certificate", str(declared)], full_log
    )
    if full != 0:
        return None
    text = full_log.read_text(encoding="utf-8")
    if "RETAINABLE: both routes accept" not in text:
        return None
    verified = directory / "candidate.verified.json"
    shutil.copyfile(declared, verified)
    return str(verified)


def repair_job_failure(state: dict[str, Any], attempt: dict[str, Any], status: str) -> None:
    attempt.update(status="ERROR", reason=status, finished_at=stamp(),
                   error_epoch=state.get("error_epoch", 0))
    state["consecutive_job_errors"] = int(state.get("consecutive_job_errors", 0)) + 1
    state.setdefault("operational_errors", []).append({
        "at": stamp(), "side": attempt["side"], "reason": status,
        "repair": attempt["directory"],
    })
    if status.endswith("-78") or state["consecutive_job_errors"] >= 3:
        state["mode"] = "BLOCKED"


def run_repair(root: Path, state: dict[str, Any]) -> bool:
    """Resume the same candidate/boost after interruption; never duplicate a live job."""
    attempts = state.setdefault("repair_attempts", [])
    attempt = next((a for a in attempts if a.get("status") in ("RUNNING", "INTERRUPTED")), None)
    if attempt is None:
        selected = select_repair_candidate(state)
        if selected is None:
            return False
        number = len(attempts) + 1
        directory = root / "repair" / f"attempt-{number:04d}-{side_name(Fraction(selected['side']))}"
        while directory.exists():
            number += 1
            directory = root / "repair" / f"attempt-{number:04d}-{side_name(Fraction(selected['side']))}"
        directory.mkdir(parents=True, exist_ok=False)
        attempt = {**selected, "status": "RUNNING", "started_at": stamp(),
                   "directory": str(directory), "repairs": [], "candidate_sha256": digest(Path(selected['candidate']))}
        attempts.append(attempt)
    directory = Path(attempt["directory"])
    candidate = Path(attempt["candidate"])
    side = Fraction(attempt["side"])
    if attempt.get("candidate_sha256") and digest(candidate) != attempt["candidate_sha256"]:
        raise ValueError("repair source changed after selection")
    if not list(directory.rglob("*.job.json")) and (pid := active_child(directory)) is not None:
        raise frontier_runtime.LiveJob(f"prior repair child pid {pid} is still running; waiting before resume")
    state["mode"] = "REPAIR"
    attempt["status"] = "RUNNING"
    save_state(root, state)
    emit(root, f"[repair] L={display(side)} exact={side} attempt={directory.name}")
    recovered = next((entry for entry in attempt.get("repairs", [])
                      if entry.get("status") == "VERIFIED" and entry.get("verified_candidate")), None)
    if recovered is not None:
        promote_verified(state, side, Path(recovered["verified_candidate"]), "resumed-uniform-weight-repair")
        attempt.update(status="VERIFIED", verified_candidate=recovered["verified_candidate"], finished_at=stamp())
        save_state(root, state)
        write_views(root, state)
        publish_findings(root, state)
        return True
    diagnosis_dir = directory / "diagnosis"
    diagnosis_dir.mkdir(exist_ok=True)
    status, verified = verify_candidate(diagnosis_dir, candidate, side)
    diagnosis_path = diagnosis_dir / "verification.json"
    diagnosis = read_json(diagnosis_path) if diagnosis_path.exists() else {"category": "operational", "status": status}
    attempt["diagnosis"] = diagnosis
    save_state(root, state)
    if verified is not None:
        promote_verified(state, side, Path(verified), "repair-diagnosis")
        attempt.update(status="VERIFIED", verified_candidate=verified, finished_at=stamp())
        save_state(root, state)
        write_views(root, state)
        publish_findings(root, state)
        return True
    if status.startswith("verification-error"):
        repair_job_failure(state, attempt, status)
        save_state(root, state)
        return True
    state["consecutive_job_errors"] = 0
    category = diagnosis.get("category")
    if category in ("invalid_input", "precondition") or diagnosis.get("uniform_repair_possible") is False:
        attempt.update(status="REJECTED", reason=f"uniform repair inappropriate: {category}", finished_at=stamp())
        save_state(root, state)
        emit(root, f"[repair] abandoning candidate: {attempt['reason']}")
        return True
    slack_fractions = list(REPAIR_SLACK_FRACTIONS)
    minimum = diagnosis.get("minimum_cell_mass")
    mass = Fraction(attempt["total_mass"])
    if minimum is not None and 0 < Fraction(minimum) < 1:
        necessary = mass / Fraction(minimum)
        if necessary < 12:
            # Exact diagnostic chooses the first useful target, rather than
            # blindly spending six gates on boosts below the measured deficit.
            slack_fractions = [((necessary + 12) / 2 - mass) / (12 - mass)]
    for slack_fraction in slack_fractions:
        label = f"{slack_fraction.numerator}-{slack_fraction.denominator}"
        # Large exact denominators need not become oversized filesystem names.
        name = hashlib.sha256(label.encode()).hexdigest()[:16]
        boost_dir = directory / f"boost-{name}"
        boost_dir.mkdir(exist_ok=True)
        boosted = boost_dir / "candidate.unverified.json"
        entry = next((r for r in attempt["repairs"] if r.get("slack_fraction") == str(slack_fraction)), None)
        if entry is not None and entry.get("status") in ("REJECTED", "VERIFIED", "ERROR"):
            continue
        if entry is None:
            total = write_boosted_candidate(candidate, boosted, slack_fraction)
            entry = {"slack_fraction": str(slack_fraction), "total_mass": str(total),
                     "directory": str(boost_dir), "status": "RUNNING"}
            attempt["repairs"].append(entry)
            save_state(root, state)
        elif not boosted.exists():
            write_boosted_candidate(candidate, boosted, slack_fraction)
        status, verified = verify_candidate(boost_dir, boosted, side)
        entry.update(status="VERIFIED" if verified else ("ERROR" if status.startswith("verification-error") else "REJECTED"),
                     verifier=status, verified_candidate=verified)
        save_state(root, state)
        poll_stop()
        emit(root, f"[repair] boost={slack_fraction} mass={entry['total_mass']} -> {status}")
        if verified is not None:
            promote_verified(state, side, Path(verified), "uniform-weight-repair")
            attempt.update(status="VERIFIED", verified_candidate=verified, finished_at=stamp())
            save_state(root, state)
            write_views(root, state)
            publish_findings(root, state)
            return True
        if entry["status"] == "ERROR":
            repair_job_failure(state, attempt, status)
            save_state(root, state)
            return True
    attempt.update(status="REJECTED", reason="configured uniform repairs exhausted", finished_at=stamp())
    state["mode"] = "FRONTIER"
    save_state(root, state)
    write_views(root, state)
    return True


def write_views(root: Path, state: dict[str, Any]) -> None:
    rows: list[dict[str, Any]] = []
    for index, cycle in enumerate(state["cycles"], 1):
        for stage in cycle["stages"]:
            result = stage.get("result") or {}
            sig = signals(result)
            rows.append(
                {
                    "timestamp": stage.get("finished_at"),
                    "side": cycle["side"],
                    "side_float": display(cycle["side"]),
                    "cycle": index,
                    "stage": stage["name"],
                    "budget": stage["budget"],
                    "scale": stage_scale(stage),
                    "seed": stage["seed_label"],
                    "objective": result.get("objective"),
                    "total_mass": result.get("total_mass"),
                    "atoms": result.get("atoms"),
                    "rounds": sig["rounds"],
                    "cumulative_rounds": stage.get("cumulative_column_rounds"),
                    "elapsed": result.get("seconds"),
                    "late_gain": sig["late_gain"],
                    "averaged_depth": sig["averaged_depth"],
                    "added": sig["added"],
                    "classification": stage.get("decision", stage["status"]),
                    "verifier": stage.get("verifier"),
                    "reason": stage.get("reason"),
                }
            )
    with (root / "summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=[str(field) for field in CSV_FIELDS])
        writer.writeheader()
        writer.writerows(rows)
    unresolved = ", ".join(state["unresolved"]) or "none"
    lines = [
        "# n=12 fractional frontier search",
        "",
        f"Updated: {state['updated_at']}",
        "",
        (
            f"Best VERIFIED lower side: `{state['verified_low']}` "
            f"(certificate `{state['verified_certificate']}`)."
        ),
        (
            f"Search high: `{state['search_high']}` "
            f"({state['search_high_kind']}; search evidence only)."
        ),
        f"UNRESOLVED sides: {unresolved}.",
        f"Next policy action: `{choose_work(state)}`.",
        "",
        (
            "SEARCH_FAILED records failure of the stated instrument and budget; "
            "it is never a proof of impossibility."
        ),
        (
            "A new VERIFIED side requires a frozen candidate below mass 12 and "
            "a positive full two-route exact decision."
        ),
        "",
        "| Side | Strategy | Status | Scale | Column rounds | Last objective | Reason |",
        "| --- | --- | --- | ---: | ---: | ---: | --- |",
    ]
    for cycle in state["cycles"]:
        last = cycle["stages"][-1] if cycle["stages"] else {}
        result = last.get("result") or {}
        lines.append(
            f"| {cycle['side']} | {cycle.get('strategy', 'baseline')} | {cycle['status']} | {stage_scale(last) or ''} | "
            f"{cycle.get('column_rounds_completed', 0)} | {result.get('objective', '')} "
            f"| {cycle.get('reason', '')} |"
        )
    repairs = state.get("repair_attempts") or []
    if repairs:
        lines.extend(
            [
                "",
                "## Automatic repair attempts",
                "",
                "| Side | Status | Source verifier | Candidate |",
                "| --- | --- | --- | --- |",
            ]
        )
        for attempt in repairs:
            lines.append(
                f"| {attempt.get('side', '')} | {attempt.get('status', '')} | "
                f"{attempt.get('verifier', '')} | {attempt.get('candidate', '')} |"
            )
    atomic_text(root / "report.md", "\n".join(lines) + "\n")


def summary(root: Path, state: dict[str, Any], started: float) -> str:
    low, high = Fraction(state["verified_low"]), Fraction(state["search_high"])
    attempts = sum(
        bool(stage.get("verifier")) and stage["verifier"] != "mass-not-below-12"
        for cycle in state["cycles"]
        for stage in cycle["stages"]
    )
    return "\n".join(
        [
            "=== n=12 frontier search summary ===",
            f"cycles completed: {sum(c['status'] in ('VERIFIED', 'SEARCH_FAILED', 'UNRESOLVED') for c in state['cycles'])}",  # noqa: E501
            f"session wall time: {time.monotonic() - started:.0f}s",
            f"best VERIFIED: {low} = {display(low)}",
            f"current search high ({state['search_high_kind']}): {high} = {display(high)}",
            (
                "nearest active UNRESOLVED: "
                f"{display(soft_high(state)) if active_unresolved(state) else 'none'}"
            ),
            f"heuristic frontier width (not a mathematical upper bound): {high - low} = {display(high - low)}",
            f"exact verifications attempted: {attempts}",
            f"automatic repair attempts: {len(state.get('repair_attempts') or [])}",
            f"mode: {state.get('mode', 'FRONTIER')}",
            f"next suggested L: {choose_work(state).get('side', 'none')}",
            f"next action: {choose_work(state)['kind']}",
            f"state: {root / 'state.json'}",
            f"report: {root / 'report.md'}",
        ]
    )


def initial_state(config: dict[str, Any], seed: Path) -> dict[str, Any]:
    low, high = Fraction(config["verified_low"]), Fraction(config["search_high"])
    if not 0 < low < high:
        raise ValueError("verified low must be positive and below search high")
    record = json.loads(seed.read_text(encoding="utf-8"))
    if (
        record.get("n") != 12
        or Fraction(record["outer_side"]) != low
        or Fraction(record["total_mass"]) >= 12
    ):
        raise ValueError("seed certificate does not establish the configured low")
    # The committed retained bytes are the trust anchor. A changed or custom
    # seed has to pass the full gate before it can initialize a VERIFIED low.
    retained = subprocess.run(
        ["git", "show", "HEAD:packing/cases/n12_fractional_certificate/certificate.json"],
        cwd=REPO,
        capture_output=True,
        check=True,
    ).stdout
    if seed.resolve() != DEFAULT_SEED.resolve() or seed.read_bytes() != retained:
        proof_log = config["root"] / "initial-verify-full.log"
        if run_child(
            [sys.executable, "-m", "devtools.decide_certificate", str(seed)], proof_log
        ):
            raise ValueError(f"initial certificate failed the full exact gate; see {proof_log}")
    return {
        "schema": SCHEMA,
        "n": 12,
        "created_at": stamp(),
        "updated_at": stamp(),
        "config": {k: v for k, v in config.items() if k != "root"},
        "initial_low": str(low),
        "initial_width": str(high - low),
        "verified_low": str(low),
        "verified_certificate": str(seed),
        "verified_sha256": digest(seed),
        "discoveries": [],
        "operational_errors": [],
        "policy_version": frontier_policy.POLICY_VERSION,
        "search_high": str(high),
        "search_high_kind": "CONFIGURED_SEARCH_ENDPOINT",
        "unresolved": [],
        "cycles": [],
        "active": None,
        "last_target": None,
        "mode": "FRONTIER",
        "repair_attempts": [],
        "git_sha": git_sha(),
    }


def import_result(root: Path, state: dict[str, Any], source: Path) -> None:
    result = json.loads(source.read_text(encoding="utf-8"))
    side = Fraction(result["settings"]["outer_side"])
    if result["settings"].get("n") != 12 or side != Fraction(state["search_high"]):
        raise ValueError("imported result side does not match search high")
    directory = root / side_name(side) / "cycle-0001" / "import"
    directory.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(source, directory / "result.json")
    decision, reason = decide_stage(
        result,
        len(state["config"]["budgets"]) - 1,
        state["config"]["budgets"],
        nearby=False,
    )
    if decision == "ESCALATE":
        decision = "UNRESOLVED"
    if result.get("total_mass") is not None and Fraction(result["total_mass"]) < 12:
        decision = "UNRESOLVED"
        reason = "imported below-12 search candidate has not passed the full exact gate"
    cycle = {
        "side": str(side),
        "status": decision,
        "reason": f"imported prior search result: {reason}",
        "seed_verified_low": state["verified_low"],
        "column_rounds_completed": len(result.get("rounds") or []),
        "column_rounds_requested": result["settings"].get("column_rounds", 0),
        "stages": [
            {
                "name": "import",
                "budget": result["settings"].get("column_rounds", 0),
                "seed_label": "imported",
                "status": "complete",
                "decision": decision,
                "reason": reason,
                "result": result,
                "cumulative_column_rounds": len(result.get("rounds") or []),
                "finished_at": stamp(),
            }
        ],
    }
    state["cycles"].append(cycle)
    apply_result(state, cycle)


class StopFlag:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.requested = False
        self.announced = False
        self.signum = None

    def handle(self, signum: int, _frame: Any) -> None:
        # Signal handlers do no I/O: interrupting print/json-write must not cause
        # reentrant stream errors or an inconsistent checkpoint.
        self.requested = True
        self.signum = signum

    def poll(self) -> None:
        if self.requested and not self.announced:
            self.announced = True
            emit(self.root, f"[stop] signal {self.signum} requested; finishing current cycle, then stopping")


def run_cycle(root: Path, state: dict[str, Any]) -> None:
    active = state["active"]
    if active is None:
        plan = state.pop("scheduled_work", {})
        side = Fraction(plan["side"]) if plan.get("side") else next_side(state)
        if side is None:
            return
        cycle = {
            "side": str(side),
            "strategy": plan.get("strategy", "baseline"),
            "search_revision": state.get("search_revision", 0),
            "plan_reason": plan.get("reason", "exact midpoint"),
            "status": "RUNNING",
            "started_at": stamp(),
            "seed_verified_low": state["verified_low"],
            "stages": [],
        }
        state["cycles"].append(cycle)
        active = len(state["cycles"]) - 1
        state["active"] = active
        state["last_target"] = str(side)
        save_state(root, state)
    cycle = state["cycles"][active]
    side = Fraction(cycle["side"])
    budgets = state["config"]["budgets"]
    for stage in cycle["stages"]:
        if ("directory" in stage and not list(Path(stage["directory"]).rglob("*.job.json"))
                and (pid := active_child(Path(stage["directory"]))) is not None):
            raise frontier_runtime.LiveJob(
                f"prior child pid {pid} is still running for {stage['directory']}; "
                "wait for it to finish, then resume"
            )
    if cycle["stages"]:
        last = cycle["stages"][-1]
        if last["status"] == "complete" and last["decision"] not in (
            "ESCALATE",
            "REFINE_SCALE",
            "RETRY_ROWS",
        ):
            cycle.update(
                {"status": last["decision"], "reason": last["reason"], "finished_at": stamp()}
            )
            apply_result(state, cycle)
            save_state(root, state)
            write_views(root, state)
            publish_findings(root, state)
            return
    while True:
        incomplete = next(
            (stage for stage in reversed(cycle["stages"]) if stage["status"] == "running"), None
        )
        if incomplete is not None:
            old_dir = Path(incomplete["directory"])
            if (old_dir / "stdout.log.job.json").exists():
                code = run_child(incomplete["command"], old_dir / "stdout.log", controlled_env(state))
                if code:
                    record_job_failure(root, state, cycle, incomplete, code)
                    return
            result_path = old_dir / "result.json"
            if result_path.exists():
                try:
                    result = json.loads(result_path.read_text(encoding="utf-8"))
                    valid_side = (
                        result["settings"].get("n") == 12
                        and Fraction(result["settings"]["outer_side"]) == side
                    )
                except ValueError, KeyError, json.JSONDecodeError:
                    incomplete["status"] = "interrupted"
                else:
                    if valid_side:
                        incomplete["result"] = result
                        incomplete["status"] = "generated"
                    else:
                        incomplete["status"] = "interrupted"
            else:
                incomplete["status"] = "interrupted"
            save_state(root, state)
        generated = next(
            (stage for stage in reversed(cycle["stages"]) if stage["status"] == "generated"),
            None,
        )
        if generated is None:
            previous_complete = next(
                (
                    stage
                    for stage in reversed(cycle["stages"])
                    if stage["status"] == "complete"
                ),
                None,
            )
            if previous_complete is None:
                stage_index = 0
                stage_scale_value = starting_scale(state, side)
            elif previous_complete["decision"] == "RETRY_ROWS":
                stage_index = STAGES.index(previous_complete["name"])
                stage_scale_value = stage_scale(previous_complete) or int(state["config"]["scale"])
            elif previous_complete["decision"] == "REFINE_SCALE":
                stage_index = STAGES.index(previous_complete["name"])
                stage_scale_value = int(previous_complete["refine_scale_to"])
            else:
                stage_index = min(
                    STAGES.index(previous_complete["name"]) + 1,
                    len(budgets) - 1,
                )
                stage_scale_value = max(
                    int(state["config"]["scale"]),
                    stage_scale(previous_complete) or int(state["config"]["scale"]),
                )
            name = STAGES[stage_index]
            stage_dir = (
                root
                / side_name(side)
                / f"cycle-{active + 1:04d}"
                / f"{name}-{len(cycle['stages']) + 1:02d}"
            )
            while stage_dir.exists():
                # An orphan may have been created between mkdir and the atomic
                # state write. Preserve its bytes and use a fresh attempt name.
                emit(root, f"[recover] preserving unindexed stage directory {stage_dir}")
                stage_dir = stage_dir.with_name(stage_dir.name + "-recovered")
            stage_dir.mkdir(parents=True, exist_ok=False)
            seed, label = seed_for(state, side)
            previous = next(
                (
                    s
                    for s in reversed(cycle["stages"])
                    if s.get("candidate_unverified")
                    and Path(s["candidate_unverified"]).exists()
                ),
                None,
            )
            if previous is not None:
                previous_scale = stage_scale(previous) or LEGACY_RATIONALISATION_SCALE
                seed, label = (
                    Path(previous["candidate_unverified"]),
                    f"search-seed-only@{side}:scale{previous_scale}",
                )
            args = command(
                side,
                budgets[stage_index],
                seed,
                stage_dir,
                int(cycle.get("row_rounds", state["config"]["row_rounds"])),
                stage_scale_value,
                cycle.get("strategy", "baseline"),
            )
            raw_source = raw_source_for(state, cycle, side, stage_scale_value)
            if raw_source is not None:
                source_stage, snapshot = raw_source
                args = [sys.executable, "-m", "devtools.frontier_rationalise",
                        "--snapshot", str(snapshot), "--source-result", str(Path(source_stage["directory"]) / "result.json"),
                        "--scale", str(stage_scale_value), "--freeze", str(stage_dir / "candidate.unverified.json"),
                        "--json", str(stage_dir / "result.json")]
            generated = {
                "name": name,
                "budget": budgets[stage_index],
                "scale": stage_scale_value,
                "directory": str(stage_dir),
                "seed": str(seed),
                "seed_label": label,
                "seed_purpose": "search-seed-only"
                if label.startswith("search")
                else "verified-search-seed",
                "command": args,
                "strategy": cycle.get("strategy", "baseline"),
                "work_kind": "rerationalisation" if raw_source is not None else "generation",
                "git_sha": git_sha(),
                "started_at": stamp(),
                "status": "running",
            }
            cycle["stages"].append(generated)
            atomic_json(stage_dir / "metadata.json", generated)
            save_state(root, state)
            emit(
                root,
                f"[cycle {active + 1}] L={display(side)} exact={side} seed={label} "
                f"stage={name}({budgets[stage_index]}) scale={stage_scale_value} "
                f"strategy={cycle.get('strategy', 'baseline')} work={generated['work_kind']}",
            )
            env = controlled_env(state)
            code = run_child(args, stage_dir / "stdout.log", env)
            if code or not (stage_dir / "result.json").exists():
                generated["status"] = "interrupted"
                generated["reason"] = f"generator exit {code}; preserved for resume"
                save_state(root, state)
                record_job_failure(root, state, cycle, generated, code)
                return
            generated["result"] = json.loads(
                (stage_dir / "result.json").read_text(encoding="utf-8")
            )
            if (
                generated["result"]["settings"].get("n") != 12
                or Fraction(generated["result"]["settings"]["outer_side"]) != side
            ):
                generated["status"] = "interrupted"
                save_state(root, state)
                raise RuntimeError(f"generator result has wrong n or side: {stage_dir}")
            generated["status"] = "generated"
            save_state(root, state)
        result = generated["result"]
        candidate = Path(generated["directory"]) / "candidate.unverified.json"
        if candidate.exists():
            generated["candidate_unverified"] = str(candidate)
        mass = result.get("total_mass")
        verifier = "mass-not-below-12"
        verified_path = None
        if mass is not None and Fraction(mass) < 12 and candidate.exists():
            verifier, verified_path = verify_candidate(
                Path(generated["directory"]), candidate, side
            )
        elif mass is not None and Fraction(mass) < 12:
            verifier = "candidate-missing"
        generated["verifier"] = verifier
        if verifier.startswith("verification-error"):
            try:
                code = int(verifier.rsplit("-", 1)[-1])
            except ValueError:
                code = frontier_runtime.INFRASTRUCTURE
            record_job_failure(root, state, cycle, generated, code)
            return
        state["consecutive_job_errors"] = 0
        if verified_path is not None:
            decision, reason = "VERIFIED", "full exact retention gate accepted frozen candidate"
            cycle["verifier"] = "full-retainable"
            cycle["verified_candidate"] = verified_path
        else:
            current_scale = stage_scale(generated) or int(state["config"]["scale"])
            refinement = next_refinement_scale(
                result, current_scale, int(state["config"]["max_scale"])
            )
            if refinement is not None:
                decision = "REFINE_SCALE"
                reason = (
                    f"LP objective {result.get('objective')} is below 12 but "
                    f"rational mass {result.get('total_mass')} is not; "
                    f"refine scale {current_scale} -> {refinement}"
                )
                generated["refine_scale_to"] = refinement
            else:
                index = STAGES.index(generated["name"])
                decision, reason = decide_stage(
                    result,
                    index,
                    budgets,
                    nearby=(
                        soft_high(state) - Fraction(state["verified_low"])
                        < Fraction(state["initial_width"]) / 4
                    ),
                )
                if verifier not in ("mass-not-below-12", "full-retainable"):
                    reason += f"; verifier={verifier}"
                    if decision == "SEARCH_FAILED":
                        decision = "UNRESOLVED"
        if decision == "ESCALATE" and cycle_stalled(cycle, result):
            decision, reason = "UNRESOLVED", "objective plateau; abandon this instrument stage and schedule another strategy"
        generated.update(
            {
                "status": "complete",
                "decision": decision,
                "reason": reason,
                "finished_at": stamp(),
            }
        )
        cycle["column_rounds_requested"] = sum(
            stage["budget"] for stage in cycle["stages"] if stage["status"] == "complete"
        )
        cycle["column_rounds_completed"] = sum(
            int(stage.get("result", {}).get("column_rounds_executed",
                len(stage.get("result", {}).get("rounds") or [])))
            for stage in cycle["stages"]
            if stage["status"] == "complete"
        )
        generated["cumulative_column_rounds"] = cycle["column_rounds_completed"]
        atomic_json(Path(generated["directory"]) / "metadata.json", generated)
        save_state(root, state)
        poll_stop()
        emit(
            root,
            f"[stage] L={display(side)} rounds={generated['budget']} "
            f"scale={stage_scale(generated)} objective={result.get('objective')} "
            f"total={result.get('total_mass')} "
            f"time={float(result.get('seconds') or 0):.0f}s -> {decision}",
            significant=significant_result(decision, result),
        )
        if decision in ("ESCALATE", "REFINE_SCALE"):
            continue
        if result.get("converged") is not True and not cycle.get("row_retry_done"):
            old_rows = int(cycle.get("row_rounds", state["config"]["row_rounds"]))
            maximum_rows = int(state["config"].get("max_row_rounds", old_rows))
            if old_rows < maximum_rows:
                cycle["row_rounds"] = min(old_rows * 2, maximum_rows)
                cycle["row_retry_done"] = True
                generated["decision"] = "RETRY_ROWS"
                save_state(root, state)
                emit(root, f"[plan] inner row budget {old_rows} -> {cycle['row_rounds']}; no failure inference")
                continue
        cycle.update({"status": decision, "reason": reason, "finished_at": stamp()})
        apply_result(state, cycle)
        save_state(root, state)
        write_views(root, state)
        publish_findings(root, state)
        emit(
            root,
            f"[result] L={display(side)} exact={side} {decision} reason={reason}",
            significant=significant_result(decision, result),
        )
        emit(
            root,
            f"[frontier] verified={display(state['verified_low'])} "
            f"soft-high={display(soft_high(state))} "
            f"search-high={display(state['search_high'])}",
        )
        return


def tail_text(path: Path, count: int = 32768) -> str:
    with path.open("rb") as handle:
        handle.seek(max(0, path.stat().st_size - count))
        return handle.read().decode("utf-8", errors="replace")


def poll_stop() -> None:
    if _ACTIVE_STOP is not None:
        _ACTIVE_STOP.poll()


def controlled_env(state: dict[str, Any]) -> dict[str, str]:
    return {**os.environ, "PACK_JOBS": str(state["config"]["workers"]),
            "OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}


def raw_source_for(state: dict[str, Any], cycle: dict[str, Any], side: Fraction,
                   target_scale: int) -> tuple[dict[str, Any], Path] | None:
    completed = [s for s in cycle["stages"] if s.get("status") == "complete"]
    if completed and completed[-1].get("decision") != "REFINE_SCALE":
        return None
    for previous_cycle in reversed(state["cycles"]):
        if (Fraction(previous_cycle["side"]) != side
                or previous_cycle.get("strategy", "baseline") != cycle.get("strategy", "baseline")
                or previous_cycle.get("search_revision", 0) != cycle.get("search_revision", 0)):
            continue
        for stage in reversed(previous_cycle.get("stages", [])):
            result = stage.get("result") or {}
            path_text = result.get("raw_weights")
            used = stage_scale(stage)
            if (path_text and used and used < target_scale and scale_limited_result(result)
                    and Path(path_text).is_file()
                    and result.get("raw_weights_sha256") == digest(Path(path_text))
                    and (Path(stage["directory"]) / "result.json").exists()):
                return stage, Path(path_text)
    return None


def cycle_stalled(cycle: dict[str, Any], result: dict[str, Any]) -> bool:
    if result.get("converged") is not True or result.get("work_kind") == "rerationalisation":
        return False
    completed = [s for s in cycle["stages"] if s.get("status") == "complete"
                 and s.get("result", {}).get("work_kind") != "rerationalisation"]
    if not completed or completed[-1].get("name") == "screen":
        return False
    old = completed[-1].get("result", {}).get("objective")
    new = result.get("objective")
    return (isinstance(old, (int, float)) and isinstance(new, (int, float))
            and math.isfinite(old) and math.isfinite(new) and abs(old - new) <= 1e-7)


def record_job_failure(root: Path, state: dict[str, Any], cycle: dict[str, Any],
                       stage: dict[str, Any], code: int) -> None:
    reason = f"operational job failure {code}; not search-failure evidence"
    stage.update(status="error", decision="ERROR", reason=reason, finished_at=stamp())
    cycle.update(status="ERROR", reason=reason, finished_at=stamp(),
                 error_epoch=state.get("error_epoch", 0))
    state.setdefault("operational_errors", []).append({
        "at": stamp(), "side": cycle["side"], "code": code, "stage": stage["directory"],
        "strategy": cycle.get("strategy", "baseline"),
    })
    state["active"] = None
    state["consecutive_job_errors"] = int(state.get("consecutive_job_errors", 0)) + 1
    if code == frontier_runtime.PERMANENT_ERROR or state["consecutive_job_errors"] >= 3:
        state["mode"] = "BLOCKED"
    save_state(root, state)
    write_views(root, state)
    emit(root, f"[ERROR] L={display(cycle['side'])} {reason}; logs={stage['directory']}", significant=True)


def promote_verified(state: dict[str, Any], side: Fraction, candidate: Path, mechanism: str) -> None:
    previous = Fraction(state["verified_low"])
    if side <= previous:
        return
    record = read_json(candidate, 8 * 1024 * 1024)
    if record.get("n") != 12 or Fraction(record["outer_side"]) != side:
        raise ValueError("verified artifact does not match the proposed bound")
    mass = sum((Fraction(atom[2]) for atom in record["atoms"]), Fraction(0))
    if mass != Fraction(record["total_mass"]) or not 0 < mass < 12:
        raise ValueError("verified artifact has inconsistent or inadmissible mass")
    proof_sha = digest(candidate)
    proof_receipt = candidate.parent / "verification.json"
    if not proof_receipt.exists():
        raise ValueError("verified artifact is missing its full exact gate receipt")
    verdict = read_json(proof_receipt)
    if (verdict.get("status") != "VERIFIED" or verdict.get("category") != "full-retainable"
            or verdict.get("finished") is not True
            or verdict.get("verified_sha256") != proof_sha
            or Fraction(verdict.get("side", "0")) != side):
        raise ValueError("verified artifact does not match its full gate receipt")
    state["verified_low"] = str(side)
    state["verified_certificate"] = str(candidate)
    state["verified_sha256"] = proof_sha
    state["mode"] = "FRONTIER"
    state["consecutive_job_errors"] = 0
    frontier_policy.reconcile(state)
    event = {"id": proof_sha, "at": stamp(), "side": str(side), "previous": str(previous),
             "improvement": str(side - previous), "mass": str(mass),
             "candidate": str(candidate), "sha256": proof_sha, "mechanism": mechanism,
             "gate_receipt": str(proof_receipt)}
    if not any(e["id"] == proof_sha for e in state.setdefault("discoveries", [])):
        state["discoveries"].append(event)


def publish_findings(root: Path, state: dict[str, Any]) -> None:
    discoveries = state.get("discoveries", [])
    atomic_json(root / "findings.json", {
        "schema": 1, "verified_improvements": discoveries,
        "current_verified": {"side": state["verified_low"], "candidate": state["verified_certificate"],
                             "sha256": state.get("verified_sha256")},
    })
    lines = ["# Verified lower-bound improvements", "",
             "Only full two-route gate successes appear here. Search opportunities are not proofs.", ""]
    for event in discoveries:
        lines.extend([f"## s(12) >= {event['side']} ({display(event['side'])})",
                      f"Improvement: `{event['improvement']}`; mass: `{event['mass']}`.",
                      f"Certificate: `{event['candidate']}`", f"SHA-256: `{event['sha256']}`", ""])
    atomic_text(root / "findings.md", "\n".join(lines) + "\n")
    for event in discoveries:
        if event.get("announced"):
            continue
        emit(root, "\n" + "=" * 72 + "\nVERIFIED LOWER BOUND IMPROVEMENT\n"
             f"s(12) >= {event['side']} = {display(event['side'])}\n"
             f"previous={display(event['previous'])}  improvement={event['improvement']}\n"
             f"full exact gate: PASS   mass={event['mass']}\n"
             f"certificate: {event['candidate']}\nsha256: {event['sha256']}\n" + "=" * 72,
             significant=True)
        event["announced"] = True
        save_state(root, state)


def choose_work(state: dict[str, Any]) -> dict[str, Any]:
    target = next_side(state)
    ceiling = soft_high(state)
    pending = target == ceiling and any(
        Fraction(c['side']) == ceiling and scale_limited_unresolved(c, int(state['config']['max_scale']))
        for c in state['cycles'][-1:]
    )
    # Find the latest record for this side, not merely the last campaign cycle.
    for cycle in reversed(state['cycles']):
        if Fraction(cycle['side']) == ceiling:
            pending = target == ceiling and scale_limited_unresolved(cycle, int(state['config']['max_scale']))
            break
    return frontier_policy.plan(
        state, next_side=target, soft_high=ceiling, scale_pending=pending,
        repair_available=select_repair_candidate(state) is not None,
        saturated=numeric_search_saturated(state),
    )


def main(argv: list[str] | None = None) -> int:
    global _ACTIVE_STOP, _RUNTIME_LIMITS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--status", action="store_true", help="print saved progress without starting work")
    for name in ("verified-low", "search-high", "target-width", "strategy-width"):
        parser.add_argument(f"--{name}", type=Fraction)
    parser.add_argument("--seed-certificate", type=Path)
    for name in ("workers", "screen-rounds", "normal-rounds", "deep-rounds", "max-rounds",
                 "row-rounds", "max-row-rounds", "scale", "max-scale", "max-cycles"):
        parser.add_argument(f"--{name}", type=int)
    parser.add_argument("--strategies", help="comma-separated portfolio (default: baseline,centre,pricing,windows,dense,fine-net)")
    parser.add_argument("--max-hours", type=float, help="request a graceful stop after this session budget")
    parser.add_argument("--stop-when-exhausted", action="store_true",
                        help="exit instead of staying idle when the configured portfolio is exhausted")
    parser.add_argument("--import-result", type=Path)
    for name in ("stage-seconds", "verify-seconds", "no-progress-seconds", "heartbeat-seconds", "backoff-seconds"):
        parser.add_argument(f"--{name}", type=float)
    for name in ("retries", "max-rss-mib", "min-free-mib"):
        parser.add_argument(f"--{name}", type=int)
    args = parser.parse_args(argv)
    root = args.root.resolve()
    started = time.monotonic()
    if args.status:
        state = read_json(root / "state.json")
        print(summary(root, state, started))
        return 0
    previous_handlers = {}
    previous_workers_env = os.environ.get("PACK_JOBS")
    previous_stop, previous_limits = _ACTIVE_STOP, _RUNTIME_LIMITS
    state = None
    exit_code = 0
    try:
        with locked(root):
            stop = StopFlag(root)
            _ACTIVE_STOP = stop
            for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
                previous_handlers[signum] = signal.signal(signum, stop.handle)
            if args.resume:
                state = load_state(root)
                config = dict(state["config"])
            else:
                if (root / "state.json").exists():
                    raise ValueError("state already exists; use --resume")
                if any(path.name != ".runner.lock" for path in root.iterdir()):
                    raise ValueError("root contains files without state; preserve them and choose a fresh root")
                config = {}
            defaults = {
                "verified_low": "99/25", "search_high": "397/100", "seed_certificate": str(DEFAULT_SEED),
                "workers": int(os.environ.get("PACK_JOBS", "16")), "budgets": [8, 20, 40, 60],
                "row_rounds": 60, "max_row_rounds": 120, "scale": DEFAULT_RATIONALISATION_SCALE,
                "max_scale": DEFAULT_MAX_RATIONALISATION_SCALE,
                "strategies": [p["name"] for p in frontier_policy.PROFILES],
                "strategy_width": "1/100000", "target_width": None, "max_cycles": None,
            }
            config = {**defaults, **config}
            for key in ("verified_low", "search_high", "seed_certificate"):
                value = getattr(args, key)
                if value is not None:
                    value = str(value.resolve()) if isinstance(value, Path) else str(value)
                    if args.resume and value != config[key]:
                        raise ValueError(f"cannot change initial {key} while resuming this campaign")
                    config[key] = value
            for key in ("workers", "row_rounds", "max_row_rounds", "scale", "max_scale"):
                if getattr(args, key) is not None:
                    config[key] = getattr(args, key)
            budgets = list(config["budgets"])
            for index, key in enumerate(("screen_rounds", "normal_rounds", "deep_rounds", "max_rounds")):
                if getattr(args, key) is not None:
                    budgets[index] = getattr(args, key)
            config["budgets"] = budgets
            if args.strategies is not None:
                config["strategies"] = list(dict.fromkeys(args.strategies.split(",")))
            for strategy in config["strategies"]:
                frontier_policy.profile(strategy)
            if args.strategy_width is not None:
                config["strategy_width"] = str(args.strategy_width)
            # Finite session limits are not inherited accidentally on resume.
            config["target_width"] = str(args.target_width) if args.target_width is not None else None
            config["max_cycles"] = args.max_cycles
            runtime = {**frontier_runtime.DEFAULTS, **config.get("runtime", {})}
            for key in frontier_runtime.DEFAULTS:
                value = getattr(args, key, None)
                if value is not None:
                    runtime[key] = value
            if any(not math.isfinite(float(value)) for value in runtime.values()):
                raise ValueError("runtime budgets must be finite")
            if args.max_hours is not None and (not math.isfinite(args.max_hours) or args.max_hours <= 0):
                raise ValueError("max-hours must be positive and finite")
            if not config["strategies"]:
                raise ValueError("at least one strategy is required")
            if runtime["max_rss_mib"] == 0:
                memory = Path("/proc/meminfo").read_text().splitlines()
                total_mib = int(next(line.split()[1] for line in memory if line.startswith("MemTotal:"))) // 1024
                runtime["max_rss_mib"] = max(256, min(24576, total_mib * 3 // 4))
            if (config["workers"] < 1 or config["row_rounds"] < 1
                    or config["max_row_rounds"] < config["row_rounds"]
                    or config["scale"] < 1 or config["max_scale"] < config["scale"]
                    or sorted(set(budgets)) != budgets or budgets[0] < 1
                    or not config["strategies"] or Fraction(config["strategy_width"]) <= 0
                    or (args.max_cycles is not None and args.max_cycles < 1)
                    or (args.target_width is not None and args.target_width <= 0)
                    or (args.max_hours is not None and args.max_hours <= 0)
                    or any(float(runtime[k]) < 0 for k in runtime)
                    or runtime["stage_seconds"] <= 0 or runtime["verify_seconds"] <= 0
                    or runtime["heartbeat_seconds"] <= 0):
                raise ValueError("invalid positive budget, scale, strategy, or runtime limit")
            config["runtime"] = runtime
            _RUNTIME_LIMITS = runtime
            os.environ["PACK_JOBS"] = str(config["workers"])
            if state is None:
                state = initial_state({**config, "root": root}, Path(config["seed_certificate"]))
            else:
                if config != state["config"]:
                    state.setdefault("configuration_history", []).append({"at": stamp(), "previous": state["config"]})
                    if any(config[k] != state["config"].get(k) for k in ("budgets", "row_rounds", "max_row_rounds")):
                        state["search_revision"] = int(state.get("search_revision", 0)) + 1
                state["config"] = config
            if args.resume:
                # Explicit resume permits fresh bounded attempts for operational
                # failures, including repairs; it does not erase mathematical refusals.
                state["error_epoch"] = int(state.get("error_epoch", 0)) + 1
                if state.get("mode") == "BLOCKED":
                    state.setdefault("recoveries", []).append({"at": stamp(), "reason": "operator resumed blocked campaign"})
                    state["mode"] = "FRONTIER"
                    state["consecutive_job_errors"] = 0
            save_state(root, state)
            if args.import_result is not None:
                if args.resume:
                    raise ValueError("import-result is an initialization operation, not a resume override")
                import_result(root, state, args.import_result)
                save_state(root, state)
            atomic_text(root / "README.md", README)
            write_views(root, state)
            publish_findings(root, state)
            emit(root, f"[start] n=12 workers={config['workers']} scale={config['scale']} max-scale={config['max_scale']} "
                 f"verified={display(state['verified_low'])} search-high={display(state['search_high'])} "
                 f"strategies={','.join(config['strategies'])}")
            if state.pop("anchor_needs_verification", False):
                seed = Path(state["verified_certificate"])
                anchor_dir = root / f"anchor-{digest(seed)[:16]}"
                anchor_dir.mkdir(exist_ok=True)
                emit(root, "[verify] checking the legacy best certificate before new work")
                status, proof = verify_candidate(anchor_dir, seed, Fraction(state["verified_low"]))
                if proof is None:
                    state["anchor_needs_verification"] = True
                    raise ValueError(f"legacy anchor did not pass the full exact gate: {status}")
                state["verified_certificate"] = proof
                state["verified_sha256"] = digest(Path(proof))
                save_state(root, state)
            idle_since = None
            idle_message_at = 0.0
            while (not stop.requested or state.get("active") is not None
                   or any(a.get("status") in ("RUNNING", "INTERRUPTED") for a in state.get("repair_attempts", []))):
                poll_stop()
                active_repair = any(a.get("status") in ("RUNNING", "INTERRUPTED")
                                    for a in state.get("repair_attempts", []))
                if stop.requested and state.get("active") is None and not active_repair:
                    break
                if state.get("active") is None and not active_repair:
                    completed = sum(c["status"] in ("VERIFIED", "SEARCH_FAILED", "UNRESOLVED", "ERROR") for c in state["cycles"])
                    if args.max_cycles is not None and completed >= args.max_cycles:
                        break
                    if args.max_hours is not None and time.monotonic() - started >= args.max_hours * 3600:
                        break
                    if args.target_width is not None and soft_high(state) - Fraction(state["verified_low"]) <= args.target_width:
                        break
                    if state.get("mode") == "BLOCKED":
                        emit(root, "[BLOCKED] repeated infrastructure/environment errors; evidence saved. Fix the environment and resume.", significant=True)
                        exit_code = 1
                        break
                work = choose_work(state)
                if work["kind"] == "idle":
                    if idle_since is None:
                        idle_since = time.monotonic()
                        state["mode"] = "IDLE_EXHAUSTED"
                        state["idle_reason"] = work["reason"]
                        save_state(root, state)
                        write_views(root, state)
                        emit(root, f"[IDLE] {work['reason']}; Ctrl-C prints the summary", significant=True)
                    if args.stop_when_exhausted:
                        break
                    if time.monotonic() - idle_message_at >= runtime["heartbeat_seconds"]:
                        emit(root, f"[idle] verified={display(state['verified_low'])}; no duplicate work submitted")
                        idle_message_at = time.monotonic()
                    time.sleep(1)
                    continue
                idle_since = None
                if work["kind"] == "search":
                    state["scheduled_work"] = work
                    state["mode"] = "FRONTIER"
                    save_state(root, state)
                    emit(root, f"[plan] L={display(work['side'])} strategy={work['strategy']} reason={work['reason']}")
                try:
                    if work["kind"] == "repair":
                        run_repair(root, state)
                    else:
                        run_cycle(root, state)
                except frontier_runtime.LiveJob as error:
                    # Only legacy children lack an adoptable supervisor. Waiting
                    # is safe; starting another computation would not be.
                    emit(root, f"[recover] {error}")
                    for _ in range(max(1, int(runtime["heartbeat_seconds"]))):
                        poll_stop()
                        if stop.requested:
                            break
                        time.sleep(1)
                    if stop.requested:
                        break
                poll_stop()
                if stop.requested and state.get("active") is None:
                    break
            save_state(root, state)
            write_views(root, state)
            publish_findings(root, state)
            emit(root, summary(root, state, started))
    except (ValueError, RuntimeError, OSError, KeyError, TypeError, OverflowError) as error:
        exit_code = 1
        if state is not None:
            try:
                with locked(root):
                    save_state(root, state)
                    write_views(root, state)
                    emit(root, summary(root, state, started))
            except (OSError, RuntimeError):
                pass  # Never race another writer; the last atomic state survives.
        print(f"frontier runner stopped safely: {error}", file=sys.stderr)
    finally:
        for signum, handler in previous_handlers.items():
            signal.signal(signum, handler)
        _ACTIVE_STOP, _RUNTIME_LIMITS = previous_stop, previous_limits
        if previous_workers_env is None:
            os.environ.pop("PACK_JOBS", None)
        else:
            os.environ["PACK_JOBS"] = previous_workers_env
    return exit_code


README = """# Persistent autonomous n=12 search

Run from packing/:

    PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier --root ../Experiments/n12-frontier-search
    PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier --root ../Experiments/n12-frontier-search --resume

Ctrl-C finishes the active bounded cycle/repair, saves state and prints a summary.
Use --status to inspect a saved campaign without starting jobs. A stopped VM must
still be restarted externally; run in tmux for ordinary SSH sessions.

State schema 3 migrates schema-2 history with a backup. Live supervised jobs are
reattached on resume, not duplicated. Child jobs have wall/progress/resource limits
and bounded retries; ERROR is never mathematical SEARCH_FAILED. Repeated execution
errors enter BLOCKED. Explicit resume permits recovery after fixing the environment.

The default portfolio is baseline,centre,pricing,windows,dense,fine-net. Stagnation
changes the instrument instead of indefinitely increasing one round budget. Scale
refinement uses raw-lp.json without re-solving LP; legacy stages without raw
snapshots require an initial fresh solve. Search failures are only heuristic
frontier points. The full existing exact two-route gate alone permits VERIFIED.

Verified improvements have prominent terminal banners and their own findings.json
and findings.md ledger with certificate SHA-256. Full logs remain in stage/job files.
No retained certificate is overwritten. A successful repair beyond the heuristic
high expands the exploration interval instead of invalidating state.

On configured portfolio exhaustion the runner idles visibly without busy-looping.
--stop-when-exhausted exits instead. Neither state means mathematical impossibility.
Detailed strategy, watchdog, migration, and testing documentation is in
packing/devtools/n12-frontier.md in the repository.
"""

if __name__ == "__main__":
    raise SystemExit(main())
