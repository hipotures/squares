"""The sequential covering-queue walker skips finished probes and halts on mass < n."""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from contextlib import suppress
from datetime import UTC, datetime
from multiprocessing import get_context
from pathlib import Path
from unittest.mock import patch

from devtools import run_covering_queue as covering_queue
from devtools.run_covering_queue import (
    EXIT_BUSY,
    EXIT_DONE,
    EXIT_FREEZE_BELOW,
    EXIT_STOP,
    Probe,
    colgen_command,
    freeze_mass_below_n,
    load_queue,
    parse_stop_at,
    remain_seconds,
    walk_queue,
)

QUEUE = """
probes:
  - id: n12-done
    n: 12
    side: '397/100'
    grid_counts: '28,38,46,54'
    seed_certificate: cases/n12_fractional_certificate/certificate.json
    seed_windows: 7
    deadline_seconds: 1200
    bead: think-h02v
  - id: n17-open
    n: 17
    side: '23/5'
    grid_counts: '34,45,56,64'
    seed_certificate: cases/n17_fractional_certificate/certificate.json
    seed_windows: 8
    deadline_seconds: 1200
"""


def _run_queue_owner(
    probe: Probe,
    results_dir: Path,
    waiter_log: Path,
    child_command: list[str],
) -> None:
    os.setsid()
    with patch.object(covering_queue, "colgen_command", return_value=child_command):
        walk_queue(
            [probe],
            results_dir,
            parse_stop_at("2099-01-01T00:00:00Z"),
            waiter_log,
        )


def test_load_queue_reads_named_fields(tmp_path: Path) -> None:
    path = tmp_path / "queue.yaml"
    path.write_text(QUEUE, encoding="utf-8")
    probes = load_queue(path)
    assert [probe.id for probe in probes] == ["n12-done", "n17-open"]
    assert probes[0].n == 12
    assert probes[0].grid_counts == "28,38,46,54"
    assert probes[1].seed_windows == 8
    assert probes[0].seed_certificate is not None


def test_freeze_mass_compare(tmp_path: Path) -> None:
    below = tmp_path / "below.json"
    below.write_text(json.dumps({"total_mass": "48534459/4000000"}), encoding="utf-8")
    assert freeze_mass_below_n(13, below)
    assert not freeze_mass_below_n(12, below)
    missing = tmp_path / "none.json"
    missing.write_text(json.dumps({"objective": 12.1}), encoding="utf-8")
    assert not freeze_mass_below_n(12, missing)


def test_walk_skips_existing_run_json(tmp_path: Path) -> None:
    started: list[str] = []
    (tmp_path / "n12-done-run.json").write_text("{}", encoding="utf-8")
    probes = [
        Probe("n12-done", 12, "397/100", "28,38,46,54", "cert.json", 7, 1200),
        Probe("n17-open", 17, "23/5", "34,45,56,64", "cert.json", 8, 1200),
    ]

    def fake(probe: Probe, prefix: Path) -> int:
        started.append(probe.id)
        Path(f"{prefix}-run.json").write_text("{}", encoding="utf-8")
        return 0

    rc = walk_queue(
        probes,
        tmp_path,
        parse_stop_at("2099-01-01T00:00:00Z"),
        tmp_path / "waiter.log",
        runner=fake,
    )
    assert rc == EXIT_DONE
    assert started == ["n17-open"]


def test_walk_halts_when_freeze_mass_is_below_n(tmp_path: Path) -> None:
    probe = Probe("n18-hit", 18, "467/100", "auto", "cert.json", 5, 1200)

    def fake(_probe: Probe, prefix: Path) -> int:
        Path(f"{prefix}-run.json").write_text(
            json.dumps({"total_mass": "17/1"}), encoding="utf-8"
        )
        Path(f"{prefix}-certificate.json").write_text("{}", encoding="utf-8")
        return 0

    rc = walk_queue(
        [probe],
        tmp_path,
        parse_stop_at("2099-01-01T00:00:00Z"),
        tmp_path / "waiter.log",
        runner=fake,
    )
    assert rc == EXIT_FREEZE_BELOW


def test_walk_stops_when_the_budget_is_gone(tmp_path: Path) -> None:
    probe = Probe("n19-late", 19, "481/100", "34,45,56", "cert.json", 6, 1200)
    rc = walk_queue(
        [probe],
        tmp_path,
        datetime(2020, 1, 1, tzinfo=UTC),
        tmp_path / "waiter.log",
        runner=lambda _probe, _prefix: 0,
    )
    assert rc == EXIT_STOP


