"""Shared repair queue controls; synthetic direction records are not proofs."""
from __future__ import annotations

import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
from pathlib import Path

import pytest

from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH
from devtools import frontier_boost_queue as queue
from devtools import frontier_verify
from devtools.frontier_dispatch import BatchSizer, dispatch
from devtools.frontier_io import atomic_json, canonical_digest, digest, read_json


def family(root: Path, factors=(Fraction(101, 100), Fraction(102, 100))):
    root.mkdir(parents=True, exist_ok=True)
    original = read_json(FIRST_RUNG_PATH)
    candidates = []
    for index, factor in enumerate(factors):
        record = dict(original)
        record["atoms"] = [[x, y, str(Fraction(w) * factor)] for x, y, w in original["atoms"]]
        record["total_mass"] = str(Fraction(original["total_mass"]) * factor)
        record["least_cell_mass"] = None
        path = root / f"boost-{index}.json"
        atomic_json(path, record)
        candidates.append({"label": str(index), "path": str(path), "sha256": digest(path)})
    manifest = root / "manifest.json"
    atomic_json(manifest, {"schema": 1, "purpose": queue.PURPOSE, "side": original["outer_side"],
                          "candidates": candidates, "target_seconds": 0.2, "max_batch": 8})
    return manifest


def fake_result(group, ids, seconds=0.001):
    return {"group": group, "records": [{"index": i, "seconds": seconds} for i in ids],
            "wall_seconds": seconds * len(ids), "cpu_seconds": 0.0, "cancelled": False}


def test_short_work_is_batched_and_inflight_is_bounded():
    completed = []
    checkpoints = []
    def work(task):
        return fake_result(*task)
    with ThreadPoolExecutor(max_workers=4) as pool:
        metrics = dispatch(pool, work, [range(100)] * 6, slots=4, active=lambda _: True,
                           accept=lambda group, record: completed.append((group, record["index"])),
                           checkpoint=lambda stats, force: checkpoints.append((stats, force)))
    assert len(set(completed)) == 600
    assert metrics["peak_in_flight"] <= 4
    assert metrics["largest_batch"] == 8
    assert metrics["submitted_batches"] < 300
    assert all(count > 0 for count in metrics["group_batches"])
    assert checkpoints[-1][1]


def test_one_slow_direction_does_not_block_refill_for_other_boosts():
    events = []
    lock = threading.Lock()
    def work(task):
        group, ids = task
        if group == 0 and 0 in ids:
            time.sleep(0.15)
        else:
            time.sleep(0.003)
        with lock:
            events.append((group, ids))
        return fake_result(group, ids, 1.0)  # Keep batches at one for the control.
    with ThreadPoolExecutor(max_workers=4) as pool:
        metrics = dispatch(pool, work, [range(8), range(24)], slots=4, active=lambda _: True,
                           accept=lambda *_: None)
    slow = next(i for i, item in enumerate(events) if item == (0, (0,)))
    assert sum(group == 1 for group, _ in events[:slow]) > 4
    assert metrics["peak_in_flight"] <= 4


def test_batch_sizer_reacts_to_expensive_work_and_tail():
    sizer = BatchSizer(target_seconds=0.5, maximum=8)
    assert sizer.size(1000, 16) == 1
    sizer.observe([0.001])
    assert [sizer.size(1000, 16) for _ in range(3)] == [2, 4, 8]
    sizer.observe([0.001, 1.1])
    assert sizer.size(1000, 16) == 1
    sizer.seconds_per_item = 0.001
    assert sizer.size(16, 16) == 1


@pytest.mark.parametrize("value", [math.nan, math.inf, -1])
def test_invalid_timing_is_not_adaptive_feedback(value):
    with pytest.raises(ValueError):
        BatchSizer().observe([value])


def test_missing_result_does_not_complete_a_job():
    def incomplete(task):
        group, _ = task
        return fake_result(group, [])
    with ThreadPoolExecutor(max_workers=1) as pool:
        with pytest.raises(ValueError, match="omitted"):
            dispatch(pool, incomplete, [range(3)], slots=1, active=lambda _: True,
                     accept=lambda *_: pytest.fail("missing result accepted"))


def test_worker_exception_is_not_a_mathematical_refusal():
    def broken(_task):
        raise RuntimeError("injected worker failure")
    checkpoints = []
    with ThreadPoolExecutor(max_workers=2) as pool:
        with pytest.raises(RuntimeError, match="injected"):
            dispatch(pool, broken, [range(4)], slots=2, active=lambda _: True,
                     accept=lambda *_: None,
                     checkpoint=lambda stats, force: checkpoints.append(force))
    assert checkpoints[-1]


