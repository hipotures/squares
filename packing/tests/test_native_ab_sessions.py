"""Real kernel/generator controls plus session accounting and process tests."""

from __future__ import annotations

import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from devtools.native_ab import PACKING, finish_report, terminal_bell
from devtools.native_ab_replay import seal_corpus, validate_corpus
from sqpack.fractional import native_ab_metrics as metrics
from sqpack.fractional import native_ab_runtime as runtime


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    for name in ("PACK_NATIVE_STATS", "PACK_NATIVE_CAPTURE", "PACK_NATIVE_SESSION"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("PACK_NATIVE_KERNELS", "none")


def test_cumulative_snapshots_are_not_double_counted(tmp_path, monkeypatch):
    stats = tmp_path / "stats"
    monkeypatch.setenv("PACK_NATIVE_STATS", str(stats))
    monkeypatch.setenv("PACK_NATIVE_SESSION", "test-one")
    metrics.record("direction", "none", 100, 1.0, 0.5)
    metrics.flush(force=True)
    assert metrics.aggregate(stats)["direction/none"]["calls"] == 1
    metrics.record("direction", "none", 200, 2.0, 1.0)
    metrics.flush(force=True)
    first = metrics.aggregate(stats)
    assert first == metrics.aggregate(stats)
    assert first["direction/none"]["calls"] == 2
    assert first["direction/none"]["units"] == 300
    # A new session in the same process must not inherit previous counters.
    other = tmp_path / "other"
    monkeypatch.setenv("PACK_NATIVE_STATS", str(other))
    monkeypatch.setenv("PACK_NATIVE_SESSION", "test-two")
    metrics.record("direction", "none", 17, 1.0, 1.0)
    metrics.flush(force=True)
    assert metrics.aggregate(other)["direction/none"]["units"] == 17


def test_capture_is_lazy_and_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_NATIVE_CAPTURE", str(tmp_path))
    called = []

    def payload():
        called.append(1)
        return {"x": 1}, None

    for _ in range(5):
        metrics.capture("exact", "same-bucket", payload)
    assert len(called) == 1
    for index in range(100):
        metrics.capture("exact", str(index), payload)
    assert len(list(tmp_path.glob("exact-*.json"))) <= 16


def make_real_corpus(path: Path, monkeypatch):
    from cases.n12_fractional_certificate.replay import FIRST_RUNG_PATH, load
    from sqpack.fractional.generate import placement_cells
    from sqpack.fractional.model import rotation_from_half_tangent
    from sqpack.fractional.colgen import Square, _arrangement_lines, _vertices
    from sqpack.fractional.exact_slabs import PreparedDepth

    certificate = load(FIRST_RUNG_PATH)
    points = np.array([[float(a.x), float(a.y)] for a in certificate.atoms])
    weights = np.array([float(a.weight) for a in certificate.atoms])
    monkeypatch.setenv("PACK_NATIVE_CAPTURE", str(path))
    for tangent in (Fraction(1, 8), Fraction(1, 5)):
        direction = rotation_from_half_tangent(str(tangent), tangent)
        placement_cells(
            points,
            weights,
            direction,
            float(certificate.outer_side),
            float(certificate.square_side),
            keep=3,
        )
    # Capture actual geometry built by the generator, not a timing sleep workload.
    square = Square(
        Fraction(1),
        Fraction(0),
        Fraction(0),
        Fraction(1),
        Fraction(0),
        Fraction(0),
        Fraction(1, 2),
    )
    weighted = ((square, Fraction(1, 3)),)
    _vertices(_arrangement_lines(weighted, Fraction(4)), Fraction(4))
    prepared = PreparedDepth(weighted)
    prepared.at(Fraction(1, 4), Fraction(1, 3))
    prepared.reduced_cost(((Fraction(1), Fraction(1)),), Fraction(4))
    monkeypatch.delenv("PACK_NATIVE_CAPTURE")
    return seal_corpus(path)


@pytest.mark.parametrize("workers", [1, 2, 4])
def test_real_replay_uses_same_sealed_inputs_and_native_profiles(
    tmp_path, monkeypatch, workers
):
    corpus = tmp_path / "corpus"
    manifest = make_real_corpus(corpus, monkeypatch)
    assert manifest["id"] == validate_corpus(corpus)["id"]
    output = tmp_path / "runs"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "devtools.native_ab",
            "replay",
            "--corpus",
            str(corpus),
            "--output",
            str(output),
            "--native",
            "all",
            "--workers",
            str(workers),
            "--minutes",
            "0",
            "--rounds",
            "2",
        ],
        cwd=PACKING,
        capture_output=True,
        text=True,
        timeout=90,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(next(output.glob("*/performance.json")).read_text())
    assert report["session"]["corpus_id"] == manifest["id"]
    assert report["session"]["completed_replays"] == 2 * len(manifest["items"])
    assert report["session"]["matched_output_checks"] == report["session"]["completed_replays"]
    assert report["metrics"]["compact/c"]["units_per_wall_second"] > 0
    assert report["completed"] is True
    # Sealed corruption must be refused before replaying any work.
    first = corpus / manifest["items"][0]["file"]
    first.write_text(first.read_text() + " ")
    with pytest.raises(ValueError, match="changed"):
        validate_corpus(corpus)


