#!/usr/bin/env python3
"""Check README.md against the directory it describes.

`SYNOPSIS.md` is reconciled against the artifacts by `check_synopsis.py`; README was
not, and it drifted twice in one day for exactly that reason -- it restated defect
counts owned by `defects.yaml` and went stale behind them both times. The counts are
gone now, moved to the generated view that owns them. What is left is the part a
checker can hold: the layout tree, the report index, the links, and the work model.

Six checks:

1. **Every link resolves**, including anchors into other documents. README and SYNOPSIS
   cross-reference each other heavily and a dead link between them is invisible until
   someone clicks it. Shared with `check_synopsis.py`, which owns the implementation.
2. **The layout tree matches the directory.** Every top-level entry appears in the tree
   and every path the tree names exists. This is a hand-maintained view of generated
   truth, which is the shape of D-010, D-017, D-022 and D-028, and it was already wrong
   about seven files.
3. **The report index is complete.** The prose says "six research reports" and the table
   lists six; both must match what is in `docs/project/research/`.
4. **The defect summary is derived.** README may state whether the gate has caught a
   soundness defect, but may not repeat a numeric aggregate owned by `defects.yaml`.
5. **The work model agrees.** README and SYNOPSIS must expose the same numbered
   workflow entry points, the agent-session schema must be able to record them, the
   synopsis must define the work units those workflows produce, and retired workflow
   identifiers must not survive elsewhere in repository-owned text.
6. **New results are complete.** Every result classified as `apparently-novel` or
   `confirmed-novel` appears in the New Results section, and every concrete result ID
   named there exists in the register.

Every one of those that asks what is in the directory asks git, not the filesystem. A
README cannot be wrong about a file the repository does not hold, so such a file cannot
fail this check. `.gitignore` excludes `.claude/worktrees/`, where the harness puts
other agents' worktrees inside this checkout; the work-model text scan walked into one
and failed on a symlink into a `tree-head` checkout that had been removed, and read the
retired identifier out of that worktree's own sources on the way past.
`repo_scope.tracked_files` is the answer `check_class_record_claims` moved to after a
scratch JSON in `attic/` turned its step red (PR 207), and asking it here retires three
private walks that held three different skip sets. A tracked file this check cannot
read is a skip carrying its reason, printed but not failed, for the same reason: unread
bytes are not evidence of drift.

Usage: uv run --frozen python -m devtools.check_readme
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import NamedTuple

from devtools.check_synopsis import check_links
from devtools.repo_scope import tracked_files, vendored_directories
from sqpack.yamlio import safe_load

ROOT = Path(__file__).resolve().parent.parent
# The repository root. The reader-facing documents live there, not under packing/.
REPO = ROOT.parent
README = REPO / "README.md"
SYNOPSIS = REPO / "SYNOPSIS.md"
RESEARCH = REPO / "docs/project/research"
DEFECTS = ROOT / "defects.yaml"
RESULTS = ROOT / "frontier/results.yaml"
SESSION_SCHEMA = ROOT / "campaign/schemas/agent-session.schema.yaml"

NEW_RESULT_NOVELTY = frozenset({"apparently-novel", "confirmed-novel"})

WORK_UNITS = (
    "Packing exploration",
    "Campaign",
    "Series",
    "Agent session",
    "Workflow phase",
    "Focus",
    "Slice",
    "Hypothesis",
    "Experiment",
    "Round",
    "Run",
    "Result",
    "Ledger",
)

# Tooling rather than orientation content: lockfiles and build config, should either
# ever sit at the root, and LICENSE, which is legal boilerplate. The layout tree may
# draw LICENSE once the README grows its license summary, but its absence from a
# reader's map of the directory is not a documentation defect.
#
# What this set no longer names is everything gitignored -- `attic`, where the tbd
# checkout shortcut clones third-party repositories; `node_modules`, which the browser
# floor's own instruction and CI both create; the caches and `.venv`. The index does not
# list them, so nothing here has to remember to, and the two private skip sets that had
# drifted apart over that same question are gone with them.
NOT_CONTENT = {
    "uv.lock",
    "pyproject.toml",
    "LICENSE",
}

#: What every check that reads the tree says when there is no index to ask. Unlike the
#: class-record sweep, this check does not fall back to a walk with a stated bound: a
#: walk is the thing that was wrong, and the check is hardwired to this repository's own
#: documents.
#:
#: The first version of this comment justified that refusal by adding that there was no
#: caller for whom "no git here" is an ordinary case. That was false as written, and it
#: turned main red the same day. The negative-control worker is exactly such a caller --
#: `check_class_record_claims` names it in its own docstring, which is why that sweep
#: kept its walk -- and it ran every check against a source snapshot carrying no `.git`,
#: so the README controls read this line where they rehearse drift and did not fire. The
#: answer was not to reintroduce the walk but to give the snapshot the index it was
#: missing: `run_negative_controls.clone_tree` now makes each worker tree a git checkout
#: of itself, so that caller asks git like every other one and the control rehearses the
#: code the gate runs rather than a fallback.
NO_INDEX = "cannot ask git which files this repository tracks, so the directory is unknown"

# This is the repository-owned text surface, not the retained literature archive. The
# latter is source evidence and may use any ordinary phrase; a workflow migration does
# not rewrite it. Build products and caches are not product state.
WORK_MODEL_TEXT_SUFFIXES = {
    ".cfg",
    ".conf",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".jsonl",
    ".lock",
    ".md",
    ".py",
    ".rs",
    ".sh",
    ".svg",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
}
WORK_MODEL_TEXT_NAMES = {
    ".flowmarkignore",
    ".gitattributes",
    ".gitignore",
    ".python-version",
    "Makefile",
}
#: The retained literature archive's extractions and captures. Tracked, so the index
#: lists them, and excluded here for the reason the suffix list above gives: they are
#: source evidence, and a workflow migration does not rewrite what was archived.
ARCHIVE_PREFIXES = {
    ("packing", "resources", "papers"),
    ("packing", "resources", "web"),
}

#: The README spells its counts out, so the check has to know the word for each one it
#: might assert. The table stopped at ten and the report count reached eleven, at which
#: point the check silently started demanding the numeral instead -- a false failure
#: against correct prose. Keep it ahead of the counts it is asked about.
_SPELLED = {
    1: "one",
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
    16: "sixteen",
    17: "seventeen",
    18: "eighteen",
    19: "nineteen",
    20: "twenty",
}


#: W1 through W10. Bumping this is the deliberate half of adding a workflow; the other
#: half is the two orientation tables in README.md and SYNOPSIS.md, which this check
#: compares against the schema rather than against each other.
EXPECTED_NUMBERED_WORKFLOWS = 10


def layout_tree(text: str) -> str | None:
    """The fenced block that draws the directory, if README still has one."""
    # Anchored on the drawing, not on a path prefix. The tree used to be found by the
    # directory name it opened with, which broke the moment that directory moved; a
    # branch marker is what actually makes a fenced block a tree, and it survives
    # renames.
    #
    # Fences are paired opener-to-closer, with or without a language tag. The old
    # pattern required a bare ``` as the opener, so every ```shell block ahead of the
    # tree shifted the pairing by one and the tree was "found" mid-prose or not at all;
    # which blocks sit ahead of the tree is a presentation choice that must not decide
    # whether this check runs.
    for block in re.findall(r"^```[^\n]*\n(.*?)^```", text, re.DOTALL | re.MULTILINE):
        if "\u251c\u2500\u2500 " in block:
            return block
    return None


def tracked_paths(root: Path) -> tuple[Path, ...] | None:
    """Every file `root` tracks, relative to it, or `None` where there is no index.

    Asked again per question rather than cached: `main` puts three of them to one tree,
    and three `git ls-files` runs cost less than a stale answer would. A cache keyed on
    the root would make the listing a function of when it was first asked, which is the
    shape of the bug this module is fixing.
    """
    listed = tracked_files(root, ".")
    if listed is None:
        return None
    return tuple(path.relative_to(root) for path in listed)


def _submodule_parts(root: Path) -> set[tuple[str, ...]]:
    """Each declared submodule path, split. Git reports a gitlink, not the files inside.

    `tracked_files` therefore drops the submodule entirely, and without this `vendor`
    would stop being a top-level entry the layout tree has to draw. A declared submodule
    is content by declaration, which is the rule `repo_scope` already states.
    """
    return {Path(declared).parts for declared in vendored_directories(root)}


def meaningful_top_level_entries(root: Path) -> set[str] | None:
    """Top-level entries with durable content, or `None` where there is no index to ask.

    Durable means tracked. The walk this replaced had to recognise a cache-only
    directory by name to avoid counting a migration remnant as content; git does not
    list one at all, so the question stopped being asked.
    """
    tracked = tracked_paths(root)
    if tracked is None:
        return None
    held = {path.parts[0] for path in tracked}
    held |= {parts[0] for parts in _submodule_parts(root)}
    return {name for name in held if not name.startswith(".") and name not in NOT_CONTENT}


def content_names(root: Path) -> frozenset[str] | None:
    """Every bare name a nested tree entry may be drawn by, or `None` with no index.

    The tree draws nested entries by bare name, so `atlas` under `packing/` has no
    repo-relative path of its own and has to be matched by segment. Dot-prefixed paths
    are left out because the tree draws the visible directory: a name that exists only
    under `.github/` is not a name the reader's map is about.
    """
    tracked = tracked_paths(root)
    if tracked is None:
        return None
    names = {
        part
        for path in tracked
        if not any(segment.startswith(".") for segment in path.parts)
        for part in path.parts
    }
    return frozenset(names | {part for parts in _submodule_parts(root) for part in parts})


def check_layout(text: str) -> list[str]:
    """Every top-level entry is drawn, and every drawn path exists."""
    tree = layout_tree(text)
    if tree is None:
        return ["README.md: the layout tree is gone; this check has nothing to hold"]

    # Only a branch marker declares an entry. Continuation lines carry the description
    # of the entry above and start with a bare `|` column, which is why matching "first
    # word on the line" reported a prose word as a missing file.
    top = re.findall(r"^[├└]── ([A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*/?)", tree, re.MULTILINE)
    nested = re.findall(r"^│\s+[├└]── ([A-Za-z0-9_.-]+/?)", tree, re.MULTILINE)
    # A top-level entry is the first path segment: `docs/project/` lives under `docs`.
    drawn_top = {name.strip("/").split("/")[0] for name in top}
    drawn_any = drawn_top | {name.strip("/") for name in top + nested}

    on_disk = meaningful_top_level_entries(REPO)
    names = content_names(REPO)
    if on_disk is None or names is None:
        return [f"README.md: {NO_INDEX}"]

    problems = [
        f"README.md: {missing} exists but the layout tree does not show it"
        for missing in sorted(on_disk - drawn_top - {README.name})
    ]
    problems += [
        f"README.md: the layout tree shows {drawn}, which does not exist"
        for drawn in sorted(drawn_any)
        if not (REPO / drawn).exists() and drawn.split("/")[-1] not in names
    ]
    return problems


def check_reports(text: str) -> list[str]:
    """The prose count, the table, and the directory agree."""
    actual = sorted(p.name for p in RESEARCH.glob("research-*.md"))
    rows = re.findall(r"^\| \[([^\]]+)\]\(([^)]+)\)", text, re.MULTILINE)
    linked = {Path(target).name for _, target in rows if "docs/project/research/" in target}

    problems = [
        f"README.md: {gone} is not in the reports table"
        for gone in sorted(set(actual) - linked)
    ]
    problems += [
        f"README.md: the reports table lists {extra}, which does not exist"
        for extra in sorted(linked - set(actual))
    ]

    n = len(actual)
    word = _SPELLED.get(n, str(n))
    if not re.search(rf"\b({n}|{word})\s+research reports\b", text, re.IGNORECASE):
        problems.append(
            f"README.md: does not say there are {word} research reports (there are)"
        )
    return problems


def check_defect_summary(text: str) -> list[str]:
    """Keep the README's qualitative gate claim reconciled without copying counts."""
    data = safe_load(DEFECTS.read_text(encoding="utf-8"))
    normalized = re.sub(r"\s+", " ", text)
    gate_soundness = sum(
        1
        for defect in data["defects"]
        if defect["detected_by"] == "gate" and defect["class"] == "soundness"
    )
    zero_claim = "No soundness defect in the log was caught by it."
    problems: list[str] = []
    if gate_soundness == 0 and zero_claim not in normalized:
        problems.append(
            "README.md: must state the derived fact that the gate caught no soundness defect"
        )
    if gate_soundness != 0 and zero_claim in normalized:
        problems.append(
            "README.md: says the gate caught no soundness defect, but defects.yaml disagrees"
        )

    number = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten)"
    if re.search(rf"\bgate\b[^.]*\bcaught\s+{number}\s+defects?\b", normalized, re.IGNORECASE):
        problems.append(
            "README.md: repeats a numeric gate-defect aggregate owned by defects.yaml"
        )
    return problems


