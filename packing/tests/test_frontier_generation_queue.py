"""Generation scheduling controls; numerical searches are not proof artifacts."""
from __future__ import annotations

import sys
import time
from fractions import Fraction
from pathlib import Path

import pytest

from devtools import frontier_generation_queue as queue
from devtools.frontier_generation_campaign import select_plans
from devtools.frontier_io import atomic_json, read_json
from devtools.frontier_phase import PhaseJournal, timestamped
from devtools.run_fractional_colgen import main as generate
from devtools import run_n12_frontier as frontier


def job(root: Path, name: str, mapping: str = "scale") -> dict:
    directory = root / name
    directory.mkdir(parents=True)
    command = [sys.executable, "-m", "devtools.run_fractional_colgen",
               "--n", "12", "--side", "99/25", "--grid-counts", "3,5",
               "--direction-steps", "12", "--column-rounds", "2", "--max-rounds", "4",
               "--support-cap", "4", "--seed-map", mapping,
               "--json", str(directory / "result.json"),
               "--freeze", str(directory / "candidate.unverified.json"),
               "--raw-weights", str(directory / "raw-lp.json"),
               "--log", str(directory / "column.log"),
               "--row-log", str(directory / "rows.log"),
               "--phase-log", str(directory / "phase.log")]
    return {"id": name, "command": command, "output": str(directory / "stdout.log")}


def mathematical_result(path: Path) -> dict:
    value = read_json(path)
    keys = ("objective", "least_covered", "converged", "total_mass", "atoms", "stopped")
    return {**{k: value.get(k) for k in keys},
            "rounds": [{k: v for k, v in row.items() if k != "seconds"} for row in value["rounds"]]}


def test_every_console_line_including_findings_has_epoch():
    assert timestamped("[stage] done\nVERIFIED\n", 1700000000).splitlines() == [
        "[1700000000] [stage] done", "[1700000000] VERIFIED"]


def test_phase_journal_reports_elapsed_and_no_unfinished_phase(tmp_path):
    journal = PhaseJournal(tmp_path / "phase.log")
    journal("lp", "start")
    time.sleep(0.002)
    journal("lp", "end")
    assert journal.seconds["lp"] > 0
    assert journal.calls == {"lp": 1}
    assert journal.summary()["unfinished"] == []
    assert "elapsed_s=" in (tmp_path / "phase.log").read_text()


@pytest.mark.parametrize("slots", [1, 2])
def test_real_generation_jobs_share_budget_and_match_serial(tmp_path, monkeypatch, slots):
    monkeypatch.setenv("PACK_JOBS", "1")
    baseline = job(tmp_path, "serial")
    assert generate(baseline["command"][3:]) == 0
    jobs = [job(tmp_path, "parallel-a"), job(tmp_path, "parallel-b", "centre")]
    report = queue.run_jobs(jobs, tmp_path / "broker", slots=slots, stage_seconds=30,
                            no_progress_seconds=0)
    assert report["finished"]
    assert all(r["returncode"] == 0 for r in report["jobs"].values())
    assert 0 < report["metrics"]["max_busy"] <= slots
    assert report["metrics"]["round_requests"] > 0
    assert report["metrics"]["chunks_completed"] > 0
    for item in jobs:
        assert mathematical_result(Path(item["output"]).parent / "result.json") == mathematical_result(tmp_path / "serial/result.json")
    assert not list((tmp_path / "broker").glob("context-*.npy"))
    restored = queue.run_jobs(jobs, tmp_path / "broker", slots=slots, stage_seconds=30,
                              no_progress_seconds=0)
    assert all(r.get("reused") for r in restored["jobs"].values())
    assert restored["metrics"]["round_requests"] == 0


def test_failed_driver_does_not_poison_independent_job(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_JOBS", "1")
    good, bad = job(tmp_path, "good"), job(tmp_path, "bad")
    bad["command"].append("--deliberately-invalid-argument")
    report = queue.run_jobs([bad, good], tmp_path / "broker", slots=2, stage_seconds=30,
                            no_progress_seconds=0)
    assert report["jobs"]["bad"]["returncode"] != 0
    assert report["jobs"]["good"]["returncode"] == 0


def test_generation_deadline_is_a_completed_operational_failure(tmp_path):
    item = job(tmp_path, "slow")
    report = queue.run_jobs([item], tmp_path / "broker", slots=1, stage_seconds=0.001,
                            no_progress_seconds=0)
    assert report["jobs"]["slow"]["returncode"] == 124
    assert report["jobs"]["slow"]["finished"] is True


def test_conflicting_output_paths_are_rejected_before_launch(tmp_path):
    item = job(tmp_path, "same")
    with pytest.raises(ValueError, match="share output"):
        queue.validate_jobs([item, {**item, "id": "other"}])


def test_tampered_generation_receipt_cannot_be_reused(tmp_path):
    item = job(tmp_path, "tampered")
    atomic_json(tmp_path / "tampered/generation-receipt.json", {
        "finished": True, "identity": "different", "outputs": {}, "returncode": 0})
    with pytest.raises(ValueError, match="identity"):
        queue.run_jobs([item], tmp_path / "broker", slots=1)


def test_plan_cohort_is_distinct_bounded_and_respects_cycle_limit():
    state = {"config": {"generation_trials": 3, "workers": 16,
                        "strategies": ["baseline", "centre", "pricing", "dense"],
                        "max_cycles": 2}, "cycles": [], "search_revision": 0}
    plan = {"kind": "search", "side": "793/200", "strategy": "centre", "reason": "new search"}
    plans = select_plans(state, plan)
    assert [p["strategy"] for p in plans] == ["centre", "baseline"]
    assert {p["side"] for p in plans} == {"793/200"}
    plan["reason"] = "untried same-side rationalisation before geometric saturation"
    assert select_plans(state, plan) == [plan]


def test_deferred_stage_does_not_launch_process_and_resumes_same_artifact(tmp_path, monkeypatch):
    config = {"verified_low": "99/25", "search_high": "397/100", "seed_certificate": str(frontier.DEFAULT_SEED),
              "workers": 2, "budgets": [1, 2, 3, 4], "row_rounds": 2,
              "scale": 1600000, "max_scale": 25600000, "root": tmp_path}
    state = frontier.initial_state(config, frontier.DEFAULT_SEED)
    monkeypatch.setattr(frontier, "run_child", lambda *_a, **_k: pytest.fail("deferred work was launched"))
    first = frontier.run_cycle(tmp_path, state, defer_generation=True)
    assert first["status"] == "queued"
    second = frontier.run_cycle(tmp_path, state, defer_generation=True)
    assert second is first
    assert len(state["cycles"][0]["stages"]) == 1
    assert "--phase-log" in first["command"]
    assert Fraction(state["verified_low"]) == Fraction(99, 25)