def test_report_has_throughput_and_separate_drain(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_NATIVE_STATS", str(tmp_path / "processes"))
    metrics.record("direction", "none", 100, 2, 1)
    metrics.flush(force=True)
    manifest = {"kind": "test", "label": "accounting", "workers": 2, "native": {"kernels": []}}
    report = finish_report(tmp_path, manifest, 10, exit_code=0, drain=2)
    assert report["metrics"]["direction/none"]["calls_per_wall_second"] == 0.1
    assert report["metrics"]["direction/none"]["units_per_wall_second"] == 10
    assert report["metrics"]["direction/none"]["units_per_kernel_cpu_second"] == 100
    assert report["drain_seconds"] == 2


def test_report_uses_stop_window_for_primary_throughput(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_NATIVE_STATS", str(tmp_path / "processes"))
    metrics.record("direction", "none", 100, 2, 1)
    metrics.flush(force=True)
    first_counts = metrics.aggregate(tmp_path / "processes")
    metrics.record("direction", "none", 300, 3, 2)
    metrics.flush(force=True)
    manifest = {"kind": "test", "label": "window", "workers": 2, "native": {"kernels": []}}
    first_window = {
        "wall_seconds": 5.0,
        "metrics": first_counts,
        "campaign_delta": {
            "completed_stages": 4,
            "bound_improvements": 1,
            "initial_verified": "1",
            "final_verified": "2",
        },
    }

    report = finish_report(
        tmp_path,
        manifest,
        10.0,
        exit_code=0,
        drain=5.0,
        campaign_delta={
            "completed_stages": 9,
            "bound_improvements": 2,
            "initial_verified": "1",
            "final_verified": "3",
        },
        first_window=first_window,
    )

    assert report["measurement_window_seconds"] == 5.0
    assert report["measurement_metrics"]["direction/none"]["calls_per_wall_second"] == 0.2
    assert report["measurement_metrics"]["direction/none"]["units_per_wall_second"] == 20
    assert report["metrics"]["direction/none"]["calls_per_wall_second"] == 0.2
    text = (tmp_path / "performance.txt").read_text()
    assert "measurement=5.000s session=10.000s drain=5.000s" in text
    assert "measurement completed stages/hour=2880.000" in text
    assert "final incl-drain completed stages=9 verified improvements=2" in text


def test_real_generator_preserves_mathematical_output(monkeypatch, tmp_path):
    from devtools.run_fractional_colgen import RunSettings, run

    settings = RunSettings(
        n=12,
        outer_side=Fraction(198111, 50000),
        square_side=Fraction(9977, 10000),
        grid_counts=(5, 7, 9),
        inset=Fraction(1, 2),
        angle_limit=Fraction(207107, 500000),
        direction_steps=12,
        scale=1600000,
        column_rounds=2,
        max_rounds=60,
        rows_per_direction=3,
        support_cap=8,
    )
    monkeypatch.setenv("PACK_JOBS", "2")
    results = []
    for mode in ("none", "all"):
        monkeypatch.setenv("PACK_NATIVE_KERNELS", mode)
        runtime.preflight()
        directory = tmp_path / mode
        directory.mkdir()
        frozen = directory / "candidate.json"
        result = run(settings, log_path=directory / "column.log", freeze=frozen)
        results.append((result, frozen.read_bytes() if frozen.exists() else None))
    for key in ("objective", "least_covered", "total_mass", "atoms", "stopped", "converged"):
        assert results[0][0][key] == results[1][0][key]
    assert results[0][1] is not None
    assert results[0][1] == results[1][1]

    def rounds(result):
        return [{k: v for k, v in row.items() if k != "seconds"} for row in result["rounds"]]

    assert rounds(results[0][0]) == rounds(results[1][0])


def test_real_campaign_graceful_budget_and_resume(tmp_path):
    root = tmp_path / "campaign"
    common = [
        sys.executable,
        "-m",
        "devtools.native_ab",
        "campaign",
        "--root",
        str(root),
        "--workers",
        "2",
        "--generation-trials",
        "1",
        "--minutes",
        "0.02",
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
    for mode, extra in (("none", []), ("compact", ["--resume"])):
        result = subprocess.run(
            [*common, "--native", mode, *extra],
            cwd=PACKING,
            capture_output=True,
            text=True,
            timeout=120,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "NATIVE A/B THROUGHPUT SUMMARY" in result.stdout
    assert (root / "state.json").exists()
    sessions = list(tmp_path.glob("campaign-native-runs/*/performance.json"))
    assert len(sessions) == 2
    reports = [json.loads(p.read_text()) for p in sessions]
    assert {tuple(r["session"]["native"]["kernels"]) for r in reports} == {(), ("compact",)}



def test_terminal_bell_marks_success_and_error(capsys):
    terminal_bell("finished")
    success = capsys.readouterr()
    assert success.err == "\a[native-ab] finished\n"

    terminal_bell("failed", error=True)
    failure = capsys.readouterr()
    assert failure.err == "\a\a[native-ab] failed\n"
