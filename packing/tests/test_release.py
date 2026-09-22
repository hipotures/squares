"""One spelling of the edition, in one place, in the shape a build identifier takes.

The atlas footer and the explainer's credits each used to compose the stamp from the
parts, in two files and two languages, joined by a literal ", revision ". Two
hand-assembled spellings of one fact is how they come to disagree, and neither could be
changed without remembering the other. What is pinned here is the shape and the single
source. The short public history is the exception: its focused regression changes when
an edition enters or leaves that two-entry record.
"""

from __future__ import annotations

import re
import subprocess

from sqpack.release import (
    PUBLICATION_DATE,
    PUBLICATION_EDITION,
    PUBLICATION_HISTORY,
    PUBLICATION_REVISION,
    PUBLICATION_STAMP,
    PUBLICATION_STATUS,
    PUBLICATION_VERSION,
)

#: `v0.1.0-3bd273e6`: a semver core, a hyphen, and this repository's short hash.
STAMP = re.compile(r"v\d+\.\d+\.\d+-[0-9a-f]{7,40}")


def test_publication_history_is_the_two_retained_editions() -> None:
    """The public history stays short, dated, and tied to the current edition."""
    assert [entry.version for entry in PUBLICATION_HISTORY] == ["v0.4.0", "v0.3.0"]
    assert [entry.first_labeled for entry in PUBLICATION_HISTORY] == [
        "September 10, 2026",
        "September 8, 2026",
    ]
    assert "3.8264474…" in PUBLICATION_HISTORY[0].result_scope
    assert "381/100 = 3.81" in PUBLICATION_HISTORY[1].result_scope
    assert all("weak" not in entry.result_scope.lower() for entry in PUBLICATION_HISTORY)
    assert PUBLICATION_HISTORY[0].version == PUBLICATION_VERSION
    assert PUBLICATION_HISTORY[0].first_labeled == PUBLICATION_DATE


def test_the_stamp_is_a_version_and_a_revision_and_nothing_else() -> None:
    assert STAMP.fullmatch(PUBLICATION_STAMP), PUBLICATION_STAMP
    assert f"{PUBLICATION_VERSION}-{PUBLICATION_REVISION}" == PUBLICATION_STAMP


def test_the_edition_is_the_stamp_with_the_status_ahead_of_it() -> None:
    """And drops the status cleanly when there is none, so going final is one edit."""
    assert PUBLICATION_EDITION.endswith(PUBLICATION_STAMP)
    expected = (
        f"{PUBLICATION_STATUS} {PUBLICATION_STAMP}" if PUBLICATION_STATUS else PUBLICATION_STAMP
    )
    assert expected == PUBLICATION_EDITION
    assert "  " not in PUBLICATION_EDITION
    assert PUBLICATION_EDITION.strip() == PUBLICATION_EDITION


def test_the_revision_names_a_commit_this_repository_has() -> None:
    """A hash a reader cannot resolve is worse than no hash.

    The stamp is printed in a footer precisely so someone can go and look, so the
    revision is held to being a real object here rather than being any eight characters
    that happen to be hexadecimal. Skipped rather than failed where git cannot answer,
    since a source tarball is a legitimate way to have this package.
    """
    found = subprocess.run(
        ("git", "cat-file", "-t", PUBLICATION_REVISION),
        capture_output=True,
        text=True,
        check=False,
    )
    if found.returncode != 0 and "not a git repository" in found.stderr.lower():
        return
    assert found.returncode == 0, f"{PUBLICATION_REVISION}: {found.stderr.strip()}"
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
