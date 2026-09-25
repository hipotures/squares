"""Short contract tests for the persistent n=12 frontier driver."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest

from devtools import run_n12_frontier as frontier
from devtools.frontier_io import atomic_json, digest
from devtools.frontier_verify import verifier_fingerprint


def state(tmp_path: Path) -> dict:
    config = {
        "verified_low": "99/25",
        "search_high": "397/100",
        "seed_certificate": str(frontier.DEFAULT_SEED),
        "workers": 1,
        "budgets": [1, 2, 3, 4],
        "row_rounds": 60,
        "scale": frontier.DEFAULT_RATIONALISATION_SCALE,
        "max_scale": frontier.DEFAULT_MAX_RATIONALISATION_SCALE,
        "target_width": None,
        "max_cycles": None,
        "root": tmp_path,
    }
    return frontier.initial_state(config, frontier.DEFAULT_SEED)


def result(side: Fraction, *, objective: float = 12.5, mass: str = "25/2") -> dict:
    return {
        "settings": {
            "n": 12,
            "outer_side": str(side),
            "column_rounds": 1,
            "scale": frontier.DEFAULT_RATIONALISATION_SCALE,
        },
        "objective": objective,
        "converged": True,
        "stopped": "converged: every placement covers mass 1",
        "total_mass": mass,
        "atoms": 3,
        "seconds": 0.1,
        "rounds": [
            {"objective": objective, "averaged_depth": 1.0, "added": 0},
        ],
    }


def fake_child(args: list[str], output: Path, _env: dict | None = None) -> int:
    output.write_text("many detailed LP rounds stay here\n", encoding="utf-8")
    side = Fraction(args[args.index("--side") + 1])
    target = Path(args[args.index("--json") + 1])
    target.write_text(json.dumps(result(side)), encoding="utf-8")
    return 0


def test_exact_midpoint_and_unresolved_soft_ceiling(tmp_path: Path) -> None:
    saved = state(tmp_path)
    assert frontier.next_side(saved) == Fraction(793, 200)
    saved["unresolved"] = ["793/200"]
    assert frontier.soft_high(saved) == Fraction(793, 200)
    assert frontier.next_side(saved) == Fraction(1585, 400)


def test_frontier_keeps_bisecting_after_float_midpoint_collapses(tmp_path: Path) -> None:
    saved = state(tmp_path)
    # Production cycle 60 reached adjacent double values. The exact midpoint
    # rounds to the high endpoint in float64, but that must not stop the runner.
    low = Fraction(871246081204179, 219902325555200)
    high = Fraction(6969968649633433, 1759218604441600)
    midpoint = (low + high) / 2
    assert float(midpoint) == float(high)
    assert midpoint != high
    saved["verified_low"] = str(low)
    saved["search_high"] = str(high)
    saved["unresolved"] = [str(high)]
    assert frontier.next_side(saved) == midpoint
    assert frontier.display(low) != frontier.display(high)


def test_numeric_saturation_is_detected_at_adjacent_float64_sides(tmp_path: Path) -> None:
    saved = state(tmp_path)
    low = Fraction(871246081204179, 219902325555200)
    high = Fraction(6969968649633433, 1759218604441600)
    saved["verified_low"] = str(low)
    saved["search_high"] = str(high)
    saved["unresolved"] = [str(high)]
    assert frontier.numeric_search_saturated(saved) is True


def test_scale_limited_unresolved_is_retried_before_bisection(tmp_path: Path) -> None:
    saved = state(tmp_path)
    side = Fraction(793, 200)
    candidate = tmp_path / "coarse-candidate.json"
    candidate.write_text("{}", encoding="utf-8")
    coarse = result(side, objective=11.9962, mass="1200067/100000")
    coarse["settings"]["scale"] = frontier.LEGACY_RATIONALISATION_SCALE
    saved["unresolved"] = [str(side)]
    saved["cycles"].append(
        {
            "side": str(side),
            "status": "UNRESOLVED",
            "seed_verified_low": saved["verified_low"],
            "stages": [
                {
                    "status": "complete",
                    "candidate_unverified": str(candidate),
                    "result": coarse,
                }
            ],
        }
    )
    assert frontier.next_side(saved) == side
    seed, label = frontier.seed_for(saved, side)
    assert seed == candidate
    assert "scale200000" in label

    coarse["objective"] = 12.001
    assert frontier.next_side(saved) == Fraction(1585, 400)

    coarse["objective"] = 11.9962
    coarse["settings"]["scale"] = frontier.DEFAULT_MAX_RATIONALISATION_SCALE
    assert frontier.next_side(saved) == Fraction(1585, 400)


def test_better_verified_seed_alone_does_not_repeat_unresolved_side(tmp_path: Path) -> None:
    saved = state(tmp_path)
    side = Fraction(793, 200)
    settled = result(side, objective=12.01, mass="1201/100")
    saved["unresolved"] = [str(side)]
    saved["cycles"].append(
        {
            "side": str(side),
            "status": "UNRESOLVED",
            "seed_verified_low": saved["verified_low"],
            "stages": [{"status": "complete", "result": settled}],
        }
    )
    saved["verified_low"] = "3961/1000"
    assert frontier.next_side(saved) == (
        Fraction(3961, 1000) + side
    ) / 2


def test_rationalisation_scale_refines_only_when_rounding_is_blocker() -> None:
    side = Fraction(793, 200)
    rounded = result(side, objective=11.9994, mass="19200023/1600000")
    assert frontier.next_refinement_scale(rounded, 1_600_000, 25_600_000) == 3_200_000
    assert frontier.next_refinement_scale(rounded, 25_600_000, 25_600_000) is None

    lp_high = result(side, objective=12.0001, mass="12001/1000")
    assert frontier.next_refinement_scale(lp_high, 1_600_000, 25_600_000) is None

    already_below = result(side, objective=11.9994, mass="11999/1000")
    assert frontier.next_refinement_scale(already_below, 1_600_000, 25_600_000) is None


def test_repair_candidate_selection_prefers_highest_untried_side(
    tmp_path: Path,
) -> None:
    saved = state(tmp_path)
    low = Fraction(saved["verified_low"])
    candidates = []
    for offset, verifier in ((1, "quick-rejected"), (2, "full-rejected")):
        side = low + Fraction(offset, 10000)
        directory = tmp_path / f"candidate-{offset}"
        directory.mkdir()
        candidate = directory / "candidate.unverified.json"
        candidate.write_text("{}", encoding="utf-8")
        candidates.append((side, candidate))
        saved["cycles"].append(
            {
                "side": str(side),
                "status": "UNRESOLVED",
                "stages": [
                    {
                        "name": "screen",
                        "verifier": verifier,
                        "candidate_unverified": str(candidate),
                        "result": {"total_mass": "11999/1000"},
                    }
                ],
            }
        )
    selected = frontier.select_repair_candidate(saved)
    assert selected is not None
    assert Fraction(selected["side"]) == candidates[-1][0]
    saved["repair_attempts"].append(
        {"candidate": str(candidates[-1][1]), "status": "REJECTED"}
    )
    assert Fraction(frontier.select_repair_candidate(saved)["side"]) == candidates[0][0]


def test_uniform_weight_repair_uses_only_part_of_strict_mass_slack(tmp_path: Path) -> None:
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps(
            {
                "total_mass": "11",
                "least_cell_mass": "1",
                "atoms": [["0", "0", "5"], ["1", "1", "6"]],
            }
        ),
        encoding="utf-8",
    )
    destination = tmp_path / "boosted.json"
    total = frontier.write_boosted_candidate(
        source, destination, Fraction(3, 4)
    )
    record = json.loads(destination.read_text(encoding="utf-8"))
    assert total == Fraction(47, 4)
    assert Fraction(record["total_mass"]) == Fraction(47, 4)
    assert sum(Fraction(atom[2]) for atom in record["atoms"]) == Fraction(47, 4)
    assert record["least_cell_mass"] is None
    assert total < 12


def fake_proof(path: Path, side: str) -> Path:
    """A structural receipt double for controller tests, not a mathematical proof."""
    atomic_json(path, {"n": 12, "outer_side": side, "total_mass": "119/10",
                       "atoms": [["1", "1", "119/10"]]})
    atomic_json(path.parent / "verification.json", {
        "status": "VERIFIED", "category": "full-retainable", "side": side,
        "verified_sha256": digest(path), "verified_candidate": str(path),
        "finished": True,
    })
    return path


def test_transitions_and_full_gate_invariant(tmp_path: Path) -> None:
    saved = state(tmp_path)
    with pytest.raises(ValueError, match="full exact gate"):
        frontier.apply_result(saved, {"side": "793/200", "status": "VERIFIED"})
    frontier.apply_result(saved, {"side": "793/200", "status": "UNRESOLVED"})
    assert saved["unresolved"] == ["793/200"]
    frontier.apply_result(saved, {"side": "1585/400", "status": "SEARCH_FAILED"})
    assert saved["search_high"] == "317/80"
    assert saved["search_high_kind"] == "SEARCH_FAILED"
    assert frontier.active_unresolved(saved) == []
    frontier.apply_result(
        saved,
        {
            "side": "3961/1000",
            "status": "VERIFIED",
            "verifier": "full-retainable",
            "verified_candidate": str(fake_proof(tmp_path / "proof.json", "3961/1000")),
        },
    )
    assert saved["verified_low"] == "3961/1000"
    assert saved["unresolved"] == ["793/200"]


def test_adaptive_policy_uses_multiple_signals() -> None:
    budgets = [1, 2, 3, 4]
    stalled = result(Fraction(793, 200))
    assert frontier.decide_stage(stalled, 0, budgets, nearby=False)[0] == "SEARCH_FAILED"
    close = result(Fraction(793, 200), objective=12.004, mass="1201/100")
    assert frontier.decide_stage(close, 0, budgets, nearby=False)[0] == "ESCALATE"
    assert frontier.decide_stage(close, 3, budgets, nearby=False)[0] == "UNRESOLVED"
    improving = result(Fraction(793, 200), objective=12.1)
    improving["rounds"] = [
        {"objective": 12.2, "averaged_depth": 1.01, "added": 2},
        {"objective": 12.1, "averaged_depth": 1.01, "added": 1},
    ]
    assert frontier.decide_stage(improving, 0, budgets, nearby=False)[0] == "ESCALATE"


def test_incomplete_inner_rows_never_shrink_search_frontier() -> None:
    incomplete = result(Fraction(793, 200))
    incomplete.update(
        {"converged": False, "stopped": "round limit 60 reached", "total_mass": None}
    )
    for stage_index in range(4):
        decision, reason = frontier.decide_stage(
            incomplete, stage_index, [8, 20, 40, 60], nearby=False
        )
        assert decision == "UNRESOLVED"
        assert "row generation did not converge" in reason


def test_atomic_state_roundtrip_and_validation(tmp_path: Path) -> None:
    saved = state(tmp_path)
    frontier.save_state(tmp_path, saved)
    assert frontier.load_state(tmp_path, saved["config"])["verified_low"] == "99/25"
    assert frontier.load_state(tmp_path, {**saved["config"], "max_cycles": 3})["n"] == 12
    assert not list(tmp_path.glob("*.tmp"))
    with pytest.raises(ValueError, match="settings differ"):
        frontier.load_state(tmp_path, {"workers": 8})

    legacy = state(tmp_path)
    legacy["config"].pop("scale")
    legacy["config"].pop("max_scale")
    frontier.save_state(tmp_path, legacy)
    upgraded = frontier.load_state(
        tmp_path,
        {
            **legacy["config"],
            "scale": frontier.DEFAULT_RATIONALISATION_SCALE,
            "max_scale": frontier.DEFAULT_MAX_RATIONALISATION_SCALE,
        },
    )
    assert upgraded["config"]["scale"] == frontier.DEFAULT_RATIONALISATION_SCALE
    assert upgraded["config"]["max_scale"] == frontier.DEFAULT_MAX_RATIONALISATION_SCALE
    assert upgraded["migrations"][-2]["from"] == frontier.LEGACY_RATIONALISATION_SCALE
    assert upgraded["migrations"][-2]["to"] == frontier.DEFAULT_RATIONALISATION_SCALE
    assert upgraded["migrations"][-1]["kind"] == "max-rationalisation-scale"

    saved = state(tmp_path)
    saved["schema"] = 1
    frontier.save_state(tmp_path, saved)
    with pytest.raises(ValueError, match="incompatible frontier state schema"):
        frontier.load_state(tmp_path)


def test_import_prior_search_result(tmp_path: Path) -> None:
    saved = state(tmp_path)
    source = tmp_path / "prior.json"
    source.write_text(json.dumps(result(Fraction(397, 100))), encoding="utf-8")
    frontier.import_result(tmp_path, saved, source)
    assert saved["search_high_kind"] == "SEARCH_FAILED"
    assert saved["cycles"][0]["status"] == "SEARCH_FAILED"
    assert (tmp_path / "L-397-100/cycle-0001/import/result.json").exists()


def test_resume_after_completed_stage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    saved = state(tmp_path)
    side = frontier.next_side(saved)
    assert side is not None
    saved["cycles"].append(
        {
            "side": str(side),
            "status": "RUNNING",
            "stages": [
                {
                    "status": "complete",
                    "decision": "SEARCH_FAILED",
                    "reason": "stalled",
                    "name": "screen",
                    "budget": 1,
                    "seed_label": "verified",
                }
            ],
        }
    )
    saved["active"] = 0
    monkeypatch.setattr(frontier, "run_child", lambda *_args: pytest.fail("reran stage"))
    frontier.run_cycle(tmp_path, saved)
    assert saved["active"] is None
    assert saved["search_high"] == str(side)


def test_resume_incomplete_stage_with_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = state(tmp_path)
    side = frontier.next_side(saved)
    assert side is not None
    directory = tmp_path / "old-stage"
    directory.mkdir()
    (directory / "result.json").write_text(json.dumps(result(side)), encoding="utf-8")
    saved["cycles"].append(
        {
            "side": str(side),
            "status": "RUNNING",
            "seed_verified_low": saved["verified_low"],
            "stages": [
                {
                    "status": "running",
                    "directory": str(directory),
                    "name": "screen",
                    "budget": 1,
                    "seed_label": "verified",
                }
            ],
        }
    )
    saved["active"] = 0
    monkeypatch.setattr(frontier, "run_child", lambda *_args: pytest.fail("reran stage"))
    frontier.run_cycle(tmp_path, saved)
    assert saved["cycles"][0]["status"] == "SEARCH_FAILED"
    assert (directory / "result.json").exists()


def test_resume_incomplete_stage_without_result_keeps_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    saved = state(tmp_path)
    side = frontier.next_side(saved)
    assert side is not None
    directory = tmp_path / "old-stage"
    directory.mkdir()
    (directory / "stdout.log").write_text("partial evidence", encoding="utf-8")
    saved["cycles"].append(
        {
            "side": str(side),
            "status": "RUNNING",
            "seed_verified_low": saved["verified_low"],
            "stages": [
                {
                    "status": "running",
                    "directory": str(directory),
                    "name": "screen",
                    "budget": 1,
                    "seed_label": "verified",
                }
            ],
        }
    )
    saved["active"] = 0
    monkeypatch.setattr(frontier, "run_child", fake_child)
    frontier.run_cycle(tmp_path, saved)
    assert saved["cycles"][0]["stages"][0]["status"] == "interrupted"
    assert (directory / "stdout.log").read_text(encoding="utf-8") == "partial evidence"
    assert saved["cycles"][0]["status"] == "SEARCH_FAILED"


def test_stop_finishes_cycle_and_console_is_concise(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def stop_after_stage(args: list[str], output: Path, env: dict | None = None) -> int:
        signal.raise_signal(signal.SIGINT)
        return fake_child(args, output, env)

    monkeypatch.setattr(frontier, "run_child", stop_after_stage)
    assert (
        frontier.main(
            [
                "--root",
                str(tmp_path),
                "--generation-trials",
                "1",
                "--screen-rounds",
                "1",
                "--normal-rounds",
                "2",
                "--deep-rounds",
                "3",
                "--max-rounds",
                "4",
            ]
        )
        == 0
    )
    saved = frontier.load_state(tmp_path)
    assert len(saved["cycles"]) == 1
    assert saved["cycles"][0]["status"] == "SEARCH_FAILED"
    output = capsys.readouterr().out
    assert "[stop]" in output
    assert "many detailed LP rounds" not in output
    assert "cycles completed: 1" in output
    assert "next suggested L:" in output
    assert (tmp_path / "summary.csv").exists()
    assert (tmp_path / "report.md").exists()


def test_cli_resume_keeps_completed_frontier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(frontier, "run_child", fake_child)
    options = [
        "--root",
        str(tmp_path),
        "--screen-rounds",
        "1",
        "--normal-rounds",
        "2",
        "--deep-rounds",
        "3",
        "--max-rounds",
        "4",
        "--max-cycles",
        "1",
    ]
    assert frontier.main(options) == 0
    first = frontier.load_state(tmp_path)
    assert len(first["cycles"]) == 1
    monkeypatch.setattr(
        frontier, "run_child", lambda *_args: pytest.fail("unexpected new stage")
    )
    assert frontier.main([*options, "--resume"]) == 0
    assert frontier.load_state(tmp_path)["cycles"] == first["cycles"]
    monkeypatch.setattr(frontier, "run_child", fake_child)
    assert frontier.main([*options[:-1], "2", "--resume"]) == 0
    assert len(frontier.load_state(tmp_path)["cycles"]) == 2


def test_unverified_candidate_is_only_search_seed(tmp_path: Path) -> None:
    saved = state(tmp_path)
    candidate = tmp_path / "candidate.unverified.json"
    candidate.write_text("{}", encoding="utf-8")
    saved["cycles"].append(
        {
            "side": "793/200",
            "status": "UNRESOLVED",
            "stages": [{"candidate_unverified": str(candidate)}],
        }
    )
    path, label = frontier.seed_for(saved, Fraction(1587, 400))
    assert path == candidate
    assert label.startswith("search-seed-only")
    assert saved["verified_certificate"] == str(frontier.DEFAULT_SEED)


def test_full_gate_output_and_target_side_required(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    candidate = tmp_path / "candidate.unverified.json"
    candidate.write_text(json.dumps({"n": 12, "outer_side": "793/200", "total_mass": "119/10"}))

    def inconclusive(_args: list[str], output: Path) -> int:
        output.write_text("RETAINABLE: both routes accept (unbound text is not a receipt)\n")
        return 0

    monkeypatch.setattr(frontier, "run_child", inconclusive)
    assert frontier.verify_candidate(tmp_path, candidate, Fraction(793, 200))[0].startswith("verification-error")
    assert not list(tmp_path.rglob("candidate.verified*.json"))
    assert frontier.verify_candidate(tmp_path, candidate, Fraction(397, 100))[0] == "candidate-side-mismatch"

    def retained(args: list[str], output: Path) -> int:
        report = Path(args[args.index("--report") + 1])
        proof = fake_proof(report.parent / "candidate.verified.json", "793/200")
        atomic_json(report, {
            "status": "VERIFIED", "category": "full-retainable", "side": "793/200",
            "source_sha256": digest(candidate), "verifier_sha256": verifier_fingerprint(),
            "verified_candidate": str(proof), "verified_sha256": digest(proof),
        })
        output.write_text("structured full gate receipt available\n")
        return 0

    monkeypatch.setattr(frontier, "run_child", retained)
    status, verified = frontier.verify_candidate(tmp_path, candidate, Fraction(793, 200))
    assert status == "full-retainable"
    assert verified is not None and Path(verified).exists()


def test_significant_output_is_blue_only_on_terminal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    frontier.emit(tmp_path, "[result] significant", significant=True)
    terminal = capsys.readouterr().out
    assert frontier.BLUE in terminal
    assert frontier.RESET in terminal
    assert "\033[" not in (tmp_path / "runner.log").read_text(encoding="utf-8")


def test_lock_rejects_second_runner(tmp_path: Path) -> None:
    with (
        frontier.locked(tmp_path),
        pytest.raises(RuntimeError, match="another frontier runner"),
        frontier.locked(tmp_path),
    ):
        pass


def test_resume_refuses_live_orphan_child(tmp_path: Path) -> None:
    ticks = frontier.process_start_ticks(os.getpid())
    if ticks is None:
        pytest.skip("process start identity requires Linux procfs")
    saved = state(tmp_path)
    side = frontier.next_side(saved)
    assert side is not None
    directory = tmp_path / "running-stage"
    directory.mkdir()
    (directory / "stdout.log.child.json").write_text(
        json.dumps({"pid": os.getpid(), "start_ticks": ticks}), encoding="utf-8"
    )
    saved["cycles"].append(
        {"side": str(side), "status": "RUNNING", "stages": [{"directory": str(directory)}]}
    )
    saved["active"] = 0
    with pytest.raises(RuntimeError, match="prior child pid"):
        frontier.run_cycle(tmp_path, saved)
    assert (directory / "stdout.log.child.json").exists()


def test_heartbeat_reads_flushed_progress(tmp_path: Path) -> None:
    stage = tmp_path / "L-793-200/cycle-0001/deep-03"
    stage.mkdir(parents=True)
    (stage / "column.log").write_text(
        "round 22: objective=12.01\nround 23: rows=100 objective=12.00600 | adding columns\n",
        encoding="utf-8",
    )
    (stage / "rows.log").write_text(
        "   lp rows added violated support objective sep_s lp_s\n"
        "    7  100  4  5  80  12.004830  1.0  0.5\n",
        encoding="utf-8",
    )
    command = frontier.command(Fraction(793, 200), 40, frontier.DEFAULT_SEED, stage, 60)
    assert command[command.index("--scale") + 1] == str(
        frontier.DEFAULT_RATIONALISATION_SCALE
    )
    assert frontier.heartbeat_message(command, stage / "stdout.log", 900) == (
        "[running] L=3.965000000 stage=deep(40) elapsed=15m "
        "last-round=23 lp-round=7 objective=12.00483"
    )


def test_timeout_emits_heartbeat_to_terminal_and_runner_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    stage = tmp_path / "L-793-200/cycle-0001/deep-03"
    stage.mkdir(parents=True)
    (tmp_path / "state.json").write_text("{}")
    (stage / "column.log").write_text("round 23: objective=12.004830\n")

    def run(_args, _output, **kwargs):
        kwargs["heartbeat"](900)
        return 0

    monkeypatch.setattr(frontier.frontier_runtime, "run", run)
    args = frontier.command(Fraction(793, 200), 40, frontier.DEFAULT_SEED, stage, 60)
    assert frontier.run_child(args, stage / "stdout.log") == 0
    assert "[running] L=3.965000000 stage=deep(40)" in capsys.readouterr().out
    assert "last-round=23" in (tmp_path / "runner.log").read_text()


def test_real_generator_one_cycle_and_resume(tmp_path: Path) -> None:
    """Exercise the real child CLI with a deliberately incomplete inner row budget."""
    packing = Path(__file__).resolve().parents[1]
    args = [
        sys.executable,
        "-m",
        "devtools.run_n12_frontier",
        "--root",
        str(tmp_path),
        "--search-high",
        "397/100",
        "--screen-rounds",
        "1",
        "--normal-rounds",
        "2",
        "--deep-rounds",
        "3",
        "--max-rounds",
        "4",
        "--row-rounds",
        "1",
        "--max-row-rounds",
        "1",
        "--max-cycles",
        "1",
    ]
    env = {**os.environ, "PACK_JOBS": "2"}
    first = subprocess.run(
        args, cwd=packing, env=env, capture_output=True, text=True, check=True
    )
    assert "UNRESOLVED" in first.stdout
    saved = frontier.load_state(tmp_path)
    assert len(saved["cycles"]) == 1
    assert saved["cycles"][0]["status"] == "UNRESOLVED"
    assert saved["search_high_kind"] == "CONFIGURED_SEARCH_ENDPOINT"
    stage = tmp_path / "L-793-200/cycle-0001/screen-01"
    for name in ("result.json", "stdout.log", "column.log", "rows.log", "metadata.json"):
        assert (stage / name).is_file()
    metadata = json.loads((stage / "metadata.json").read_text(encoding="utf-8"))
    progress = frontier.heartbeat_message(metadata["command"], stage / "stdout.log", 300)
    assert "L=3.965000000 stage=screen(1) elapsed=5m last-round=0" in progress
    assert "objective=unknown" not in progress
    assert not (stage / "candidate.unverified.json").exists()
    assert frontier.load_state(tmp_path)["cycles"][0]["column_rounds_completed"] == 1
    resumed = subprocess.run(
        [*args, "--resume"],
        cwd=packing,
        env=env,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "cycles completed: 1" in resumed.stdout
    assert len(frontier.load_state(tmp_path)["cycles"]) == 1


def test_real_generator_freezes_a_candidate(tmp_path: Path) -> None:
    """A tiny n=1 run checks the generator's real freeze/result/log contract."""
    packing = Path(__file__).resolve().parents[1]
    frozen = tmp_path / "candidate.unverified.json"
    result_path = tmp_path / "result.json"
    args = [
        sys.executable,
        "-m",
        "devtools.run_fractional_colgen",
        "--n",
        "1",
        "--side",
        "2",
        "--shrink",
        "9977/10000",
        "--direction-steps",
        "8",
        "--grid-counts",
        "2,3",
        "--column-rounds",
        "1",
        "--max-rounds",
        "10",
        "--scale",
        "1000",
        "--freeze",
        str(frozen),
        "--json",
        str(result_path),
        "--log",
        str(tmp_path / "column.log"),
        "--row-log",
        str(tmp_path / "rows.log"),
    ]
    subprocess.run(args, cwd=packing, capture_output=True, text=True, check=True)
    assert frozen.is_file()
    assert json.loads(result_path.read_text(encoding="utf-8"))["converged"] is True
    assert (tmp_path / "column.log").is_file()
    assert (tmp_path / "rows.log").is_file()