def test_orphaned_generator_retains_ownership_until_it_exits(
    tmp_path: Path,
) -> None:
    probe = Probe("n20-shared", 20, "973/200", "auto", None, 5, 1200)
    context = get_context("spawn")
    child_pid_path = tmp_path / "generator.pid"
    child_command = [
        sys.executable,
        "-c",
        (
            "import os, sys, time; from pathlib import Path; "
            "Path(sys.argv[1]).write_text(str(os.getpid()), encoding='utf-8'); "
            "time.sleep(60)"
        ),
        str(child_pid_path),
    ]

    process = context.Process(
        target=_run_queue_owner,
        args=(probe, tmp_path, tmp_path / "first-waiter.log", child_command),
    )
    process_started = False
    orphan_pid: int | None = None
    second_started: list[str] = []
    try:
        process.start()
        process_started = True
        deadline = time.monotonic() + 5
        while True:
            if child_pid_path.is_file():
                child_pid_text = child_pid_path.read_text(encoding="utf-8")
                if child_pid_text:
                    orphan_pid = int(child_pid_text)
                    break
            if not process.is_alive():
                raise AssertionError("queue walker exited before starting its generator")
            if time.monotonic() >= deadline:
                raise AssertionError("queue walker did not start its generator")
            time.sleep(0.01)
        process.kill()
        process.join(timeout=5)
        assert not process.is_alive()
        os.kill(orphan_pid, 0)

        rc = walk_queue(
            [probe],
            tmp_path,
            parse_stop_at("2099-01-01T00:00:00Z"),
            tmp_path / "second-waiter.log",
            runner=lambda candidate, _prefix: second_started.append(candidate.id) or 0,
        )
        assert rc == EXIT_BUSY
        assert second_started == []

        os.kill(orphan_pid, signal.SIGKILL)
        orphan_pid = None
        deadline = time.monotonic() + 5
        while True:
            rc = walk_queue(
                [probe],
                tmp_path,
                parse_stop_at("2099-01-01T00:00:00Z"),
                tmp_path / "after-death-waiter.log",
                runner=lambda candidate, _prefix: second_started.append(candidate.id) or 0,
            )
            if rc != EXIT_BUSY:
                break
            if time.monotonic() >= deadline:
                raise AssertionError("orphaned generator did not release queue ownership")
            time.sleep(0.01)
        assert rc == EXIT_DONE
        assert second_started == [probe.id]
    finally:
        if process_started:
            if process.is_alive():
                process.kill()
            process.join(timeout=5)
        process_pid = process.pid
        if process_pid is not None:
            with suppress(ProcessLookupError):
                os.killpg(process_pid, signal.SIGKILL)
        if orphan_pid is not None:
            with suppress(ProcessLookupError):
                os.kill(orphan_pid, signal.SIGKILL)


def test_queue_ownership_is_released_when_the_runner_raises(tmp_path: Path) -> None:
    probe = Probe("n21-error", 21, "5", "auto", None, 5, 1200)

    def fail(_probe: Probe, _prefix: Path) -> int:
        raise RuntimeError("runner failed")

    try:
        walk_queue(
            [probe],
            tmp_path,
            parse_stop_at("2099-01-01T00:00:00Z"),
            tmp_path / "failed-waiter.log",
            runner=fail,
        )
    except RuntimeError as error:
        assert str(error) == "runner failed"
    else:
        raise AssertionError("runner failure did not escape")

    started: list[str] = []
    rc = walk_queue(
        [probe],
        tmp_path,
        parse_stop_at("2099-01-01T00:00:00Z"),
        tmp_path / "retry-waiter.log",
        runner=lambda candidate, _prefix: started.append(candidate.id) or 0,
    )
    assert rc == EXIT_DONE
    assert started == [probe.id]


def test_remain_and_command_use_the_project_interpreter() -> None:
    stop = parse_stop_at("2099-01-01T00:00:00Z")
    assert remain_seconds(stop, now=datetime(2098, 12, 31, 23, 59, 0, tzinfo=UTC)) == 60
    probe = Probe("n20", 20, "973/200", "34,46,56,64", "cases/n20.json", 7, 1200)
    command = colgen_command(probe, Path("/tmp/n20"))
    assert command[0] == sys.executable
    assert sys.version_info[:2] == (3, 14)
    assert command[1:3] == ["-m", "devtools.run_fractional_colgen"]
    assert "--n" in command
    assert "20" in command
    assert "--seed-certificate" in command


def test_session_140_queue_files_parse() -> None:
    """The live leftover and second-wave lists must stay walker-readable."""

    agenda = (
        Path(__file__).resolve().parent.parent
        / "campaign/series/series-000-smoke-and-calibration/results/agenda-038"
    )
    leftover = load_queue(agenda / "leftover-queue.yaml")
    second = load_queue(agenda / "second-wave-queue.yaml")
    assert leftover[0].n == 19
    assert leftover[0].side == "241/50"
    assert leftover[1].n == 17
    assert leftover[1].side == "461/100"
    assert leftover[2].n == 20
    assert leftover[2].side == "971/200"
    assert leftover[3].n == 12
    assert leftover[4].n == 18
    assert leftover[4].side == "1871/400"
    assert second[0].seed_certificate is None
    assert second[0].n == 32


def test_omitted_seed_certificate_drops_the_seed_flags(tmp_path: Path) -> None:
    path = tmp_path / "queue.yaml"
    path.write_text(
        """
probes:
  - id: n32-auto
    n: 32
    side: '29/5'
    grid_counts: auto
    seed_windows: 5
    deadline_seconds: 1200
""",
        encoding="utf-8",
    )
    probe = load_queue(path)[0]
    assert probe.seed_certificate is None
    command = colgen_command(probe, tmp_path / "n32-auto")
    assert "--seed-certificate" not in command
    assert "--seed-map" not in command
    assert command[command.index("--seed-windows") + 1] == "5"
