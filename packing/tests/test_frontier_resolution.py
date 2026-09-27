"""Automatic grid-refinement regressions; synthetic outcomes are not proofs."""
from __future__ import annotations

import copy
import math
import signal
from fractions import Fraction
from types import SimpleNamespace

import pytest

from devtools import frontier_policy as policy
from devtools import frontier_resolution as resolution
from devtools import run_n12_frontier as frontier
from devtools.frontier_io import atomic_json, read_json


LOW = Fraction(3964699, 1000000)
HIGH = Fraction(39647, 10000)
WIDTH = Fraction(1, 1000000)


def exhausted(low=LOW, high=HIGH, width=WIDTH):
    names = [p["name"] for p in policy.PROFILES]
    return {
        "verified_low": str(low), "search_high": str(high), "initial_width": "1/100",
        "search_high_kind": "SEARCH_FAILED", "preferred_strategy": "fine-net",
        "unresolved": [str(high)], "search_revision": 0, "error_epoch": 0,
        "mode": "IDLE_EXHAUSTED", "idle_reason": "old grid exhausted",
        "active": None, "active_generation": [], "generation_wave": None,
        "repair_attempts": [],
        "config": {"strategy_width": str(width), "search_high": "397/100",
                   "strategies": names, "workers": 16, "generation_trials": 3,
                   "max_scale": 25600000},
        "cycles": [{"side": str(high), "strategy": name, "status": "UNRESOLVED",
                    "search_revision": 0, "stages": []} for name in names],
    }


def controller(events=None, stopped=lambda: False):
    def save(root, state):
        atomic_json(root / "state.json", state)
    return SimpleNamespace(stamp=lambda: "fixture", save_state=save,
                           stop_requested=stopped,
                           emit=lambda *args: events.append(args[1]) if events is not None else None)


@pytest.mark.parametrize("low,width,target", [
    (Fraction(396469, 100000), Fraction(1, 100000), Fraction(792939, 200000)),
    (LOW, WIDTH, Fraction(7929399, 2000000)),
])
def test_supplied_exhaustion_log_refines_without_manual_restart(tmp_path, low, width, target):
    state = exhausted(low=low, width=width)
    before = copy.deepcopy(state)
    proposal = frontier.choose_work(state)
    assert proposal["kind"] == "refine-resolution"
    assert Fraction(proposal["from"]) == width
    assert Fraction(proposal["to"]) == width / 10
    assert state == before
    events = []
    assert resolution.apply_refinement(tmp_path, state, proposal, controller(events))
    assert state["config"] == before["config"]
    assert state["cycles"] == before["cycles"]
    assert state["verified_low"] == before["verified_low"]
    assert state["search_high"] == before["search_high"]
    assert state["search_revision"] == before["search_revision"]
    saved = read_json(tmp_path / "state.json")
    assert saved == state
    assert len(saved["resolution_history"]) == 1
    assert "[resolution]" in events[0]
    work = frontier.choose_work(saved)
    assert work["kind"] == "search"
    assert Fraction(work["side"]) == target
    assert policy.search_resolution(saved) == width / 10
    assert resolution.refinement_proposal(saved) is None


def test_multiple_successive_decades_are_automatic_and_exact(tmp_path):
    state = exhausted()
    for width in (Fraction(1, 10**n) for n in range(6, 11)):
        assert policy.search_resolution(state) == width
        proposal = frontier.choose_work(state)
        assert proposal["kind"] == "refine-resolution"
        assert resolution.apply_refinement(tmp_path, state, proposal, controller())
        target = Fraction(frontier.choose_work(state)["side"])
        assert LOW < target < HIGH
        # Controller-only fixture: pretend later verified search closed the gap.
        state["verified_low"] = str(HIGH - width / 10)
    assert policy.search_resolution(state) == Fraction(1, 10**11)
    assert len(state["resolution_history"]) == 5


def test_refinement_stops_at_32_ulp_without_a_spin_or_duplicate_work(tmp_path):
    low = Fraction.from_float(3.96469)
    ulp = Fraction.from_float(math.ulp(float(low)))
    state = exhausted(low=low, high=low + 2 * ulp)
    for _ in range(20):
        proposal = frontier.choose_work(state)
        if proposal["kind"] == "idle":
            break
        assert proposal["kind"] == "refine-resolution"
        assert Fraction(proposal["to"]) < Fraction(proposal["from"])
        assert Fraction(proposal["to"]) >= 32 * ulp
        resolution.apply_refinement(tmp_path, state, proposal, controller())
    else:
        pytest.fail("automatic refinement did not reach the numeric floor")
    assert policy.search_resolution(state) == 32 * ulp
    before = copy.deepcopy(state)
    for _ in range(10):
        assert frontier.choose_work(state)["kind"] == "idle"
    assert "32-ULP" in frontier.choose_work(state)["reason"]
    assert state == before


