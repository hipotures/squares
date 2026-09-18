"""Controls for the ceiling-family polish, focused on the D4 orbit lookup.

The polish refuses a family that is not closed under D4. Axis-parallel
placements are the same square at ``t = 0`` and ``t = 1``, and records store
them as ``t = 0``. Looking up the raw reflection image ``t = 1`` then claims
an orbit is missing (G2). Folding that pair is the same convention the
independent ceiling reader already uses.
"""

from __future__ import annotations

from fractions import Fraction

from devtools.polish_ceiling_family import fold_half_tangent, placement_orbits
from sqpack.fractional.ceiling import CeilingCertificate, Placement

B = Fraction(1)
SIDE = Fraction(2)
NET = (Fraction(0), Fraction(1, 5))


def test_fold_half_tangent_identifies_the_two_axis_parallel_writings() -> None:
    assert fold_half_tangent(Fraction(0)) == 0
    assert fold_half_tangent(Fraction(1)) == 0
    assert fold_half_tangent(Fraction(1, 5)) == Fraction(1, 5)


def test_axis_parallel_corners_stored_as_t0_are_one_orbit() -> None:
    """Four upright corner squares, every half-tangent written 0, form one orbit."""

    low, high = B / 2, SIDE - B / 2
    family = CeilingCertificate(
        4,
        SIDE,
        B,
        NET,
        tuple(
            Placement(Fraction(0), x, y, Fraction(1), B)
            for x in (low, high)
            for y in (low, high)
        ),
    )
    orbit, count = placement_orbits(family)
    assert count == 1
    assert set(orbit.tolist()) == {0}


def test_a_record_that_mixes_t0_and_t1_at_one_centre_is_a_duplicate() -> None:
    """The two writings of one upright square are the same placement."""

    square = Placement(Fraction(0), Fraction(1), Fraction(1), Fraction(1), B)
    turned = Placement(Fraction(1), Fraction(1), Fraction(1), Fraction(1), B)
    family = CeilingCertificate(1, SIDE, B, NET, (square, turned))
    try:
        placement_orbits(family)
    except ValueError as error:
        assert "repeats a placement" in str(error)
    else:
        raise AssertionError("t = 0 and t = 1 at the same centre were treated as distinct")
