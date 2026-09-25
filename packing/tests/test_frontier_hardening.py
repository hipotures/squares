"""Controller hardening tests. Synthetic receipts are not mathematical evidence."""
from __future__ import annotations

import signal
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from devtools import frontier_rationalise as refine
from devtools import frontier_snapshot as snapshot
from devtools import frontier_verify
from devtools import run_n12_frontier as frontier
from devtools.frontier_io import atomic_json, digest, read_json
from sqpack.fractional import certificate as certificate_module
from sqpack.fractional import interval as interval_module
from sqpack.fractional.colgen import site_set_from_grids
from sqpack.fractional.interval import doubled_net, interval_worker_count, verify_by_intervals


def fresh(root: Path) -> dict:
    return frontier.initial_state(dict(
        verified_low="99/25", search_high="397/100",
        seed_certificate=str(frontier.DEFAULT_SEED), workers=1,
        budgets=[1, 2, 3, 4], row_rounds=1, max_row_rounds=2,
        scale=1600000, max_scale=25600000, strategies=["baseline", "centre"],
        strategy_width="1/100000", root=root,
    ), frontier.DEFAULT_SEED)


def test_operational_repair_error_becomes_eligible_in_next_epoch_only(tmp_path):
    state = fresh(tmp_path)
    candidate = tmp_path / "rejected.json"
    atomic_json(candidate, {"n": 12, "outer_side": "793/200", "total_mass": "119/10", "atoms": [["1", "1", "119/10"]]})
    state["cycles"] = [{"side": "793/200", "status": "UNRESOLVED", "stages": [{
        "verifier": "declaration-rejected", "candidate_unverified": str(candidate),
        "result": {"total_mass": "119/10"},
    }]}]
    attempt = {"candidate": str(candidate), "candidate_sha256": digest(candidate), "status": "ERROR", "error_epoch": 0}
    state["repair_attempts"] = [attempt]
    assert frontier.select_repair_candidate(state) is None
    state["error_epoch"] = 1
    assert frontier.select_repair_candidate(state)["candidate"] == str(candidate)
    attempt["status"] = "REJECTED"
    assert frontier.select_repair_candidate(state) is None


def test_repair_failure_records_current_epoch(tmp_path):
    state = fresh(tmp_path)
    state["error_epoch"] = 4
    attempt = {"side": "793/200", "directory": str(tmp_path)}
    frontier.repair_job_failure(state, attempt, "verification-error-70")
    assert attempt["status"] == "ERROR" and attempt["error_epoch"] == 4


def test_raw_reuse_requires_digest_and_current_search_revision(tmp_path):
    state = fresh(tmp_path)
    side = Fraction(793, 200)
    raw = tmp_path / "raw-lp.json"
    atomic_json(raw, {"unit_test_snapshot": True})
    result = {"converged": True, "objective": 11.99, "total_mass": "12001/1000",
              "settings": {"scale": 1600000}, "raw_weights": str(raw), "raw_weights_sha256": digest(raw)}
    atomic_json(tmp_path / "result.json", result)
    stage = {"status": "complete", "result": result, "directory": str(tmp_path)}
    previous = {"side": str(side), "strategy": "baseline", "search_revision": 0, "stages": [stage]}
    state["cycles"] = [previous]
    cycle = {"side": str(side), "strategy": "baseline", "search_revision": 0, "stages": []}
    assert frontier.raw_source_for(state, cycle, side, 3200000) == (stage, raw)
    cycle["search_revision"] = 1
    assert frontier.raw_source_for(state, cycle, side, 3200000) is None
    cycle["search_revision"] = 0
    atomic_json(raw, {"changed": True})
    assert frontier.raw_source_for(state, cycle, side, 3200000) is None


