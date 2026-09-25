"""Explicit, bounded research policy; heuristic failures are never upper bounds.

The portfolio changes one mechanism at a time. Every profile remains in the
unconditional fractional-certificate family and uses the unchanged exact gate.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path
from typing import Any

from devtools.frontier_io import digest

POLICY_VERSION = 2
PROFILES: tuple[dict[str, Any], ...] = (
    {"name": "baseline", "reason": "current production instrument", "options": {}},
    {"name": "centre", "reason": "preserve mutual seed distances instead of dilating them",
     "options": {"seed-map": "centre"}},
    {"name": "pricing", "reason": "price a broader dual support instead of only 32 rows",
     "options": {"support-cap": "128"}},
    {"name": "windows", "reason": "add sites in the axis-aligned overlap windows",
     "options": {"seed-windows": "5"}},
    {"name": "dense", "reason": "change candidate-site resolution",
     "options": {"grid-counts": "31,43,53"}},
    {"name": "fine-net", "reason": "reduce shrink using a finer valid direction net",
     "options": {"direction-steps": "720", "shrink": "4997/5000"}},
)


def profile(name: str) -> dict[str, Any]:
    for item in PROFILES:
        if item["name"] == name:
            return item
    raise ValueError(f"unknown search strategy: {name}")


def backend_key(side: Fraction) -> str:
    """The float backend cannot distinguish sides with the same binary64 value."""
    return float(side).hex()


def useful_for_side(name: str, side: Fraction) -> bool:
    shrink = Fraction(profile(name)["options"].get("shrink", "9977/10000"))
    return side < 4 * shrink


def reconcile(state: dict[str, Any]) -> None:
    """A proved improvement supersedes a heuristic ceiling, never vice versa."""
    low, high = Fraction(state["verified_low"]), Fraction(state["search_high"])
    if high > low:
        return
    if low >= 4:
        raise ValueError("verified endpoint reached the known grid upper bound; review required")
    state.setdefault("superseded_search_highs", []).append({
        "side": str(high), "kind": state.get("search_high_kind"),
        "superseded_by": str(low),
    })
    step = max(Fraction(state.get("initial_width", "1/100")) / 4, Fraction(1, 1000000))
    state["search_high"] = str(min(Fraction(4), low + step))
    state["search_high_kind"] = "EXPANDED_SEARCH_ENDPOINT"


def stagnating(cycle: dict[str, Any], tolerance: float = 1e-7) -> bool:
    generation = [stage for stage in cycle.get("stages", [])
                  if stage.get("status") == "complete"
                  and stage.get("result", {}).get("work_kind") != "rerationalisation"]
    values = [stage.get("result", {}).get("objective") for stage in generation]
    values = [float(value) for value in values if isinstance(value, (int, float))
              and math.isfinite(value)]
    return len(values) >= 2 and abs(values[-1] - values[-2]) <= tolerance


def tried(state: dict[str, Any], side: Fraction, strategy: str) -> bool:
    """Do not repeat a deterministic instrument just because a fraction changed."""
    key = backend_key(side)
    return any(
        backend_key(Fraction(c["side"])) == key
        and c.get("strategy", "baseline") == strategy
        and c.get("search_revision", 0) == state.get("search_revision", 0)
        and c.get("status") in ("VERIFIED", "SEARCH_FAILED", "UNRESOLVED", "ERROR")
        and (c.get("status") != "ERROR" or c.get("error_epoch", 0) >= state.get("error_epoch", 0))
        for c in state["cycles"]
    )


def search_resolution(state: dict[str, Any]) -> Fraction:
    """Smallest useful new-L experiment, not a proof or rounding tolerance.

    Reuse the operator's strategy-width setting (default 1e-5). The numerical
    floor also excludes a new ULP staircase when an unusually small width is
    configured. Same-side weight refinement is exempt from this admission rule.
    """
    requested = Fraction(state.get("config", {}).get("strategy_width", "1/100000"))
    if requested <= 0:
        raise ValueError("strategy-width must be positive")
    low = Fraction(state["verified_low"])
    return max(requested, 32 * Fraction.from_float(math.ulp(float(low))))


def _enabled(state: dict[str, Any]) -> list[str]:
    return state.get("config", {}).get("strategies", [p["name"] for p in PROFILES])


def _records(state: dict[str, Any], strategy: str) -> list[dict[str, Any]]:
    return [c for c in state.get("cycles", [])
            if c.get("strategy", "baseline") == strategy
            and c.get("search_revision", 0) == state.get("search_revision", 0)]


def strategy_frontier(state: dict[str, Any], strategy: str) -> dict[str, Any]:
    """Reconstruct one instrument's observations from immutable campaign history.

    All strategies share the proved low. Only this strategy/revision contributes
    heuristic ceilings. Neither another strategy's UNRESOLVED nor its reduction
    of the legacy global search_high constrains this instrument.
    """
    low = Fraction(state["verified_low"])
    resolution = search_resolution(state)
    width = Fraction(state.get("initial_width", "1/100"))
    base_step = max(resolution, min(Fraction(1, 10000), width / 100))
    records = _records(state, strategy)
    successes = sorted({Fraction(c["side"]) for c in records
                        if c.get("status") == "VERIFIED"})
    step = base_step
    if successes:
        previous = next((s for s in reversed(successes[:-1])
                         if successes[-1] - s >= resolution), None)
        if previous is not None:
            step = max(step, min(2 * (successes[-1] - previous), width / 2))
    # The configured endpoint is an exploration horizon, not a negative result.
    # A sibling's SEARCH_FAILED can shrink the legacy search_high below it.
    configured = Fraction(state.get("config", {}).get("search_high", state["search_high"]))
    horizon = max(configured, Fraction(state["search_high"]))
    if horizon <= low:
        horizon = low + max(step, width / 4)
    limit = 4 * Fraction(profile(strategy)["options"].get("shrink", "9977/10000"))
    horizon = min(horizon, limit)
    negatives = [Fraction(c["side"]) for c in records
                 if c.get("status") in ("UNRESOLVED", "SEARCH_FAILED")
                 and not c.get("superseded_by") and low < Fraction(c["side"]) <= horizon]
    ceiling = min(negatives, default=horizon)
    return {"strategy": strategy, "low": low, "ceiling": ceiling,
            "observed_ceiling": bool(negatives), "horizon": horizon,
            "resolution": resolution, "step": step,
            "last_success": successes[-1] if successes else None}


def _near_attempt(state: dict[str, Any], side: Fraction, strategy: str) -> bool:
    resolution = search_resolution(state)
    for cycle in _records(state, strategy):
        status = cycle.get("status")
        if status not in ("RUNNING", "INTERRUPTED", "VERIFIED", "UNRESOLVED", "SEARCH_FAILED", "ERROR"):
            continue
        if status == "ERROR" and cycle.get("error_epoch", 0) < state.get("error_epoch", 0):
            continue
        previous = Fraction(cycle["side"])
        if abs(side - previous) < resolution or backend_key(side) == backend_key(previous):
            return True
    return False


def strategy_proposal(state: dict[str, Any], strategy: str) -> dict[str, Any] | None:
    """Grow a successful instrument's step; bisect only its own failed bracket."""
    if strategy not in _enabled(state):
        return None
    bounds = strategy_frontier(state, strategy)
    low, ceiling, resolution = bounds["low"], bounds["ceiling"], bounds["resolution"]
    if ceiling - low < 2 * resolution:
        return None  # Local instrument exhausted at this resolution, not impossible.
    if bounds["observed_ceiling"] or bounds["last_success"] is None:
        units = (low + ceiling) / (2 * resolution)
        target = (units.numerator // units.denominator) * resolution
        mode = "strategy-local bracket" if bounds["observed_ceiling"] else "strategy-local exploration"
    else:
        unrounded = min(low + bounds["step"], ceiling)
        units = unrounded / resolution
        target = -(-units.numerator // units.denominator) * resolution
        mode = "successful-strategy advance"
    # Keep an exact, meaningful gap from both the proved low and an observed
    # failure. Rounding the midpoint must not accidentally violate that gap.
    units = (low + resolution) / resolution
    lower = -(-units.numerator // units.denominator) * resolution
    strict = bounds["observed_ceiling"] or not useful_for_side(strategy, ceiling)
    units = (ceiling - resolution if strict else ceiling) / resolution
    upper = (units.numerator // units.denominator) * resolution
    if lower > upper:
        return None
    target = max(lower, min(target, upper))
    if (target < low + resolution or target > ceiling
            or not useful_for_side(strategy, target) or _near_attempt(state, target, strategy)):
        return None
    return {"kind": "search", "side": str(target), "strategy": strategy,
            "reason": (f"{mode}; low={low} own-high={ceiling} "
                       f"step={target - low} resolution={resolution}; "
                       "other instruments' unresolved points do not bound this strategy"),
            "frontier_mode": mode}


def _priority(state: dict[str, Any]) -> list[str]:
    names = list(_enabled(state))
    preferred = state.get("preferred_strategy", "baseline")
    # A sibling may verify an already proved side and overwrite preferred_strategy
    # without replacing the actual best certificate. Prefer its real producer.
    certificate = state.get("verified_certificate")
    if certificate:
        for cycle in reversed(state.get("cycles", [])):
            if cycle.get("status") == "VERIFIED" and cycle.get("verified_candidate") == certificate:
                preferred = cycle.get("strategy", "baseline")
                break
    recent = state.get("cycles", [])[-3:]
    stalled = len(recent) == 3 and all(c.get("status") in ("UNRESOLVED", "SEARCH_FAILED", "ERROR")
                                      for c in recent)
    has_success = any(c.get("status") == "VERIFIED" for c in _records(state, preferred))
    if preferred in names:
        names.remove(preferred)
        if stalled and not has_success:
            names.append(preferred)
        else:
            names.insert(0, preferred)
    return names


def _stage_scale(stage: dict[str, Any]) -> int | None:
    """Read the recorded scale without rewriting pre-option legacy stages."""
    result = stage.get("result") or {}
    scale = result.get("settings", {}).get("scale", stage.get("scale"))
    if type(scale) is int:
        return scale
    command = stage.get("command") or []
    if "--scale" in command:
        try:
            return int(command[command.index("--scale") + 1])
        except (IndexError, TypeError, ValueError):
            return None
    return None


def precision_proposal(state: dict[str, Any]) -> dict[str, Any] | None:
    """Finite same-side scale retries remain useful below the geometric floor."""
    low = Fraction(state["verified_low"])
    maximum = int(state.get("config", {}).get("max_scale", 25_600_000))
    for strategy in _priority(state):
        seen: set[Fraction] = set()
        for cycle in reversed(_records(state, strategy)):
            side = Fraction(cycle["side"])
            if side in seen:
                continue
            seen.add(side)
            if side <= low or cycle.get("status") != "UNRESOLVED":
                continue
            finest = None
            for stage in reversed(cycle.get("stages", [])):
                result = stage.get("result") or {}
                scale = _stage_scale(stage)
                if type(scale) is int and (finest is None or scale > finest[0]):
                    finest = (scale, result)
            if finest is None:
                continue
            scale, result = finest
            objective, mass = result.get("objective"), result.get("total_mass")
            if (scale < maximum and result.get("converged") is True
                    and type(objective) in (int, float) and math.isfinite(objective)
                    and objective < 12 and mass is not None and Fraction(mass) >= 12):
                return {"kind": "search", "side": str(side), "strategy": strategy,
                        "reason": "untried same-side rationalisation before geometric saturation"}
    return None


def alternative(state: dict[str, Any], preferred: Fraction) -> dict[str, Any] | None:
    """Compatibility entry point; preferred is no longer a global soft ceiling."""
    del preferred
    for strategy in _priority(state):
        choice = strategy_proposal(state, strategy)
        if choice is not None:
            return choice
    return None


def _material_repair(state: dict[str, Any]) -> bool:
    """Match pending source eligibility before admitting an archival repair.

    Checking paths/digests matters here: a previously repaired material candidate
    must not be used as a pretext to start the only remaining microscopic repair.
    The runner independently checks the selected artifact again before execution.
    """
    low = Fraction(state["verified_low"])
    resolution = search_resolution(state)
    finished = [a for a in state.get("repair_attempts", [])
                if a.get("status") in ("VERIFIED", "REJECTED")
                or (a.get("status") == "ERROR"
                    and a.get("error_epoch", 0) >= state.get("error_epoch", 0))]
    paths = {a.get("candidate") for a in finished}
    hashes = {a.get("candidate_sha256") for a in finished}
    for cycle in state.get("cycles", []):
        if Fraction(cycle["side"]) < low + resolution:
            continue
        for stage in cycle.get("stages", []):
            if stage.get("verifier") not in (
                "quick-rejected", "full-rejected", "declaration-rejected"
            ):
                continue
            mass = (stage.get("result") or {}).get("total_mass")
            source = stage.get("candidate_unverified")
            if mass is None or source is None:
                continue
            try:
                if Fraction(mass) >= 12:
                    continue
            except (ValueError, ZeroDivisionError):
                continue
            path = Path(source)
            if str(path) not in paths and path.is_file() and digest(path) not in hashes:
                return True
    return False


def plan(
    state: dict[str, Any], *, next_side: Fraction | None,
    soft_high: Fraction, scale_pending: bool, repair_available: bool,
    saturated: bool,
) -> dict[str, Any]:
    """Select useful work without treating the nearest legacy ULP as a frontier.

    The legacy caller's soft_high/saturated values are diagnostics only for new
    geometry. They must not cap a different, newly successful instrument.
    """
    del next_side, soft_high, scale_pending, saturated
    if state.get("active") is not None:
        return {"kind": "resume-cycle", "reason": "finish the durable active cycle"}
    if any(a.get("status") in ("RUNNING", "INTERRUPTED") for a in state.get("repair_attempts", [])):
        return {"kind": "repair", "reason": "resume the durable active repair"}
    precision = precision_proposal(state)
    if precision is not None:
        return precision
    choice = alternative(state, Fraction(state["verified_low"]))
    if choice is not None:
        return choice
    if repair_available and _material_repair(state):
        return {"kind": "repair", "reason": "remaining repair evidence above the meaningful step floor"}
    return {"kind": "idle", "reason": "configured strategy frontiers exhausted at this search resolution; not a mathematical impossibility proof"}
