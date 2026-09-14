"""Compare an admitted exp-158 receipt with H-162's frozen integer cutoffs.

This tool reads JSON only. It checks 182 unique chart rows but not their exact eligible
set. Its output is conditional on exp-158's separate source, control, exact-manifest,
and witness admission; it never invokes the charge sweep.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

SOURCE_REVISION = "39714308ce2081abbd76624387d134fee4be6deb"
SOURCE_FILE = (
    "packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/"
    "bc-293-measure-free-96-25.json"
)
ATOM_COUNT = 377
TOTAL_MASS = 45_048_398
CHART_COUNT = 182
ORIENTATION_COUNT = 181
H160_C_THRESHOLD = 4_524_200
H160_S_THRESHOLD = 4_524_185
H162_THRESHOLD = 4_524_132
REPO = Path(__file__).resolve().parents[2]


def _mapping(value: object, name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _integer(value: object, name: str) -> int:
    if type(value) is not int:
        raise ValueError(f"{name} must be an integer")
    return value


def _expect(receipt: dict[str, Any], field: str, expected: object) -> None:
    actual = receipt.get(field)
    if type(actual) is not type(expected) or actual != expected:
        raise ValueError(f"{field} differs from the frozen exp-158 contract")


def analyze_receipt(value: object) -> dict[str, object]:
    """Return a conditional verdict candidate without asserting target admission."""
    receipt = _mapping(value, "exp-158 receipt")
    for field, expected in (
        ("experiment", "exp-158"),
        ("source_revision", SOURCE_REVISION),
        ("source_file", SOURCE_FILE),
        ("atom_count", ATOM_COUNT),
        ("integer_total_mass", TOTAL_MASS),
        ("eligible_source_charts", CHART_COUNT),
        ("distinct_orientations", ORIENTATION_COUNT),
        ("c_threshold", H160_C_THRESHOLD),
        ("s_first_owner_threshold", H160_S_THRESHOLD),
    ):
        _expect(receipt, field, expected)
    revision = receipt.get("executing_revision")
    if not isinstance(revision, str) or re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("executing_revision must be a full committed Git revision")

    rows = receipt.get("per_chart")
    if not isinstance(rows, list) or len(rows) != CHART_COUNT:
        raise ValueError("the exp-158 per-chart receipt is incomplete")
    seen: set[tuple[int, bool]] = set()
    for raw_row in rows:
        row = _mapping(raw_row, "per-chart row")
        index = _integer(row.get("source_index"), "source_index")
        if not 0 <= index <= 180:
            raise ValueError("source_index lies outside the frozen source grid")
        reflected = row.get("reflected")
        if type(reflected) is not bool:
            raise ValueError("reflected must be Boolean")
        key = (index, reflected)
        if key in seen:
            raise ValueError("duplicate source chart in exp-158 receipt")
        seen.add(key)
        if _integer(row.get("c_minimum"), "c_minimum") < 0:
            raise ValueError("c_minimum must be nonnegative")
        if _integer(row.get("s_first_owner_minimum"), "s_first_owner_minimum") < 0:
            raise ValueError("s_first_owner_minimum must be nonnegative")

    minima: dict[str, int] = {}
    for role, row_field, minimum_field, witness_field in (
        ("C", "c_minimum", "c_minimum", "c_witness"),
        (
            "S_first_owner",
            "s_first_owner_minimum",
            "s_first_owner_minimum",
            "s_first_owner_witness",
        ),
    ):
        minimum = _mapping(receipt.get(minimum_field), minimum_field)
        witness = _mapping(receipt.get(witness_field), witness_field)
        mass = _integer(minimum.get("integer_charge"), f"{minimum_field}.integer_charge")
        expected_mass = min(_integer(row[row_field], row_field) for row in rows)
        if mass != expected_mass:
            raise ValueError(f"{minimum_field} disagrees with the per-chart minimum")
        key = (
            _integer(minimum.get("source_index"), f"{minimum_field}.source_index"),
            minimum.get("reflected"),
        )
        if type(key[1]) is not bool:
            raise ValueError(f"{minimum_field}.reflected must be Boolean")
        if key not in seen:
            raise ValueError(f"{minimum_field} names no covered chart")
        matching_row = next(
            row for row in rows if (row["source_index"], row["reflected"]) == key
        )
        if matching_row[row_field] != mass:
            raise ValueError(f"{minimum_field} disagrees with its covered chart")
        if any(
            witness.get(field) != expected
            for field, expected in (
                ("role", role),
                ("integer_charge", mass),
                ("source_index", key[0]),
                ("reflected", key[1]),
            )
        ):
            raise ValueError(f"{witness_field} disagrees with the retained minimum")
        minima[role] = mass

    c_mass = minima["C"]
    s_mass = minima["S_first_owner"]
    if c_mass < H162_THRESHOLD:
        branch = "low_c_requires_rational_replay"
        helper = "reject_only_after_admitted_c_replay"
    elif s_mass < H162_THRESHOLD:
        branch = "sufficient_filter_failed_only"
        helper = "unresolved_actual_s"
    else:
        branch = "sufficient_filter_passed"
        helper = "proved_if_exp158_admitted"
    return {
        "experiment": "exp-160",
        "hypothesis": "H-162",
        "input_experiment": "exp-158",
        "input_executing_revision": revision,
        "source_revision": SOURCE_REVISION,
        "source_file": SOURCE_FILE,
        "c_minimum": c_mass,
        "s_first_owner_minimum": s_mass,
        "threshold_each": H162_THRESHOLD,
        "conditional_filter_branch": branch,
        "conditional_helper_implication": helper,
        "admission": (
            "conditional: verify exp-158 source, controls, complete manifest, "
            "and replay separately"
        ),
        "structural_check": (
            "182 unique rows checked; exact eligible-chart set requires "
            "external exp-158 admission"
        ),
        "scope": (
            "first-owner sufficient filter; no actual S pair, new target, or global s(11) claim"
        ),
    }


def analysis_revision(expected: str) -> str:
    """Bind this analyzer to the clean committed checkout that executed it."""
    actual = subprocess.run(
        ["git", "-C", str(REPO), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if re.fullmatch(r"[0-9a-f]{40}", expected) is None or expected != actual:
        raise ValueError("wrong H-162 analysis checkout revision")
    dirty = subprocess.run(
        ["git", "-C", str(REPO), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if dirty:
        raise ValueError("H-162 analysis requires a clean committed checkout")
    return actual


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--expect-analysis-revision", required=True)
    args = parser.parse_args()
    revision = analysis_revision(args.expect_analysis_revision)
    result = analyze_receipt(json.loads(args.input.read_text(encoding="utf-8")))
    result["analysis_revision"] = revision
    result["analysis_entry_point"] = "packing/devtools/analyze_bc303_h162_receipt.py"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(args.output),
                "conditional_filter_branch": result["conditional_filter_branch"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
