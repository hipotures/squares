"""Small real fixed-B runs and full-dual candidate-discovery controls."""
import json
import time
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest

from devtools.frontier_hybrid_worker import generate
from devtools.frontier_io import digest
from devtools.frontier_verify import decide
from sqpack.fractional.colgen import Square, site_set_from_points
from sqpack.fractional.hybrid_pricing import price_full, scores


def square(half):
    return Square(Fraction(1), Fraction(0), Fraction(0), Fraction(0),
                  Fraction(1), Fraction(0), Fraction(half))


def test_full_dual_sees_combined_small_weights():
    sites = site_set_from_points(Fraction(2), {(Fraction(0), Fraction(0))})
    weighted = tuple((square(Fraction(1, 2)), Fraction(1, 50)) for _ in range(64))
    full, info = price_full(sites, weighted, wanted=16, grid_steps=16,
                           arrangement_rows=0, deadline=time.perf_counter() + 10)
    truncated, _ = price_full(sites, weighted[:32], wanted=16, grid_steps=16,
                             arrangement_rows=0, deadline=time.perf_counter() + 10)
    assert full
    assert not truncated
    assert all(item.cost < 0 for item in full)
    assert info["pricing_rows"] == 64
    assert not info["pricing_exhaustive"]
    assert len({item.orbit for item in full}) == len(full)


def test_variable_half_sides_and_expired_budget():
    weighted = ((square(Fraction(1, 4)), Fraction(1)),
                (square(Fraction(1, 2)), Fraction(2)))
    values = scores(np.array([[0., 0.], [0.4, 0.], [0.6, 0.]]), weighted,
                    deadline=time.perf_counter() + 10)
    assert values == pytest.approx([3, 2, 0])
    sites = site_set_from_points(Fraction(2), {(Fraction(0), Fraction(0))})
    found, info = price_full(sites, weighted, wanted=16, grid_steps=8,
                            deadline=time.perf_counter() - 1)
    assert not found
    assert info["pricing_budget_exhausted"]
    assert not info["pricing_exhaustive"]


@pytest.mark.parametrize("mode", ["control", "batched", "interleaved"])
def test_real_small_generator_and_unchanged_full_gate(tmp_path, monkeypatch, mode):
    monkeypatch.setenv("PACK_JOBS", "1")
    monkeypatch.setenv("PACK_GENERATION_MANAGED", "1")
    monkeypatch.setenv("OMP_NUM_THREADS", "1")
    monkeypatch.setenv("OPENBLAS_NUM_THREADS", "1")
    source = tmp_path / "seed.json"
    source.write_text(json.dumps({"outer_side": "3/2", "atoms": [["3/4", "3/4", "1"]]}))
    directory = tmp_path / "job"
    directory.mkdir()
    config = {
        "mode": mode, "seed_map": "scale", "grid_counts": [3, 4],
        "stage_seconds": 30, "workers": 1, "shrink": "19/20",
        "angle_limit": "207107/500000", "direction_steps": 16, "scale": 1600000,
        "row_rounds": 30, "column_rounds": 12, "columns_per_round": 4,
        "rows_per_direction": 3, "support_cap": 32, "pricing_seconds": 2,
        "pricing_grid_steps": 16, "arrangement_rows": 8, "pricing_every": 2,
    }
    result = generate({"side": "3/2", "config": config,
                       "sources": [{"path": str(source), "sha256": digest(source)}]}, directory)
    assert result["status"] == "CANDIDATE"
    assert Fraction(result["mass"]) < 12
    assert result["candidate_sha256"] == digest(directory / "candidate.json")
    report = decide(directory / "candidate.json", directory / "gate", Fraction(3, 2))
    assert report["status"] == "VERIFIED"
    assert report["verified_sha256"] == digest(Path(report["verified_candidate"]))
    assert (directory / "search-support.json").is_file()
