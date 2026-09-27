"""Differential tests; native build is mandatory, not silently skipped."""

from __future__ import annotations

from fractions import Fraction
from types import SimpleNamespace

import numpy as np
import pytest

from devtools.native_ab_replay import signature
from sqpack.fractional import native_ab_hooks as hooks
from sqpack.fractional import native_ab_runtime as runtime
from sqpack.fractional.colgen import _vertices
from sqpack.fractional.exact_slabs import PreparedDepth
from sqpack.fractional.generate import _least_finite_indices, event_grid, placement_cells
from sqpack.fractional.model import rotation_from_half_tangent


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch):
    monkeypatch.setenv("PACK_NATIVE_KERNELS", "none")
    monkeypatch.delenv("PACK_NATIVE_STATS", raising=False)
    monkeypatch.delenv("PACK_NATIVE_CAPTURE", raising=False)


def select(monkeypatch, mode):
    monkeypatch.setenv("PACK_NATIVE_KERNELS", mode)
    runtime.preflight()


@pytest.mark.parametrize("native", ["prefix", "topk", "scatter", "compact", "all"])
@pytest.mark.parametrize("seed", range(4))
def test_direction_reference_identity(monkeypatch, native, seed):
    rng = np.random.default_rng(seed)
    points = rng.uniform(0.5, 3.46, size=(50 + seed * 13, 2))
    weights = rng.uniform(0.0, 0.3, len(points))
    weights[::3] = 0
    direction = rotation_from_half_tangent("test", Fraction(seed + 1, 15))
    kwargs = dict(keep=3)
    select(monkeypatch, "none")
    reference = placement_cells(points, weights, direction, 3.96, 0.9977, **kwargs)
    grid = event_grid(points, weights, direction, 3.96, 0.9977)
    select(monkeypatch, native)
    candidate = placement_cells(points, weights, direction, 3.96, 0.9977, **kwargs)
    native_grid = event_grid(points, weights, direction, 3.96, 0.9977)
    assert signature(candidate) == signature(reference)
    assert signature(native_grid.mass) == signature(grid.mass)
    assert np.array_equal(native_grid.reachable, grid.reachable)


@pytest.mark.parametrize("mode", ["none", "production", "all"])
def test_zero_grid_keeps_spatial_tie_rule(monkeypatch, mode):
    scores = np.zeros(100)
    scores[::7] = np.inf
    select(monkeypatch, "none")
    reference = _least_finite_indices(scores, 13, zero_weight_grid=True)
    select(monkeypatch, mode)
    assert np.array_equal(reference, _least_finite_indices(scores, 13, zero_weight_grid=True))


def test_topk_signed_zero_nan_inf_and_ties(monkeypatch):
    scores = np.array([0.0, -0.0, np.inf, -np.inf, np.nan, 2.0, 1.0, 1.0, -3.0, -3.0, 1.0])
    for count in (1, 3, 6, 10):
        select(monkeypatch, "none")
        reference = _least_finite_indices(scores, count)
        select(monkeypatch, "topk")
        assert np.array_equal(reference, _least_finite_indices(scores, count))


def test_scatter_preserves_four_pass_order(monkeypatch):
    left = np.array([0, 0, 0, 1, 1, 0])
    right = np.array([1, 1, 0, 0, 1, 0])
    bottom = np.array([0, 0, 1, 1, 1, 0])
    top = np.array([1, 1, 0, 0, 1, 1])
    weights = np.array([1e30, 1.0, 1e-30, 3.0, -2.0, -0.0])
    a = np.zeros((2, 2))
    b = a.copy()
    select(monkeypatch, "none")
    hooks.scatter(a, left, right, bottom, top, weights)
    select(monkeypatch, "scatter")
    hooks.scatter(b, left, right, bottom, top, weights)
    assert a.tobytes() == b.tobytes()


def test_scatter_rejects_invalid_index_before_mutation(monkeypatch):
    select(monkeypatch, "scatter")
    grid = np.zeros((3, 3))
    good = np.array([0, 1])
    with pytest.raises(ValueError):
        hooks.scatter(grid, good, good, good, np.array([0, 8]), np.array([2.0, 3.0]))
    assert not grid.any()