def test_incomplete_proof_receipt_cannot_promote_bound(tmp_path):
    state = fresh(tmp_path)
    side = Fraction(793, 200)
    candidate = tmp_path / "candidate.verified.json"
    atomic_json(candidate, {"n": 12, "outer_side": str(side), "total_mass": "119/10", "atoms": [["1", "1", "119/10"]]})
    atomic_json(tmp_path / "verification.json", {"status": "VERIFIED", "category": "full-retainable",
                "side": str(side), "verified_sha256": digest(candidate), "finished": False})
    with pytest.raises(ValueError, match="full gate receipt"):
        frontier.promote_verified(state, side, candidate, "unit-test-only")
    assert state["verified_low"] == "99/25"


def test_stop_at_scheduling_boundary_does_not_start_a_new_cycle(tmp_path, monkeypatch):
    def signal_before_scheduling():
        if frontier._ACTIVE_STOP is not None:
            frontier._ACTIVE_STOP.handle(signal.SIGINT, None)
            frontier._ACTIVE_STOP.poll()
    monkeypatch.setattr(frontier, "poll_stop", signal_before_scheduling)
    monkeypatch.setattr(frontier, "run_cycle", lambda *_args: pytest.fail("started work after boundary stop"))
    assert frontier.main(["--root", str(tmp_path), "--max-cycles", "1"]) == 0
    assert read_json(tmp_path / "state.json")["cycles"] == []


def test_finite_cycle_limit_finishes_active_repair_on_resume(tmp_path, monkeypatch):
    state = fresh(tmp_path)
    state["cycles"] = [{"side": "793/200", "status": "UNRESOLVED", "stages": []}]
    state["repair_attempts"] = [{"side": "793/200", "status": "RUNNING", "repairs": []}]
    frontier.save_state(tmp_path, state)
    called = []
    def finish_repair(_root, current):
        called.append(True)
        current["repair_attempts"][0]["status"] = "REJECTED"
        current["mode"] = "FRONTIER"
        return True
    monkeypatch.setattr(frontier, "run_repair", finish_repair)
    assert frontier.main(["--root", str(tmp_path), "--resume", "--max-cycles", "1"]) == 0
    assert called == [True]
    assert read_json(tmp_path / "state.json")["repair_attempts"][0]["status"] == "REJECTED"


def test_resume_changes_error_epoch_but_preserves_search_failures(tmp_path):
    state = fresh(tmp_path)
    state["error_epoch"] = 5
    state["cycles"] = [{"side": "793/200", "status": "SEARCH_FAILED", "stages": []}]
    frontier.save_state(tmp_path, state)
    assert frontier.main(["--root", str(tmp_path), "--resume", "--max-cycles", "1"]) == 0
    restored = read_json(tmp_path / "state.json")
    assert restored["error_epoch"] == 6
    assert restored["cycles"][0]["status"] == "SEARCH_FAILED"


def test_controller_changes_strategy_after_three_failed_cycles(tmp_path, monkeypatch):
    commands = []
    def simulated_search(args, output, _env=None):
        commands.append(args)
        side = args[args.index("--side") + 1]
        output.write_text("synthetic search fixture, not a proof\n")
        atomic_json(Path(args[args.index("--json") + 1]), {
            "settings": {"n": 12, "outer_side": side, "scale": int(args[args.index("--scale") + 1])},
            "converged": True, "objective": 12.5, "total_mass": "25/2", "seconds": .01,
            "rounds": [{"objective": 12.5, "averaged_depth": 1.0, "added": 0}],
        })
        return 0
    monkeypatch.setattr(frontier, "run_child", simulated_search)
    assert frontier.main(["--root", str(tmp_path), "--strategies", "baseline,centre", "--max-cycles", "4"]) == 0
    state = read_json(tmp_path / "state.json")
    assert [c["strategy"] for c in state["cycles"]] == ["baseline", "baseline", "baseline", "centre"]
    assert len(commands) == 4
    assert state["cycles"][-1]["side"] == state["cycles"][-2]["side"]
    assert state["verified_low"] == "99/25"


