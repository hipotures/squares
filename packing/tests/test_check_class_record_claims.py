"""A retained class record may not also state the unconditional claim or id.

The gate refuses such a record when it decides one; this is the check on the bytes that
are kept, which is what nothing covered when `exp-219-n11-96-25-clip-covering.json` was
retained carrying the unconditional id (review finding L3).
"""

from __future__ import annotations

import json
from pathlib import Path

from devtools.check_class_record_claims import EXEMPT, check, problems

REPO = Path(__file__).resolve().parents[2]


def test_the_repository_as_it_stands_passes() -> None:
    assert check() == []


def test_the_one_exemption_still_has_the_shape_it_is_exempt_for() -> None:
    """A stale exemption is a failure, so it cannot outlive its reason."""
    for relative in EXEMPT:
        record = json.loads((REPO / relative).read_text(encoding="utf-8"))
        assert record["variant"] == "class"
        assert problems(record) != []


def test_a_class_record_stating_the_unconditional_claim_or_id_is_reported(
    tmp_path: Path,
) -> None:
    root = tmp_path
    (root / "results").mkdir()
    (root / "results/bad.json").write_text(
        json.dumps(
            {
                "id": "C-n011-fractional-96-25",
                "claim": "s(11) >= 96/25",
                "variant": "class",
                "corner_clip": "1/2",
            }
        ),
        encoding="utf-8",
    )
    failures = check(root)
    assert any("unconditional claim" in line for line in failures)
    assert any("unconditional id" in line for line in failures)
    # The exemption is by exact repository-relative path, so it does not cover this one.
    assert any("no longer has" in line for line in failures)


def test_a_class_record_in_the_class_strings_is_accepted(tmp_path: Path) -> None:
    (tmp_path / "good.json").write_text(
        json.dumps(
            {
                "id": "C-n011-fractional-96-25-clip-1-2",
                "claim": "corner class d = 1/2 excluded at s(11) >= 96/25",
                "variant": "class",
                "corner_clip": "1/2",
            }
        ),
        encoding="utf-8",
    )
    # Only the stale-exemption line, since the retained exp-219 is not under tmp_path.
    assert [line for line in check(tmp_path) if "no longer has" not in line] == []


def test_a_corner_clip_without_the_variant_is_checked_too(tmp_path: Path) -> None:
    """Leaving the variant out must not leave the record unchecked."""
    (tmp_path / "bare.json").write_text(
        json.dumps({"claim": "s(11) >= 96/25", "corner_clip": "1/2"}), encoding="utf-8"
    )
    assert any("unconditional claim" in line for line in check(tmp_path))


def test_an_unclipped_record_is_left_alone(tmp_path: Path) -> None:
    (tmp_path / "plain.json").write_text(
        json.dumps(
            {"id": "C-n011-fractional-96-25", "claim": "s(11) >= 96/25", "variant": None}
        ),
        encoding="utf-8",
    )
    assert [line for line in check(tmp_path) if "no longer has" not in line] == []
