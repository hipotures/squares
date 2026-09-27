"""Durable search-grid refinement, independent of certificate precision.

Planning is read-only. Only the controller, after checking stop and resource
limits, commits a resolution change. Historical search outcomes, budgets,
seeds, and proof gates are never rewritten by this policy.
"""
from __future__ import annotations

import math
from fractions import Fraction
from pathlib import Path
from typing import Any


def requested_width(state: dict[str, Any]) -> Fraction:
    value = Fraction(state.get("config", {}).get("strategy_width", "1/100000"))
    if value <= 0:
        raise ValueError("strategy-width must be positive")
    return value


def numerical_floor(state: dict[str, Any]) -> Fraction:
    low = Fraction(state["verified_low"])
    return 32 * Fraction.from_float(math.ulp(float(low)))


def effective_resolution(state: dict[str, Any]) -> Fraction:
    """Keep automatic progress on resume; an explicit width change starts anew."""
    requested = requested_width(state)
    effective = requested
    saved = state.get("adaptive_resolution")
    if saved is not None:
        if not isinstance(saved, dict):
            raise ValueError("invalid adaptive resolution state")
        try:
            origin = Fraction(saved["requested_width"])
            previous = Fraction(saved["effective_width"])
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise ValueError("invalid adaptive resolution state") from exc
        if not 0 < previous <= origin:
            raise ValueError("invalid adaptive resolution range")
        if origin == requested:
            effective = previous
    return max(effective, numerical_floor(state))


def _busy(state: dict[str, Any]) -> bool:
    return bool(
        state.get("mode") == "BLOCKED"
        or state.get("active") is not None
        or state.get("active_generation")
        or state.get("generation_wave")
        or any(c.get("status") in ("RUNNING", "INTERRUPTED") for c in state.get("cycles", []))
        or any(a.get("status") in ("RUNNING", "INTERRUPTED") for a in state.get("repair_attempts", []))
    )


def refinement_proposal(state: dict[str, Any]) -> dict[str, Any] | None:
    """Propose one decade only when an observed bracket is grid-limited.

    No random retries or reset of failed instruments: a duplicate or operational
    error at an otherwise usable resolution is not a reason to refine. An
    unobserved exploration horizon is not promoted to a negative observation.
    Several cheap administrative steps may be needed for a legacy narrow gap;
    each strictly decreases the grid and the existing 32-ULP floor is final.
    """
    from devtools import frontier_policy as policy

    if _busy(state):
        return None
    current = effective_resolution(state)
    floor = numerical_floor(state)
    if current <= floor:
        return None
    low = Fraction(state["verified_low"])
    if policy.precision_proposal(state) is not None or policy.alternative(state, low) is not None:
        return None
    brackets = []
    for name in state.get("config", {}).get("strategies", [p["name"] for p in policy.PROFILES]):
        bounds = policy.strategy_frontier(state, name)
        ceiling = bounds["ceiling"]
        if not bounds["observed_ceiling"] or ceiling <= low:
            continue
        lower_units = (low + current) / current
        lower = -(-lower_units.numerator // lower_units.denominator)
        upper_units = (ceiling - current) / current
        upper = upper_units.numerator // upper_units.denominator
        if ceiling - low < 2 * current or lower > upper:
            brackets.append({"strategy": name, "ceiling": str(ceiling), "gap": str(ceiling - low)})
    if not brackets:
        return None
    refined = max(current / 10, floor)
    result = {
        "kind": "refine-resolution",
        "from": str(current),
        "to": str(refined),
        "floor": str(floor),
        "requested_width": str(requested_width(state)),
        "verified_low": str(low),
        "search_revision": state.get("search_revision", 0),
        "brackets": brackets,
        "reason": "observed strategy brackets exhausted at the current search grid; refine automatically, not a proof of impossibility",
    }
    preview = {**state, "adaptive_resolution": {
        "requested_width": result["requested_width"], "effective_width": str(refined),
    }}
    next_work = policy.alternative(preview, low)
    if next_work is not None:
        result["side"] = next_work["side"]
        result["strategy"] = next_work["strategy"]
    return result


def apply_refinement(root: Path, state: dict[str, Any], proposal: dict[str, Any], frontier) -> bool:
    """Checkpoint before admitting work; return False when stopping takes priority."""
    stopped = getattr(frontier, "stop_requested", lambda: False)
    if stopped():
        return False
    if proposal != refinement_proposal(state):
        raise ValueError("stale or invalid search-resolution proposal")
    if stopped():
        return False
    state["adaptive_resolution"] = {
        "requested_width": proposal["requested_width"],
        "effective_width": proposal["to"],
    }
    state.setdefault("resolution_history", []).append({**proposal, "at": frontier.stamp()})
    state["mode"] = "FRONTIER"
    state.pop("idle_reason", None)
    frontier.save_state(root, state)
    old, new = Fraction(proposal["from"]), Fraction(proposal["to"])
    frontier.emit(
        root,
        f"[resolution] search grid {float(old):.12g} -> {float(new):.12g} "
        f"exact={old}->{new} floor={proposal['floor']} "
        f"verified={proposal['verified_low']}; checkpoint saved; automatic refinement",
    )
    return True
