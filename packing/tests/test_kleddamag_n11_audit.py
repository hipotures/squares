"""Fast controls for the external n11 auditor's mathematical trust boundaries."""

import json
import shutil
from fractions import Fraction
from pathlib import Path

import pytest

from devtools.audit_kleddamag_n11 import (
    clip_vertical,
    containment,
    quadratic_minimum,
    read_certificate,
    reconcile_replay,
    structure,
    verify_source_tree,
)

PACKING = Path(__file__).resolve().parents[1]
CERTIFICATE = (
    PACKING
    / "resources/web/external-square-certificates-2026-09-22/kleddamag-11"
    / "global-certificate.json"
)


def test_quadratic_audit_detects_an_interior_dip_between_positive_endpoints() -> None:
    # Endpoint-only checking misses this negative interval around u=1/3.
    polynomial = (Fraction(1, 9) - Fraction(1, 100), Fraction(-2, 3), Fraction(1))
    assert polynomial[0] > 0
    assert sum(polynomial) > 0
    assert quadratic_minimum(polynomial, Fraction(0), Fraction(1)) == -Fraction(1, 100)


def test_polygon_clipping_retains_vertices_inside_a_slab() -> None:
    polygon = [
        (Fraction(-2), Fraction(0)),
        (Fraction(0), Fraction(-3)),
        (Fraction(2), Fraction(0)),
        (Fraction(0), Fraction(3)),
    ]
    clipped = clip_vertical(polygon, Fraction(-1, 2), keep_right=True)
    clipped = clip_vertical(clipped, Fraction(1, 3), keep_right=False)
    assert set(clipped) == {
        (Fraction(-1, 2), Fraction(-9, 4)),
        (Fraction(-1, 2), Fraction(9, 4)),
        (Fraction(1, 3), Fraction(-5, 2)),
        (Fraction(1, 3), Fraction(5, 2)),
        (Fraction(0), Fraction(-3)),
        (Fraction(0), Fraction(3)),
    }


def test_structure_refuses_charging_only_one_budget_unit_for_two_of_five() -> None:
    certificate = read_certificate(CERTIFICATE)
    omitted_capacity = sum(
        len(atom["sets"]) * atom["weight"]
        for atom in certificate["charge_orbits"]
        if atom["threshold"] == 2 and len(atom["sets"][0]) == 5
    )
    assert omitted_capacity > 0
    certificate["budget_units"] -= omitted_capacity
    try:
        structure(certificate)
    except ValueError as error:
        assert str(error) == "incorrect counting budget"
    else:
        raise AssertionError("the auditor accepted an understated two-of-five budget")


def test_containment_refuses_exact_contact_at_an_angle_endpoint() -> None:
    parent = Fraction(764, 775)
    certificate = {
        "L": "191/50",
        "A": str(parent),
        # At u=1/3, cos(theta)+sin(theta)=7/5, so this smaller core touches.
        "entries": [["0", "1/3", "0", str(parent * Fraction(5, 7))]],
    }
    try:
        containment(certificate)
    except ValueError as error:
        assert str(error) == "core reaches a parent boundary"
    else:
        raise AssertionError("the auditor accepted a core without strict containment")


def test_source_binding_refuses_modified_checker_and_injected_module(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(CERTIFICATE.parent, source)
    assert verify_source_tree(source)["verified_files"] == 54
    checker = source / "exact_mixed.py"
    original = checker.read_bytes()
    checker.write_bytes(original + b"\nraise RuntimeError('altered checker')\n")
    with pytest.raises(ValueError, match=r"altered source file: exact_mixed\.py"):
        verify_source_tree(source)
    checker.write_bytes(original)
    (source / "numpy.py").write_text("raise RuntimeError('injected module')\n")
    with pytest.raises(ValueError, match=r"unrecorded source file: numpy\.py"):
        verify_source_tree(source)


def test_reconciliation_refuses_a_bound_header_detached_from_certificate(
    tmp_path: Path,
) -> None:
    source = CERTIFICATE.parent / "evidence/portable"
    for name in (
        "RESULT.json",
        "python.json",
        "secondary/RESULT.json",
        "secondary/range-0-4009.json",
        "secondary/range-4009-8018.json",
        "secondary/range-8018-12028.json",
        "controls.json",
    ):
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source / name, target)
    certificate = read_certificate(CERTIFICATE)
    assert reconcile_replay(tmp_path, certificate)["bound"] == "31/8"
    aggregate = json.loads((tmp_path / "RESULT.json").read_text())
    aggregate["bound"] = "4"
    (tmp_path / "RESULT.json").write_text(json.dumps(aggregate))
    with pytest.raises(ValueError, match="replay bound differs"):
        reconcile_replay(tmp_path, certificate)
    aggregate["bound"] = "31/8"
    (tmp_path / "RESULT.json").write_text(json.dumps(aggregate))
    part_path = tmp_path / "secondary/range-4009-8018.json"
    part = json.loads(part_path.read_text())
    part["range"] = [0, 4009]
    part_path.write_text(json.dumps(part))
    with pytest.raises(ValueError, match="JavaScript range receipt differs"):
        reconcile_replay(tmp_path, certificate)
