"""A pull request is the template, not a session chronology.

#196 and #197 filled `.github/PULL_REQUEST_TEMPLATE.md`. Session-141's first #201
draft, and the #199/#200 drafts, opened with a cost sentence and a probe list.
`devtools.check_pr_description` is the contract those later drafts skipped.
"""

from __future__ import annotations

from pathlib import Path

from devtools.check_pr_description import (
    CHANGE_COLUMNS,
    DISPOSITION_COLUMNS,
    TEMPLATE,
    check,
    headings,
)
from devtools.render_pr_rollup import render_agenda_closeout

REPO = Path(__file__).resolve().parents[2]


def _table(columns: tuple[str, ...], row: tuple[str, ...]) -> str:
    header = "| " + " | ".join(columns) + " |"
    rule = "| " + " | ".join("---" for _ in columns) + " |"
    data = "| " + " | ".join(row) + " |"
    return f"{header}\n{rule}\n{data}"


FILLED = "\n".join(
    (
        "## What this branch cost",
        "",
        "Not a terminal agenda close. G3 of BC-357 / think-qqzs.",
        "",
        "## New Results and Their Significance",
        "",
        "Omitted: no result registered.",
        "",
        "## Results and Dispositions",
        "",
        _table(
            DISPOSITION_COLUMNS,
            (
                "G3 reader",
                "Slack families accepted",
                "`test_reader.py`",
                "Tooling gap closed",
                "continue via `think-qqzs`",
            ),
        ),
        "",
        "## Changes by Purpose",
        "",
        _table(
            CHANGE_COLUMNS,
            (
                "Reader",
                "K2 `best <= 1`; K3 `total >= n`",
                "`independent_ceiling_reader.py`",
            ),
        ),
        "",
        "## Validation",
        "",
        "- Local: five tests passed.",
        "- Hosted: packing-required pending.",
        "",
        "## Documentation and Replanning",
        "",
        "- Selected next entry: `think-qqzs`",
        "- Deferred: Route S",
        "",
        "## Limits",
        "",
        "This does not move s(11).",
        "",
    )
)

CHRONOLOGY = """\
Stacked on #200. Session-141 eight-hour n<100 research loop.

**Cost.** T-029 retain (covering 650 s + decide). exp-164 2516 s.

T-030 retains `s(18) >= 4679/1000`. H-218 stays unconfirmed.

Do not merge. Do not close think-qqzs.
"""


def test_the_in_tree_template_still_carries_the_or9_headings() -> None:
    problems = check(TEMPLATE.read_text(encoding="utf-8"), filled=False)
    assert problems == []
    assert headings(TEMPLATE.read_text(encoding="utf-8"))[:1] == ["What this branch cost"]


def test_a_filled_template_body_is_accepted() -> None:
    assert check(FILLED, filled=True) == []


def test_a_session_chronology_is_refused() -> None:
    problems = check(CHRONOLOGY, filled=True)
    assert problems
    assert any("no `##` headings" in item for item in problems)


def test_the_cost_heading_has_to_come_first() -> None:
    body = FILLED.replace("## What this branch cost\n\n", "## Notes\n\n", 1)
    problems = check(body, filled=True)
    assert any("first heading" in item for item in problems)


def test_empty_tables_pass_the_template_and_fail_a_filled_body() -> None:
    skeleton = TEMPLATE.read_text(encoding="utf-8")
    assert check(skeleton, filled=False) == []
    problems = check(skeleton, filled=True)
    assert any("no data row" in item for item in problems)


def test_an_agenda_closeout_render_fills_the_contract() -> None:
    """The generated W10 block is already the template from Results down."""
    agenda = {
        "id": "agenda-999",
        "updated": "2026-09-03",
        "items": [
            {
                "id": "BC-999",
                "bead": "think-only",
                "outcomes": [
                    {
                        "scope": "one exact certificate",
                        "classification": "achieved",
                        "result": "The certificate replayed exactly.",
                        "evidence": ["A passing replay."],
                        "disposition": "retire-success",
                        "follow_up": None,
                    }
                ],
            }
        ],
        "closeout": {
            "changes": [
                {
                    "name": "adoption",
                    "result": "Installed the reviewed packet.",
                    "paths": ["packing/cases/example.py"],
                }
            ],
            "validation": [
                {"scope": "Local", "status": "passed", "evidence": "Three tests."},
                {"scope": "Hosted", "status": "passed", "evidence": "packing-required."},
            ],
            "documentation_review": [
                {"path": "README.md", "decision": "updated", "reason": "New bound."}
            ],
            "replanning": {
                "operator_input": {"status": "unchanged", "note": "No revision."},
                "candidates": [
                    {
                        "priority": 0,
                        "bead": "think-next",
                        "workflow": "research-loop",
                        "rationale": "The remaining rung.",
                    }
                ],
                "selected": {
                    "bead": "think-next",
                    "workflow": "research-loop",
                    "rationale": "Highest-ranked valid continuation.",
                },
            },
        },
    }
    rendered = "## What this branch cost\n\nstub\n" + render_agenda_closeout(agenda)
    assert check(rendered, filled=True) == []


def test_the_template_lives_at_the_repository_root() -> None:
    assert TEMPLATE == REPO / ".github" / "PULL_REQUEST_TEMPLATE.md"
    assert TEMPLATE.is_file()
