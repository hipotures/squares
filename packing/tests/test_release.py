"""One spelling of the version, in one place, and the pin that keeps it naming the data.

The atlas footer and the explainer's credits each used to compose the stamp from the
parts, in two files and two languages, and the page named its build commit where the
atlas named a pinned one. Hand-assembled spellings of one fact are how they come to
disagree. What is pinned here is the shape, the single source, and the drift check that
holds the pinned data revision to git.

The version history is held to two rules of its own: it only grows, back to the first
edition, and each edition is dated by when it was first published rather than when its
label was first written down.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from sqpack.release import (
    DATA_REVISION,
    DATA_REVISION_LENGTH,
    FIRST_PUBLISHED,
    PUBLICATION_DATE,
    PUBLICATION_EDITION,
    PUBLICATION_HISTORY,
    PUBLICATION_REVISION,
    PUBLICATION_STAMP,
    PUBLICATION_STATUS,
    PUBLICATION_VERSION,
    PublicationHistoryEntry,
    data_pathspec,
    data_revision,
    data_version,
)

REPO = Path(__file__).resolve().parents[2]

#: `v0.4.1-f5e113`: a semver core, a hyphen, and six characters of the data commit.
STAMP = re.compile(rf"v\d+\.\d+\.\d+-[0-9a-f]{{{DATA_REVISION_LENGTH}}}")

#: The identity and settings a scratch repository commits under, so the user's global
#: signing and hooks cannot reach it.
SCRATCH_GIT = (
    "-c",
    "user.name=release test",
    "-c",
    "user.email=release-test@example.invalid",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.hooksPath=/dev/null",
)


def _git(repo: Path, *arguments: str) -> str:
    done = subprocess.run(
        ("git", "-C", str(repo), *SCRATCH_GIT, *arguments),
        capture_output=True,
        text=True,
        check=True,
    )
    return done.stdout.strip()


def _commit(repo: Path, path: str, text: str) -> str:
    """Write `path` under `repo`, commit it alone, and return the commit's hash."""
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    _git(repo, "add", path)
    _git(repo, "commit", "--quiet", "-m", f"touch {path}")
    return _git(repo, "rev-parse", "HEAD")


@pytest.fixture
def history(tmp_path: Path) -> tuple[Path, str]:
    """A scratch repository whose last data commit is followed by three that are not.

    One commit re-stamps an atlas composite and one edits a video spike, which the data
    paths exclude; one changes a file outside them. Returns the repository and the hash
    of its last data commit.
    """
    repo = tmp_path / "origin"
    repo.mkdir()
    _git(repo, "init", "--quiet")
    _commit(repo, "packing/frontier/n-017.md", "first\n")
    data = _commit(repo, "packing/frontier/n-017.md", "second\n")
    _commit(repo, "packing/atlas/known-best/known-best-1-100.svg", "<svg/>\n")
    _commit(repo, "packing/atlas/known-best/video/spikes/player.js", "play();\n")
    _commit(repo, "README.md", "prose\n")
    return repo, data


def _version(entry: PublicationHistoryEntry) -> tuple[int, ...]:
    return tuple(int(part) for part in entry.version.removeprefix("v").split("."))


def test_the_history_keeps_every_edition_back_to_the_first() -> None:
    """An edition that was published stays in the history, and the first one most of all.

    This test used to say the history was "the two retained editions", which is the rule
    that let adding v0.4.1 drop v0.3.0 -- the proof of s(11) >= 381/100 the publication
    began with -- and pass. The history now only grows: every edition ever published is
    listed, newest first, and the oldest is the 381/100 edition. A new edition goes on the
    front; nothing comes off the back.
    """
    versions = [entry.version for entry in PUBLICATION_HISTORY]
    assert {"v0.4.1", "v0.4.0", "v0.3.0"} <= set(versions)
    assert len(set(versions)) == len(versions)
    assert [_version(e) for e in PUBLICATION_HISTORY] == sorted(
        (_version(e) for e in PUBLICATION_HISTORY), reverse=True
    )
    first = PUBLICATION_HISTORY[-1]
    assert first.version == "v0.3.0"
    assert "381/100" in first.result_scope
    assert all("weak" not in entry.result_scope.lower() for entry in PUBLICATION_HISTORY)
    assert PUBLICATION_HISTORY[0].version == PUBLICATION_VERSION


