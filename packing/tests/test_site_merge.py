"""Guards for the G5 near-site merge.

Merging is optional and off by default. A zero radius is a no-op. A radius
smaller than the grid spacing of the in-tree stall fixture leaves that stall
untouched, because that stall is a region-edge coincidence, not a pair of
near sites. A D4-symmetric pair of near sites collapses to one orbit and keeps
Condition 1.
"""

from __future__ import annotations

from fractions import Fraction

from sqpack.fractional.certificate import Certificate, closed_form_conditions, d4_images
from sqpack.fractional.interval import verify_by_intervals
from sqpack.fractional.model import Atom
from sqpack.fractional.site_merge import merge_near_atoms, site_weights

NET = (Fraction(0), Fraction(1, 5))
SIDE = Fraction(4)
B = Fraction(1)


def _grid_certificate(square_side: Fraction) -> Certificate:
    coordinates = [Fraction(k, 2) for k in range(1, 6)]
    atoms = tuple(
        Atom(f"{i},{j}", x, y, Fraction(1))
        for i, x in enumerate(coordinates)
        for j, y in enumerate(coordinates)
    )
    return Certificate(
        n=26,
        outer_side=Fraction(3),
        square_side=square_side,
        atoms=atoms,
        half_tangents=(Fraction(0), Fraction(1, 2)),
    )


def _orbit_atoms(
    x: Fraction, y: Fraction, weight: Fraction, side: Fraction
) -> tuple[Atom, ...]:
    return tuple(
        Atom(f"{index:04d}", px, py, weight)
        for index, (px, py) in enumerate(dict.fromkeys(d4_images(x, y, side)))
    )


def test_zero_radius_returns_the_same_certificate() -> None:
    certificate = _grid_certificate(Fraction(1, 2))
    merged, receipt = merge_near_atoms(certificate, radius=Fraction(0))
    assert merged is certificate
    assert receipt.collapsed == 0
    assert receipt.atoms_after == receipt.atoms_before


def test_a_radius_below_the_grid_spacing_does_not_clear_the_seam_stall() -> None:
    """The synthetic stall is region-edge coincidence; site-merge does not fix it."""

    certificate = _grid_certificate(Fraction(1, 2))
    merged, receipt = merge_near_atoms(certificate, radius=Fraction(1, 10))
    assert merged is certificate
    assert receipt.collapsed == 0
    assert site_weights(merged) == site_weights(certificate)
    stalled = verify_by_intervals(merged, directions=("0",))
    original = verify_by_intervals(certificate, directions=("0",))
    assert stalled.directions[0].stalled == original.directions[0].stalled
    assert stalled.directions[0].stalled > 0
    assert not stalled.accepted


def test_near_sites_collapse_to_one_d4_orbit() -> None:
    first = _orbit_atoms(Fraction(1), Fraction(3, 2), Fraction(1), SIDE)
    second = _orbit_atoms(Fraction(1) + Fraction(1, 1000), Fraction(3, 2), Fraction(1), SIDE)
    certificate = Certificate(
        n=20,
        outer_side=SIDE,
        square_side=B,
        atoms=first + tuple(
            Atom(f"{len(first) + index:04d}", atom.x, atom.y, atom.weight)
            for index, atom in enumerate(second)
        ),
        half_tangents=NET,
    )
    assert closed_form_conditions(certificate)[0].holds
    assert len(certificate.atoms) == 16
    merged, receipt = merge_near_atoms(certificate, radius=Fraction(1, 100))
    assert receipt.collapsed == 1
    assert len(merged.atoms) == 8
    assert closed_form_conditions(merged)[0].holds
    assert sum((atom.weight for atom in merged.atoms), start=Fraction(0)) == 16
    assert all(atom.weight == 2 for atom in merged.atoms)


def test_a_negative_radius_is_refused() -> None:
    certificate = _grid_certificate(Fraction(1, 2))
    try:
        merge_near_atoms(certificate, radius=Fraction(-1, 10))
    except ValueError as error:
        assert "non-negative" in str(error)
    else:
        raise AssertionError("a negative radius was accepted")
