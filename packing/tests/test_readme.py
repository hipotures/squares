"""Reader-facing result coverage, and which tree the directory checks read."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from devtools.check_readme import (
    NO_INDEX,
    TextScan,
    content_names,
    meaningful_top_level_entries,
    result_coverage_problems,
    scan_retired_workflow_identifiers,
    work_model_text,
)


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


#: The identifier the work-model scan bans, assembled rather than spelled for the same
#: reason `check_readme` assembles it: a test that writes the token into a tracked file
#: to prove the scan finds it must not make itself the thing the scan finds.
RETIRED = "-".join(("research", "pass"))  # noqa: FLY002 - the literal is what this bans


def _git(directory: Path, *arguments: str) -> None:
    subprocess.run(("git", "-C", str(directory), *arguments), check=True, capture_output=True)


def _repository(root: Path) -> Path:
    """A checkout holding one README, one drawn directory and one declared submodule."""
    root.mkdir()
    _git(root, "init", "-q")
    (root / ".gitignore").write_text(".claude/worktrees/\nattic/\n", encoding="utf-8")
    (root / ".gitmodules").write_text(
        '[submodule "vendor/kpress"]\n\tpath = vendor/kpress\n\turl = https://example/kpress\n',
        encoding="utf-8",
    )
    (root / "README.md").write_text("# Example\n", encoding="utf-8")
    (root / "packing").mkdir()
    (root / "packing" / "atlas").mkdir()
    (root / "packing" / "atlas" / "notes.md").write_text("held\n", encoding="utf-8")
    _git(root, "add", ".gitignore", ".gitmodules", "README.md", "packing/atlas/notes.md")
    return root


def test_an_ignored_worktree_cannot_fail_the_directory_checks(tmp_path: Path) -> None:
    """A path `.gitignore` excludes is not a path the README can be wrong about.

    The harness puts other agents' worktrees under `.claude/worktrees/`, and one of them
    held thirteen symlinks into a `tree-head` checkout that had since been removed. The
    work-model scan walked in, could not read them, and reported README drift. Both
    halves of that visit are pinned here: the unreadable path, which is what was
    observed, and a file in the same ignored tree carrying the banned token, which the
    scan was equally willing to read and report. Neither is this repository's to be
    answerable for.
    """
    repository = _repository(tmp_path / "repository")
    worktree = repository / ".claude" / "worktrees" / "other" / "probes"
    worktree.mkdir(parents=True)
    (worktree / "dangling.d.ts").symlink_to(repository / "gone" / "tree-head" / "probe.d.ts")
    # The suffix is what puts it in scope for the scan; the bytes need only carry the
    # token, and must not be JavaScript, which may not live in a Python string here.
    (worktree / "probe.js").write_text(f"{RETIRED}\n", encoding="utf-8")
    (repository / "attic").mkdir()
    (repository / "attic" / "scratch.md").write_text(f"{RETIRED}\n", encoding="utf-8")

    assert scan_retired_workflow_identifiers(repository) == TextScan([], [])
    assert all(".claude" not in path.parts for path in work_model_text(repository) or [])
    assert meaningful_top_level_entries(repository) == {"README.md", "packing", "vendor"}
    assert content_names(repository) == frozenset(
        {"README.md", "packing", "atlas", "notes.md", "vendor", "kpress"}
    )


def test_the_scan_reads_the_tracked_tree_and_not_the_working_directory(
    tmp_path: Path,
) -> None:
    """Untracked is untracked wherever it sits; staging the same file makes it count."""
    repository = _repository(tmp_path / "repository")
    carrier = repository / "packing" / "atlas" / "carrier.md"
    carrier.write_text(f"a line\nnaming the {RETIRED} workflow\n", encoding="utf-8")

    assert scan_retired_workflow_identifiers(repository) == TextScan([], [])

    _git(repository, "add", "packing/atlas/carrier.md")
    assert scan_retired_workflow_identifiers(repository) == TextScan(
        ["packing/atlas/carrier.md:2: contains retired workflow identifier"], []
    )


def test_a_tracked_file_the_scan_cannot_decode_is_skipped_with_its_reason(
    tmp_path: Path,
) -> None:
    repository = _repository(tmp_path / "repository")
    (repository / "packing" / "atlas" / "bytes.md").write_bytes(b"\xff\xfe not utf-8\n")
    _git(repository, "add", "packing/atlas/bytes.md")

    scan = scan_retired_workflow_identifiers(repository)
    assert scan.problems == []
    assert [line.split(":")[0] for line in scan.skipped] == ["packing/atlas/bytes.md"]
    assert "codec can't decode" in scan.skipped[0]


@pytest.mark.skipif(os.geteuid() == 0, reason="root reads a file whatever its mode says")
def test_a_tracked_file_the_scan_cannot_open_is_skipped_with_its_reason(
    tmp_path: Path,
) -> None:
    """The reported failure was an unreadable path, and unread bytes are not drift."""
    repository = _repository(tmp_path / "repository")
    denied = repository / "packing" / "atlas" / "denied.md"
    denied.write_text(f"{RETIRED}\n", encoding="utf-8")
    _git(repository, "add", "packing/atlas/denied.md")
    denied.chmod(0o000)

    scan = scan_retired_workflow_identifiers(repository)
    assert scan.problems == []
    assert [line.split(":")[0] for line in scan.skipped] == ["packing/atlas/denied.md"]
    assert "Permission denied" in scan.skipped[0]


def test_without_an_index_the_directory_checks_say_so_rather_than_walking(
    tmp_path: Path,
) -> None:
    """`None` is "no index to ask", which is not "nothing is here"."""
    (tmp_path / "loose.md").write_text(f"{RETIRED}\n", encoding="utf-8")

    assert meaningful_top_level_entries(tmp_path) is None
    assert content_names(tmp_path) is None
    assert work_model_text(tmp_path) is None
    assert scan_retired_workflow_identifiers(tmp_path) == TextScan(
        [f"README.md: {NO_INDEX}"], []
    )