def raw_case(root):
    raw, source = root / "raw.json", root / "source.json"
    sites = site_set_from_grids(Fraction(99, 25), (3,), Fraction(1, 2))
    snapshot.save(raw, sites, np.array([.125] * len(sites.orbits)), n=12,
                  square_side=Fraction(9977, 10000), angle_limit=Fraction(207107, 500000), direction_steps=180)
    atomic_json(source, {"converged": True, "settings": {"n": 12, "outer_side": "99/25",
                "square_side": "9977/10000", "angle_limit": "207107/500000", "direction_steps": 180},
                "raw_weights_sha256": digest(raw)})
    return raw, source


def test_rerationalisation_refuses_tampered_snapshot(tmp_path):
    raw, source = raw_case(tmp_path)
    record = read_json(raw)
    record["weights_hex"][0] = (.25).hex()
    atomic_json(raw, record)
    output = tmp_path / "candidate.json"
    with pytest.raises(ValueError, match="source result digest"):
        refine.main(["--snapshot", str(raw), "--source-result", str(source), "--scale", "3200000",
                     "--freeze", str(output), "--json", str(tmp_path / "refined.json")])
    assert not output.exists()


@pytest.mark.parametrize("which", ["snapshot", "result", "shared-output"])
def test_rerationalisation_cannot_overwrite_inputs(tmp_path, which):
    raw, source = raw_case(tmp_path)
    before = {raw: raw.read_bytes(), source: source.read_bytes()}
    freeze = raw if which == "snapshot" else (source if which == "result" else tmp_path / "out.json")
    summary = freeze if which == "shared-output" else tmp_path / "summary.json"
    with pytest.raises(ValueError, match="overwrite inputs"):
        refine.main(["--snapshot", str(raw), "--source-result", str(source), "--scale", "3200000",
                     "--freeze", str(freeze), "--json", str(summary)])
    assert {path: path.read_bytes() for path in before} == before


def test_interval_parallel_route_matches_serial_and_uses_pack_jobs(monkeypatch):
    from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH, load

    certificate = load(FIRST_RUNG_PATH)
    labels = tuple(
        rotation.label for rotation in doubled_net(certificate.half_tangents)[:40]
    )
    monkeypatch.setenv("PACK_JOBS", "4")
    monkeypatch.setattr(interval_module.os, "process_cpu_count", lambda: 8)
    monkeypatch.setattr(interval_module, "_available_memory_bytes", lambda: 8 * 1024**3)
    assert interval_worker_count(len(labels)) == 4

    serial = verify_by_intervals(certificate, directions=labels, workers=1)
    parallel = verify_by_intervals(certificate, directions=labels, workers=4)
    assert parallel.directions == serial.directions
    assert parallel.conditions == serial.conditions
    assert parallel.scale == serial.scale
    assert parallel.total_mass == serial.total_mass


def test_exact_sweep_can_use_sixteen_workers_when_memory_allows(monkeypatch):
    from cases.n12_fractional_certificate.replay import load

    certificate = load()
    monkeypatch.setenv("PACK_JOBS", "16")
    monkeypatch.setattr(certificate_module.os, "process_cpu_count", lambda: 16)
    monkeypatch.setattr(
        certificate_module, "_available_memory_bytes", lambda: 32 * 1024**3
    )
    assert certificate_module._worker_count(certificate, None) == 16


def test_quick_first_repair_rejection_skips_exact_sweep(tmp_path, monkeypatch):
    source = frontier.DEFAULT_SEED
    side = Fraction("99/25")

    def quick_reject(_path, *, quick, dump_stalls=None, **_kwargs):
        assert quick is True
        if dump_stalls is not None:
            atomic_json(dump_stalls, {"stalled": 1})
        return False

    monkeypatch.setattr(frontier_verify.gate, "decide", quick_reject)
    monkeypatch.setattr(
        frontier_verify,
        "verify",
        lambda *_args, **_kwargs: pytest.fail("exact sweep ran before quick rejection"),
    )
    report = frontier_verify.decide(source, tmp_path, side, quick_first=True)
    assert report["status"] == "REJECTED"
    assert report["category"] == "interval_stall"
    assert report["finished"] is True
