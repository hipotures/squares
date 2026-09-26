"""Policy/recovery fixtures, not certificate evidence or new mathematical results.

The ULP staircase and objective values reproduce the supplied campaign log. A
VERIFIED status in these fixtures is a controller input, never a verifier test.
The real full-gate smoke tests remain separate and unchanged.
"""
from __future__ import annotations

import copy
import math
from fractions import Fraction
from types import SimpleNamespace

import pytest

from devtools import frontier_policy as policy
from devtools import run_n12_frontier as frontier
from devtools.frontier_generation_campaign import retire_superseded, run_portfolio, select_plans
from devtools.frontier_io import read_json

LOG_LOW = Fraction(43562304060209, 10995116277760)
RESOLUTION = Fraction(1, 100000)


def campaign() -> dict:
    return {
        "verified_low": str(LOG_LOW), "search_high": "793/200",
        "initial_width": "1/100", "preferred_strategy": "windows",
        "config": {"search_high": "397/100", "strategy_width": str(RESOLUTION),
                   "strategies": [p["name"] for p in policy.PROFILES],
                   "generation_trials": 3, "workers": 16, "max_scale": 25600000},
        "cycles": [], "repair_attempts": [], "active": None,
        "search_revision": 0, "error_epoch": 0,
    }


def outcome(state: dict, side: Fraction, name: str, status: str, **kwargs) -> dict:
    cycle = {"side": str(side), "strategy": name, "status": status,
             "search_revision": state.get("search_revision", 0), "stages": [], **kwargs}
    state["cycles"].append(cycle)
    return cycle


def choose(state: dict) -> dict:
    # Deliberately stale global diagnostics: the new policy must not obey them.
    return policy.plan(state, next_side=LOG_LOW + Fraction(1, 10**20),
                       soft_high=LOG_LOW + Fraction(1, 10**18), saturated=True,
                       scale_pending=False, repair_available=False)


def prove_fixture(state: dict, side: Fraction, name: str = "windows") -> None:
    outcome(state, side, name, "VERIFIED")
    state["verified_low"] = str(side)
    state["preferred_strategy"] = name


def test_live_log_windows_escapes_siblings_ulp_staircase():
    state = campaign()
    for i in range(1, 81):
        for name in ("centre", "pricing", "baseline", "dense", "fine-net"):
            outcome(state, LOG_LOW + Fraction(i, 10**17), name, "UNRESOLVED")
    prove_fixture(state, LOG_LOW)
    before = copy.deepcopy(state)
    work = choose(state)
    assert work["strategy"] == "windows"
    assert Fraction(work["side"]) == Fraction(396207, 100000)
    assert Fraction(work["side"]) - LOG_LOW >= RESOLUTION
    assert "successful-strategy advance" in work["reason"]
    assert state == before  # Status/preview calls do not migrate or erase history.


def test_only_own_revision_failure_brackets_a_successful_strategy():
    state = campaign()
    prove_fixture(state, LOG_LOW)
    outcome(state, LOG_LOW + Fraction(1, 10**15), "centre", "UNRESOLVED")
    cap = Fraction(317, 80)
    outcome(state, cap, "windows", "UNRESOLVED")
    bounds = policy.strategy_frontier(state, "windows")
    assert bounds["ceiling"] == cap
    assert bounds["observed_ceiling"]
    target = Fraction(choose(state)["side"])
    assert LOG_LOW + RESOLUTION <= target <= cap - RESOLUTION
    state["search_revision"] += 1
    assert policy.strategy_frontier(state, "windows")["observed_ceiling"] is False


def test_successful_steps_grow_and_failure_returns_to_own_bracket():
    state = campaign()
    state["config"]["strategies"] = ["windows"]
    prove_fixture(state, LOG_LOW)
    steps = []
    for _ in range(3):
        low = Fraction(state["verified_low"])
        side = Fraction(choose(state)["side"])
        steps.append(side - low)
        prove_fixture(state, side)
    assert steps[0] >= RESOLUTION
    assert steps[1] > steps[0] and steps[2] > steps[1]
    high = Fraction(choose(state)["side"])
    outcome(state, high, "windows", "SEARCH_FAILED")
    low = Fraction(state["verified_low"])
    next_target = Fraction(choose(state)["side"])
    assert low + RESOLUTION <= next_target <= high - RESOLUTION
    assert state["verified_low"] == str(low)  # Failure cannot alter a proved bound.