def test_floor_still_allows_a_backend_distinct_interior_target(tmp_path):
    low = Fraction(127, 32)
    floor = 32 * Fraction.from_float(math.ulp(float(low)))
    state = exhausted(low=low, high=low + 2 * floor, width=10 * floor)
    resolution.apply_refinement(tmp_path, state, frontier.choose_work(state), controller())
    work = frontier.choose_work(state)
    assert work["kind"] == "search"
    assert Fraction(work["side"]) == low + floor
    assert policy.backend_key(Fraction(work["side"])) != policy.backend_key(low)


def test_off_grid_bracket_with_no_admissible_grid_point_can_refine():
    low = LOW + WIDTH / 3
    state = exhausted(low=low, high=low + 2 * WIDTH)
    assert all(policy.strategy_proposal(state, n) is None for n in state["config"]["strategies"])
    assert resolution.refinement_proposal(state)["kind"] == "refine-resolution"


@pytest.mark.parametrize("field,value", [
    ("active", 0), ("active_generation", [0]), ("generation_wave", {"id": "live"}),
    ("repair_attempts", [{"status": "INTERRUPTED"}]), ("mode", "BLOCKED"),
])
def test_no_refinement_during_owned_or_blocked_work(field, value):
    state = exhausted()
    state[field] = value
    assert resolution.refinement_proposal(state) is None


def test_pending_scale_refinement_precedes_search_grid_change():
    state = exhausted()
    state["cycles"][0]["stages"] = [{"scale": 1600000, "result": {
        "converged": True, "objective": 11.9999, "total_mass": "12001/1000",
    }}]
    assert "rationalisation" in frontier.choose_work(state)["reason"]
    assert resolution.refinement_proposal(state) is None


def test_duplicate_operational_failure_and_disabled_brackets_do_not_trigger_refinement():
    state = exhausted()
    state["config"]["strategies"] = ["windows"]
    state["cycles"] = []
    work = frontier.choose_work(state)
    state["cycles"].append({"side": work["side"], "strategy": "windows", "status": "ERROR",
                            "error_epoch": 0, "stages": []})
    # A narrow ceiling in a disabled strategy cannot unlock retries in windows.
    state["cycles"].append({"side": str(HIGH), "strategy": "centre", "status": "UNRESOLVED", "stages": []})
    assert resolution.refinement_proposal(state) is None
    assert frontier.choose_work(state)["kind"] == "idle"
    state["error_epoch"] += 1
    assert frontier.choose_work(state)["side"] == work["side"]


def test_an_available_strategy_is_tried_before_any_global_refinement():
    state = exhausted()
    state["cycles"] = [c for c in state["cycles"] if c["strategy"] != "windows"]
    assert frontier.choose_work(state)["strategy"] == "windows"
    assert resolution.refinement_proposal(state) is None


def test_explicit_width_change_does_not_accidentally_reuse_an_old_auto_setting(tmp_path):
    state = exhausted()
    resolution.apply_refinement(tmp_path, state, frontier.choose_work(state), controller())
    assert policy.search_resolution(state) == WIDTH / 10
    same = copy.deepcopy(state)
    same["config"]["strategy_width"] = "0.000001"
    assert policy.search_resolution(same) == WIDTH / 10
    state["config"]["strategy_width"] = "1/100000"
    assert policy.search_resolution(state) == Fraction(1, 100000)
    state["config"]["strategy_width"] = "1/1000000000"
    assert policy.search_resolution(state) == Fraction(1, 1000000000)


def test_stop_before_commit_preserves_every_byte(tmp_path):
    state = exhausted()
    atomic_json(tmp_path / "state.json", state)
    before = (tmp_path / "state.json").read_bytes()
    proposal = frontier.choose_work(state)
    assert not resolution.apply_refinement(tmp_path, state, proposal, controller(stopped=lambda: True))
    assert (tmp_path / "state.json").read_bytes() == before
    assert "adaptive_resolution" not in state


