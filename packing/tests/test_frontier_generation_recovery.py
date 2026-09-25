"""Real tiny generation waves through the campaign controller and supervisor."""
from __future__ import annotations

import signal
from pathlib import Path

from devtools import run_n12_frontier as frontier
from devtools.frontier_io import read_json


def tiny_commands(monkeypatch):
    original = frontier.command

    def command(*args, **kwargs):
        argv = original(*args, **kwargs)
        for flag, value in (("--grid-counts", "3,5"), ("--direction-steps", "12"),
                            ("--support-cap", "4")):
            argv[argv.index(flag) + 1] = value
        index = argv.index("--seed-certificate")
        del argv[index:index + 2]
        return argv

    monkeypatch.setattr(frontier, "command", command)


def options(root: Path) -> list[str]:
    return ["--root", str(root), "--workers", "2", "--strategies", "baseline,centre",
            "--generation-trials", "2", "--screen-rounds", "1", "--normal-rounds", "2",
            "--deep-rounds", "3", "--max-rounds", "4", "--row-rounds", "2",
            "--max-row-rounds", "2", "--max-cycles", "2", "--stage-seconds", "30",
            "--no-progress-seconds", "0", "--min-free-mib", "0"]


def test_ctrl_c_drains_admitted_generation_cohort_and_starts_no_new_side(tmp_path, monkeypatch, capsys):
    tiny_commands(monkeypatch)
    original = frontier.run_child
    waves = []

    def stop_after_wave(args, output, env=None):
        code = original(args, output, env)
        if "devtools.frontier_generation_queue" in args:
            waves.append(str(output))
            signal.raise_signal(signal.SIGINT)
        return code

    monkeypatch.setattr(frontier, "run_child", stop_after_wave)
    assert frontier.main(options(tmp_path)) == 0
    state = read_json(tmp_path / "state.json")
    assert len(state["cycles"]) == 2
    assert {c["strategy"] for c in state["cycles"]} == {"baseline", "centre"}
    assert all(c["status"] == "UNRESOLVED" for c in state["cycles"])
    assert state["active_generation"] == []
    assert state["active"] is None
    assert state["generation_wave"] is None
    assert waves
    lines = capsys.readouterr().out.splitlines()
    assert all(line.startswith("[") and line[1:11].isdigit() for line in lines if line)
    assert any("[stop]" in line for line in lines)
    assert any("[generation-wave]" in line for line in lines)


def test_resume_adopts_finished_generation_wave_without_recomputing(tmp_path, monkeypatch):
    tiny_commands(monkeypatch)
    original = frontier.run_child
    injected = []

    def crash_after_wave(args, output, env=None):
        code = original(args, output, env)
        if "devtools.frontier_generation_queue" in args and not injected:
            injected.append(True)
            raise RuntimeError("injected crash between job receipt and wave adoption")
        return code

    monkeypatch.setattr(frontier, "run_child", crash_after_wave)
    assert frontier.main(options(tmp_path)) == 1
    checkpoint = read_json(tmp_path / "state.json")
    assert checkpoint["generation_wave"] is not None
    receipts = list(tmp_path.rglob("generation-receipt.json"))
    assert len(receipts) == 2
    before = {str(p): p.read_bytes() for p in receipts}
    monkeypatch.setattr(frontier, "run_child", original)
    assert frontier.main(["--root", str(tmp_path), "--resume", "--max-cycles", "2"]) == 0
    recovered = read_json(tmp_path / "state.json")
    assert len(recovered["cycles"]) == 2
    assert recovered["active_generation"] == []
    assert recovered["generation_wave"] is None
    assert all(c["status"] == "UNRESOLVED" for c in recovered["cycles"])
    assert {str(p): p.read_bytes() for p in receipts} == before
    assert recovered["verified_low"] == "99/25"
