"""Autonomy regression tests: proof boundaries, policy, real jobs, and recovery.

Receipt doubles in controller-only tests are not certificate evidence. The real
verifier smoke test separately exercises the unchanged two-route exact gate.
"""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from devtools import frontier_policy as policy
from devtools import frontier_runtime as jobs
from devtools import frontier_snapshot as snapshot
from devtools import frontier_verify as verification
from devtools import run_n12_frontier as frontier
from devtools.frontier_io import atomic_json, digest, read_json
from sqpack.fractional.colgen import site_set_from_grids

PACKING = Path(__file__).resolve().parents[1]


def fresh(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    config = dict(verified_low="99/25", search_high="397/100",
                  seed_certificate=str(frontier.DEFAULT_SEED), workers=1,
                  budgets=[1, 2, 3, 4], row_rounds=1, max_row_rounds=2,
                  scale=1600000, max_scale=25600000,
                  strategies=[p["name"] for p in policy.PROFILES],
                  strategy_width="1/100000", root=root)
    state = frontier.initial_state(config, frontier.DEFAULT_SEED)
    state["verified_sha256"] = digest(frontier.DEFAULT_SEED)
    return state


def proof_double(path: Path, side: Fraction, mass: str = "119/10") -> Path:
    atomic_json(path, {"n": 12, "outer_side": str(side), "total_mass": mass,
                       "atoms": [["1", "1", mass]]})
    atomic_json(path.parent / "verification.json", {
        "status": "VERIFIED", "category": "full-retainable", "side": str(side),
        "verified_candidate": str(path), "verified_sha256": digest(path),
        "finished": True,
    })
    return path


def rejected_cycle(root: Path, state: dict, side: Fraction) -> Path:
    path = root / f"rejected-{side.numerator}.json"
    atomic_json(path, {"n": 12, "outer_side": str(side), "total_mass": "119/10",
                       "atoms": [["1", "1", "119/10"]]})
    state["cycles"].append({
        "side": str(side), "status": "UNRESOLVED", "strategy": "baseline", "stages": [{
            "name": "screen", "budget": 1, "status": "complete", "seed_label": "unit-double",
            "candidate_unverified": str(path), "verifier": "declaration-rejected",
            "result": {"total_mass": "119/10", "objective": 11.9, "rounds": []},
        }],
    })
    return path


@pytest.mark.parametrize("side", [Fraction(793, 200), Fraction(1983, 500)])
def test_repair_crossing_old_high_keeps_resumable_state(tmp_path, monkeypatch, side):
    state = fresh(tmp_path)
    state["search_high"] = "793/200"
    rejected_cycle(tmp_path, state, side)

    def accepted(directory, _candidate, expected_side):
        proof = proof_double(directory / "candidate.verified.json", expected_side)
        return "full-retainable", str(proof)

    monkeypatch.setattr(frontier, "verify_candidate", accepted)
    assert frontier.run_repair(tmp_path, state)
    assert Fraction(state["verified_low"]) == side
    assert Fraction(state["search_high"]) > side
    assert state["superseded_search_highs"][-1]["side"] == "793/200"
    assert frontier.load_state(tmp_path)["verified_low"] == str(side)
    assert frontier.choose_work(state)["kind"] != "idle"


def test_same_side_scale_work_precedes_numeric_saturation(tmp_path):
    state = fresh(tmp_path)
    low = Fraction("871246081204179/219902325555200")
    high = Fraction("6969968649633433/1759218604441600")
    state.update(verified_low=str(low), search_high=str(high), unresolved=[str(high)])
    state["cycles"] = [{"side": str(high), "status": "UNRESOLVED", "stages": [{
        "status": "complete", "result": {"converged": True, "objective": 11.9994,
        "total_mass": "12001/1000", "settings": {"scale": 1600000}}}]}]
    assert frontier.numeric_search_saturated(state)
    work = frontier.choose_work(state)
    assert work["kind"] == "search" and Fraction(work["side"]) == high
    assert "rationalisation" in work["reason"]


def test_strategy_switches_after_plateau_and_no_duplicate_float_work(tmp_path):
    state = fresh(tmp_path)
    for side in ("793/200", "317/80", "3169/800"):
        state["cycles"].append({"side": side, "status": "UNRESOLVED", "strategy": "baseline", "stages": []})
    state["unresolved"] = ["3169/800"]
    work = frontier.choose_work(state)
    assert work["strategy"] == "centre"
    side = Fraction(work["side"])
    # Every instrument at this binary64 coordinate is marked tried.
    for item in policy.PROFILES:
        state["cycles"].append({"side": str(side), "strategy": item["name"], "status": "UNRESOLVED"})
    assert all(policy.tried(state, side + Fraction(1, 10**30), p["name"]) for p in policy.PROFILES)


def test_profile_containment_is_valid():
    for item in policy.PROFILES:
        opts = item["options"]
        shrink = Fraction(opts.get("shrink", "9977/10000"))
        half_gap = Fraction(207107, 500000) / int(opts.get("direction-steps", "180"))
        assert shrink * (1 + half_gap) < 1


def test_no_remaining_portfolio_returns_honest_idle(tmp_path):
    state = fresh(tmp_path)
    high = Fraction(397, 100)
    for item in policy.PROFILES:
        state["cycles"].append({"side": str(high), "strategy": item["name"], "status": "UNRESOLVED", "stages": []})
    work = policy.plan(state, next_side=high, soft_high=high, scale_pending=False,
                       repair_available=False, saturated=True)
    assert work["kind"] == "idle"
    assert "not a mathematical" in work["reason"]


def test_resume_boost_success_does_not_repeat_gate(tmp_path, monkeypatch):
    state = fresh(tmp_path)
    side = Fraction(1983, 500)
    source = rejected_cycle(tmp_path, state, side)
    directory = tmp_path / "repair/attempt-0001"
    proof = proof_double(directory / "boost/candidate.verified.json", side)
    state["repair_attempts"] = [{
        "status": "RUNNING", "side": str(side), "candidate": str(source),
        "candidate_sha256": digest(source), "directory": str(directory),
        "repairs": [{"status": "VERIFIED", "verified_candidate": str(proof)}],
    }]
    monkeypatch.setattr(frontier, "verify_candidate", lambda *a: pytest.fail("completed boost rerun"))
    assert frontier.run_repair(tmp_path, state)
    assert state["repair_attempts"][0]["status"] == "VERIFIED"
    assert Fraction(state["verified_low"]) == side


def test_declaration_rejection_is_diagnosed_and_repaired(tmp_path, monkeypatch):
    state = fresh(tmp_path)
    side = Fraction(793, 200)
    rejected_cycle(tmp_path, state, side)
    calls = []

    def gate(directory, _candidate, expected_side):
        calls.append(directory)
        if len(calls) == 1:
            atomic_json(directory / "verification.json", {
                "status": "REJECTED", "category": "coverage_deficit",
                "minimum_cell_mass": "9999/10000", "uniform_repair_possible": True,
            })
            return "declaration-rejected", None
        proof = proof_double(directory / "candidate.verified.json", expected_side)
        return "full-retainable", str(proof)

    monkeypatch.setattr(frontier, "verify_candidate", gate)
    assert frontier.select_repair_candidate(state) is not None
    assert frontier.run_repair(tmp_path, state)
    assert len(calls) == 2
    assert state["repair_attempts"][0]["status"] == "VERIFIED"
    assert Fraction(state["repair_attempts"][0]["repairs"][0]["total_mass"]) < 12


def test_impossible_uniform_repair_abandoned_without_six_blind_boosts(tmp_path, monkeypatch):
    state = fresh(tmp_path)
    rejected_cycle(tmp_path, state, Fraction(793, 200))

    def reject(directory, *_):
        atomic_json(directory / "verification.json", {
            "category": "coverage_deficit", "minimum_cell_mass": "1/2",
            "uniform_repair_possible": False,
        })
        return "declaration-rejected", None

    monkeypatch.setattr(frontier, "verify_candidate", reject)
    assert frontier.run_repair(tmp_path, state)
    assert not state["repair_attempts"][0]["repairs"]
    assert state["repair_attempts"][0]["status"] == "REJECTED"
    assert frontier.select_repair_candidate(state) is None


def test_nested_legacy_repair_child_prevents_duplicate(tmp_path, monkeypatch):
    state = fresh(tmp_path)
    source = rejected_cycle(tmp_path, state, Fraction(793, 200))
    directory = tmp_path / "repair/old"
    nested = directory / "boost/diagnosis"
    nested.mkdir(parents=True)
    atomic_json(nested / "stdout.log.child.json", jobs.identity(os.getpid()))
    state["repair_attempts"] = [{"status": "INTERRUPTED", "side": "793/200",
        "candidate": str(source), "directory": str(directory), "repairs": []}]
    monkeypatch.setattr(frontier, "verify_candidate", lambda *a: pytest.fail("duplicate gate"))
    with pytest.raises(jobs.LiveJob):
        frontier.run_repair(tmp_path, state)
    assert len(state["repair_attempts"]) == 1


def test_state_backup_recovers_truncated_current_and_preserves_bytes(tmp_path):
    state = fresh(tmp_path)
    frontier.save_state(tmp_path, state)
    state["mode"] = "REPAIR"
    frontier.save_state(tmp_path, state)
    (tmp_path / "state.json").write_text('{"schema":')
    restored = frontier.load_state(tmp_path)
    assert restored["verified_low"] == "99/25"
    assert list(tmp_path.glob("state.damaged-*.json"))[0].read_text() == '{"schema":'


def test_schema2_history_is_backed_up_and_running_repair_preserved(tmp_path):
    state = fresh(tmp_path)
    state["schema"] = 2
    state["repair_attempts"] = [{"status": "RUNNING", "directory": "example"}]
    frontier.save_state(tmp_path, state)
    before = (tmp_path / "state.json").read_bytes()
    restored = frontier.load_state(tmp_path)
    assert restored["schema"] == 3
    assert restored["repair_attempts"][0]["status"] == "RUNNING"
    assert list(tmp_path.glob("state.schema-2-*.json"))[0].read_bytes() == before


def test_verified_artifact_change_refused(tmp_path):
    state = fresh(tmp_path)
    proof = proof_double(tmp_path / "proof/candidate.verified.json", Fraction(793, 200))
    frontier.promote_verified(state, Fraction(793, 200), proof, "unit-test")
    frontier.save_state(tmp_path, state)
    proof.write_text(proof.read_text() + " ")
    with pytest.raises(ValueError, match="changed after acceptance"):
        frontier.load_state(tmp_path)


def test_findings_have_banner_digest_and_no_false_opportunity_proof(tmp_path, capsys):
    state = fresh(tmp_path)
    proof = proof_double(tmp_path / "proof/candidate.verified.json", Fraction(793, 200))
    frontier.promote_verified(state, Fraction(793, 200), proof, "unit-test")
    frontier.publish_findings(tmp_path, state)
    output = capsys.readouterr().out
    assert "VERIFIED LOWER BOUND IMPROVEMENT" in output
    assert digest(proof) in output and "=" * 72 in output
    frontier.publish_findings(tmp_path, state)
    assert capsys.readouterr().out == ""
    assert len(read_json(tmp_path / "findings.json")["verified_improvements"]) == 1


def test_operational_failure_does_not_shrink_bounds(tmp_path):
    state = fresh(tmp_path)
    stage = {"directory": str(tmp_path / "stage"), "name": "screen", "budget": 1, "seed_label": "test"}
    cycle = {"side": "793/200", "status": "RUNNING", "stages": [stage]}
    state["cycles"] = [cycle]
    state["active"] = 0
    frontier.record_job_failure(tmp_path, state, cycle, stage, jobs.TIMEOUT)
    assert state["search_high"] == "397/100"
    assert cycle["status"] == "ERROR"
    assert state["active"] is None


def fast_limits(**overrides):
    return dict(jobs.DEFAULTS, poll_seconds=0.025, heartbeat_seconds=0.05,
                terminate_seconds=0.05, backoff_seconds=0.01, min_free_mib=0,
                **overrides)


def wait_file(path: Path, seconds=10):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if path.exists():
            return
        time.sleep(0.02)
    pytest.fail(f"child did not produce {path}")


def test_real_job_reuses_receipt_and_recovers_receipt_write_window(tmp_path):
    marker = tmp_path / "marker"
    script = f"from pathlib import Path; p=Path({str(marker)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x')"
    args = [sys.executable, "-c", script]
    log = tmp_path / "stdout.log"
    assert jobs.run(args, log, cwd=PACKING, limits=fast_limits(retries=0)) == 0
    assert jobs.run(args, log, cwd=PACKING, limits=fast_limits(retries=0)) == 0
    assert marker.read_text() == "x"
    log.with_name("stdout.log.receipt.json").unlink()
    assert jobs.run(args, log, cwd=PACKING, limits=fast_limits(retries=0)) == 0
    assert marker.read_text() == "x"


def test_real_parent_kill_and_resume_attaches_without_duplicate(tmp_path):
    marker = tmp_path / "marker"
    args = [sys.executable, "-c", f"import time; from pathlib import Path; p=Path({str(marker)!r}); p.write_text('start'); time.sleep(1.5); p.write_text(p.read_text()+'end')"]
    log = tmp_path / "stdout.log"
    limits = fast_limits(retries=0)
    code = f"from pathlib import Path; from devtools.frontier_runtime import run; raise SystemExit(run({args!r}, Path({str(log)!r}), cwd=Path({str(PACKING)!r}), limits={limits!r}))"
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=PACKING)
    try:
        wait_file(marker)
        controller.kill()
        controller.wait(timeout=10)
        assert jobs.run(args, log, cwd=PACKING, limits=limits) == 0
        assert marker.read_text() == "startend"
        receipt = read_json(log.with_name("stdout.log.receipt.json"))
        assert len([a for a in receipt["attempts"] if a["kind"] == "execution"]) == 1
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.wait()


