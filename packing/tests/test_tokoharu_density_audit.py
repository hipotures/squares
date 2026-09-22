"""Controls for the independent preconditions of the retained density certificates."""

from __future__ import annotations

import json
import shutil
import tempfile
from fractions import Fraction
from pathlib import Path

import pytest

from devtools import audit_tokoharu_density
from devtools.audit_tokoharu_density import CASES, SOURCE, exact_area, preflight, square_polygon


def test_exact_area_handles_rotated_containment_halving_and_tangency() -> None:
    polygon = square_polygon(
        Fraction(0), Fraction(0), Fraction(3, 5), Fraction(4, 5), Fraction(1)
    )
    assert (
        exact_area((Fraction(-1), Fraction(-1), Fraction(1), Fraction(1), Fraction(1)), polygon)
        == 1
    )
    assert exact_area(
        (Fraction(0), Fraction(-1), Fraction(1), Fraction(1), Fraction(1)), polygon
    ) == Fraction(1, 2)
    assert (
        exact_area(
            (Fraction(7, 10), Fraction(-1), Fraction(1), Fraction(1), Fraction(1)), polygon
        )
        == 0
    )


def test_retained_density_preconditions_pass() -> None:
    for n, name in CASES.items():
        report = preflight(SOURCE / "certificates" / name, n)
        assert report["status"] == "PASS"
        assert Fraction(report["mass_exact"]) < n


def test_missing_axis_events_refuse_before_global_replay() -> None:
    with tempfile.TemporaryDirectory() as directory:
        case = Path(directory)
        source = SOURCE / "certificates" / CASES[11]
        for name in (
            "certified_candidate.json",
            "certificate_metadata.json",
            "certificate_input.txt",
        ):
            shutil.copyfile(source / name, case / name)
        path = case / "certificate_input.txt"
        lines = path.read_text().splitlines()
        count_index = 3 + int(lines[2])
        lines[count_index] = str(int(lines[count_index]) - 1)
        lines.pop()
        path.write_text("\n".join(lines) + "\n")
        try:
            preflight(case, 11)
        except ValueError as error:
            assert "axis-event count" in str(error)
        else:
            raise AssertionError("incomplete axis partition accepted")


def test_non_enclosing_header_refuses_before_global_replay() -> None:
    with tempfile.TemporaryDirectory() as directory:
        case = Path(directory)
        source = SOURCE / "certificates" / CASES[11]
        for name in (
            "certified_candidate.json",
            "certificate_metadata.json",
            "certificate_input.txt",
        ):
            shutil.copyfile(source / name, case / name)
        path = case / "certificate_input.txt"
        lines = path.read_text().splitlines()
        lines[0] = "0x1p+2 0x1p+2"
        path.write_text("\n".join(lines) + "\n")
        try:
            preflight(case, 11)
        except ValueError as error:
            assert "interval fails exact enclosure: L" in str(error)
        else:
            raise AssertionError("wrong container side accepted")


@pytest.mark.parametrize("mutation", ["altered", "missing"])
def test_archive_changes_refuse_before_any_external_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    source = tmp_path / SOURCE.relative_to(audit_tokoharu_density.REPO)
    shutil.copytree(SOURCE, source)
    acquisition = source.parent / "acquisition"
    acquisition.mkdir()
    for name in ("sources.json", "tokoharu-density.sha256"):
        shutil.copyfile(SOURCE.parent / "acquisition" / name, acquisition / name)
    monkeypatch.setattr(audit_tokoharu_density, "REPO", tmp_path)
    monkeypatch.setattr(audit_tokoharu_density, "SOURCE", source)
    provenance = audit_tokoharu_density.source_provenance(source)
    assert provenance["kind"] == "verified-acquisition-archive"
    assert provenance["files_verified"] > 0

    checker = source / "src/verify.cpp"
    if mutation == "altered":
        checker.write_text(checker.read_text() + "\n// changed after acquisition\n")
        expected_error = "archive SHA-256 mismatch: src/verify.cpp"
    else:
        checker.unlink()
        expected_error = "archive file set mismatch: missing=['src/verify.cpp']"

    def unexpected_process(*_args: object, **_kwargs: object) -> None:
        pytest.fail("unverified archive must be refused before any external process")

    output = tmp_path / "receipt"
    monkeypatch.setattr(audit_tokoharu_density.subprocess, "run", unexpected_process)
    monkeypatch.setattr(
        audit_tokoharu_density.sys,
        "argv",
        ["audit", "--source", str(source), "--out", str(output), "--replay"],
    )
    assert audit_tokoharu_density.main() == 1
    receipt = json.loads((output / "audit.json").read_text())
    assert receipt["status"] == "FAIL"
    assert expected_error in receipt["error"]