def test_global_failed_endpoint_does_not_limit_another_instrument():
    state = campaign()
    state["search_high"] = str(LOG_LOW + Fraction(1, 10**12))
    prove_fixture(state, LOG_LOW)
    target = Fraction(choose(state)["side"])
    assert target > Fraction(state["search_high"])
    assert target < Fraction(state["config"]["search_high"])


def test_own_failed_configured_endpoint_is_still_a_bracket():
    state = campaign()
    outcome(state, Fraction(397, 100), "windows", "SEARCH_FAILED")
    prove_fixture(state, LOG_LOW)
    bounds = policy.strategy_frontier(state, "windows")
    assert bounds["observed_ceiling"] is True
    assert Fraction(choose(state)["side"]) < bounds["ceiling"]


def test_all_narrow_instrument_frontiers_idle_without_micro_steps():
    state = campaign()
    for name in state["config"]["strategies"]:
        outcome(state, LOG_LOW + RESOLUTION / 2, name, "UNRESOLVED")
    work = choose(state)
    assert work["kind"] == "idle"
    assert "not a mathematical" in work["reason"]
    assert state["search_high"] == "793/200"


def test_actual_best_certificate_producer_has_priority_over_last_sibling():
    state = campaign()
    state["verified_certificate"] = "windows-proof.json"
    outcome(state, LOG_LOW, "windows", "VERIFIED", verified_candidate="windows-proof.json")
    outcome(state, LOG_LOW, "dense", "VERIFIED", verified_candidate="dense-proof.json")
    state["preferred_strategy"] = "dense"
    assert choose(state)["strategy"] == "windows"


def test_disabled_strategy_and_unknown_legacy_unresolved_do_not_leak():
    state = campaign()
    prove_fixture(state, LOG_LOW)
    state["config"]["strategies"] = ["centre"]
    state["unresolved"] = [str(LOG_LOW + Fraction(1, 10**18))]
    work = choose(state)
    assert work["strategy"] == "centre"
    assert Fraction(work["side"]) - LOG_LOW >= RESOLUTION


def test_operational_error_is_not_an_instrument_ceiling_and_resume_can_retry():
    state = campaign()
    state["config"]["strategies"] = ["windows"]
    prove_fixture(state, LOG_LOW)
    work = choose(state)
    outcome(state, Fraction(work["side"]), "windows", "ERROR", error_epoch=0)
    assert policy.strategy_frontier(state, "windows")["observed_ceiling"] is False
    assert choose(state)["kind"] == "idle"
    state["error_epoch"] += 1
    assert choose(state)["side"] == work["side"]


def test_active_cycle_and_repair_keep_precedence():
    state = campaign()
    state["active"] = 0
    assert choose(state)["kind"] == "resume-cycle"
    state["active"] = None
    state["repair_attempts"] = [{"status": "INTERRUPTED"}]
    assert choose(state)["kind"] == "repair"


def test_precision_retry_remains_allowed_below_geometric_step():
    state = campaign()
    side = LOG_LOW + Fraction(1, 10**18)
    cycle = outcome(state, side, "windows", "UNRESOLVED")
    cycle["stages"] = [{"result": {"converged": True, "objective": 11.9994,
        "total_mass": "12001/1000", "settings": {"scale": 1600000}}}]
    work = choose(state)
    assert Fraction(work["side"]) == side
    assert "rationalisation" in work["reason"]
    assert select_plans(state, work) == [work]
    cycle["stages"][0]["result"]["settings"]["scale"] = 25600000
    assert choose(state).get("side") != str(side)


def test_same_scale_latest_outcome_not_an_older_rounding_failure():
    state = campaign()
    side = LOG_LOW + Fraction(1, 10**18)
    cycle = outcome(state, side, "windows", "UNRESOLVED")
    cycle["stages"] = [
        {"scale": 1600000, "result": {"converged": True, "objective": 11.9, "total_mass": "121/10"}},
        {"scale": 1600000, "result": {"converged": True, "objective": 11.8, "total_mass": "119/10"}},
    ]
    assert policy.precision_proposal(state) is None