def test_compaction_strided_grid_is_bitwise(monkeypatch):
    parent = np.arange(120.0, dtype=np.float64).reshape(10, 12)
    parent[1, 2] = -0.0
    parent[5, 3] = np.nan
    mass = parent[:-1, :-1]
    ids, firsts, widths, offsets = map(np.array, ([1, 5, 8], [2, 1, 0], [4, 6, 11], [0, 4, 10]))
    reference, candidate = np.empty(21), np.empty(21)
    select(monkeypatch, "none")
    hooks.compact(mass, ids, firsts, widths, offsets, reference)
    select(monkeypatch, "compact")
    hooks.compact(mass, ids, firsts, widths, offsets, candidate)
    assert candidate.tobytes() == reference.tobytes()
    with pytest.raises(ValueError):
        hooks.compact(mass, ids, firsts, widths + 100, offsets, candidate)


@pytest.mark.parametrize("seed", range(5))
def test_vertices_order_and_bits(monkeypatch, seed):
    rng = np.random.default_rng(seed)
    lines = [
        (Fraction(1), Fraction(0), Fraction(-2)),
        (Fraction(1), Fraction(0), Fraction(2)),
        (Fraction(0), Fraction(1), Fraction(-2)),
        (Fraction(0), Fraction(1), Fraction(2)),
    ]
    for _ in range(25):
        lines.append(tuple(Fraction(int(v), 17) for v in rng.integers(-20, 20, 3)))
    select(monkeypatch, "none")
    reference = _vertices(lines, Fraction(4))
    select(monkeypatch, "vertices")
    candidate = _vertices(lines, Fraction(4))
    assert signature(candidate) == signature(reference)


def depth_fixture():
    square = SimpleNamespace(
        ax=Fraction(1),
        ay=Fraction(0),
        u=Fraction(0),
        bx=Fraction(0),
        by=Fraction(1),
        v=Fraction(0),
        half=Fraction(1, 2),
    )
    tilted = SimpleNamespace(
        ax=Fraction(3, 5),
        ay=Fraction(4, 5),
        u=Fraction(2, 7),
        bx=Fraction(-4, 5),
        by=Fraction(3, 5),
        v=Fraction(-3, 11),
        half=Fraction(1, 2),
    )
    return PreparedDepth(
        [
            (square, Fraction(1, 3)),
            (tilted, Fraction(2, 13)),
            (square, Fraction(-1, 17)),
            (square, Fraction(1, 2**257 + 1)),
        ]
    )


@pytest.mark.parametrize("offset", [Fraction(0), Fraction(1, 2**200), Fraction(-1, 2**200)])
def test_exact_boundary_and_large_denominators(monkeypatch, offset):
    value = depth_fixture()
    points = [
        (Fraction(1, 2) + offset, Fraction(0)),
        (Fraction(-1, 2) + offset, Fraction(1, 2)),
        (Fraction(11, 2**180 + 3), Fraction(7, 2**190 + 9)),
    ]
    select(monkeypatch, "none")
    reference = [value.at(x, y) for x, y in points]
    cost = value.reduced_cost(tuple(points), Fraction(4))
    select(monkeypatch, "exact-depth")
    assert [value.at(x, y) for x, y in points] == reference
    assert value.reduced_cost(tuple(points), Fraction(4)) == cost


def test_empty_exact_family(monkeypatch):
    value = PreparedDepth([])
    select(monkeypatch, "exact-depth")
    assert value.at(Fraction(0), Fraction(0)) == 0
    assert value.reduced_cost(((Fraction(0), Fraction(0)),), Fraction(4)) == 1


def test_selection_is_explicit_and_missing_native_fails(monkeypatch, tmp_path):
    assert runtime.parse_selection("none") == ()
    assert runtime.parse_selection("production") == ("prefix", "topk", "scatter", "compact")
    monkeypatch.delenv("PACK_NATIVE_KERNELS")
    assert runtime.selection() == runtime.PRODUCTION_KERNELS
    with pytest.raises(ValueError):
        runtime.parse_selection("compcat")
    with pytest.raises(ValueError):
        runtime.parse_selection("compact,compact")
    monkeypatch.setenv("PACK_NATIVE_BUILD_ROOT", str(tmp_path))
    select(monkeypatch, "none")
    with pytest.raises(RuntimeError, match="unavailable"):
        select(monkeypatch, "exact-depth")
