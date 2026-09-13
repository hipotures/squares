"""Independent target-free BC303 T2 reader readmission controls, 2026-09-13.

Run under project Python 3.14 with the reviewed packing and packing/src on
PYTHONPATH. Source atoms and run_target are forbidden by the autouse fixture.
The reviewed commit is fixed here; the file can be retained beside the review.
"""

from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from random import Random

import pytest

from cases.n11_five_dot_cover import bc303_t2_charge_sweep as reader
from cases.n11_five_dot_cover import bc303_t2_geometry_control as geometry
from devtools import owner_footprints
from sqpack.fractional import adaptive, generate, model, sweep

EXPECTED_REVISION = "0f20fdcdd5bac7e0734b29cd0b0efef4ffea3699"

spec = importlib.util.spec_from_file_location(
    "admitted_direct_reference", reader.REPO / "packing/tests/test_bc303_t2_charge_sweep.py"
)
assert spec is not None
assert spec.loader is not None
controls = importlib.util.module_from_spec(spec)
spec.loader.exec_module(controls)


@pytest.fixture(autouse=True)
def synthetic_only(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("source atom loading and target execution are forbidden here")

    monkeypatch.setattr(reader, "source_atoms", forbidden)
    monkeypatch.setattr(reader, "run_target", forbidden)


def test_reviewed_runtime_identity() -> None:
    assert sys.version_info[:2] == (3, 14)
    assert reader.execution_revision(EXPECTED_REVISION) == EXPECTED_REVISION
    modules = (
        (reader, "packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py"),
        (geometry, "packing/cases/n11_five_dot_cover/bc303_t2_geometry_control.py"),
        (owner_footprints, "packing/devtools/owner_footprints.py"),
        (adaptive, "packing/src/sqpack/fractional/adaptive.py"),
        (generate, "packing/src/sqpack/fractional/generate.py"),
        (model, "packing/src/sqpack/fractional/model.py"),
        (sweep, "packing/src/sqpack/fractional/sweep.py"),
    )
    for module, relative in modules:
        assert module.__file__ is not None
        assert Path(module.__file__).resolve() == reader.REPO / relative


@pytest.mark.parametrize(
    "chart", reader.charts(), ids=lambda chart: f"{chart.index}-{chart.reflected}"
)
def test_every_chart_parent_replays_and_transports_under_d4(chart: reader.Chart) -> None:
    atoms = (
        reader.AtomMass(reader.centre_of(chart, reader.H, reader.H), 3),
        reader.AtomMass(reader.centre_of(chart, chart.x_cut / 2 + reader.H, reader.H / 2), 5),
        reader.AtomMass(reader.centre_of(chart, reader.H / 3, reader.H / 3), 7),
    )
    c_minimum, s_minimum, _ = reader.sweep_chart(chart, atoms)
    for minimum, role in ((c_minimum, "C"), (s_minimum, "S_first_owner")):
        receipt = reader.replay(minimum, atoms, role)
        physical = tuple(Fraction(value) for value in receipt["physical_parent_ray"])
        px, py = physical
        # Check the positive folded source ray without calling the inverse under review.
        if chart.axis:
            assert px * py == 0
            assert px * px + py * py == 1
        else:
            folded_x, folded_y = (py, px) if chart.reflected else (px, py)
            assert folded_x > 0
            assert folded_y >= 0
            assert chart.lower_tangent * folded_x < folded_y
            assert folded_y < chart.upper_tangent * folded_x
        for a, b, c, d in geometry.D4:
            target = (a * px + b * py, c * px + d * py)
            transformed = replace(chart, reflected=chart.reflected ^ (a * d - b * c < 0))
            assert reader.source_cell_admits(transformed, target)


def test_all_chart_endpoints_and_exterior_rays_under_d4() -> None:
    for chart in reader.charts():
        width = chart.upper_tangent - chart.lower_tangent
        candidates = (
            (chart.lower_tangent, True),
            (chart.upper_tangent, True),
            ((chart.lower_tangent + chart.upper_tangent) / 2, True),
            (chart.lower_tangent - width / 3, False),
            (chart.upper_tangent + width / 3, False),
        )
        for tangent, admitted in candidates:
            px, py = (tangent, Fraction(1)) if chart.reflected else (Fraction(1), tangent)
            for a, b, c, d in geometry.D4:
                target = (a * px + b * py, c * px + d * py)
                transformed = replace(chart, reflected=chart.reflected ^ (a * d - b * c < 0))
                assert reader.source_cell_admits(transformed, target) is admitted


@pytest.mark.parametrize("index", [0, 90, 180])
def test_replay_accepts_quarter_turns_and_refuses_nonunit_parent(
    index: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    chart = next(chart for chart in reader.charts() if chart.index == index)
    minima = reader.sweep_chart(chart, ())[:2]
    original_constructor = reader.rational_parent
    for minimum, role in zip(minima, ("C", "S_first_owner"), strict=True):
        monkeypatch.setattr(reader, "rational_parent", original_constructor)
        receipt = reader.replay(minimum, (), role)
        px, py = (Fraction(value) for value in receipt["physical_parent_ray"])
        for target in ((px, py), (-py, px), (-px, -py), (py, -px)):
            monkeypatch.setattr(
                reader, "rational_parent", lambda _chart, _centre, target=target: target
            )
            assert reader.replay(minimum, (), role)["integer_charge"] == 0
        target = (px * Fraction(1001, 1000), py * Fraction(1001, 1000))
        monkeypatch.setattr(
            reader, "rational_parent", lambda _chart, _centre, target=target: target
        )
        with pytest.raises(ValueError, match="not unit length"):
            reader.replay(minimum, (), role)


def test_exact_wall_equality_on_point_and_open_edge_strata() -> None:
    chart = reader.Chart(
        index=1,
        reflected=False,
        selected_ray=(Fraction(4, 5), Fraction(3, 5)),
        lower_tangent=Fraction(3, 4),
        upper_tangent=Fraction(1),
        x_cut=reader.H - reader.DELTA / 5,
    )
    x = Fraction(1, 1000)
    y = (reader.A + Fraction(4, 5) * x - Fraction(7, 10)) / Fraction(3, 5)
    assert 0 < x < chart.x_cut
    assert 0 < y < reader.H
    point = controls.direct_c_representative(chart, x, x, y, y)
    assert point == (x, y)
    assert controls.direct_c_representative(chart, 0, x, y, y) is None
    assert controls.direct_c_representative(chart, x, x, y, reader.H) is None
    assert controls.direct_c_representative(chart, 0, x, y, reader.H) is None
    assert controls.direct_c_representative(chart, x, x, 0, y) is not None
    assert controls.direct_c_representative(chart, x, chart.x_cut, y, y) is not None


def test_all_strata_surface_propagates_narrow_cell_refusal() -> None:
    chart = reader.Chart(
        index=1,
        reflected=False,
        selected_ray=(Fraction(4, 5), Fraction(3, 5)),
        lower_tangent=Fraction(3, 4),
        upper_tangent=Fraction(1),
        x_cut=reader.H - reader.DELTA / 5,
    )
    x_high = Fraction(1, 1000)
    y_low = (
        reader.A + Fraction(4, 5) * x_high - Fraction(7, 10) - Fraction(1, 2**300)
    ) / Fraction(3, 5)
    atoms = (
        reader.AtomMass(reader.centre_of(chart, x_high + reader.H, reader.H / 2), 1),
        reader.AtomMass(reader.centre_of(chart, reader.H / 2, y_low - reader.H), 1),
    )
    with pytest.raises(ValueError, match="unresolved rational C representative"):
        controls.direct_all_strata_minima(chart, atoms)


@pytest.mark.parametrize("index", [0, 1, 2, 45, 90, 135, 178, 179, 180])
def test_independent_synthetic_event_layouts_match_reference(index: int) -> None:
    chart = next(chart for chart in reader.charts() if chart.index == index)
    random = Random(303_160 + index)
    for _layout in range(3):
        atoms = tuple(
            reader.AtomMass(
                reader.centre_of(
                    chart,
                    reader.H * Fraction(random.randrange(-6, 19), 12),
                    reader.H * Fraction(random.randrange(-6, 19), 12),
                ),
                random.randrange(0, 20),
            )
            for _atom in range(7)
        )
        c_minimum, s_minimum, _ = reader.sweep_chart(chart, atoms)
        assert controls.direct_all_strata_minima(chart, atoms) == (
            c_minimum.integer_mass,
            s_minimum.integer_mass,
        )