def test_each_edition_is_dated_by_when_it_was_first_published() -> None:
    """The dates are first publication, read from the Pages deployments, not labelling.

    Two of the three differ from the old label dates, in opposite directions: v0.3.0 went
    live on September 5 and was named on September 8; v0.4.0 was named on a branch on
    September 10 and went live on September 13. The deployments behind each are in the
    comment on `PUBLICATION_HISTORY`.
    """
    dated = {entry.version: entry.first_published for entry in PUBLICATION_HISTORY}
    assert dated["v0.3.0"] == "September 5, 2026"
    assert dated["v0.4.0"] == "September 13, 2026"
    assert dated["v0.4.1"] == "September 22, 2026"
    assert PUBLICATION_HISTORY[0].first_published == PUBLICATION_DATE
    assert PUBLICATION_HISTORY[-1].first_published == FIRST_PUBLISHED


def test_the_stamp_is_a_version_and_a_data_revision_and_nothing_else() -> None:
    assert STAMP.fullmatch(PUBLICATION_STAMP), PUBLICATION_STAMP
    assert re.fullmatch(r"[0-9a-f]{40}", DATA_REVISION), DATA_REVISION
    assert f"{PUBLICATION_VERSION}-{DATA_REVISION[:DATA_REVISION_LENGTH]}" == PUBLICATION_STAMP


def test_the_edition_is_the_stamp_with_the_status_ahead_of_it() -> None:
    """And drops the status cleanly when there is none, so going final is one edit."""
    assert PUBLICATION_EDITION.endswith(PUBLICATION_STAMP)
    expected = (
        f"{PUBLICATION_STATUS} {PUBLICATION_STAMP}" if PUBLICATION_STATUS else PUBLICATION_STAMP
    )
    assert expected == PUBLICATION_EDITION
    assert "  " not in PUBLICATION_EDITION
    assert PUBLICATION_EDITION.strip() == PUBLICATION_EDITION