def test_real_ctrl_c_does_not_interrupt_child(tmp_path):
    marker = tmp_path / "started"
    done = tmp_path / "done"
    args = [sys.executable, "-c", f"import time; from pathlib import Path; Path({str(marker)!r}).touch(); time.sleep(.5); Path({str(done)!r}).touch()"]
    log = tmp_path / "stdout.log"
    code = ("import signal; from pathlib import Path; from devtools.frontier_runtime import run; "
            "signal.signal(signal.SIGINT, lambda *a: print('stop requested', flush=True)); "
            f"raise SystemExit(run({args!r}, Path({str(log)!r}), cwd=Path({str(PACKING)!r}), limits={fast_limits(retries=0)!r}))")
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=PACKING, stdout=subprocess.PIPE, text=True)
    wait_file(marker)
    controller.send_signal(signal.SIGINT)
    output, _ = controller.communicate(timeout=15)
    assert controller.returncode == 0 and done.exists()
    assert "stop requested" in output


def test_real_watchdog_kills_owned_group_and_bounds_retries(tmp_path):
    child_pid = tmp_path / "descendant"
    script = ("import subprocess,sys,time; from pathlib import Path; "
              "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(60)']); "
              f"Path({str(child_pid)!r}).write_text(str(p.pid)); time.sleep(60)")
    log = tmp_path / "stdout.log"
    code = jobs.run([sys.executable, "-c", script], log, cwd=PACKING,
                    limits=fast_limits(verify_seconds=0.25, retries=1))
    assert code == jobs.TIMEOUT
    receipt = read_json(log.with_name("stdout.log.receipt.json"))
    assert 1 <= len([a for a in receipt["attempts"] if a["kind"] == "execution"]) <= 2
    info = jobs.process_info(int(child_pid.read_text()))
    assert info is None or info["state"] == "Z"