def test_actual_direction_records_match_serial_parallel(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_JOBS", "2")
    serial_input = family(tmp_path / "serial")
    parallel_input = family(tmp_path / "parallel")
    serial = queue.screen(serial_input, serial_input.parent / "report.json", workers=1)
    parallel = queue.screen(parallel_input, parallel_input.parent / "report.json", workers=2)
    a = read_json(serial_input.parent / "queue-checkpoint.json")
    b = read_json(parallel_input.parent / "queue-checkpoint.json")
    assert all(result["state"] == "QUICK_ACCEPTED" for result in serial["results"])
    assert [r["state"] for r in parallel["results"]] == [r["state"] for r in serial["results"]]
    for left, right in zip(a["results"], b["results"]):
        assert len(left["records"]) == len(right["records"]) == 361
        assert {i: record["outcome"] for i, record in left["records"].items()} == {
            i: record["outcome"] for i, record in right["records"].items()}
    assert parallel["metrics"]["slots"] == 2
    assert parallel["metrics"]["peak_in_flight"] <= 2


def test_finished_direction_checkpoint_is_reused(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_JOBS", "2")
    manifest = family(tmp_path, factors=(Fraction(102, 100),))
    first = queue.screen(manifest, tmp_path / "report.json", workers=2)
    second = queue.screen(manifest, tmp_path / "report.json", workers=1)
    assert first["results"] == second["results"]
    assert second["reused_directions"] == 361
    assert second["metrics"]["submitted_batches"] == 0
    assert second["purpose"] == queue.PURPOSE
    assert not list(tmp_path.rglob("*verified.json"))


def test_partial_checkpoint_recovers_after_injected_parent_failure(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_JOBS", "2")
    manifest = family(tmp_path)
    real_save, real_dispatch = queue.atomic_json, queue.dispatch
    injected = []
    def save_then_crash(path, record):
        real_save(path, record)
        if path.name == "queue-checkpoint.json" and not injected and record["metrics"]["completed_items"] >= 10:
            injected.append(True)
            raise RuntimeError("injected crash after checkpoint")
    def frequent(*args, **kwargs):
        return real_dispatch(*args, **kwargs, checkpoint_seconds=0.01)
    monkeypatch.setattr(queue, "atomic_json", save_then_crash)
    monkeypatch.setattr(queue, "dispatch", frequent)
    with pytest.raises(RuntimeError, match="injected"):
        queue.screen(manifest, tmp_path / "report.json", workers=2)
    assert not (tmp_path / "report.json").exists()
    monkeypatch.setattr(queue, "atomic_json", real_save)
    monkeypatch.setattr(queue, "dispatch", real_dispatch)
    result = queue.screen(manifest, tmp_path / "report.json", workers=2)
    assert 0 < result["reused_directions"] < 722
    assert result["reused_directions"] + result["metrics"]["completed_items"] == 722
    assert all(r["state"] == "QUICK_ACCEPTED" for r in result["results"])


def test_stall_does_not_prune_other_boosts(tmp_path, monkeypatch):
    manifest = family(tmp_path)
    def synthetic(task):
        group, ids = task
        atoms = queue._PREPARED.atoms[group]
        answer = fake_result(group, ids)
        for record in answer["records"]:
            record["outcome"] = {
                "label": queue._PREPARED.rotations[record["index"]].label,
                "status": "undecided" if group else "certified", "lower": 0 if group else atoms.scale,
                "upper": atoms.scale, "witness": None, "boxes": 1,
                "stalled": 1 if group else 0, "budget_exhausted": False,
            }
        return answer
    monkeypatch.setattr(queue, "evaluate_batch", synthetic)
    result = queue.screen(manifest, tmp_path / "report.json", workers=1)
    assert [r["state"] for r in result["results"]] == ["QUICK_ACCEPTED", "QUICK_REJECTED"]
    assert result["results"][1]["reason"] == "interval-undecided"


def test_true_refutation_can_prune_lighter_uniform_boost(tmp_path, monkeypatch):
    manifest = family(tmp_path, factors=(Fraction(1, 2), Fraction(3, 5)))
    result = queue.screen(manifest, tmp_path / "report.json", workers=2)
    assert all(r["state"] == "QUICK_REJECTED" for r in result["results"])
    assert result["metrics"]["completed_items"] < 722
    assert result["purpose"] == queue.PURPOSE


def test_cooperative_cancellation_is_an_exception_not_a_verdict(tmp_path):
    manifest = family(tmp_path)
    _, _, prepared, _ = queue._load_family(manifest)
    queue.initialise(prepared, [1, 0])
    search = queue.InterruptibleSearch(prepared.atoms[0], prepared.rotations[0], prepared.outer, prepared.square)
    search.group = 0
    with pytest.raises(queue.BatchCancelled):
        search.search(prune_at=None)
    result = queue.evaluate_batch((0, (0, 1)))
    assert result["cancelled"] and result["records"] == []


@pytest.mark.parametrize("change", ["geometry", "weights", "bytes", "duplicate-json"])
def test_changed_or_nonuniform_inputs_are_refused(tmp_path, change):
    manifest = family(tmp_path)
    request = read_json(manifest)
    path = Path(request["candidates"][1]["path"])
    record = read_json(path)
    if change == "bytes":
        path.write_text(path.read_text() + "\n")
    elif change == "duplicate-json":
        path.write_text(path.read_text().replace('"n": 12', '"n": 12, "n": 12'))
        request["candidates"][1]["sha256"] = digest(path)
    else:
        if change == "geometry":
            # Same total and D4 invariance, but not the same coordinate support.
            record["atoms"] = [["19/10", "19/10", record["total_mass"]]]
        else:
            from sqpack.fractional.certificate import d4_images
            x, y, _ = record["atoms"][0]
            orbit = set(d4_images(Fraction(x), Fraction(y), Fraction("19/5")))
            record["atoms"] = [[x, y, str(Fraction(w) + (
                Fraction(1, 1000000) if (Fraction(x), Fraction(y)) in orbit else 0))]
                for x, y, w in record["atoms"]]
            record["total_mass"] = str(sum(Fraction(w) for _, _, w in record["atoms"]))
        atomic_json(path, record)
        request["candidates"][1]["sha256"] = digest(path)
    atomic_json(manifest, request)
    with pytest.raises(ValueError):
        queue.screen(manifest, tmp_path / "report.json", workers=1)
    assert not (tmp_path / "report.json").exists()



def test_quick_first_normalises_null_declaration_without_accepting_it_as_a_proof(tmp_path, monkeypatch):
    record = read_json(FIRST_RUNG_PATH)
    record["least_cell_mass"] = None
    source = tmp_path / "candidate.json"
    atomic_json(source, record)
    monkeypatch.setenv("PACK_JOBS", "2")
    result = frontier_verify.decide(source, tmp_path / "gate", Fraction("19/5"), quick_first=True)
    assert result["status"] == "VERIFIED", result
    assert result["category"] == "full-retainable"
    assert result["finished"] is True
    assert "RETAINABLE: both routes accept" in (tmp_path / "gate/verify-full.log").read_text()
    assert read_json(source)["least_cell_mass"] is None


def test_quick_accept_never_shortcuts_the_full_gate(tmp_path, monkeypatch):
    source = FIRST_RUNG_PATH
    calls = []
    real = frontier_verify.gate.decide
    def gate(path, *, quick, **kwargs):
        calls.append(quick)
        if quick:
            return True
        return real(path, quick=False, **kwargs)
    monkeypatch.setenv("PACK_JOBS", "2")
    monkeypatch.setattr(frontier_verify.gate, "decide", gate)
    result = frontier_verify.decide(source, tmp_path, Fraction("19/5"), quick_first=True)
    assert calls == [True, False]
    assert result["status"] == "VERIFIED"


def test_corrupt_checkpoint_is_not_reused(tmp_path):
    manifest = family(tmp_path)
    atomic_json(tmp_path / "queue-checkpoint.json", {"fingerprint": "wrong", "results": [], "checksum": "wrong"})
    with pytest.raises(ValueError, match="identity/integrity"):
        queue.screen(manifest, tmp_path / "report.json", workers=1)


def test_queue_output_cannot_overwrite_a_candidate(tmp_path):
    manifest = family(tmp_path)
    source = Path(read_json(manifest)["candidates"][0]["path"])
    before = source.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        queue.screen(manifest, source, workers=1)
    assert source.read_bytes() == before


def test_only_saved_direction_evidence_is_replayed_not_status_text(tmp_path, monkeypatch):
    manifest = family(tmp_path, factors=(Fraction(102, 100),))
    request = read_json(manifest)
    source_sha = queue.code_fingerprint(Path(queue.__file__).resolve().parents[1])
    saved = {"fingerprint": canonical_digest({"manifest": digest(manifest), "source": source_sha, "schema": 1}),
             "results": [{"source_sha256": request["candidates"][0]["sha256"],
                          "state": "QUICK_ACCEPTED", "records": {}}]}
    atomic_json(tmp_path / "queue-checkpoint.json", {**saved, "checksum": canonical_digest(saved)})
    def refuse(task):
        group, indices = task
        result = fake_result(group, indices)
        for record in result["records"]:
            record["outcome"] = {"label": queue._PREPARED.rotations[record["index"]].label,
                "status": "undecided", "lower": 0, "upper": queue._PREPARED.atoms[group].scale,
                "witness": None, "boxes": 1, "stalled": 1, "budget_exhausted": False}
        return result
    monkeypatch.setattr(queue, "evaluate_batch", refuse)
    result = queue.screen(manifest, tmp_path / "report.json", workers=1)
    assert result["results"][0]["state"] == "QUICK_REJECTED"
    assert result["metrics"]["submitted_batches"] > 0
