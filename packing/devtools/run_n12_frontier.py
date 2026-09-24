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
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
DEFAULT_SEED = REPO / "packing/cases/n12_fractional_certificate/certificate.json"
SCHEMA = 2
LEGACY_RATIONALISATION_SCALE = 200_000
DEFAULT_RATIONALISATION_SCALE = 1_600_000
DEFAULT_MAX_RATIONALISATION_SCALE = 25_600_000
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
    return "none" if side is None else f"{float(Fraction(side)):.9f}"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    temporary.replace(path)
    directory = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def load_state(root: Path, config: dict[str, Any] | None = None) -> dict[str, Any]:
    state = json.loads((root / "state.json").read_text(encoding="utf-8"))
    if state.get("schema") != SCHEMA or state.get("n") != 12:
        raise ValueError("incompatible frontier state schema or n")
    if config is not None:
        stored_config = state.get("config")
        if not isinstance(stored_config, dict):
            raise ValueError("invalid frontier state config")
        if any(
            stored_config.get(key) != config.get(key)
            for key in (
                "verified_low",
                "search_high",
                "seed_certificate",
                "workers",
                "budgets",
                "row_rounds",
            )
        ):
            raise ValueError("resume settings differ from the saved experiment")
        requested_scale = config.get("scale")
        stored_scale = stored_config.get("scale")
        if stored_scale is None and requested_scale is not None:
            # Schema-2 states written before the scale became configurable used
            # 200000 unconditionally. Preserve that history in old stage results,
            # then upgrade only future work to the requested nested refinement.
            stored_config["scale"] = requested_scale
            state.setdefault("migrations", []).append(
                {
                    "at": stamp(),
                    "kind": "rationalisation-scale",
                    "from": LEGACY_RATIONALISATION_SCALE,
                    "to": requested_scale,
                }
            )
        elif stored_scale != requested_scale:
            raise ValueError("resume rationalisation scale differs from the saved experiment")
        requested_max_scale = config.get("max_scale")
        stored_max_scale = stored_config.get("max_scale")
        if stored_max_scale is None and requested_max_scale is not None:
            stored_config["max_scale"] = requested_max_scale
            state.setdefault("migrations", []).append(
                {
                    "at": stamp(),
                    "kind": "max-rationalisation-scale",
                    "from": None,
                    "to": requested_max_scale,
                }
            )
        elif stored_max_scale != requested_max_scale:
            raise ValueError(
                "resume maximum rationalisation scale differs from the saved experiment"
            )
    low, high = Fraction(state["verified_low"]), Fraction(state["search_high"])
    if not low < high or not isinstance(state.get("cycles"), list):
        raise ValueError("invalid frontier state")
    if state.get("active") is not None and state["active"] >= len(state["cycles"]):
        raise ValueError("active cycle is missing")
    if not Path(state["verified_certificate"]).exists():
        raise ValueError("verified certificate is missing")
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = stamp()
    atomic_json(root / "state.json", state)


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
    if float(ceiling) == float(low) or ceiling - low < Fraction(1, 10**10):
        return None
    # Revisit an unresolved ceiling only when the search instrument actually
    # became stronger. A better VERIFIED seed alone is not enough: the old
    # policy repeatedly reran the deterministic 3.961875 search after every
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
    return (low + ceiling) / 2


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
        if side > Fraction(state["verified_low"]):
            state["verified_low"] = str(side)
            state["verified_certificate"] = cycle["verified_candidate"]
    elif status == "SEARCH_FAILED":
        if side <= Fraction(state["search_high"]):
            state["search_high"] = str(side)
            state["search_high_kind"] = "SEARCH_FAILED"
    elif status == "UNRESOLVED":
        if str(side) not in state["unresolved"]:
            state["unresolved"].append(str(side))
            state["unresolved"].sort(key=Fraction)
    else:
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
    colour = (
        significant
        and "NO_COLOR" not in os.environ
        and (sys.stdout.isatty() or os.environ.get("FORCE_COLOR") == "1")
    )
    print(f"{BLUE}{message}{RESET}" if colour else message, flush=True)
    with (root / "runner.log").open("a", encoding="utf-8") as handle:
        # Persistent logs remain plain text even when the terminal line is blue.
        handle.write(f"{stamp()} {message}\n")


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
) -> list[str]:
    return [
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


def process_start_ticks(pid: int) -> str | None:
    """Linux process identity, including its start time to exclude PID reuse."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text(encoding="utf-8")
    except OSError, ValueError:
        return None
    fields = stat.rsplit(") ", 1)
    if len(fields) != 2:
        return None
    parts = fields[1].split()
    return parts[19] if len(parts) > 19 else None


def active_child(directory: Path) -> int | None:
    """Return a retained child still writing this stage, if any."""
    for record_path in directory.glob("*.child.json"):
        try:
            record = json.loads(record_path.read_text(encoding="utf-8"))
            pid = int(record["pid"])
            ticks = record["start_ticks"]
        except OSError, ValueError, KeyError, TypeError:
            continue
        if ticks is not None and process_start_ticks(pid) == ticks:
            return pid
    return None


def latest_progress(directory: Path) -> tuple[str, str, str]:
    """Read flushed logs for the latest column, LP round, and finite objective."""
    column_round = "none"
    lp_round = "none"
    objective = "unknown"
    column_log = directory / "column.log"
    if column_log.exists():
        for line in reversed(column_log.read_text(encoding="utf-8").splitlines()):
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
        for line in reversed(row_log.read_text(encoding="utf-8").splitlines()):
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
    with output.open("w", encoding="utf-8") as handle:
        process = subprocess.Popen(
            args,
            cwd=REPO / "packing",
            stdout=handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
        atomic_json(
            output.with_name(output.name + ".child.json"),
            {
                "pid": process.pid,
                "start_ticks": process_start_ticks(process.pid),
                "started_at": stamp(),
                "command": args,
            },
        )
        started = time.monotonic()
        while True:
            try:
                return process.wait(timeout=300)
            except subprocess.TimeoutExpired:
                if output.parent.parent.name.startswith("cycle-"):
                    emit(
                        output.parents[3],
                        heartbeat_message(args, output, time.monotonic() - started),
                    )


def verify_candidate(  # noqa: PLR0911 - each exit names a retained gate outcome
    directory: Path, candidate: Path, expected_side: Fraction
) -> tuple[str, str | None]:
    """Declare by exact sweep, then require the full two-route retention decision."""
    try:
        record = json.loads(candidate.read_text(encoding="utf-8"))
        candidate_side = Fraction(record["outer_side"])
        candidate_mass = Fraction(record["total_mass"])
    except ValueError, KeyError, TypeError, json.JSONDecodeError:
        return "candidate-invalid", None
    if record.get("n") != 12 or candidate_side != expected_side:
        return "candidate-side-mismatch", None
    if candidate_mass >= 12:
        return "mass-not-below-12", None
    attempt = 1
    while (directory / f"verify-declare-{attempt}.log").exists():
        attempt += 1
    pending = directory / (
        "candidate.pending-verification.json"
        if attempt == 1
        else f"candidate.pending-verification-{attempt}.json"
    )
    verified = directory / (
        "candidate.verified.json" if attempt == 1 else f"candidate.verified-{attempt}.json"
    )
    shutil.copyfile(candidate, pending)
    declaration = run_child(
        [sys.executable, "-m", "devtools.declare_least_cell_mass", str(pending)],
        directory / f"verify-declare-{attempt}.log",
    )
    if declaration:
        return "declaration-rejected", None
    quick_log = directory / f"verify-quick-{attempt}.log"
    quick = run_child(
        [sys.executable, "-m", "devtools.decide_certificate", "--quick", str(pending)],
        quick_log,
    )
    if quick:
        return "quick-rejected", None
    full_log = directory / f"verify-full-{attempt}.log"
    full = run_child(
        [sys.executable, "-m", "devtools.decide_certificate", str(pending)], full_log
    )
    if full == 0 and "RETAINABLE: both routes accept" in full_log.read_text(encoding="utf-8"):
        pending.replace(verified)
        return "full-retainable", str(verified)
    return "full-rejected", None


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
        f"Next side: `{next_side(state)}`.",
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
        "| Side | Status | Scale | Column rounds | Last objective | Reason |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for cycle in state["cycles"]:
        last = cycle["stages"][-1] if cycle["stages"] else {}
        result = last.get("result") or {}
        lines.append(
            f"| {cycle['side']} | {cycle['status']} | {stage_scale(last) or ''} | "
            f"{cycle.get('column_rounds_completed', 0)} | {result.get('objective', '')} "
            f"| {cycle.get('reason', '')} |"
        )
    (root / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
            f"frontier width: {high - low} = {display(high - low)}",
            f"exact verifications attempted: {attempts}",
            f"next suggested L: {next_side(state)}",
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
        "search_high": str(high),
        "search_high_kind": "CONFIGURED_SEARCH_ENDPOINT",
        "unresolved": [],
        "cycles": [],
        "active": None,
        "last_target": None,
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

    def handle(self, signum: int, _frame: Any) -> None:
        if not self.requested:
            self.requested = True
            emit(
                self.root,
                f"[stop] signal {signum} requested; finishing current L cycle, then stopping",
            )


def run_cycle(root: Path, state: dict[str, Any]) -> None:
    active = state["active"]
    if active is None:
        side = next_side(state)
        if side is None:
            return
        cycle = {
            "side": str(side),
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
        if "directory" in stage and (pid := active_child(Path(stage["directory"]))) is not None:
            raise RuntimeError(
                f"prior child pid {pid} is still running for {stage['directory']}; "
                "wait for it to finish, then resume"
            )
    if cycle["stages"]:
        last = cycle["stages"][-1]
        if last["status"] == "complete" and last["decision"] not in (
            "ESCALATE",
            "REFINE_SCALE",
        ):
            cycle.update(
                {"status": last["decision"], "reason": last["reason"], "finished_at": stamp()}
            )
            apply_result(state, cycle)
            save_state(root, state)
            write_views(root, state)
            return
    while True:
        incomplete = next(
            (stage for stage in reversed(cycle["stages"]) if stage["status"] == "running"), None
        )
        if incomplete is not None:
            result_path = Path(incomplete["directory"]) / "result.json"
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
                state["config"]["row_rounds"],
                stage_scale_value,
            )
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
                "git_sha": git_sha(),
                "started_at": stamp(),
                "status": "running",
            }
            cycle["stages"].append(generated)
            atomic_json(stage_dir / "metadata.json", generated)
            save_state(root, state)
            emit(
                root,
                f"[cycle {active + 1}] L={display(side)} seed={label} "
                f"stage={name}({budgets[stage_index]}) scale={stage_scale_value}",
            )
            env = os.environ.copy()
            env.update(
                {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"}
            )
            code = run_child(args, stage_dir / "stdout.log", env)
            if code or not (stage_dir / "result.json").exists():
                generated["status"] = "interrupted"
                generated["reason"] = f"generator exit {code}; preserved for resume"
                save_state(root, state)
                raise RuntimeError(
                    f"generator failed at L={side}; see {stage_dir / 'stdout.log'}"
                )
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
            len(stage.get("result", {}).get("rounds") or [])
            for stage in cycle["stages"]
            if stage["status"] == "complete"
        )
        generated["cumulative_column_rounds"] = cycle["column_rounds_completed"]
        atomic_json(Path(generated["directory"]) / "metadata.json", generated)
        save_state(root, state)
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
        cycle.update({"status": decision, "reason": reason, "finished_at": stamp()})
        apply_result(state, cycle)
        save_state(root, state)
        write_views(root, state)
        emit(
            root,
            f"[result] L={display(side)} {decision} reason={reason}",
            significant=significant_result(decision, result),
        )
        emit(
            root,
            f"[frontier] verified={display(state['verified_low'])} "
            f"soft-high={display(soft_high(state))} "
            f"search-high={display(state['search_high'])}",
        )
        return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--verified-low", type=Fraction, default=Fraction(99, 25))
    parser.add_argument("--search-high", type=Fraction, default=Fraction(397, 100))
    parser.add_argument("--seed-certificate", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--workers", type=int, default=int(os.environ.get("PACK_JOBS", "1")))
    parser.add_argument("--screen-rounds", type=int, default=8)
    parser.add_argument("--normal-rounds", type=int, default=20)
    parser.add_argument("--deep-rounds", type=int, default=40)
    parser.add_argument("--max-rounds", type=int, default=60)
    parser.add_argument(
        "--row-rounds",
        type=int,
        default=60,
        help="maximum inner row-generation rounds per column round",
    )
    parser.add_argument(
        "--scale",
        type=int,
        default=DEFAULT_RATIONALISATION_SCALE,
        help=(
            "initial weight rationalisation denominator; default 1600000 is an "
            "exact 8x refinement of the historical 200000 grid"
        ),
    )
    parser.add_argument(
        "--max-scale",
        type=int,
        default=DEFAULT_MAX_RATIONALISATION_SCALE,
        help=(
            "largest automatic rationalisation denominator; scale doubles only "
            "when LP objective < 12 but rationalised mass is still >= 12"
        ),
    )
    parser.add_argument("--target-width", type=Fraction)
    parser.add_argument("--max-cycles", type=int)
    parser.add_argument("--import-result", type=Path)
    args = parser.parse_args(argv)
    budgets = [args.screen_rounds, args.normal_rounds, args.deep_rounds, args.max_rounds]
    if (
        args.workers < 1
        or args.row_rounds < 1
        or args.scale < 1
        or args.max_scale < args.scale
        or sorted(set(budgets)) != budgets
        or budgets[0] < 1
        or (args.max_cycles is not None and args.max_cycles < 1)
        or (args.target_width is not None and args.target_width <= 0)
    ):
        parser.error(
            "workers and budgets must be positive, budgets strictly increasing, "
            "and finite stops positive"
        )
    root = args.root.resolve()
    seed = args.seed_certificate.resolve()
    config: dict[str, Any] = {
        "verified_low": str(args.verified_low),
        "search_high": str(args.search_high),
        "seed_certificate": str(seed),
        "workers": args.workers,
        "budgets": budgets,
        "row_rounds": args.row_rounds,
        "scale": args.scale,
        "max_scale": args.max_scale,
        "target_width": str(args.target_width) if args.target_width is not None else None,
        "max_cycles": args.max_cycles,
    }
    started = time.monotonic()
    try:
        with locked(root):
            if args.resume:
                state = load_state(root, config)
            else:
                if (root / "state.json").exists():
                    parser.error("state already exists; use --resume")
                if any(path.name != ".runner.lock" for path in root.iterdir()):
                    parser.error("root contains files without state; choose a fresh root")
                state = initial_state({**config, "root": root}, seed)
                (root / "README.md").write_text(README, encoding="utf-8")
                save_state(root, state)
                if args.import_result is not None:
                    import_result(root, state, args.import_result)
                    save_state(root, state)
            state["session_limits"] = {
                "target_width": config["target_width"],
                "max_cycles": config["max_cycles"],
            }
            save_state(root, state)
            write_views(root, state)
            stop = StopFlag(root)
            signal.signal(signal.SIGINT, stop.handle)
            signal.signal(signal.SIGTERM, stop.handle)
            if hasattr(signal, "SIGHUP"):
                signal.signal(signal.SIGHUP, stop.handle)
            os.environ["PACK_JOBS"] = str(args.workers)
            emit(
                root,
                f"[start] n=12 workers={args.workers} scale={state['config']['scale']} "
                f"max-scale={state['config']['max_scale']} "
                f"verified={display(state['verified_low'])} "
                f"search-high={display(state['search_high'])}",
            )
            try:
                while not stop.requested or state["active"] is not None:
                    if state["active"] is None:
                        if (
                            args.max_cycles is not None
                            and sum(
                                c["status"] in ("VERIFIED", "SEARCH_FAILED", "UNRESOLVED")
                                for c in state["cycles"]
                            )
                            >= args.max_cycles
                        ):
                            break
                        if (
                            args.target_width is not None
                            and soft_high(state) - Fraction(state["verified_low"])
                            <= args.target_width
                        ):
                            break
                        if next_side(state) is None:
                            break
                    run_cycle(root, state)
            finally:
                save_state(root, state)
                write_views(root, state)
                emit(root, summary(root, state, started))
    except (ValueError, RuntimeError, FileNotFoundError) as error:
        print(f"frontier runner: {error}", file=sys.stderr)
        return 1
    return 0


README = """# n=12 frontier search record

From `packing/`:

```bash
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \\
  --root ../Experiments/n12-frontier-search
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \\
  --root ../Experiments/n12-frontier-search --resume
```

`state.json` is authoritative. Each side has stable rational naming; each cycle
and stage has its own directory. `summary.csv` and `report.md` are views of state.
Use `--resume` after interruption. The lock prevents concurrent writers.
Each subprocess records its PID and Linux process start identity beside its log.
If a parent crash leaves a child alive, resume refuses to launch a duplicate
until that child exits. SIGINT, SIGTERM, and SIGHUP request a graceful stop;
long subprocesses emit a heartbeat every five minutes, including the latest
flushed column round, LP round, and objective when available.

A cycle is one side from screening through its final VERIFIED, SEARCH_FAILED, or
UNRESOLVED decision. The first Ctrl-C finishes that cycle. Stage budgets rerun
the generator with sites from the preceding frozen candidate; that candidate is
only a search seed. Budgets are additional restart budgets: the default
8/20/40/60 schedule can request up to 128 column rounds across four runs,
plus repeated inner row generation. State and report record the cumulative
column rounds actually completed. No stage resumes solver internals.

The runner uses `--scale 1600000` initially and an automatic nested scale
ladder up to `--max-scale 25600000`. If a converged stage has LP objective
below 12 but upward rationalisation still leaves total mass at or above 12,
the runner first repeats the same column budget on the same side at twice the
scale, seeded from the preceding candidate's sites. It keeps doubling only
while rationalisation is the blocker. A point whose LP objective is itself at
or above 12 spends effort on the column search instead.

A schema-2 state written before these options existed is migrated in place on
`--resume`; old stages remain auditable at their original scale. An unresolved
point is revisited only when a finer scale remains untried there. Merely
improving the VERIFIED low no longer causes the deterministic unresolved
ceiling to be recomputed over and over.

VERIFIED results, scale-refinement opportunities, and final scale-limited
UNRESOLVED results are printed in blue on an interactive terminal so they stand
out during occasional checks. `NO_COLOR` disables this; persistent logs never
contain ANSI colour codes.

`--row-rounds` limits inner row generation per column round; a stage that does
not converge there is UNRESOLVED regardless of its floating-point objective.
An incomplete stage with
a valid result JSON is finalized on resume; otherwise its files remain in place
and a new stage attempt is made.

The next side is the exact midpoint between the best VERIFIED low and the
nearest UNRESOLVED point above it, or the SEARCH_FAILED/configured high if no
such point exists. When a verified low improves and the gap to the nearest
UNRESOLVED point is at most one sixteenth of the initial width, that point is
retried once with the new seed. A gap below 1e-10 has no useful float input to
the current generator, so the runner stops.

The search policy escalates when the result is close to mass/objective 12, is
improving with useful columns or priced depth, or has priced depth near the
frontier. A stalled distant run is SEARCH_FAILED; a close or improving run at
maximum budget is UNRESOLVED. These are instrument judgments, never proofs.
Only a frozen below-12 candidate accepted by the full exact two-route gate is
VERIFIED. The original retained certificate is never changed.
"""


if __name__ == "__main__":
    raise SystemExit(main())
