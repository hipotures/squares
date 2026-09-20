"""Reader-facing result coverage in README.md."""

from __future__ import annotations

from devtools.check_readme import result_coverage_problems


def test_new_results_covers_both_novelty_labels_and_rejects_unknown_ids() -> None:
    results: list[dict[str, object]] = [
        {"id": "T-001", "novelty": "apparently-novel"},
        {"id": "T-002", "novelty": "confirmed-novel"},
        {"id": "T-003", "novelty": "previously-published"},
    ]
    text = """# Front door

## New Results

T-001, T-003, and T-999.

## Survey
"""
    assert result_coverage_problems(text, results) == [
        "README.md: New Results does not name novel result T-002",
        "README.md: New Results names unregistered result T-999",
    ]

    final_section = "# Front door\n\n## New Results\n\nT-001 and T-002.\n"
    assert result_coverage_problems(final_section, results) == []
