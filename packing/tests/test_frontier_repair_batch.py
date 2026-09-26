"""Controller/queue contracts with explicit synthetic screen receipts, not proofs."""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH
from devtools import frontier_boost_queue as queue
from devtools.frontier_io import atomic_json, digest, read_json
from devtools.frontier_repair_batch import run_boosts


def harness(root, *, screening="QUICK_ACCEPTED", exit_code=0):
    state = {"config": {"workers": 2}, "mode": "REPAIR"}
    attempt = {"directory": str(root), "candidate": str(FIRST_RUNG_PATH), "side": "19/5", "repairs": []}
    trace = []
    def boost(source, destination, slack):
        record = read_json(source)
        mass = Fraction(record["total_mass"])
        target = mass + (12 - mass) * slack
        record["atoms"] = [[x, y, str(Fraction(w) * target / mass)] for x, y, w in record["atoms"]]
        record["total_mass"] = str(target)
        record["least_cell_mass"] = None
        atomic_json(destination, record)
        return target
    def child(args, output):
        if exit_code:
            return exit_code
        manifest = Path(args[args.index("--input") + 1])
        report_path = Path(args[args.index("--report") + 1])
        if report_path.exists():
            trace.append("screen-reuse")
            return 0
        trace.append("screen")
        request = read_json(manifest)
        checkpoint = report_path.parent / "queue-checkpoint.json"
        atomic_json(checkpoint, {"test_only": "synthetic screen evidence"})
        atomic_json(report_path, {"purpose": queue.PURPOSE, "finished": True,
            "manifest_sha256": digest(manifest),
            "code_sha256": queue.code_fingerprint(Path(queue.__file__).resolve().parents[1]),
            "checkpoint_sha256": digest(checkpoint), "reused_directions": 0,
            "metrics": {"slots": 2, "completed_items": 2, "submitted_batches": 2,
                        "total_seconds": .01, "coordinator_cpu_seconds": .001},
            "results": [{"source": item["path"], "source_sha256": item["sha256"],
                         "label": item["label"], "state": screening} for item in request["candidates"]]})
        return 0
    def verify(*_args):
        trace.append("full-gate")
        return "full-rejected", None
    def error(_state, current, reason):
        current.update(status="ERROR", reason=reason)
    api = SimpleNamespace(REPO=Path(queue.__file__).resolve().parents[2], write_boosted_candidate=boost,
        stamp=lambda: "test-time", save_state=lambda *_: None, write_views=lambda *_: None,
        emit=lambda *_: None, poll_stop=lambda: None, run_child=child, verify_candidate=verify,
        repair_job_failure=error, promote_verified=lambda *_: pytest.fail("promoted a screen without a full proof"),
        publish_findings=lambda *_: None)
    return state, attempt, api, trace


def test_positive_screen_always_requires_full_gate(tmp_path):
    state, attempt, api, trace = harness(tmp_path)
    assert run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert trace == ["screen", "full-gate", "full-gate"]
    assert attempt["status"] == "REJECTED"


def test_negative_screen_does_not_pay_for_a_full_gate(tmp_path):
    state, attempt, api, trace = harness(tmp_path, screening="QUICK_REJECTED")
    assert run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert trace == ["screen"]
    assert all(entry["status"] == "REJECTED" for entry in attempt["repairs"])


def test_queue_error_is_not_a_search_or_mathematical_failure(tmp_path):
    state, attempt, api, trace = harness(tmp_path, exit_code=70)
    run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert attempt["status"] == "ERROR"
    assert trace == []
    assert all(entry["status"] == "RUNNING" for entry in attempt["repairs"])


def test_resume_after_screen_before_gate_reuses_same_queue(tmp_path):
    state, attempt, api, trace = harness(tmp_path)
    def interrupt(*_):
        raise RuntimeError("injected controller crash")
    original = api.verify_candidate
    api.verify_candidate = interrupt
    with pytest.raises(RuntimeError, match="injected"):
        run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    manifest = attempt["shared_queue"]["manifest"]
    api.verify_candidate = original
    run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert attempt["shared_queue"]["manifest"] == manifest
    assert trace == ["screen", "screen-reuse", "full-gate", "full-gate"]


def test_partial_applied_screen_keeps_other_results_on_resume(tmp_path):
    state, attempt, api, trace = harness(tmp_path)
    original = api.verify_candidate
    calls = []
    def interrupted_gate(*args):
        calls.append(True)
        if len(calls) == 2:
            raise RuntimeError("injected crash between full gates")
        return original(*args)
    api.verify_candidate = interrupted_gate
    with pytest.raises(RuntimeError):
        run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert attempt["repairs"][0]["status"] == "REJECTED"
    api.verify_candidate = original
    run_boosts(tmp_path, state, attempt, [Fraction(1, 2), Fraction(3, 4)], api)
    assert trace == ["screen", "full-gate", "screen-reuse", "full-gate"]
