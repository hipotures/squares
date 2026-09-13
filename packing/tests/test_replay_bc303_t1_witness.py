"""Exact and adversarial controls for the literal BC303 T1 witness reader."""

# The tests exercise independent reconstruction helpers at their trust boundaries.
# pyright: reportPrivateUsage=false
# ruff: noqa: SLF001

from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from fractions import Fraction
from pathlib import Path
from typing import cast

import pytest

from devtools import replay_bc303_t1_witness as replay

REPO = Path(__file__).resolve().parents[2]


def _measure_document() -> dict[str, object]:
    return replay.strict_json_bytes(REPO.joinpath(replay.MEASURE_PATH).read_bytes(), "measure")


def test_bound_replay_emits_the_closed_narrow_determination() -> None:
    record = replay.replay(REPO)
    replay.validate_record(record)
    witness = cast(dict[str, object], record["witness"])
    determination = cast(dict[str, object], record["determination"])
    memberships = cast(list[dict[str, object]], record["memberships"])

    assert len(cast(list[object], record["sources"])) == 18
    assert len(memberships) == 377
    assert [row["index"] for row in memberships if row["inside_core"]] == list(
        replay.CAPTURED_INDICES
    )
    assert witness["labels"] == [3, 4, 11, 12]
    assert witness["captured_mass"] == "800003/800000"
    assert witness["surplus"] == "3/800000"
    assert witness["named_strict_inequality_holds"] is False
    assert determination == {
        "outcome": "rejected",
        "claim": (
            "for every X in the bottom-left one-corner role-C domain with labels 0 and "
            "15 absent, S(X) > epsilon"
        ),
        "scope": "the named one-corner BC303 T1 local surplus inequality only",
        "global_routing": "not-claimed",
        "n11_lower_bound": "not-claimed",
        "minimum_surplus": "not-claimed",
    }
    assert replay.encode_record(record) == replay.encode_record(deepcopy(record))


def test_source_binding_rejects_changed_missing_and_duplicate_json_bytes() -> None:
    sources = {source.path: (REPO / source.path).read_bytes() for source in replay.SOURCES}
    replay.validate_source_bytes(sources)

    changed = dict(sources)
    changed[replay.SOURCES[0].path] += b"\n"
    with pytest.raises(replay.T1ReplayError, match="source bytes changed"):
        replay.validate_source_bytes(changed)

    missing = dict(sources)
    del missing[replay.SOURCES[-1].path]
    with pytest.raises(replay.T1ReplayError, match="source path set"):
        replay.validate_source_bytes(missing)

    with pytest.raises(replay.T1ReplayError, match="duplicate JSON object key"):
        replay.strict_json_bytes(b'{"atoms":[],"atoms":[]}\n', "measure")


def test_same_total_d4_measure_mutation_cannot_preserve_the_witness() -> None:
    document = _measure_document()
    atoms = cast(list[list[str]], document["atoms"])
    delta = Fraction(1, replay.WEIGHT_SCALE)
    for index in range(8):
        atoms[index][2] = str(Fraction(atoms[index][2]) + delta)
    for index in range(32, 40):
        atoms[index][2] = str(Fraction(atoms[index][2]) - delta)

    measure = replay._parse_measure(document)
    assert measure.total_mass == replay.TOTAL_MASS
    with pytest.raises(replay.T1ReplayError, match="atom capture or T1 allowance"):
        replay._literal_witness(measure)


def test_closed_membership_distinguishes_core_edges_vertices_and_parent_only_points() -> None:
    center = (Fraction(1, 2), Fraction(1, 2))
    ray = (Fraction(1), Fraction(0))
    edge = (replay.CORE_LOWER, Fraction(1, 2))
    vertex = (replay.CORE_UPPER, replay.CORE_UPPER)
    parent_only = (Fraction(0), Fraction(1, 2))
    just_outside = (replay.CORE_UPPER + Fraction(1, replay.WEIGHT_SCALE), Fraction(1, 2))

    assert replay.closed_core_membership(edge, center, ray)[0]
    assert replay.closed_core_membership(vertex, center, ray)[0]
    assert not replay.closed_core_membership(parent_only, center, ray)[0]
    assert 0 <= parent_only[0] <= 1
    assert 0 <= parent_only[1] <= 1
    assert not replay.closed_core_membership(just_outside, center, ray)[0]


def test_complete_labels_preserve_zero_sign_bin_wrap_and_axis_aliases() -> None:
    zero = (Fraction(0), Fraction(0))
    ray = (Fraction(1), Fraction(0))
    half = replay.HALF_CORE_SIDE
    synthetic_mark = (zero,)

    assert replay.complete_labels(zero, ray, synthetic_mark, half) == list(range(8))
    assert replay.complete_labels((half, Fraction(0)), ray, synthetic_mark, half) == [
        0,
        5,
        6,
        7,
    ]
    assert replay.complete_labels((half, half), ray, synthetic_mark, half) == [0, 7]
    assert (
        replay.complete_labels(
            (half + Fraction(1, replay.WEIGHT_SCALE), Fraction(0)),
            ray,
            synthetic_mark,
            half,
        )
        == []
    )
    literal_center = (Fraction(1, 2), Fraction(1, 2))
    assert replay.complete_labels(literal_center, ray, replay.MARKS, half) == [3, 4, 11, 12]
    assert replay.complete_labels(
        literal_center, (Fraction(0), Fraction(1)), replay.MARKS, half
    ) == [
        3,
        4,
        11,
        12,
    ]
    assert replay._axis_aliases() == [
        {"folded_index": 0, "reflected": False, "canonical_axis": ["1", "0"]},
        {"folded_index": 0, "reflected": True, "canonical_axis": ["1", "0"]},
    ]


def test_owner_identity_and_record_scope_mutations_are_refused() -> None:
    with pytest.raises(replay.T1ReplayError, match="repeats an owner identity"):
        replay.unique_owner_surplus(
            (("same-owner", replay.CAPTURED_MASS), ("same-owner", replay.CAPTURED_MASS))
        )

    record = replay.replay(REPO)
    determination = cast(dict[str, object], record["determination"])
    determination["global_routing"] = "established"
    with pytest.raises(replay.T1ReplayError, match="overstates"):
        replay.validate_record(record)


def test_cli_atomically_writes_the_same_strict_record_as_stdout(tmp_path: Path) -> None:
    output = tmp_path / "t1.json"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "devtools.replay_bc303_t1_witness",
            "--repository",
            str(REPO),
            "--output",
            str(output),
        ),
        cwd=REPO / "packing",
        check=False,
        capture_output=True,
    )

    assert result.returncode == 0
    assert result.stderr == b""
    assert result.stdout == output.read_bytes()
    retained = replay.strict_json_bytes(output.read_bytes(), "retained record")
    replay.validate_record(retained)


def test_cli_refusal_is_nonzero_and_does_not_publish(tmp_path: Path) -> None:
    output = tmp_path / "refused.json"
    result = subprocess.run(
        (
            sys.executable,
            "-m",
            "devtools.replay_bc303_t1_witness",
            "--repository",
            str(tmp_path),
            "--output",
            str(output),
        ),
        cwd=REPO / "packing",
        check=False,
        capture_output=True,
    )

    assert result.returncode == 2
    assert result.stdout == b""
    refusal = json.loads(result.stderr)
    assert refusal["status"] == "refused"
    assert not output.exists()