def test_stale_proposal_is_rejected_without_state_changes(tmp_path):
    state = exhausted()
    proposal = frontier.choose_work(state)
    state["verified_low"] = str(LOW + WIDTH / 2)
    before = copy.deepcopy(state)
    with pytest.raises(ValueError, match="stale"):
        resolution.apply_refinement(tmp_path, state, proposal, controller())
    assert state == before


@pytest.mark.parametrize("saved", ["bad", {}, {"requested_width": "1/1000", "effective_width": "0"},
                                    {"requested_width": "1/1000", "effective_width": "1"}])
def test_corrupt_adaptive_state_is_not_silently_discarded(saved):
    state = exhausted()
    state["adaptive_resolution"] = saved
    with pytest.raises(ValueError, match="adaptive"):
        policy.search_resolution(state)


def stored_campaign(root):
    config = {"verified_low": "99/25", "search_high": "397/100",
              "seed_certificate": str(frontier.DEFAULT_SEED), "workers": 1,
              "budgets": [1, 2, 3, 4], "row_rounds": 2, "max_row_rounds": 2,
              "scale": 1600000, "max_scale": 25600000, "strategy_width": str(WIDTH),
              "strategies": [p["name"] for p in policy.PROFILES], "generation_trials": 1,
              "root": root}
    state = frontier.initial_state(config, frontier.DEFAULT_SEED)
    high = Fraction(99, 25) + WIDTH
    state["cycles"] = exhausted(high=high)["cycles"]
    state["mode"] = "IDLE_EXHAUSTED"
    frontier.save_state(root, state)
    return state


def test_real_state_loader_preserves_grid_history_without_changing_anchor(tmp_path):
    state = stored_campaign(tmp_path)
    anchor = (state["verified_low"], state["verified_sha256"], state["verified_certificate"])
    resolution.apply_refinement(tmp_path, state, frontier.choose_work(state), frontier)
    restored = frontier.load_state(tmp_path)
    assert policy.search_resolution(restored) == WIDTH / 10
    assert restored["resolution_history"] == state["resolution_history"]
    assert (restored["verified_low"], restored["verified_sha256"], restored["verified_certificate"]) == anchor
    assert frontier.choose_work(restored) == frontier.choose_work(state)


def test_status_preview_does_not_commit_refinement(tmp_path, capsys):
    stored_campaign(tmp_path)
    before = (tmp_path / "state.json").read_bytes()
    assert frontier.main(["--root", str(tmp_path), "--status"]) == 0
    assert "next action: refine-resolution" in capsys.readouterr().out
    assert (tmp_path / "state.json").read_bytes() == before


def test_real_controller_checkpoints_then_continues_in_same_session(tmp_path, monkeypatch, capsys):
    stored_campaign(tmp_path)
    launched = []
    def cycle(root, state):
        saved = read_json(root / "state.json")
        assert saved["adaptive_resolution"] == state["adaptive_resolution"]
        assert policy.search_resolution(saved) == WIDTH / 10
        launched.append(state["scheduled_work"]["side"])
        signal.raise_signal(signal.SIGINT)
    monkeypatch.setattr(frontier, "run_cycle", cycle)
    assert frontier.main(["--root", str(tmp_path), "--resume"]) == 0
    assert len(launched) == 1
    assert "[resolution]" in capsys.readouterr().out
    assert len(read_json(tmp_path / "state.json")["resolution_history"]) == 1


def test_stop_during_planning_cannot_commit_or_start_generation(tmp_path, monkeypatch):
    stored_campaign(tmp_path)
    original = resolution.refinement_proposal
    def interrupted(state):
        proposal = original(state)
        if proposal is not None and frontier._ACTIVE_STOP is not None:
            signal.raise_signal(signal.SIGINT)
        return proposal
    monkeypatch.setattr(resolution, "refinement_proposal", interrupted)
    monkeypatch.setattr(frontier, "run_cycle", lambda *_: pytest.fail("started work after stop"))
    assert frontier.main(["--root", str(tmp_path), "--resume"]) == 0
    assert "adaptive_resolution" not in read_json(tmp_path / "state.json")


def test_operator_cycle_limit_precedes_auto_refinement(tmp_path, monkeypatch):
    state = stored_campaign(tmp_path)
    monkeypatch.setattr(frontier, "run_cycle", lambda *_: pytest.fail("cycle limit was ignored"))
    assert frontier.main(["--root", str(tmp_path), "--resume", "--max-cycles", str(len(state["cycles"]))]) == 0
    assert "adaptive_resolution" not in read_json(tmp_path / "state.json")
