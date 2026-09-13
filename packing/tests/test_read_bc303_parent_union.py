"""Synthetic geometry and source-boundary controls for the BC303 parent reader."""

# ruff: noqa: SLF001
# pyright: reportPrivateUsage=false

from __future__ import annotations

import hashlib
from fractions import Fraction
from pathlib import Path

import pytest

from devtools import read_bc303_parent_union as reader

REPO = Path(__file__).resolve().parents[2]


def test_closed_union_counts_contact_atoms_once() -> None:
    atoms: tuple[reader.Atom, ...] = (
        ((Fraction(0), Fraction(0)), Fraction(1, 4)),
        ((Fraction(1), Fraction(1, 2)), Fraction(1, 3)),
        ((Fraction(2), Fraction(1, 2)), Fraction(1, 5)),
        ((Fraction(2) + Fraction(1, 10), Fraction(1, 2)), Fraction(1, 7)),
    )
    first = (Fraction(0), Fraction(0), Fraction(1), Fraction(1))
    second = (Fraction(1), Fraction(0), Fraction(2), Fraction(1))
    assert reader.parent_union_mass(atoms, (first,)) == Fraction(7, 12)
    assert reader.parent_union_mass(atoms, (first, second)) == Fraction(47, 60)
    assert reader.parent_union_mass(atoms, (first, first)) == Fraction(7, 12)


def test_parent_geometry_refuses_invalid_squares() -> None:
    atoms: tuple[reader.Atom, ...] = (((Fraction(0), Fraction(0)), Fraction(1)),)
    with pytest.raises(reader.ParentUnionError, match="empty"):
        reader.parent_union_mass(atoms, ())
    with pytest.raises(reader.ParentUnionError, match="unit square"):
        reader.parent_union_mass(atoms, ((Fraction(0), Fraction(0), Fraction(2), Fraction(1)),))
    with pytest.raises(reader.ParentUnionError, match="outside container"):
        reader.parent_union_mass(
            atoms, ((Fraction(-1), Fraction(0), Fraction(0), Fraction(1)),)
        )


def test_source_forgery_and_duplicate_keys_are_refused_before_scan() -> None:
    data = (REPO / reader.SOURCE_PATH).read_bytes()
    assert reader.parse_measure(data)
    with pytest.raises(reader.ParentUnionError, match="source bytes changed"):
        reader.parse_measure(data + b"\n")
    duplicate = b'{"atoms":[],"atoms":[]}'
    with pytest.raises(reader.ParentUnionError, match="duplicate JSON key"):
        reader.parse_measure(duplicate, expected_sha256=hashlib.sha256(duplicate).hexdigest())


def test_revision_and_executing_reader_binding_before_scan(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    measure = reader.load_bound_measure(REPO)
    assert measure.source_revision == reader.SOURCE_REVISION
    assert measure.source_sha256 == reader.SOURCE_SHA256
    assert len(measure.atoms) == 377

    original_git = reader._git

    def forged_git(repository: Path, *arguments: str) -> bytes:
        if arguments == ("cat-file", "blob", f"{reader.SOURCE_REVISION}:{reader.SOURCE_PATH}"):
            return b"forged source"
        return original_git(repository, *arguments)

    monkeypatch.setattr(reader, "_git", forged_git)
    with pytest.raises(reader.ParentUnionError, match="source differs"):
        reader.load_bound_measure(REPO)

    monkeypatch.setattr(reader, "_git", original_git)

    def forged_reader_git(repository: Path, *arguments: str) -> bytes:
        if arguments == (
            "cat-file",
            "blob",
            f"{measure.implementation_revision}:{reader.READER_PATH}",
        ):
            return b"forged reader"
        return original_git(repository, *arguments)

    monkeypatch.setattr(reader, "_git", forged_reader_git)
    with pytest.raises(reader.ParentUnionError, match="executing reader differs"):
        reader.load_bound_measure(REPO)
