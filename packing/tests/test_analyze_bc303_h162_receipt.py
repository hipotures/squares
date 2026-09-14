"""Receipt-only H-162 comparison, without invoking the BC303 target sweep."""

from __future__ import annotations

import pytest

from devtools.analyze_bc303_h162_receipt import analysis_revision, analyze_receipt


def receipt(c_mass: int, s_mass: int) -> dict[str, object]:
    rows = [
        {
            "source_index": index,
            "reflected": False,
            "c_minimum": c_mass if index == 0 else c_mass + 1,
            "s_first_owner_minimum": s_mass if index == 0 else s_mass + 1,
        }
        for index in range(181)
    ]
    rows.append(
        {
            "source_index": 0,
            "reflected": True,
            "c_minimum": c_mass + 1,
            "s_first_owner_minimum": s_mass + 1,
        }
    )

    def minimum(mass: int) -> dict[str, object]:
        return {"integer_charge": mass, "source_index": 0, "reflected": False}

    def witness(role: str, mass: int) -> dict[str, object]:
        return {"role": role, **minimum(mass)}

    return {
        "experiment": "exp-158",
        "source_revision": "39714308ce2081abbd76624387d134fee4be6deb",
        "source_file": (
            "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/"
            "bc-293-measure-free-96-25.json"
        ),
        "executing_revision": "1" * 40,
        "atom_count": 377,
        "integer_total_mass": 45_048_398,
        "eligible_source_charts": 182,
        "distinct_orientations": 181,
        "c_threshold": 4_524_200,
        "s_first_owner_threshold": 4_524_185,
        "c_minimum": minimum(c_mass),
        "s_first_owner_minimum": minimum(s_mass),
        "c_witness": witness("C", c_mass),
        "s_first_owner_witness": witness("S_first_owner", s_mass),
        "per_chart": rows,
    }


@pytest.mark.parametrize(
    ("c_mass", "s_mass", "branch", "helper"),
    [
        (
            4_524_131,
            4_524_132,
            "low_c_requires_rational_replay",
            "reject_only_after_admitted_c_replay",
        ),
        (4_524_132, 4_524_131, "sufficient_filter_failed_only", "unresolved_actual_s"),
        (4_524_132, 4_524_132, "sufficient_filter_passed", "proved_if_exp158_admitted"),
    ],
)
def test_ordered_conditional_branches(
    c_mass: int, s_mass: int, branch: str, helper: str
) -> None:
    result = analyze_receipt(receipt(c_mass, s_mass))
    assert result["conditional_filter_branch"] == branch
    assert result["conditional_helper_implication"] == helper
    assert str(result["admission"]).startswith("conditional:")


def test_duplicate_chart_refused() -> None:
    value = receipt(4_524_132, 4_524_132)
    rows = value["per_chart"]
    assert isinstance(rows, list)
    rows[-1] = rows[0]
    with pytest.raises(ValueError, match="duplicate source chart"):
        analyze_receipt(value)


def test_changed_source_refused() -> None:
    value = receipt(4_524_132, 4_524_132)
    value["source_revision"] = "2" * 40
    with pytest.raises(ValueError, match="source_revision differs"):
        analyze_receipt(value)


def test_wrong_analysis_revision_refused() -> None:
    with pytest.raises(ValueError, match="wrong H-162 analysis checkout revision"):
        analysis_revision("0" * 40)


def test_minimum_must_match_its_chart() -> None:
    value = receipt(4_524_132, 4_524_132)
    minimum = value["c_minimum"]
    assert isinstance(minimum, dict)
    minimum["source_index"] = 1
    with pytest.raises(ValueError, match="disagrees with its covered chart"):
        analyze_receipt(value)