def test_generation_siblings_get_their_own_targets_not_the_winners_ulp():
    state = campaign()
    state["config"]["strategies"] = ["windows", "centre", "pricing"]
    prove_fixture(state, LOG_LOW)
    outcome(state, Fraction(317, 80), "centre", "UNRESOLVED")
    outcome(state, LOG_LOW + RESOLUTION / 2, "pricing", "UNRESOLVED")
    work = choose(state)
    plans = select_plans(state, work)
    assert [p["strategy"] for p in plans] == ["windows", "centre"]
    assert len({p["side"] for p in plans}) == 2
    assert all(Fraction(p["side"]) >= LOG_LOW + RESOLUTION for p in plans)


def test_generation_cycle_budget_and_resolution_floor():
    state = campaign()
    state["config"]["max_cycles"] = 2
    prove_fixture(state, LOG_LOW)
    work = choose(state)
    assert select_plans(state, work) == [work]
    state["config"]["strategy_width"] = "1/1000000000000000000000000000000"
    assert policy.search_resolution(state) >= 32 * Fraction.from_float(math.ulp(float(LOG_LOW)))


@pytest.mark.parametrize("status", ["VERIFIED", "REJECTED", "ERROR"])
def test_finished_material_repair_cannot_unlock_only_remaining_micro_repair(tmp_path, status):
    state = campaign()
    path = tmp_path / "candidate.json"
    path.write_text("fixture")
    c = outcome(state, LOG_LOW + RESOLUTION * 10, "windows", "UNRESOLVED")
    c["stages"] = [{"verifier": "quick-rejected", "candidate_unverified": str(path),
                    "result": {"total_mass": "119/10"}}]
    assert policy._material_repair(state)
    state["repair_attempts"] = [{"status": status, "candidate": str(path), "error_epoch": 0}]
    assert not policy._material_repair(state)


def test_superseded_queued_stages_are_retired_without_execution(tmp_path):
    state = campaign()
    directory = tmp_path / "normal-02"
    directory.mkdir()
    candidate = directory / "candidate.unverified.json"
    candidate.write_text("preserved fixture")
    stage = {"status": "queued", "directory": str(directory), "name": "normal"}
    cycle = outcome(state, LOG_LOW, "pricing", "RUNNING", stages=[stage])
    state["active_generation"] = [0]
    state["generation_wave"] = None
    calls = []
    stub = SimpleNamespace(stamp=lambda: "fixture", display=str,
                           save_state=lambda *_: None, emit=lambda *args: calls.append(args))
    retire_superseded(tmp_path, state, stub)
    assert state["active_generation"] == []
    assert cycle["status"] == "UNRESOLVED" and cycle["superseded_by"] == str(LOG_LOW)
    assert stage["status"] == "superseded"
    assert candidate.read_text() == "preserved fixture"
    assert read_json(directory / "metadata.json")["status"] == "superseded"
    retire_superseded(tmp_path, state, stub)
    assert len(calls) == 1


def test_legacy_state_reconstructs_same_proposal_after_resume(tmp_path):
    # Use the existing real retained anchor for the state-loading contract.
    config = {"verified_low": "99/25", "search_high": "397/100",
              "workers": 1, "budgets": [1, 2, 3, 4], "row_rounds": 60,
              "scale": 1600000, "max_scale": 25600000,
              "seed_certificate": str(frontier.DEFAULT_SEED), "root": tmp_path}
    state = frontier.initial_state(config, frontier.DEFAULT_SEED)
    state["preferred_strategy"] = "windows"
    outcome(state, Fraction(99, 25), "windows", "VERIFIED")
    for name in ("baseline", "centre", "pricing"):
        outcome(state, Fraction(99, 25) + Fraction(1, 10**15), name, "UNRESOLVED")
    frontier.save_state(tmp_path, state)
    before = choose(state)
    restored = frontier.load_state(tmp_path)
    assert choose(restored) == before
    assert restored["cycles"] == state["cycles"]
    assert restored["verified_sha256"] == state["verified_sha256"]
    assert restored["policy_version"] == policy.POLICY_VERSION


