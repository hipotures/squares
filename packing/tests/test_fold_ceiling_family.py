"""The upright-square fold sums only one square's two writings and preserves the total.

The retained cases re-fold the two raw families Session 144 merged by scratch script
and compare against the retained merged bytes. Only the mathematical content is
compared -- the container and net, the placements as exact rationals in order, and the
total weight -- because the retained records carry the scratch script's own provenance
block under a different tool name; everything else in those records is the same field
for the same value. Row order is part of that content: the fold emits keys in order of
first appearance, so the same rows always fold to the same sequence.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from devtools.fold_ceiling_family import differences, fold, main

RESULTS = (
    Path(__file__).resolve().parents[1]
    / "campaign/series/series-000-smoke-and-calibration/results/agenda-040"
)
RETAINED = [
    ("exp-214-n13-399-100-family.json", "exp-214-n13-399-100-family-merged.json", 8),
    ("exp-218-n17-23-5-family.json", "exp-218-n17-23-5-family-merged.json", 0),
]


def family(placements: list[list[str]], **overrides: Any) -> dict[str, Any]:
    """A synthetic family whose header agrees with its own rows unless asked otherwise.

    The declared total is computed rather than typed, because `fold` now refuses a
    record whose `total_weight` disagrees with its placements: the fixtures used to
    declare `"0"` against rows summing to 1 and were accepted without a word, which is
    what review finding M2 named.
    """

    total = sum((Fraction(row[3]) for row in placements), Fraction(0))
    return {
        "n": 2,
        "outer_side": "2",
        "square_side": "1/2",
        "half_tangents": ["0", "1/5", "1"],
        "placements": placements,
        "total_weight": str(total),
        "total_weight_float": float(total),
    } | overrides


def test_the_two_writings_of_one_upright_square_fold_and_the_total_is_preserved() -> None:
    record = family(
        [
            ["0", "1/4", "1/4", "1/3", "1/2"],
            ["1/5", "3/4", "1/4", "1/7", "1/2"],
            ["1", "1/4", "1/4", "1/6", "1/2"],
        ]
    )
    folded = fold(record)
    assert folded["placements"] == [
        ["0", "1/4", "1/4", "1/2", "1/2"],
        ["1/5", "3/4", "1/4", "1/7", "1/2"],
    ]
    assert Fraction(folded["total_weight"]) == Fraction(1, 3) + Fraction(1, 7) + Fraction(1, 6)
    assert folded["provenance"]["merge"] == {
        "tool": "devtools.fold_ceiling_family",
        "rule": "fold half-tangent 1 to 0 at the same centre and side, summing weights",
        "placements_before": 3,
        "placements_after": 2,
        "folded": 1,
        "total_weight_preserved": str(Fraction(27, 42)),
    }
    assert record["placements"] == [
        ["0", "1/4", "1/4", "1/3", "1/2"],
        ["1/5", "3/4", "1/4", "1/7", "1/2"],
        ["1", "1/4", "1/4", "1/6", "1/2"],
    ]
    assert "merge" not in record.get("provenance", {})


def test_a_foreign_duplicate_aborts_instead_of_summing_its_weight() -> None:
    tilted = family(
        [
            ["1/5", "1/4", "1/4", "1/3", "1/2"],
            ["1/5", "1/4", "1/4", "1/3", "1/2"],
        ]
    )
    with pytest.raises(ValueError, match="not one upright square"):
        fold(tilted)

    twice_upright = family(
        [
            ["0", "1/4", "1/4", "1/3", "1/2"],
            ["0", "1/4", "1/4", "1/3", "1/2"],
        ]
    )
    with pytest.raises(ValueError, match="not one upright square"):
        fold(twice_upright)

    three_writings = family(
        [
            ["0", "1/4", "1/4", "1/3", "1/2"],
            ["1", "1/4", "1/4", "1/3", "1/2"],
            ["1", "1/4", "1/4", "1/3", "1/2"],
        ]
    )
    with pytest.raises(ValueError, match="not one upright square"):
        fold(three_writings)


def test_a_different_centre_or_side_is_not_a_duplicate() -> None:
    record = family(
        [
            ["0", "1/4", "1/4", "1/3", "1/2"],
            ["1", "1/4", "3/4", "1/3", "1/2"],
            ["1", "1/4", "1/4", "1/3", "1/4"],
        ]
    )
    folded = fold(record)
    assert [row[0] for row in folded["placements"]] == ["0", "0", "0"]
    assert folded["provenance"]["merge"]["folded"] == 0
    assert Fraction(folded["total_weight"]) == 1


@pytest.mark.parametrize(("raw", "merged", "expected_folded"), RETAINED)
def test_retained_families_refold_to_the_retained_merged_bytes(
    raw: str, merged: str, expected_folded: int
) -> None:
    record: dict[str, Any] = json.loads((RESULTS / raw).read_text(encoding="utf-8"))
    expected: dict[str, Any] = json.loads((RESULTS / merged).read_text(encoding="utf-8"))
    folded = fold(record)
    assert differences(folded, expected) == []
    assert folded["placements"] == expected["placements"]
    assert Fraction(folded["total_weight"]) == Fraction(expected["total_weight"])
    assert folded["provenance"]["merge"]["folded"] == expected_folded
    assert Fraction(folded["total_weight"]) == sum(
        (Fraction(row[3]) for row in record["placements"]), Fraction(0)
    )


def test_check_reports_a_difference_and_exits_one(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "family.json"
    source.write_text(
        json.dumps(
            family([["0", "1/4", "1/4", "1/3", "1/2"], ["1", "1/4", "1/4", "1/6", "1/2"]])
        ),
        encoding="utf-8",
    )
    expected = tmp_path / "merged.json"
    expected.write_text(
        json.dumps(family([["0", "1/4", "1/4", "1/2", "1/2"]]) | {"total_weight": "1/2"}),
        encoding="utf-8",
    )
    destination = tmp_path / "out.json"
    assert main([str(source), str(destination), "--check", str(expected)]) == 0
    assert json.loads(destination.read_text(encoding="utf-8"))["total_weight"] == "1/2"

    wrong = tmp_path / "wrong.json"
    wrong.write_text(
        json.dumps(family([["0", "1/4", "1/4", "1/3", "1/2"]]) | {"total_weight": "1/3"}),
        encoding="utf-8",
    )
    assert main([str(source), str(destination), "--check", str(wrong)]) == 1
    printed = capsys.readouterr().out
    assert "total weight: fold 1/2 != expected 1/3" in printed


def test_check_refuses_to_overwrite_the_source_or_the_expected_bytes(tmp_path: Path) -> None:
    source = tmp_path / "family.json"
    source.write_text(json.dumps(family([["0", "1/4", "1/4", "1/3", "1/2"]])), encoding="utf-8")
    with pytest.raises(SystemExit):
        main([str(source), str(source)])
    with pytest.raises(SystemExit):
        main([str(source), str(tmp_path / "out.json"), "--check", str(tmp_path / "out.json")])


def test_a_header_that_disagrees_with_its_own_rows_is_refused(tmp_path: Path) -> None:
    """M2: the declared total is read, and a record is not corrected into agreement.

    The old guard compared the row sum with itself and could not fire, while
    `total_weight` was overwritten with the recomputed sum, so a family whose header
    said `0` against rows summing to 1 was accepted and then reported as preserved.
    """
    record = family([["0", "1/4", "1/4", "1/3", "1/2"]], total_weight="0")
    with pytest.raises(ValueError, match="not the sum of its own placements"):
        fold(record)

    source = tmp_path / "family.json"
    source.write_text(json.dumps(record), encoding="utf-8")
    assert main([str(source), str(tmp_path / "out.json")]) == 2
    assert not (tmp_path / "out.json").exists()


def test_the_declared_total_is_what_the_fold_is_checked_against() -> None:
    """The emitted placement strings are summed back and must equal that same total."""
    folded = fold(
        family([["0", "1/4", "1/4", "1/3", "1/2"], ["1", "1/4", "1/4", "1/6", "1/2"]])
    )
    assert folded["total_weight"] == "1/2"
    assert folded["provenance"]["merge"]["total_weight_preserved"] == "1/2"
    assert sum((Fraction(row[3]) for row in folded["placements"]), Fraction(0)) == Fraction(
        1, 2
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [("n", 3), ("outer_side", "3"), ("square_side", "1/3"), ("half_tangents", ["0", "1"])],
)
def test_check_reports_a_different_container_even_with_identical_rows(
    field: str, value: object, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """M3: identical placements under another container are not a reproduction."""
    placements = [["0", "1/4", "1/4", "1/3", "1/2"]]
    source = tmp_path / "family.json"
    source.write_text(json.dumps(family(placements)), encoding="utf-8")
    other = tmp_path / "other.json"
    other.write_text(json.dumps(family(placements) | {field: value}), encoding="utf-8")
    destination = tmp_path / "out.json"
    assert main([str(source), str(destination), "--check", str(other)]) == 1
    printed = capsys.readouterr().out
    assert field in printed
    assert '"matches": false' in printed
    # The same bytes against themselves still match.
    assert main([str(source), str(destination), "--check", str(source)]) == 0


def test_row_order_is_part_of_the_contract_and_is_reported(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """A permutation of the same rows is a difference, and the docstrings say so."""
    rows = [["0", "1/4", "1/4", "1/3", "1/2"], ["1/5", "3/4", "1/4", "1/7", "1/2"]]
    source = tmp_path / "family.json"
    source.write_text(json.dumps(family(rows)), encoding="utf-8")
    permuted = tmp_path / "permuted.json"
    permuted.write_text(json.dumps(family(list(reversed(rows)))), encoding="utf-8")
    assert main([str(source), str(tmp_path / "out.json"), "--check", str(permuted)]) == 1
    assert "the same placements in a different order" in capsys.readouterr().out


def test_a_placement_written_as_a_json_float_is_refused(tmp_path: Path) -> None:
    """L2: an exact-rational reader does not binarise a float it was handed."""
    with pytest.raises(ValueError, match="exact rationals are written as strings"):
        fold(
            family([["0", "1/4", "1/4", "1/3", "1/2"]])
            | {"placements": [[0, 0.25, 0.25, 1, 0.5]]}
        )
    with pytest.raises(ValueError, match="exact rationals are written as strings"):
        fold(family([["0", "1/4", "1/4", "1/3", "1/2"]], total_weight=0.3333))
    source = tmp_path / "family.json"
    source.write_text('{"placements": [[0.0, 0.25, 0.25, 1.0, 0.5]]}', encoding="utf-8")
    assert main([str(source), str(tmp_path / "out.json")]) == 2


def test_a_malformed_family_prints_a_refusal_rather_than_a_traceback(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "family.json"
    source.write_text("{not json", encoding="utf-8")
    assert main([str(source), str(tmp_path / "out.json")]) == 2
    printed = capsys.readouterr().out
    assert "is not JSON" in printed
    assert '"tool": "devtools.fold_ceiling_family"' in printed

    missing = tmp_path / "missing.json"
    missing.write_text(
        json.dumps({"placements": [["0", "0", "0", "1", "1/2"]]}), encoding="utf-8"
    )
    assert main([str(missing), str(tmp_path / "out.json")]) == 2
    assert "declares no total_weight" in capsys.readouterr().out
