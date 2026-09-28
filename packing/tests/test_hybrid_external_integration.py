"""Opt-in real external-checker integration on tiny, non-record fixtures."""
import json
import os
from fractions import Fraction

import pytest

from devtools.frontier_hybrid_bin_gate import checked_receipt, decide
from devtools.frontier_hybrid_external import EXTERNAL, check_cover
from devtools.frontier_hybrid_worker import generate
from devtools.frontier_io import digest

pytestmark = pytest.mark.skipif(
    os.environ.get("HYBRID_EXTERNAL_TESTS") != "1",
    reason="run prepare-external and set HYBRID_EXTERNAL_TESTS=1 for the pinned real checkers",
)


def test_real_external_three_check_gate_accepts_and_rejects(tmp_path):
    good = tmp_path / "good.txt"
    good.write_text("3 2\n4\n100\n1\n3 3 100\n")
    accepted = check_cover(good, EXTERNAL, tmp_path / "good-gate", Fraction(3, 2),
                           net=12, workers=1, seconds=30)
    assert accepted["status"] == "VERIFIED"
    assert len(accepted["checks"]) == 3
    bad = tmp_path / "bad.txt"
    bad.write_text("3 2\n4\n100\n1\n3 3 50\n")
    rejected = check_cover(bad, EXTERNAL, tmp_path / "bad-gate", Fraction(3, 2),
                           net=12, workers=1, seconds=30)
    assert rejected["status"] == "REJECTED"


def test_real_bin_generation_and_independent_gate(tmp_path, monkeypatch):
    monkeypatch.setenv("PACK_JOBS", "1")
    source = tmp_path / "seed.json"
    source.write_text(json.dumps({"outer_side": "3/2", "atoms": [["3/4", "3/4", "1"]]}))
    directory = tmp_path / "job"
    directory.mkdir()
    config = {
        "mode": "bins", "seed_map": "scale", "stage_seconds": 30, "workers": 1,
        "scale": 10000000, "bin_net": 12, "column_rounds": 8,
        "columns_per_round": 4, "rows_per_direction": 3,
        "pricing_seconds": 2, "pricing_grid_steps": 16,
    }
    result = generate({"side": "3/2", "config": config,
                       "sources": [{"path": str(source), "sha256": digest(source)}]}, directory)
    assert result["status"] == "CANDIDATE"
    candidate = directory / "candidate.json"
    record = json.loads(candidate.read_text())
    assert "square_side" not in record
    report = decide(candidate, directory / "gate", Fraction(3, 2), workers=1, seconds=30)
    assert report["status"] == "VERIFIED"
    assert checked_receipt(directory / "gate/verification.json", candidate, Fraction(3, 2))
    candidate.write_text(candidate.read_text() + "\n")
    assert checked_receipt(directory / "gate/verification.json", candidate, Fraction(3, 2)) is None
