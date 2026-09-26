"""Exact predicate and full pricing/ceiling equivalence to the Fraction control."""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from random import Random

import pytest

from sqpack.fractional import colgen
from sqpack.fractional.exact_slabs import PreparedDepth
from sqpack.fractional.model import rotation_from_half_tangent


class FractionDepth:
    """The previous Fraction expressions, retained only as a test oracle."""

    def __init__(self, weighted):
        self.weighted = tuple(weighted)

    def at(self, x, y):
        return sum((w for s, w in self.weighted if s.covers(x, y)), start=Fraction(0))

    def reduced_cost(self, orbit, outer_side):
        return colgen.reduced_cost(orbit, self.weighted, outer_side)


def family():
    outer = Fraction(99, 25)
    return tuple(
        (colgen.square_at(rotation_from_half_tangent(str(t), t), (x, y), outer, Fraction(9977, 10000)), 8 * w)
        for t, x, y, w in (
            (Fraction(0), Fraction(1), Fraction(1), Fraction(3, 2)),
            (Fraction(1, 5), Fraction(3, 2), Fraction(7, 5), Fraction(7, 6)),
            (Fraction(2, 5), Fraction(2), Fraction(2), Fraction(1, 3)),
        )
    )


def test_fraction_grid_and_duplicate_signed_weights():
    weighted = family()
    weighted += (weighted[0], (weighted[1][0], Fraction(-1, 4)), (weighted[2][0], Fraction(0)))
    prepared, reference = PreparedDepth(weighted), FractionDepth(weighted)
    coordinates = [Fraction(i, 11) for i in range(-25, 26)]
    for x, y in product(coordinates, repeat=2):
        assert prepared.at(x, y) == reference.at(x, y)


def test_closed_edges_corners_and_sub_float64_offsets():
    epsilon = Fraction(1, 2**200)
    for square, _ in family():
        prepared = PreparedDepth(((square, Fraction(1)),))
        for u, v in product((-square.half, Fraction(0), square.half), repeat=2):
            x = square.ax * (square.u + u) + square.bx * (square.v + v)
            y = square.ay * (square.u + u) + square.by * (square.v + v)
            for dx, dy in product((-epsilon, Fraction(0), epsilon), repeat=2):
                assert prepared.at(x + dx, y + dy) == int(square.covers(x + dx, y + dy))
            assert prepared.at(x, y) == 1


def test_random_rationals_with_large_unequal_denominators():
    rng = Random(40192)
    for _ in range(80):
        values = [Fraction(rng.randrange(-10**55, 10**55), rng.randrange(1, 10**45)) for _ in range(7)]
        square = colgen.Square(values[0], values[1], values[2], values[3], values[4], values[5], abs(values[6]))
        prepared = PreparedDepth(((square, Fraction(19, 23)),))
        for _ in range(30):
            x, y = (Fraction(rng.randrange(-10**50, 10**50), rng.randrange(1, 10**50)) for _ in range(2))
            assert prepared.at(x, y) == (Fraction(19, 23) if square.covers(x, y) else Fraction(0))


def test_empty_degenerate_and_integer_inputs():
    assert PreparedDepth(()).at(Fraction(0), Fraction(1)) == 0
    assert PreparedDepth(()).reduced_cost((), Fraction(4)) == 0
    for half in (Fraction(0), Fraction(-1), Fraction(1)):
        s = colgen.Square(Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(0), Fraction(0), half)
        assert PreparedDepth(((s, Fraction(1)),)).at(Fraction(2), Fraction(3)) == int(s.covers(Fraction(2), Fraction(3)))
    s = colgen.Square(Fraction(1), Fraction(0), Fraction(0), Fraction(0), Fraction(1), Fraction(0), Fraction(1))
    assert PreparedDepth(((s, Fraction(1)),)).at(Fraction(1), Fraction(1)) == 1
    assert PreparedDepth(((s, Fraction(1)),)).at(Fraction(2), Fraction(1)) == 0


def test_orbits_keep_stabilisers_duplicates_and_exact_cost():
    outer = Fraction(99, 25)
    weighted = colgen.symmetrise(family())
    prepared = PreparedDepth(weighted)
    for x, y in ((outer / 2, outer / 2), (Fraction(1), Fraction(1)), (Fraction(1), outer / 2), (Fraction(1), Fraction(2))):
        orbit = colgen.d4_orbit(x, y, outer)
        assert prepared.reduced_cost(orbit, outer) == colgen.reduced_cost(orbit, weighted, outer)


@pytest.mark.parametrize('wanted', [1, 3])
def test_ordered_ranked_candidates_match_fraction_control(monkeypatch, wanted):
    sites = colgen.site_set_from_grids(Fraction(99, 25), (3, 5), Fraction(1, 2))
    weighted = family()
    candidate = colgen.rank_candidates(sites, weighted, wanted=wanted)
    with monkeypatch.context() as context:
        context.setattr(colgen, 'PreparedDepth', FractionDepth)
        control = colgen.rank_candidates(sites, weighted, wanted=wanted)
    assert candidate == control
    assert candidate  # Exercise actual pricing, not only the empty case.


@pytest.mark.parametrize('n', [1, 2, 12])
def test_complete_ceiling_result_matches_fraction_control(monkeypatch, n):
    weighted = colgen.symmetrise(family())
    candidate = colgen.check_ceiling(n, weighted, Fraction(99, 25))
    with monkeypatch.context() as context:
        context.setattr(colgen, 'PreparedDepth', FractionDepth)
        control = colgen.check_ceiling(n, weighted, Fraction(99, 25))
    assert candidate == control
