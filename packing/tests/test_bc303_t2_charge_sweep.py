"""Adversarial synthetic controls for the source-bound BC303 C/S event sweep."""

from __future__ import annotations

from fractions import Fraction
from itertools import pairwise

import pytest

from cases.n11_five_dot_cover.bc303_t2_charge_sweep import (
    DELTA,
    MARKS,
    REPO,
    SOURCE_PATH,
    SOURCE_REVISION,
    A,
    AtomMass,
    Chart,
    H,
    centre_of,
    charge_at,
    charts,
    execution_revision,
    git_bytes,
    parse_atom_rows,
    replay,
    source_atoms,
    sweep_chart,
    validate_manifest,
    wall_cell_feasible,
)
from cases.n11_five_dot_cover.bc303_t2_geometry_control import B, labels


def direct_all_strata_minima(chart: Chart, atoms: tuple[AtomMass, ...]) -> tuple[int, int]:
    """Direct closed-membership grid, independent of the range-update tree."""
    xs = {Fraction(0), chart.x_cut, H}
    ys = {Fraction(0), H}
    if chart.axis:
        ys.add(DELTA)
    c, s = chart.selected_ray
    for atom in atoms:
        dx, dy = atom.point[0] - MARKS[0][0], atom.point[1] - MARKS[0][1]
        u, v = dx * c + dy * s, -dx * s + dy * c
        xs.update(value for value in (u - H, u + H) if 0 < value < H)
        ys.update(value for value in (v - H, v + H) if 0 < value < H)
    x_levels, y_levels = sorted(xs), sorted(ys)
    c_values: list[int] = []
    s_values: list[int] = []
    for x_low, x_high in pairwise(x_levels):
        for y_low, y_high in pairwise(y_levels):
            for exponent in range(1, 65):
                x = x_high - (x_high - x_low) / 2**exponent
                y = y_low + (y_high - y_low) / 2**exponent
                if x_high <= chart.x_cut and (not chart.axis or y_high <= DELTA):
                    z = centre_of(chart, x, y)
                    if (
                        chart.axis
                        or 4 * z[0] ** 2 * (1 + chart.lower_tangent**2)
                        > (1 + chart.lower_tangent) ** 2
                    ):
                        c_values.append(charge_at(atoms, z, chart.selected_ray))
                        break
            if x_low >= chart.x_cut:
                x, y = (x_low + x_high) / 2, (y_low + y_high) / 2
                s_values.append(charge_at(atoms, centre_of(chart, x, y), chart.selected_ray))
    x_samples = x_levels + [(left + right) / 2 for left, right in pairwise(x_levels)]
    y_samples = y_levels + [(left + right) / 2 for left, right in pairwise(y_levels)]
    for x in x_samples:
        for y in y_samples:
            z = centre_of(chart, x, y)
            if (
                x <= chart.x_cut
                and (not chart.axis or y < DELTA)
                and (
                    chart.axis
                    or 4 * z[0] ** 2 * (1 + chart.lower_tangent**2)
                    >= (1 + chart.lower_tangent) ** 2
                )
            ):
                c_values.append(charge_at(atoms, z, chart.selected_ray))
            if x > chart.x_cut:
                s_values.append(charge_at(atoms, z, chart.selected_ray))
    return min(c_values), min(s_values)


def test_axis_sweep_matches_direct_all_strata_with_closed_edges_and_coincident_events() -> None:
    axis = charts()[0]
    assert axis.axis
    x_event = axis.x_cut / 2
    atoms = (
        AtomMass((A + H, B + H), 13),  # covers every open cell
        AtomMass((A + H + x_event, B), 7),
        AtomMass((A + H + x_event, B + H + DELTA / 2), 11),
        AtomMass((A + H + axis.x_cut, B), 5),
        AtomMass((A - H, B - H), 19),  # closed vertex only
    )
    c_min, s_min, counts = sweep_chart(axis, atoms)
    assert (c_min.integer_mass, s_min.integer_mass) == direct_all_strata_minima(axis, atoms)
    assert counts["nondegenerate_rectangles"] == 4
    assert counts["c_feasible_cells"] > 0
    assert counts["s_strip_cells"] > 0
    assert charge_at(atoms, MARKS[0], axis.selected_ray) > c_min.integer_mass
    assert {0, 15} <= labels((A, A), axis.selected_ray)
    # Both axis aliases are independently represented, even though their geometry agrees.
    second_axis = charts()[1]
    assert (second_axis.index, second_axis.reflected) == (0, True)
    assert sweep_chart(second_axis, atoms)[0].integer_mass == c_min.integer_mass


def test_nonaxis_wall_cut_matches_direct_reference_and_replays_parent() -> None:
    chart = next(c for c in charts() if c.index == 180 and c.reflected)
    atoms = (
        AtomMass(centre_of(chart, H, H), 3),
        AtomMass(centre_of(chart, chart.x_cut / 2 + H, H / 2), 5),
        AtomMass(centre_of(chart, H / 3, H / 3), 7),
    )
    c_min, s_min, _ = sweep_chart(chart, atoms)
    assert (c_min.integer_mass, s_min.integer_mass) == direct_all_strata_minima(chart, atoms)
    assert replay(c_min, atoms, "C")["integer_charge"] == c_min.integer_mass
    assert replay(s_min, atoms, "S_first_owner")["integer_charge"] == s_min.integer_mass


def test_rational_wall_equality_is_infeasible_for_an_open_cell() -> None:
    chart = Chart(
        index=1,
        reflected=False,
        selected_ray=(Fraction(1), Fraction(0)),
        lower_tangent=Fraction(0),
        upper_tangent=Fraction(1),
        x_cut=H / 2,
    )
    assert not wall_cell_feasible(chart, Fraction(1, 2) - A, Fraction(0))
    assert wall_cell_feasible(chart, Fraction(1, 2) - A + Fraction(1, 100), Fraction(0))


def test_lower_dimensional_domain_and_missing_alias_are_refused() -> None:
    manifest = charts()
    with pytest.raises(ValueError, match="manifest"):
        validate_manifest(manifest[1:])
    collapsed = Chart(
        index=0,
        reflected=False,
        selected_ray=(Fraction(1), Fraction(0)),
        lower_tangent=Fraction(0),
        upper_tangent=Fraction(1),
        x_cut=Fraction(0),
    )
    with pytest.raises(ValueError, match="lower-dimensional"):
        sweep_chart(collapsed, ())


def test_changed_source_row_and_wrong_execution_revision_are_refused() -> None:
    reviewed = git_bytes(SOURCE_REVISION, SOURCE_PATH)
    assert len(parse_atom_rows(reviewed, reviewed)) == 377
    altered = reviewed.replace(b'"371/600"', b'"372/600"', 1)
    with pytest.raises(ValueError, match="differs"):
        parse_atom_rows(altered, reviewed)
    with pytest.raises(ValueError, match="wrong executing checkout"):
        execution_revision("0" * 40)
    assert REPO / SOURCE_PATH
    assert len(source_atoms()) == 377