def test_success_failure_simulation_never_creeps_by_ulps_or_claims_a_proof():
    state = campaign()
    state["config"]["strategies"] = ["windows"]
    prove_fixture(state, LOG_LOW)
    oracle_cutoff = Fraction(39624, 10000)  # Synthetic controller oracle only.
    for _ in range(30):
        previous = Fraction(state["verified_low"])
        work = choose(state)
        if work["kind"] == "idle":
            break
        side = Fraction(work["side"])
        assert side >= previous + RESOLUTION
        assert "proof" not in work
        if side <= oracle_cutoff:
            prove_fixture(state, side)
        else:
            outcome(state, side, "windows", "UNRESOLVED")
    else:
        pytest.fail("bounded strategy bracket did not exhaust")
    assert oracle_cutoff - Fraction(state["verified_low"]) < 2 * RESOLUTION



def test_drained_wave_sibling_proof_skips_prepared_and_uninterpreted_redundant_stages(tmp_path):
    state = campaign()
    side = LOG_LOW + RESOLUTION * 10
    states = []
    for index, name in enumerate(("centre", "windows", "pricing")):
        directory = tmp_path / f"cycle-{index}"
        directory.mkdir()
        stage = {"status": "queued", "name": "normal", "directory": str(directory),
                 "work_kind": "generation"}
        states.append(outcome(state, side, name, "RUNNING", stages=[stage]))
    state["active_generation"] = [0, 1, 2]
    state["generation_wave"] = None
    called = []

    def finish_stage(_root, current, *, defer_generation):
        assert defer_generation
        index = current["active"]
        called.append(index)
        if index == 0:
            return states[0]["stages"][0]
        assert index == 1
        # Explicit controller-only full-gate outcome, not a real certificate.
        current["verified_low"] = str(side)
        states[1]["status"] = "VERIFIED"
        return None

    stub = SimpleNamespace(stamp=lambda: "fixture", display=str,
                           save_state=lambda *_: None, write_views=lambda *_: None,
                           emit=lambda *_: None, run_cycle=finish_stage)
    run_portfolio(tmp_path, state, frontier=stub)
    assert called == [0, 1]
    assert state["active_generation"] == []
    assert states[0]["stages"][0]["status"] == "superseded"
    assert states[2]["superseded_by"] == str(side)
    assert state["generation_wave"] is None


def test_unadopted_wave_is_not_retired_even_when_target_is_already_proved(tmp_path):
    state = campaign()
    outcome(state, LOG_LOW, "pricing", "RUNNING")
    state["active_generation"] = [0]
    state["generation_wave"] = {"directory": "unadopted"}
    retire_superseded(tmp_path, state, SimpleNamespace())
    assert state["active_generation"] == [0]
    assert state["cycles"][0]["status"] == "RUNNING"


@pytest.mark.parametrize("offset", range(1, 20))
def test_grid_proposals_stay_inside_own_bracket_and_keep_meaningful_gaps(offset):
    state = campaign()
    state["verified_low"] = str(LOG_LOW + RESOLUTION * offset / 19)
    low = Fraction(state["verified_low"])
    high = low + RESOLUTION * (2 + Fraction(offset, 2))
    prove_fixture(state, low)
    outcome(state, high, "windows", "UNRESOLVED")
    work = policy.strategy_proposal(state, "windows")
    if work is not None:
        target = Fraction(work["side"])
        assert low + RESOLUTION <= target <= high - RESOLUTION
        assert (target / RESOLUTION).denominator == 1



def test_status_labels_legacy_globals_and_shows_strategy_local_frontiers():
    state = campaign()
    state["unresolved"] = []
    state["config"]["strategies"] = ["windows", "centre"]
    prove_fixture(state, LOG_LOW)
    outcome(state, LOG_LOW + 4 * RESOLUTION, "centre", "UNRESOLVED")

    text = frontier.frontier_status(state)

    assert "[frontier] verified=" in text
    assert "legacy-soft-high=" in text
    assert "legacy-search-high=" in text
    assert "[strategy-frontiers]" in text
    assert "windows:next=" in text
    assert "windows:" in text and "own-high=" in text
    assert "centre:" in text and "(observed)" in text
    assert "soft-high=" not in text.replace("legacy-soft-high=", "")
