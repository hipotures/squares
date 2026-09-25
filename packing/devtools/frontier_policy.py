"""Explicit, bounded research policy; heuristic failures are never upper bounds.

The portfolio changes one mechanism at a time. Every profile remains in the
unconditional fractional-certificate family and uses the unchanged exact gate.
"""
from __future__ import annotations

import math
from fractions import Fraction
from typing import Any

POLICY_VERSION = 1
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


def alternative(state: dict[str, Any], preferred: Fraction) -> dict[str, Any] | None:
    low = Fraction(state["verified_low"])
    # Nearest unresolved points first, then the previous failed search frontier.
    points = {preferred, Fraction(state["search_high"])}
    points.update(Fraction(c["side"]) for c in state["cycles"]
                  if c.get("status") in ("UNRESOLVED", "SEARCH_FAILED", "ERROR")
                  and low < Fraction(c["side"]) < 4)
    for side in sorted(points):
        if side <= low:
            continue
        for item in PROFILES:
            name = item["name"]
            if name not in state.get("config", {}).get("strategies", [p["name"] for p in PROFILES]):
                continue
            if not useful_for_side(name, side) or tried(state, side, name):
                continue
            return {"kind": "search", "side": str(side), "strategy": name,
                    "reason": item["reason"]}
    return None


def plan(
    state: dict[str, Any], *, next_side: Fraction | None,
    soft_high: Fraction, scale_pending: bool, repair_available: bool,
    saturated: bool,
) -> dict[str, Any]:
    """Select one meaningful unit of work, including recovery and safe exhaustion."""
    if state.get("active") is not None:
        return {"kind": "resume-cycle", "reason": "finish the durable active cycle"}
    if any(a.get("status") in ("RUNNING", "INTERRUPTED") for a in state.get("repair_attempts", [])):
        return {"kind": "repair", "reason": "resume the durable active repair"}
    if scale_pending and next_side is not None:
        strategy = next((c.get("strategy", "baseline") for c in reversed(state["cycles"])
                         if Fraction(c["side"]) == next_side), "baseline")
        return {"kind": "search", "side": str(next_side), "strategy": strategy,
                "reason": "untried same-side rationalisation before geometric saturation"}
    config = state.get("config", {})
    narrow = soft_high - Fraction(state["verified_low"]) <= Fraction(
        config.get("strategy_width", "1/100000")
    )
    recent = state["cycles"][-3:]
    stalled = len(recent) >= 3 and all(c.get("status") != "VERIFIED" for c in recent)
    if repair_available and (narrow or saturated or stalled):
        return {"kind": "repair", "reason": "diagnose a promising rejected candidate before more bisection"}
    if narrow or saturated or stalled:
        choice = alternative(state, soft_high)
        if choice is not None:
            return choice
    preferred = state.get("preferred_strategy", "baseline")
    if preferred not in config.get("strategies", [p["name"] for p in PROFILES]):
        preferred = config.get("strategies", ["baseline"])[0]
    if next_side is not None and not saturated and not tried(state, next_side, preferred):
        if useful_for_side(preferred, next_side):
            return {"kind": "search", "side": str(next_side), "strategy": preferred,
                    "reason": "exact midpoint using the last successful search strategy"}
        choice = alternative(state, next_side)
        if choice is not None:
            return choice
    if repair_available:
        return {"kind": "repair", "reason": "remaining untried repair evidence"}
    choice = alternative(state, soft_high)
    if choice is not None:
        return choice
    return {"kind": "idle", "reason": "configured strategy portfolio exhausted; not a mathematical impossibility proof"}