@pytest.mark.parametrize("revision", [DATA_REVISION, PUBLICATION_REVISION])
def test_each_pinned_revision_names_a_commit_this_repository_has(revision: str) -> None:
    """A hash a reader cannot resolve is worse than no hash.

    The version is printed in a footer precisely so someone can go and look, and the
    claim documents' links are followed, so each pin is held to being a real commit here
    rather than being any characters that happen to be hexadecimal. Skipped rather than
    failed where git cannot answer: a source tarball is a legitimate way to have this
    package, and a shallow clone's cut can fall above the commit.
    """
    found = subprocess.run(
        ("git", "-C", str(REPO), "cat-file", "-t", revision),
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0 and "not a git repository" in found.stderr.lower():
        pytest.skip("not a git checkout")
    if found.returncode != 0 and _git(REPO, "rev-parse", "--is-shallow-repository") == "true":
        pytest.skip(f"{revision} is below this shallow clone's cut")
    assert found.returncode == 0, f"{revision}: {found.stderr.strip()}"
    assert found.stdout.strip() == "commit", found.stdout.strip()


def test_the_pinned_revision_is_an_unambiguous_object_prefix() -> None:
    """Repository growth must not force a historical edition's stamp to change.

    Git's automatic abbreviation length grows with the object database and can differ
    between clones. The pinned prefix must still identify exactly one object, rather
    than have the same length as today's unrelated HEAD abbreviation.
    """
    found = subprocess.run(
        ("git", "rev-parse", f"--disambiguate={PUBLICATION_REVISION}"),
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0 and "not a git repository" in found.stderr.lower():
        return
    assert found.returncode == 0, found.stderr.strip()
    matches = found.stdout.splitlines()
    assert len(matches) == 1, matches
    assert matches[0].startswith(PUBLICATION_REVISION)


def test_the_pinned_data_revision_is_the_last_data_commit() -> None:
    """The drift check: every artifact prints the pin, so the pin must be what git says.

    It fails on the commit that changes the data, since no commit can carry its own
    hash, and passes again once a following commit re-pins; the message says how.
    """
    try:
        live = data_revision(REPO)
    except RuntimeError as error:
        pytest.skip(str(error))
    assert live == DATA_REVISION, (
        f"the data changed at {live[:12]}, but the version still names "
        f"{DATA_REVISION[:12]}: set DATA_REVISION = {live!r} in "
        "packing/src/sqpack/release.py, then run "
        "`python -m devtools.build_known_best_atlas --update` from packing/ to re-stamp "
        "the atlas, and commit the two together"
    )
    assert data_version(REPO) == PUBLICATION_STAMP


def test_no_file_inside_the_data_carries_the_stamp_unless_it_is_excluded() -> None:
    """Rule 4: a stamped file counted as data would make every re-stamp a data commit.

    The pin would then chase its own hash: re-pinning rewrites the file, the rewrite is
    the new last data commit, and the pin is stale again. Only text files can be
    searched; the raster and PDF exports are excluded with the composite they are drawn
    from.
    """
    search = ("grep", "-lIF", "-e", PUBLICATION_STAMP, "--", *data_pathspec())
    found = subprocess.run(
        ("git", "-C", str(REPO), *search),
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode > 1:
        pytest.skip(found.stderr.strip() or "git grep cannot search here")
    assert not found.stdout.strip(), (
        f"these carry {PUBLICATION_STAMP!r} inside the data paths; add them to "
        f"DATA_EXCLUDED or stop stamping them:\n{found.stdout}"
    )


def test_the_data_commit_is_the_last_one_that_changed_the_data(
    history: tuple[Path, str],
) -> None:
    """Re-stamping a composite, editing a video spike and editing prose do not count."""
    repo, data = history
    assert data_revision(repo) == data
    assert data_version(repo) == f"{PUBLICATION_VERSION}-{data[:DATA_REVISION_LENGTH]}"


def test_a_merge_keeps_the_data_commit_its_branch_pinned(history: tuple[Path, str]) -> None:
    """Rule 3's claim about merge commits, held here rather than asserted in prose.

    A branch whose data is the only data that moved keeps its data commit through the
    merge, so the pin it carries is still right on `main`. When `main`'s data moved too,
    the merge itself is the new data commit, and the pin has to follow it.
    """
    repo, _ = history
    base = _git(repo, "rev-parse", "HEAD")
    _git(repo, "switch", "--quiet", "-c", "branch")
    branch_data = _commit(repo, "packing/frontier/n-018.md", "branch\n")
    _git(repo, "switch", "--quiet", "-")
    _commit(repo, "docs.md", "main moves, but not its data\n")
    _git(repo, "merge", "--quiet", "--no-ff", "--no-edit", "branch")
    assert data_revision(repo) == branch_data

    _git(repo, "switch", "--quiet", "-c", "second", base)
    _commit(repo, "packing/frontier/n-019.md", "second branch\n")
    _git(repo, "switch", "--quiet", "-")
    _git(repo, "merge", "--quiet", "--no-ff", "--no-edit", "second")
    assert data_revision(repo) == _git(repo, "rev-parse", "HEAD")


def test_a_shallow_clone_cut_above_the_data_commit_refuses_to_name_one(
    history: tuple[Path, str], tmp_path: Path
) -> None:
    """git reports a shallow clone's cut as changing every path, so the cut is refused.

    Before this was checked, a one-commit clone answered with its own `HEAD` -- a
    commit that touched no data -- and exited zero, which is how the deploy's shallow
    checkout would have stamped a version naming the wrong commit.
    """
    repo, data = history
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "--quiet", "--depth", "1", f"file://{repo}", str(shallow))
    with pytest.raises(RuntimeError, match="shallow history is cut"):
        data_revision(shallow)

    # Five commits reach the one below the data commit, so the data commit is not the cut.
    deep_enough = tmp_path / "deep-enough"
    _git(tmp_path, "clone", "--quiet", "--depth", "5", f"file://{repo}", str(deep_enough))
    assert data_revision(deep_enough) == data


def test_a_directory_that_is_not_a_repository_cannot_name_a_data_commit(
    tmp_path: Path,
) -> None:
    with pytest.raises(RuntimeError, match="cannot name the last data commit"):
        data_revision(tmp_path)