def result_coverage_problems(text: str, results: list[dict[str, object]]) -> list[str]:
    """Reconcile a New Results section with registered novel results."""
    section = re.search(
        r"^## New Results\s*$\n(?P<body>.*?)(?=^##\s|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if section is None:
        return ["README.md: has no New Results section"]

    registered = {str(result["id"]) for result in results}
    required = {
        str(result["id"]) for result in results if result.get("novelty") in NEW_RESULT_NOVELTY
    }
    named = set(re.findall(r"\bT-\d{3}\b", section.group("body")))

    problems = [
        f"README.md: New Results does not name novel result {result_id}"
        for result_id in sorted(required - named)
    ]
    problems.extend(
        f"README.md: New Results names unregistered result {result_id}"
        for result_id in sorted(named - registered)
    )
    return problems


def check_result_coverage(text: str) -> list[str]:
    """Load the results register and check the curated reader-facing section."""
    register = safe_load(RESULTS.read_text(encoding="utf-8"))
    return result_coverage_problems(text, register["results"])


def workflow_rows(text: str) -> list[tuple[str, str]]:
    """Numbered workflow rows in a Markdown table."""
    return re.findall(r"^\| (W\d+) \| `([^`]+)` \|", text, re.MULTILINE)


def work_model_text(root: Path) -> list[Path] | None:
    """Every repository-owned text file `root` tracks, or `None` with no index to ask."""
    tracked = tracked_paths(root)
    if tracked is None:
        return None
    return [
        root / path
        for path in tracked
        if (
            path.suffix.lower() in WORK_MODEL_TEXT_SUFFIXES
            or path.name in WORK_MODEL_TEXT_NAMES
        )
        and path.parts[:3] not in ARCHIVE_PREFIXES
    ]


class TextScan(NamedTuple):
    """What the work-model text sweep decided, and what it never got to read."""

    problems: list[str]
    skipped: list[str]


def scan_retired_workflow_identifiers(root: Path = REPO) -> TextScan:
    """Reject old controlled names without rewriting retained source evidence.

    A file the sweep cannot read is a skip carrying its reason, not a problem. The
    sweep is looking for a token, and not having read a file is not having found one;
    reporting it as README drift says the document is wrong about the directory on the
    strength of bytes nobody looked at. It is still reported, so a tracked file that
    stops being readable is visible rather than silently dropped.
    """
    # Assemble the previous W1 slug so the guard does not preserve the token it bans.
    retired = "-".join(("research", "pass"))  # noqa: FLY002 - the literal is what this bans
    paths = work_model_text(root)
    if paths is None:
        return TextScan([f"README.md: {NO_INDEX}"], [])

    problems: list[str] = []
    skipped: list[str] = []
    for path in paths:
        relative = path.relative_to(root)
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError) as error:
            skipped.append(f"{relative}: not scanned for retired workflow identifiers: {error}")
            continue
        problems.extend(
            f"{relative}:{line_number}: contains retired workflow identifier"
            for line_number, line in enumerate(lines, start=1)
            if retired in line
        )
    return TextScan(problems, skipped)