def test_permanent_environment_error_does_not_retry_forever(tmp_path):
    log = tmp_path / "stdout.log"
    code = jobs.run([sys.executable, "-c", "import nonexistent_frontier_test_dependency"], log,
                    cwd=PACKING, limits=fast_limits(retries=2))
    assert code == jobs.PERMANENT_ERROR
    assert len(read_json(log.with_name("stdout.log.receipt.json"))["attempts"]) == 1


def test_foreign_boot_identity_never_matches_current_process():
    record = jobs.identity(os.getpid())
    assert jobs.is_alive(record)
    record["boot_id"] = "not-this-boot"
    assert not jobs.is_alive(record)
    assert jobs.owned_members(os.getpgrp(), "not-our-token") == []


def test_disk_budget_refuses_job_without_launch(tmp_path):
    marker = tmp_path / "never-created"
    log = tmp_path / "stdout.log"
    args = [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"]
    limits = fast_limits(retries=0)
    limits["min_free_mib"] = 10**15
    assert jobs.run(args, log, cwd=PACKING, limits=limits) == jobs.RESOURCE_LIMIT
    assert not marker.exists()


def test_real_small_full_gate_and_rejection_diagnosis(tmp_path):
    source = PACKING / "cases/n12_fractional_certificate/certificate-19-5.json"
    report = verification.decide(source, tmp_path / "valid", Fraction(19, 5))
    assert report["status"] == "VERIFIED"
    assert report["verified_sha256"] == digest(Path(report["verified_candidate"]))
    # Lower all weights; format and Conditions 1-4 remain valid, coverage does not.
    record = read_json(source)
    record["atoms"] = [[x, y, str(Fraction(w) / 2)] for x, y, w in record["atoms"]]
    record["total_mass"] = str(Fraction(record["total_mass"]) / 2)
    record["least_cell_mass"] = None
    bad = tmp_path / "under-covered.json"
    atomic_json(bad, record)
    rejection = verification.decide(bad, tmp_path / "invalid", Fraction(19, 5))
    assert rejection["category"] == "coverage_deficit"
    assert rejection["uniform_repair_possible"] is True
    assert not list((tmp_path / "invalid").glob("candidate.verified*.json"))


def test_real_snapshot_and_rerationalisation_without_lp(tmp_path, monkeypatch):
    from devtools import frontier_rationalise as refine
    from sqpack.fractional import colgen

    raw = tmp_path / "raw.json"
    candidate = tmp_path / "candidate.json"
    result = tmp_path / "result.json"
    command = [sys.executable, "-m", "devtools.run_fractional_colgen", "--n", "1", "--side", "2",
               "--direction-steps", "8", "--grid-counts", "2,3", "--column-rounds", "1",
               "--max-rounds", "10", "--scale", "1000", "--raw-weights", str(raw),
               "--freeze", str(candidate), "--json", str(result)]
    subprocess.run(command, cwd=PACKING, check=True, capture_output=True, text=True, timeout=30)
    assert raw.exists()
    monkeypatch.setattr(colgen, "solve_rows", lambda *a, **k: pytest.fail("LP rerun during rationalisation"))
    output = tmp_path / "refined.json"
    assert refine.main(["--snapshot", str(raw), "--source-result", str(result), "--scale", "8000",
                        "--freeze", str(tmp_path / "refined-candidate.json"), "--json", str(output)]) == 0
    refined = read_json(output)
    assert refined["work_kind"] == "rerationalisation"
    assert refined["column_rounds_executed"] == refined["lp_rounds_executed"] == 0
    assert Fraction(refined["total_mass"]) <= Fraction(read_json(result)["total_mass"])


def test_real_transient_failure_retries_then_succeeds(tmp_path):
    marker = tmp_path / "attempt-count"
    script = (f"from pathlib import Path; import sys; p=Path({str(marker)!r}); "
              "n=int(p.read_text())+1 if p.exists() else 1; p.write_text(str(n)); sys.exit(5 if n==1 else 0)")
    log = tmp_path / "stdout.log"
    assert jobs.run([sys.executable, "-c", script], log, cwd=PACKING,
                    limits=fast_limits(retries=2, verify_seconds=10)) == 0
    assert marker.read_text() == "2"
    assert (tmp_path / "stdout.log.attempt-01/stdout.log").exists()
    receipt = read_json(tmp_path / "stdout.log.receipt.json")
    assert [a["returncode"] for a in receipt["attempts"]] == [5, 0]


def test_real_no_progress_watchdog_with_silent_search_standin(tmp_path):
    # The last argv value deliberately gives this isolated child the search job
    # classification; no solver or certificate is mocked as a successful result.
    args = [sys.executable, "-c", "import time; time.sleep(60)", "devtools.run_fractional_colgen"]
    log = tmp_path / "stdout.log"
    began = time.monotonic()
    code = jobs.run(args, log, cwd=PACKING,
                    limits=fast_limits(retries=0, stage_seconds=20, no_progress_seconds=.2))
    assert code == jobs.TIMEOUT
    assert time.monotonic() - began < 10
    assert read_json(tmp_path / "stdout.log.receipt.json")["reason"] == "no solver log progress"


def test_real_memory_guard_reduces_worker_budget_on_retry(tmp_path):
    args = [sys.executable, "-c", "import time; memory=bytearray(8*1024*1024); time.sleep(60)"]
    log = tmp_path / "stdout.log"
    limits = fast_limits(retries=1, verify_seconds=10, max_rss_mib=1)
    assert jobs.run(args, log, cwd=PACKING, env={**os.environ, "PACK_JOBS": "4"}, limits=limits) == jobs.RESOURCE_LIMIT
    attempts = read_json(tmp_path / "stdout.log.receipt.json")["attempts"]
    assert [a["workers"] for a in attempts] == ["4", "2"]


def test_explicit_environment_recovery_allows_error_only_retrial(tmp_path):
    state = fresh(tmp_path)
    side = Fraction(793, 200)
    state["cycles"] = [{"side": str(side), "strategy": "baseline", "status": "ERROR", "error_epoch": 0}]
    assert policy.tried(state, side, "baseline")
    state["error_epoch"] = 1
    assert not policy.tried(state, side, "baseline")
    state["cycles"][0]["status"] = "SEARCH_FAILED"
    assert policy.tried(state, side, "baseline")


def test_changed_budgets_allow_new_instrument_revision(tmp_path):
    state = fresh(tmp_path)
    side = Fraction(793, 200)
    state["cycles"] = [{"side": str(side), "strategy": "baseline", "status": "UNRESOLVED", "search_revision": 0}]
    assert policy.tried(state, side, "baseline")
    state["search_revision"] = 1
    assert not policy.tried(state, side, "baseline")


def test_raw_weights_round_trip_and_nested_rounding(tmp_path):
    sites = site_set_from_grids(Fraction(99, 25), (3,), Fraction(1, 2))
    weights = np.array([float.fromhex("0x1.0000000000001p-4")] * len(sites.orbits))
    path = tmp_path / "raw.json"
    snapshot.save(path, sites, weights, n=12, square_side=Fraction(9977, 10000),
                  angle_limit=Fraction(207107, 500000), direction_steps=180)
    _record, loaded_sites, loaded_weights = snapshot.load(path)
    assert loaded_sites.orbits == sites.orbits
    assert [x.hex() for x in loaded_weights] == [x.hex() for x in weights]
    masses = [snapshot.rationalise(path, scale).total_mass for scale in (200000, 400000, 800000, 1600000)]
    assert masses == sorted(masses, reverse=True)
    record = read_json(path)
    record["weights_hex"][0] = "nan"
    atomic_json(path, record)
    with pytest.raises(ValueError, match="raw weight"):
        snapshot.load(path)
