"""Adversarial synthetic controls for the source-bound BC303 C/S event sweep."""

from __future__ import annotations

from fractions import Fraction
from itertools import pairwise

import pytest

from cases.n11_five_dot_cover import bc303_t2_charge_sweep as reader
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
    source_cell_admits,
    sweep_chart,
    validate_manifest,
    wall_cell_feasible,
)
from cases.n11_five_dot_cover.bc303_t2_geometry_control import B, labels
from devtools.owner_footprints import full_owner_direction_manifest
from sqpack.fractional.adaptive import derive_cells
from sqpack.fractional.generate import net_half_tangents


def direct_c_representative(
    chart: Chart,
    x_low: Fraction,
    x_high: Fraction,
    y_low: Fraction,
    y_high: Fraction,
) -> tuple[Fraction, Fraction] | None:
    """Return an exact feasible point or prove this product stratum infeasible."""
    x_open, y_open = x_low < x_high, y_low < y_high
    if x_high > chart.x_cut or (
        chart.axis and y_high >= DELTA and not (y_open and y_high == DELTA)
    ):
        return None
    lower = chart.lower_tangent
    rhs = (1 + lower) ** 2
    if not chart.axis:
        c, s = chart.selected_ray
        maximum = A + c * x_high - s * y_low
        lhs = 4 * maximum**2 * (1 + lower**2) if maximum > 0 else -1
        if lhs < rhs or (lhs == rhs and ((x_open and c != 0) or (y_open and s != 0))):
            return None
    for exponent in range(1, 257):
        x = x_high - (x_high - x_low) / 2**exponent
        y = y_low + (y_high - y_low) / 2**exponent
        z = centre_of(chart, x, y)
        if chart.axis or 4 * z[0] ** 2 * (1 + lower**2) >= rhs:
            return x, y
    raise ValueError("unresolved rational C representative for feasible stratum")


def direct_all_strata_minima(chart: Chart, atoms: tuple[AtomMass, ...]) -> tuple[int, int]:
    """Decide every point/open-interval stratum without range-tree updates."""
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
    x_strata = [(value, value) for value in x_levels] + list(pairwise(x_levels))
    y_strata = [(value, value) for value in y_levels] + list(pairwise(y_levels))
    c_values: list[int] = []
    s_values: list[int] = []
    for x_low, x_high in x_strata:
        for y_low, y_high in y_strata:
            representative = direct_c_representative(chart, x_low, x_high, y_low, y_high)
            if representative is not None:
                c_values.append(
                    charge_at(atoms, centre_of(chart, *representative), chart.selected_ray)
                )
            if x_high > chart.x_cut:
                x, y = (x_low + x_high) / 2, (y_low + y_high) / 2
                s_values.append(charge_at(atoms, centre_of(chart, x, y), chart.selected_ray))
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
    alias_c, alias_s, _ = sweep_chart(second_axis, atoms)
    assert alias_c.integer_mass == c_min.integer_mass
    assert replay(alias_c, atoms, "C")["integer_charge"] == alias_c.integer_mass
    assert replay(alias_s, atoms, "S_first_owner")["integer_charge"] == alias_s.integer_mass


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


def test_source_charts_match_frozen_manifest_and_angle_cells() -> None:
    source_manifest = full_owner_direction_manifest()
    tangents = net_half_tangents(source_manifest.angle_limit, source_manifest.direction_steps)
    source_cells = derive_cells(tangents, (2 * H,) * len(tangents))
    source_rows = {}
    for orientation in source_manifest.orientations:
        u = orientation.direction.ux, orientation.direction.uy
        signed = (u, (-u[1], u[0]), (-u[0], -u[1]), (u[1], -u[0]))
        eligible = [direction for direction in signed if direction[0] >= direction[1] >= 0]
        if eligible:
            assert len(eligible) == 1
            for source in orientation.sources:
                cell = source_cells[source.folded_index]
                source_rows[source.folded_index, source.reflected] = (
                    eligible[0],
                    cell.lower_boundary_tangent,
                    cell.upper_boundary_tangent,
                )
    reader_rows = {
        (chart.index, chart.reflected): (
            chart.selected_ray,
            chart.lower_tangent,
            chart.upper_tangent,
        )
        for chart in charts()
    }
    assert len(source_rows) == 182
    assert reader_rows == source_rows


def test_interior_coincident_end_and_start_preserve_closed_charge() -> None:
    chart = charts()[0]
    event = chart.x_cut / 2
    atoms = (
        AtomMass((A + event - H, B + H / 2), 7),
        AtomMass((A + H / 2, B + H / 2), 13),
        AtomMass((A + event + H, B + H / 2), 11),
    )
    c_minimum, s_minimum, _ = sweep_chart(chart, atoms)
    assert (c_minimum.integer_mass, s_minimum.integer_mass) == (20, 24)
    assert direct_all_strata_minima(chart, atoms) == (20, 24)
    assert charge_at(atoms, (A + event, B + H / 4), chart.selected_ray) == 31


