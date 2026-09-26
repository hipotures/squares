"""Utilization regressions: real numerical controls and controller-only fixtures.

Synthetic controller statuses are not certificates. Timing observations are
printed for diagnosis, never asserted as hardware-independent speedups.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from devtools import frontier_generation_campaign as campaign
from devtools import frontier_generation_queue as queue
from devtools.frontier_io import atomic_json, read_json
from sqpack.fractional import depth_parallel
from sqpack.fractional.colgen import _depths


def arrays(squares=128, blocks=3):
    rng = np.random.default_rng(789)
    chunk = max(1, 4_000_000 // squares)
    query = rng.uniform(-2, 2, (chunk * blocks + 7, 2))
    axes = rng.uniform(-1, 1, (squares, 2, 2))
    offsets = rng.uniform(-0.5, 0.5, (squares, 2))
    weights = rng.uniform(-1, 1, squares)
    weights[:4] = [1e20, 1e-20, -1e20, -0.0]
    query[:4] = [[0, 0], [0.5, 0], [-0.5, 0], [0.5 + 1e-9, 0]]
    axes[:4] = [[[1, 0], [0, 1]]] * 4
    offsets[:4] = 0
    return query, axes, offsets, weights


@pytest.mark.parametrize("squares", [31, 128, 1024])
def test_depth_worker_preserves_oracle_bits_and_tail(tmp_path, squares):
    query, axes, offsets, weights = arrays(squares, 2)
    expected = _depths.__wrapped__(query, axes, offsets, weights, 0.5, slack=1e-9)
    key = str(tmp_path / "context-depth")
    for value, suffix in zip((query, axes, offsets, weights), depth_parallel.SUFFIXES, strict=True):
        np.save(key + suffix, value, allow_pickle=False)
    actual = np.concatenate([
        depth_parallel.worker(key, (start, stop, 0.5, 1e-9))[0]
        for start, stop in depth_parallel.block_ranges(len(query), squares)
    ])
    assert actual.tobytes() == expected.tobytes()
    assert np.array_equal(np.argsort(-actual), np.argsort(-expected))


def test_depth_ranges_keep_full_original_blocks():
    block = 4_000_000 // 1024
    ranges = depth_parallel.block_ranges(block * 33 + 5, 1024)
    assert len(ranges) == 9
    assert ranges[0] == (0, 4 * block)
    assert ranges[-1][1] == block * 33 + 5
    assert all(start % block == 0 for start, _ in ranges)
    assert all(a[1] == b[0] for a, b in zip(ranges, ranges[1:]))
    assert depth_parallel.block_ranges(0, 1024) == []
    with pytest.raises(ValueError):
        depth_parallel.block_ranges(-1, 1)


def test_depth_executor_scope_and_small_work_remain_serial():
    tiny = tuple(value[:4] for value in arrays(128, 0))
    called = []

    class Borrowed:
        def depth_survey(self, *args, **kwargs):
            called.append(True)
            raise RuntimeError("injected executor failure")

    executor = Borrowed()
    with depth_parallel.using_executor(executor):
        _depths(*tiny, 0.5, slack=1e-9)
        assert not called
        with pytest.raises(RuntimeError, match="injected"):
            _depths(*arrays(128, 2), 0.5, slack=1e-9)
    assert called == [True]
    assert _depths(*tiny, 0.5, slack=1e-9).shape == (4,)


def _numeric_driver(connection, command, output):
    """Real depth arithmetic through broker IPC, not a full generator fixture."""
    started, cpu = time.monotonic(), time.process_time()
    kind, _ = connection.recv()
    assert kind == "resume"
    proxy = queue.SharedDirections(connection)
    data = arrays(128, 3)
    expected = _depths.__wrapped__(*data, 0.5, slack=1e-9)
    bad = Path(output).parent.name == "bad"
    if bad:
        data = (*data[:3], data[3][:-1])
    code = 0
    try:
        actual = proxy.depth_survey(*data, 0.5, slack=1e-9)
        if actual.tobytes() != expected.tobytes():
            raise AssertionError("parallel depth output changed")
        atomic_json(Path(output).parent / "result.json", {"matched": True})
    except (RuntimeError, AssertionError):
        code = 70
    connection.send(("finished", {"returncode": code,
        "driver_cpu_seconds": time.process_time() - cpu,
        "wall_seconds": time.monotonic() - started}))
    connection.close()


def job(root, name, *, real=False):
    directory = root / name
    directory.mkdir(parents=True)
    command = [sys.executable, "-m", "devtools.run_fractional_colgen",
               "--n", "12", "--side", "198111/50000", "--grid-counts", "5,7,9",
               "--direction-steps", "12", "--column-rounds", "2", "--max-rounds", "60",
               "--support-cap", "128", "--json", str(directory / "result.json")]
    if real:
        command.extend(["--freeze", str(directory / "candidate.json"),
                        "--log", str(directory / "column.log"),
                        "--row-log", str(directory / "rows.log"),
                        "--phase-log", str(directory / "phase.log")])
    return {"id": name, "command": command, "output": str(directory / "stdout.log")}


@pytest.mark.parametrize("slots", [1, 2, 4])
def test_depth_tasks_share_leases_and_cleanup(tmp_path, monkeypatch, slots):
    monkeypatch.setattr(queue, "_drive", _numeric_driver)
    samples = []
    jobs = [job(tmp_path, "a"), job(tmp_path, "b")]
    report = queue.run_jobs(jobs, tmp_path / "broker", slots=slots,
                            stage_seconds=60, no_progress_seconds=0,
                            code_sha="numeric-fixture", on_progress=samples.append)
    assert all(item["returncode"] == 0 for item in report["jobs"].values())
    assert report["metrics"]["depth_requests"] == 2
    assert report["metrics"]["depth_chunks_completed"] >= 6
    assert 0 < report["metrics"]["max_busy"] <= slots
    assert all(s["serial_owners"] + s["direction_tasks"] + s["depth_tasks"] <= slots for s in samples)
    assert 0 <= report["metrics"]["mean_leased_slots"] <= slots
    assert not list((tmp_path / "broker").glob("context-*.npy"))
    restored = queue.run_jobs(jobs, tmp_path / "broker", slots=slots, code_sha="numeric-fixture")
    assert all(record["reused"] for record in restored["jobs"].values())
    assert restored["metrics"]["depth_requests"] == 0
    assert restored["metrics"]["depth_worker_cpu_seconds"] == 0


def test_bad_depth_task_is_operational_and_does_not_poison_sibling(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "_drive", _numeric_driver)
    report = queue.run_jobs([job(tmp_path, "bad"), job(tmp_path, "good")], tmp_path / "broker",
                            slots=2, stage_seconds=60, no_progress_seconds=0,
                            code_sha="numeric-fixture")
    assert report["jobs"]["bad"]["returncode"] != 0
    assert report["jobs"]["good"]["returncode"] == 0
    assert not list((tmp_path / "broker").glob("context-*.npy"))


def test_real_generator_parallel_depth_matches_serial_depth(tmp_path, monkeypatch):
    results, reports = [], []
    for mode in ("0", "1"):
        monkeypatch.setenv("PACK_DEPTH_PARALLEL", mode)
        item = job(tmp_path, f"mode-{mode}", real=True)
        report = queue.run_jobs([item], tmp_path / f"broker-{mode}", slots=2,
                                stage_seconds=90, no_progress_seconds=0)
        assert report["jobs"][item["id"]]["returncode"] == 0
        results.append(read_json(Path(item["output"]).parent / "result.json"))
        reports.append(report)
    for key in ("objective", "least_covered", "total_mass", "atoms", "stopped", "converged"):
        assert results[0][key] == results[1][key]
    def rounds(result):
        return [{k: v for k, v in row.items() if k != "seconds"} for row in result["rounds"]]
    assert rounds(results[0]) == rounds(results[1])
    assert (tmp_path / "mode-0/candidate.json").read_bytes() == (tmp_path / "mode-1/candidate.json").read_bytes()
    assert reports[0]["metrics"]["depth_requests"] == 0
    assert reports[1]["metrics"]["depth_requests"] > 0
    print("real generator depth control:", [r["metrics"] for r in reports])


def controller_state(tmp_path, names):
    state = {"verified_low": "99/25", "search_high": "397/100", "initial_width": "1/100",
             "search_revision": 0, "active": None, "generation_wave": None,
             "config": {"generation_trials": 3, "workers": 16,
                        "strategies": ["pricing", "centre", "windows", "dense", "fine-net"],
                        "runtime": {"stage_seconds": 30, "no_progress_seconds": 0}},
             "cycles": [], "active_generation": []}
    for name in names:
        index = len(state["cycles"])
        state["cycles"].append({"strategy": name, "side": "793/200", "status": "RUNNING", "stages": []})
        state["active_generation"].append(index)
    return state


def queued_stage(tmp_path, index, cycle, work="generation"):
    directory = tmp_path / f"cycle-{index}" / f"stage-{len(cycle['stages'])}"
    directory.mkdir(parents=True)
    stage = {"status": "queued", "work_kind": work, "name": "screen", "directory": str(directory),
             "command": [sys.executable, "-m", "devtools.run_fractional_colgen"]}
    cycle["stages"].append(stage)
    return stage


@pytest.mark.parametrize("limit,expected", [(None, [3, 3]), (4, [3, 2])])
def test_refill_after_wave_not_only_after_resume(tmp_path, monkeypatch, limit, expected):
    state = controller_state(tmp_path, ["pricing", "centre", "windows"])
    state["config"]["max_cycles"] = limit
    waves = []
    monkeypatch.setattr(campaign.frontier_policy, "strategy_proposal", lambda s, n: {
        "side": "793/200", "strategy": n, "reason": "controller fixture"})

    def run_cycle(root, current, *, defer_generation):
        index = current["active"]
        cycle = current["cycles"][index]
        if cycle["stages"]:
            cycle["stages"][-1]["status"] = "complete"
            if cycle["strategy"] != "pricing" or len(cycle["stages"]) >= 2:
                cycle["status"] = "UNRESOLVED"
                return None
        return queued_stage(root, index, cycle)

    def finish(root, current, frontier):
        entries = current["generation_wave"]["stages"]
        waves.append(len(entries))
        for index, stage_index in entries:
            current["cycles"][index]["stages"][stage_index]["status"] = "generated"
        current["generation_wave"] = None

    monkeypatch.setattr(campaign, "_finish_wave", finish)
    stub = SimpleNamespace(stamp=lambda: "fixture", display=str, save_state=lambda *_: None,
                           emit=lambda *_: None, write_views=lambda *_: None, run_cycle=run_cycle)
    campaign.run_portfolio(tmp_path, state, stub)
    assert waves == expected
    assert not state["active_generation"]
    assert len(state["cycles"]) == (5 if limit is None else 4)
    assert len({c["strategy"] for c in state["cycles"]}) == len(state["cycles"])
    assert state["verified_low"] == "99/25"


@pytest.mark.parametrize("stop_during_refine", [False, True])
def test_rationalisation_is_interpreted_before_unrelated_generation(tmp_path, monkeypatch, stop_during_refine):
    state = controller_state(tmp_path, ["fine-net", "pricing"])
    state["config"]["generation_trials"] = 2
    state["config"]["max_cycles"] = 2
    events = []
    stopped = [False]

    def run_cycle(root, current, *, defer_generation):
        index = current["active"]
        cycle = current["cycles"][index]
        if not cycle["stages"]:
            return queued_stage(root, index, cycle, "rerationalisation" if index == 0 else "generation")
        cycle["stages"][-1]["status"] = "complete"
        events.append("adopt-refine" if index == 0 else "adopt-generation")
        cycle["status"] = "UNRESOLVED"
        return None

    def child(command, output, environment):
        atomic_json(output.parent / "result.json", {"fixture": "scale result"})
        events.append("refine")
        stopped[0] = stop_during_refine
        return 0

    def finish(root, current, frontier):
        assert "adopt-refine" in events
        events.append("generation")
        for i, j in current["generation_wave"]["stages"]:
            current["cycles"][i]["stages"][j]["status"] = "generated"
        current["generation_wave"] = None

    monkeypatch.setattr(campaign, "_finish_wave", finish)
    stub = SimpleNamespace(stamp=lambda: "fixture", display=str, save_state=lambda *_: None,
                           emit=lambda *_: None, write_views=lambda *_: None, run_cycle=run_cycle,
                           run_child=child, controlled_env=lambda _: {}, stop_requested=lambda: stopped[0])
    campaign.run_portfolio(tmp_path, state, stub)
    assert events[:2] == ["refine", "adopt-refine"]
    assert ("generation" in events) is not stop_during_refine
    assert len(state["cycles"]) == 2


def test_refill_never_changes_live_wave_or_admits_after_stop(tmp_path):
    state = controller_state(tmp_path, ["pricing"])
    state["generation_wave"] = {"immutable": True}
    stub = SimpleNamespace(stop_requested=lambda: False)
    assert campaign.refill_resumed_cohort(tmp_path, state, stub) == []
    state["generation_wave"] = None
    stub.stop_requested = lambda: True
    assert campaign.refill_resumed_cohort(tmp_path, state, stub) == []
    assert len(state["cycles"]) == 1
