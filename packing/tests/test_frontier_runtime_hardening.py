"""Real subprocess failure tests; no solver results or proof verdicts are inferred."""
from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

from devtools import frontier_runtime as jobs
from devtools.frontier_io import atomic_json, read_json

PACKING = Path(__file__).resolve().parents[1]


def limits(**changes):
    return {**jobs.DEFAULTS, "retries": 0, "stage_seconds": 12,
            "verify_seconds": 12, "no_progress_seconds": 0,
            "poll_seconds": .02, "terminate_seconds": .1,
            "backoff_seconds": .01, "min_free_mib": 0, **changes}


def wait_for(path: Path, seconds=10):
    end = time.monotonic() + seconds
    while not path.exists():
        if time.monotonic() >= end:
            pytest.fail(f"child did not create {path}")
        time.sleep(.02)


def test_missing_executable_has_a_durable_permanent_error(tmp_path):
    output = tmp_path / "stdout.log"
    missing = str(tmp_path / "does-not-exist")
    assert jobs.run([missing], output, cwd=PACKING, limits=limits(retries=2)) == jobs.PERMANENT_ERROR
    receipt = read_json(tmp_path / "stdout.log.receipt.json")
    assert len(receipt["attempts"]) == 1
    assert receipt["attempts"][0]["spawn_error"] is True


def test_resumed_job_keeps_recorded_environment(tmp_path):
    marker = tmp_path / "workers"
    args = [sys.executable, "-c", f"import os; from pathlib import Path; Path({str(marker)!r}).write_text(os.environ['PACK_JOBS'])"]
    output = tmp_path / "stdout.log"
    assert jobs.run(args, output, cwd=PACKING, env={**os.environ, "PACK_JOBS": "3"}, limits=limits()) == 0
    # Updating the controller's worker option must neither duplicate nor corrupt
    # a job already associated with its own immutable specification.
    assert jobs.run(args, output, cwd=PACKING, env={**os.environ, "PACK_JOBS": "8"}, limits=limits()) == 0
    assert marker.read_text() == "3"
    assert len(read_json(tmp_path / "stdout.log.receipt.json")["attempts"]) == 1


def test_backoff_cannot_start_a_child_after_total_deadline(tmp_path):
    marker = tmp_path / "count"
    script = (f"from pathlib import Path; import sys; p=Path({str(marker)!r}); "
              "p.write_text(str(int(p.read_text())+1 if p.exists() else 1)); sys.exit(5)")
    output = tmp_path / "stdout.log"
    began = time.monotonic()
    assert jobs.run([sys.executable, "-c", script], output, cwd=PACKING,
                    limits=limits(verify_seconds=1, retries=2, backoff_seconds=60)) == jobs.TIMEOUT
    assert time.monotonic() - began < 5
    assert marker.read_text() == "1"
    assert "backoff" in read_json(tmp_path / "stdout.log.receipt.json")["reason"]


def test_pending_job_refuses_a_different_code_fingerprint(tmp_path, monkeypatch):
    marker = tmp_path / "never"
    args = [sys.executable, "-c", f"from pathlib import Path; Path({str(marker)!r}).touch()"]
    output = tmp_path / "stdout.log"
    with monkeypatch.context() as patch:
        def stop_before_spawn(*_args, **_kwargs):
            raise RuntimeError("simulated controller interruption before supervisor spawn")
        patch.setattr(jobs, "_spawn_supervisor", stop_before_spawn)
        with pytest.raises(RuntimeError, match="simulated controller interruption"):
            jobs.run(args, output, cwd=PACKING, limits=limits())
    spec_path = tmp_path / "stdout.log.job.json"
    spec = read_json(spec_path)
    spec["code_sha256"] = "previous-version"
    atomic_json(spec_path, spec)
    assert jobs.run(args, output, cwd=PACKING, limits=limits()) == jobs.PERMANENT_ERROR
    assert not marker.exists()
    assert "source changed" in read_json(tmp_path / "stdout.log.receipt.json")["reason"]


def test_mutating_input_blocks_retry_instead_of_changing_the_experiment(tmp_path):
    source = tmp_path / "input.json"
    source.write_text("original")
    marker = tmp_path / "executions"
    script = ("from pathlib import Path; import sys; "
              f"p=Path({str(marker)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x'); "
              f"Path({str(source)!r}).write_text('changed'); sys.exit(5)")
    args = [sys.executable, "-c", script, "--input", str(source)]
    assert jobs.run(args, tmp_path / "stdout.log", cwd=PACKING, limits=limits(retries=2)) == jobs.PERMANENT_ERROR
    assert marker.read_text() == "x"
    assert "inputs changed" in read_json(tmp_path / "stdout.log.receipt.json")["reason"]