def check_work_model(text: str) -> list[str]:
    """Keep the human workflow entry points and machine contract in lockstep."""
    synopsis = SYNOPSIS.read_text(encoding="utf-8")
    schema = safe_load(SESSION_SCHEMA.read_text(encoding="utf-8"))
    properties = schema.get("properties", {})
    schema_workflows = (schema.get("$defs") or {}).get("workflow", {}).get("enum", [])
    phase_workflow = (
        properties.get("workflow_phases", {})
        .get("items", {})
        .get("properties", {})
        .get("workflow", {})
    )

    problems: list[str] = []
    if not isinstance(schema_workflows, list) or not all(
        isinstance(workflow, str) and workflow for workflow in schema_workflows
    ):
        problems.append(
            "agent-session.schema.yaml: canonical workflow enum is missing or malformed"
        )
        schema_workflows = []

    # The schema owns names and ordering. Its final enum value is the unnumbered
    # fallback; everything before it receives the compact W1, W2, ... labels used by
    # the two human orientation tables.
    numbered_workflows = schema_workflows[:-1]
    fallback = schema_workflows[-1] if schema_workflows else ""
    expected_rows = [
        (f"W{index}", workflow) for index, workflow in enumerate(numbered_workflows, start=1)
    ]
    # The count is asserted rather than derived on purpose: an enum that silently grows or
    # shrinks would still produce a self-consistent pair of tables, and the point of this
    # check is that a workflow cannot be added without a human editing both orientation
    # tables and this number.
    if len(numbered_workflows) != EXPECTED_NUMBERED_WORKFLOWS or not fallback:
        problems.append(
            f"agent-session.schema.yaml: workflow enum must contain "
            f"{EXPECTED_NUMBERED_WORKFLOWS} numbered workflows followed by one fallback"
        )
    for label, rows in (
        ("README.md", workflow_rows(text)),
        ("SYNOPSIS.md", workflow_rows(synopsis)),
    ):
        if rows != expected_rows:
            problems.append(
                f"{label}: workflow table is {rows or 'missing'}, expected {expected_rows}"
            )
        if fallback and fallback not in (text if label == "README.md" else synopsis):
            problems.append(f"{label}: does not name the {fallback} fallback")
    if phase_workflow.get("$ref") != "#/$defs/workflow":
        problems.append(
            "agent-session.schema.yaml: phase workflow does not reference the canonical enum"
        )
    if "entry_workflow" in properties or "entry_workflow" in schema.get("required", []):
        problems.append(
            "agent-session.schema.yaml: redundant entry_workflow must be derived "
            "from the first phase"
        )

    terminology = re.search(
        r"^### Work Units and Records\s*$\n(?P<body>.*?)(?=^###\s)",
        synopsis,
        re.MULTILINE | re.DOTALL,
    )
    if terminology is None:
        problems.append("SYNOPSIS.md: has no Work Units and Records section")
    else:
        body = terminology.group("body")
        problems.extend(
            f"SYNOPSIS.md: does not define {term}"
            for term in WORK_UNITS
            if not re.search(rf"\*\*{re.escape(term)}(?:\.|\s|\()", body)
        )
    return problems


def main() -> int:
    text = README.read_text(encoding="utf-8")
    scan = scan_retired_workflow_identifiers()
    problems = (
        check_links(text, README)
        + check_layout(text)
        + check_reports(text)
        + check_defect_summary(text)
        + check_result_coverage(text)
        + check_work_model(text)
        + scan.problems
    )
    for skip in scan.skipped:
        print(f"  skipped: {skip}")
    if problems:
        print("README.md has drifted from the directory:", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    print(
        "  README.md agrees with the directory, reports, defect and result sources, "
        "work model and its own links"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
