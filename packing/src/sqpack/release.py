"""What this project calls the edition its reader-facing artifacts belong to.

The atlas draws it under its title and the explainer prints it in its credits, so a
release is stamped in one place and both follow. This is the publication's version, not
the package's: `pyproject.toml` versions the code, and the two move for different
reasons.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import NamedTuple


class PublicationHistoryEntry(NamedTuple):
    """One retained public edition and its headline result scope."""

    version: str
    first_labeled: str
    result_scope: str


#: The two editions retained in the explainer's short public history, newest first.
#: Dates say when each label first appeared in Git as an edition of this publication,
#: rather than when a theorem was proved or when the page was deployed.
PUBLICATION_HISTORY = (
    PublicationHistoryEntry(
        version="v0.4.0",
        first_labeled="September 10, 2026",
        result_scope=(
            "The current lower-bound edition: T-025 proves "
            "$s(11) ≥ 191/50 = 3.82$, and T-026 proves "
            "$s(11) ≥ 3.8264474…$."
        ),
    ),
    PublicationHistoryEntry(
        version="v0.3.0",
        first_labeled="September 8, 2026",
        result_scope=(
            "The 3.81-result edition: T-018's point certificate proves "
            "$s(11) ≥ 381/100 = 3.81$."
        ),
    ),
)

#: The edition the figures and the explainer state. Choose at most one version bump per
#: merge, and keep it fixed while revising that pull request.
PUBLICATION_VERSION = PUBLICATION_HISTORY[0].version

#: Where the edition stands, said ahead of the version. Empty once it is final; the
#: join below then drops it and the stray space with it, so going final is one edit.
PUBLICATION_STATUS = ""

#: The commit the committed artifacts are stamped with, at this repository's own short
#: length -- the eight characters `git rev-parse --short` prints here -- so the hash a
#: reader sees in the atlas footer is one they can paste into `git show` and have
#: resolve.
#:
#: Pinned rather than read from git at build time, because the artifacts that carry it
#: are checked in: the atlas SVG is compared byte for byte against a fresh render, and
#: the claim documents' links name it, so a live revision would differ from the
#: committed one the moment it was committed and fail those gates forever. The page is
#: the exception, and deliberately: it is rendered on every deploy and stamps the commit
#: it is built from (`render_explainer.page_edition`), so its hash moves with every push
#: while this one moves when an edition is cut.
PUBLICATION_REVISION = "277f8b1a"

#: The version, written the one way it is ever written: `v0.1.0-3bd273e6`. Semver core,
#: then the revision, in the shape a build identifier takes everywhere else.
#:
#: This is the value to reach for. It exists because the two artifacts that stamp an
#: edition -- the atlas footer and the explainer's credits -- each used to compose their
#: own string from the parts, in two files and two languages, joined by a literal
#: ", revision ". Two hand-assembled spellings of one fact is how they come to disagree,
#: and neither could be changed without remembering the other.
PUBLICATION_STAMP = f"{PUBLICATION_VERSION}-{PUBLICATION_REVISION}"

#: How the edition is written wherever it is stamped: the stamp, with the status ahead
#: of it while there is one. The atlas footer and the explainer's credits both take this
#: string whole, so the two artifacts cannot disagree about whether the reader is holding
#: a draft, nor about how the version is spelled.
PUBLICATION_EDITION = " ".join(part for part in (PUBLICATION_STATUS, PUBLICATION_STAMP) if part)

#: The date that edition carries, written the way a reader reads it.
PUBLICATION_DATE = PUBLICATION_HISTORY[0].first_labeled


#: What the shared version's hash names (the owner, 2026-09-22): the last commit that changed
#: the evidence and data every artifact is drawn from. The explainer, the atlas SVGs, the
#: workbench page and the videos built from the same data then carry one version, whatever
#: code commit built them. Repository-relative, as every declared path here is.
DATA_PATHS: tuple[str, ...] = ("packing/frontier", "packing/atlas/known-best")

#: How many characters of that commit the version carries (the owner, 2026-09-22).
DATA_REVISION_LENGTH = 6


def data_revision(repo: Path) -> str:
    """The full hash of the last commit in `repo` that changed any of `DATA_PATHS`.

    Raises where git cannot say, which includes a shallow clone whose one commit did not
    touch the data: a version stamped from a guess would name the wrong data.
    """
    found = subprocess.run(
        ["git", "-C", str(repo), "log", "-1", "--format=%H", "--", *DATA_PATHS],
        capture_output=True,
        text=True,
        check=False,
    )
    revision = found.stdout.strip()
    if found.returncode != 0 or not revision:
        raise RuntimeError(
            f"git cannot name the last data commit in {repo} (a shallow clone?): "
            f"{found.stderr.strip() or 'no commit touches ' + ', '.join(DATA_PATHS)}"
        )
    return revision


def data_version(repo: Path) -> str:
    """The shared version, written the one way it is ever written: `v0.4.1-f5e113`.

    The edition's semver core, then the first `DATA_REVISION_LENGTH` characters of the last
    data commit.
    """
    return f"{PUBLICATION_VERSION}-{data_revision(repo)[:DATA_REVISION_LENGTH]}"