def test_exact_only_verified_refinement_uses_quiet_banner(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    saved = state(tmp_path)
    previous = Fraction.from_float(3.961968473978136)
    side = previous + Fraction(1, 10**20)
    assert side > previous
    assert float(side) == float(previous)
    saved["verified_low"] = str(side)
    saved["discoveries"] = [
        {
            "id": "micro-proof",
            "at": frontier.stamp(),
            "side": str(side),
            "previous": str(previous),
            "improvement": str(side - previous),
            "mass": "11999/1000",
            "candidate": str(tmp_path / "candidate.verified.json"),
            "sha256": "abc",
            "mechanism": "search",
            "float64_distinct": False,
            "gate_receipt": str(tmp_path / "verification.json"),
        }
    ]
    frontier.save_state(tmp_path, saved)
    frontier.publish_findings(tmp_path, saved)
    output = capsys.readouterr().out
    assert "VERIFIED EXACT REFINEMENT" in output
    assert "unchanged at float64 search resolution" in output
    assert "VERIFIED LOWER BOUND IMPROVEMENT" not in output
    ledger = json.loads((tmp_path / "findings.json").read_text())
    assert ledger["schema"] == 2


def test_notable_search_improvement_is_separate_nonproof_event(tmp_path: Path) -> None:
    saved = state(tmp_path)
    side = Fraction(3169574779182501, 800000000000000)
    prior_stage = {
        "name": "screen",
        "status": "complete",
        "work_kind": "generation",
        "directory": str(tmp_path / "prior"),
        "result": {"converged": True, "objective": 11.999660486864869},
    }
    prior_cycle = {
        "side": str(side),
        "strategy": "centre",
        "search_revision": 0,
        "stages": [prior_stage],
    }
    current_stage = {
        "name": "screen",
        "status": "complete",
        "work_kind": "generation",
        "directory": str(tmp_path / "windows"),
        "result": {"converged": True, "objective": 11.99571691213635},
    }
    current_cycle = {
        "side": str(side),
        "strategy": "windows",
        "search_revision": 0,
        "stages": [current_stage],
    }
    saved["cycles"] = [prior_cycle, current_cycle]
    event = frontier.record_notable_search(saved, current_cycle, current_stage)
    assert event is not None
    assert event["proof"] is False
    assert event["strategy"] == "windows"
    assert event["previous_best_strategy"] == "centre"
    assert event["gain"] > frontier.NOTABLE_OBJECTIVE_GAIN
    assert saved["search_findings"] == [event]