def test_narrow_feasible_cell_is_present_in_direct_reference() -> None:
    c, s = Fraction(4, 5), Fraction(3, 5)
    chart = Chart(
        index=1,
        reflected=False,
        selected_ray=(c, s),
        lower_tangent=Fraction(3, 4),
        upper_tangent=Fraction(1),
        x_cut=H - DELTA * (c - s),
    )
    x_high = Fraction(1, 1000)
    epsilon = Fraction(1, 2**100)
    y_low = (A + c * x_high - Fraction(7, 10) - epsilon) / s
    atoms = (
        AtomMass(centre_of(chart, x_high + H, H / 2), 1),
        AtomMass(centre_of(chart, H / 2, y_low - H), 1),
    )
    x = x_high - x_high / 2**110
    y = y_low + (H - y_low) / 2**110
    assert centre_of(chart, x, y)[0] > Fraction(7, 10)
    assert charge_at(atoms, centre_of(chart, x, y), chart.selected_ray) == 0
    assert direct_all_strata_minima(chart, atoms)[0] == 0
    assert sweep_chart(chart, atoms)[0].integer_mass == 0


def test_direct_reference_wall_equality_obeys_endpoint_attainment() -> None:
    chart = Chart(
        index=1,
        reflected=False,
        selected_ray=(Fraction(1), Fraction(0)),
        lower_tangent=Fraction(0),
        upper_tangent=Fraction(1),
        x_cut=H,
    )
    x = Fraction(1, 2) - A
    assert direct_c_representative(chart, x, x, Fraction(0), H) is not None
    assert direct_c_representative(chart, x - Fraction(1, 100), x, Fraction(0), H) is None
    assert direct_c_representative(chart, x, x + Fraction(1, 100), Fraction(0), H) is not None


def test_direct_reference_refuses_unresolved_rational_reconstruction() -> None:
    c, s = Fraction(4, 5), Fraction(3, 5)
    chart = Chart(
        index=1,
        reflected=False,
        selected_ray=(c, s),
        lower_tangent=Fraction(3, 4),
        upper_tangent=Fraction(1),
        x_cut=H,
    )
    x_high = Fraction(1, 1000)
    y_low = (A + c * x_high - Fraction(7, 10) - Fraction(1, 2**300)) / s
    with pytest.raises(ValueError, match="unresolved rational C representative"):
        direct_c_representative(chart, Fraction(0), x_high, y_low, H)


@pytest.mark.parametrize("role", ["C", "S_first_owner"])
def test_reflected_parent_transport_and_wrong_reflection_refusal(
    role: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    chart = next(chart for chart in charts() if chart.index == 180 and chart.reflected)
    atoms = (
        AtomMass(centre_of(chart, H, H), 3),
        AtomMass(centre_of(chart, chart.x_cut / 2 + H, H / 2), 5),
        AtomMass(centre_of(chart, H / 3, H / 3), 7),
    )
    c_minimum, s_minimum, _ = sweep_chart(chart, atoms)
    minimum = c_minimum if role == "C" else s_minimum
    receipt = replay(minimum, atoms, role)
    physical = (
        Fraction(receipt["physical_parent_ray"][0]),
        Fraction(receipt["physical_parent_ray"][1]),
    )
    assert source_cell_admits(chart, physical)
    assert chart.lower_tangent <= physical[0] / physical[1] <= chart.upper_tangent
    wrong = (
        (Fraction(13575, 19193), Fraction(13568, 19193)) if role == "C" else chart.selected_ray
    )
    assert not source_cell_admits(chart, wrong)
    monkeypatch.setattr(reader, "rational_parent", lambda _chart, _centre: wrong)
    with pytest.raises(ValueError, match="outside its declared source cell"):
        replay(minimum, atoms, role)


def test_reflected_source_endpoints_are_inclusive_and_overshoots_refused() -> None:
    chart = next(chart for chart in charts() if chart.index == 180 and chart.reflected)
    lower, upper = chart.lower_tangent, chart.upper_tangent
    assert source_cell_admits(chart, (lower, Fraction(1)))
    assert source_cell_admits(chart, (upper, Fraction(1)))
    assert not source_cell_admits(chart, (lower - Fraction(1, 1000), Fraction(1)))
    assert not source_cell_admits(chart, (upper + Fraction(1, 1000), Fraction(1)))
