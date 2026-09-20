"""The upright-square fold sums only one square's two writings and preserves the total.

The retained cases re-fold the two raw families Session 144 merged by scratch script
and compare against the retained merged bytes. Only the mathematical content is
compared -- placements as exact rationals and the total weight -- because the retained
records carry the scratch script's own provenance block under a different tool name;
everything else in those records is the same field for the same value.
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


def family(placements: list[list[str]]) -> dict[str, Any]:
    return {
        "n": 2,
        "outer_side": "2",
        "square_side": "1/2",
        "half_tangents": ["0", "1/5", "1"],
        "placements": placements,
        "total_weight": "0",
        "total_weight_float": 0.0,
    }


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
        json.dumps(family([["0", "1/4", "1/4", "1/3", "1/2"], ["1", "1/4", "1/4", "1/6", "1/2"]])),
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