def test_repeated_memory_failures_progressively_reduce_workers(tmp_path):
    args = [sys.executable, "-c", "import time; data=bytearray(8*1024*1024); time.sleep(60)"]
    output = tmp_path / "stdout.log"
    assert jobs.run(args, output, cwd=PACKING, env={**os.environ, "PACK_JOBS": "8"},
                    limits=limits(retries=2, max_rss_mib=1)) == jobs.RESOURCE_LIMIT
    attempts = read_json(tmp_path / "stdout.log.receipt.json")["attempts"]
    assert [a["workers"] for a in attempts if a["kind"] == "execution"] == ["8", "4", "2"]


def test_supervisor_crash_does_not_disable_orphan_no_progress_watchdog(tmp_path):
    marker = tmp_path / "child-started"
    args = [sys.executable, "-c", f"from pathlib import Path; import time; Path({str(marker)!r}).touch(); time.sleep(60)",
            "devtools.run_fractional_colgen"]
    output = tmp_path / "stdout.log"
    budget = limits(stage_seconds=20, no_progress_seconds=2)
    code = ("from pathlib import Path; from devtools.frontier_runtime import run; "
            f"raise SystemExit(run({args!r}, Path({str(output)!r}), cwd=Path({str(PACKING)!r}), limits={budget!r}))")
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=PACKING)
    spec = None
    try:
        wait_for(marker)
        controller.kill()
        controller.wait(timeout=10)
        spec = read_json(tmp_path / "stdout.log.job.json")
        assert jobs.is_alive(spec["supervisor"])
        os.kill(spec["supervisor"]["pid"], signal.SIGKILL)
        began = time.monotonic()
        assert jobs.run(args, output, cwd=PACKING, limits=budget) != 0
        assert time.monotonic() - began < 5
        receipt = read_json(tmp_path / "stdout.log.receipt.json")
        recovered = [a for a in receipt["attempts"] if a["kind"] == "orphan-reconciled"]
        assert recovered and recovered[0]["reason"] == "orphan no-progress watchdog"
        assert not jobs.owned_members(None, spec["token"])
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.wait(timeout=10)
        if spec:
            for member in jobs.owned_members(None, spec["token"]):
                jobs.terminate_owned(member["pgid"], spec["token"], .1)


def test_wrong_token_never_terminates_an_unrelated_process():
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True)
    try:
        jobs.terminate_owned(child.pid, "not-owned-by-this-job", .1)
        assert child.poll() is None
    finally:
        child.terminate()
        child.wait(timeout=10)


def test_controller_recovers_one_supervisor_crash_without_operator_resume(tmp_path):
    marker = tmp_path / "executions"
    script = ("from pathlib import Path; import time; "
              f"p=Path({str(marker)!r}); p.write_text(p.read_text()+'x' if p.exists() else 'x'); "
              "time.sleep(2)")
    args = [sys.executable, "-c", script]
    output = tmp_path / "stdout.log"
    budget = limits(retries=1, verify_seconds=20)
    code = ("from pathlib import Path; from devtools.frontier_runtime import run; "
            f"raise SystemExit(run({args!r}, Path({str(output)!r}), cwd=Path({str(PACKING)!r}), limits={budget!r}))")
    controller = subprocess.Popen([sys.executable, "-c", code], cwd=PACKING)
    spec = None
    try:
        wait_for(marker)
        spec = read_json(tmp_path / "stdout.log.job.json")
        os.kill(spec["supervisor"]["pid"], signal.SIGKILL)
        assert controller.wait(timeout=20) == 0
        receipt = read_json(tmp_path / "stdout.log.receipt.json")
        assert any(a["kind"] == "orphan-reconciled" for a in receipt["attempts"])
        assert marker.read_text() == "xx"
        assert not jobs.owned_members(None, spec["token"])
    finally:
        if controller.poll() is None:
            controller.kill()
            controller.wait(timeout=10)
        if spec:
            for member in jobs.owned_members(None, spec["token"]):
                jobs.terminate_owned(member["pgid"], spec["token"], .1)
