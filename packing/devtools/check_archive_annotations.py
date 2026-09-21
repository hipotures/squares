#!/usr/bin/env python3
"""The archive annotation census: the file, its banner, and the README must agree.

`packing/resources/` is the one place this repository keeps an external source, and the
one boundary where a model-assisted transcription can quietly say something the printed
paper does not. The guard against that is an annotation: a `GARBLED` or `NOTE` comment
beside the passage, a count in the file's own opening banner, and a row in the census
table of `packing/resources/README.md`, whose closing sentence -- "Files not listed
carry no annotations" -- is a claim about every other transcription in the archive.

Three statements of one number, and until this sweep nothing compared them. The owner's
review of PR 204 named that (finding F4): the defect count is gated end to end while the
archive annotation census is not, so a miscount "would pass every gate and silently
degrade the one ground-truth boundary this repo keeps against an external source". It
then drifted inside the same stack. `2aef9421` added the eighth and ninth annotations to
`bentz-2016-optimal-packings-22-and-33.md`, carrying D-507's factor-2 Theorem 9 repair,
and updated the README census to 9; the file's own banner stayed at 7. The two earlier
states were consistent -- 3/3/3 at `fb6be453`, 7/7/7 at `3dc129e0` -- so the drift is
exactly one commit wide, and grep found nothing that would have caught it:
`grep -rln "annotated passage" packing/devtools/ packing/tests/ packing/src/` was empty.
`OR-1` is the rule that turns that measurement into a tool.

What is compared, per transcription:

1. **file** -- the annotations the bytes actually carry, re-derived, never read off a
   declaration;
2. **banner** -- the count the file states at its top;
3. **census** -- the `Annotated` cell of the README table.

Any two of the three that disagree is a failure naming the file and the pair, because
which pair disagrees is what says where the repair goes: file/banner with census
agreeing is a stale banner, file/census with banner agreeing is a stale census row.

**Scope.** A transcription is a tracked `.md` file one directory under
`packing/resources/` -- `papers/`, `web/`, `private-correspondence/`, the layout the
README documents -- that is not a `.raw.md` extraction. Files deeper than that are
contributed packets, reproduced as received and covered by their own intake documents
rather than by this census; the archive's own transcriptions are never nested. So that
the depth rule cannot become an escape hatch, a packet file carrying an annotation
banner is itself a failure: it means a transcription was filed where the census does not
look.

**Two conventions, both counted.** Nine files use the counted convention: a banner
reading "contains **N** annotated passage(s)" and one `<!-- GARBLED` or `<!-- NOTE`
comment per annotated passage. `stromquist-2003-packing-10-or-11-unit-squares` uses the
archive's older narrative one and is listed in `NARRATIVE` below with its reason. It is
an exception in how its three numbers are read, not in whether they are checked, and it
fails here if it ever stops having the shape the exception is written for.

Usage, from `packing/`:

    uv run --frozen --all-extras --group dev python -m devtools.check_archive_annotations

Exits 1 if any two of a transcription's three counts disagree, if an annotated file is
missing from the census, or if a census row names no transcription. Nothing is written:
the archive is read-only to this tool, as `.flowmarkignore` and `AGENTS.md` require.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

from devtools.repo_scope import REPO, tracked_files

#: The archive root, repository-relative, as every declared path in the record is.
ARCHIVE = Path("packing/resources")
#: The census lives in the archive's own README, beside the transcriptions it counts.
CENSUS = ARCHIVE / "README.md"
#: Directories the fallback walk skips where there is no git index to ask.
SKIP = frozenset({".venv", ".git", "node_modules", "__pycache__", ".mypy_cache"})

#: One annotated passage under the counted convention: an HTML comment opening with
#: either marker the banner tells a reader to search for. `GARBLED/NOTE` opens with
#: `GARBLED` and is one annotation, not two. Several may sit on one line -- the
#: Roth-Vaughan sentence in `friedman-ds7` carries two -- so occurrences are counted,
#: never lines.
MARKER = re.compile(r"<!--\s*(?:GARBLED|NOTE)\b")
#: The counted convention's banner. Matched against the banner block with its `>`
#: continuations flattened, so the number is found wherever the wrap puts it.
COUNTED_BANNER = re.compile(r"contains \*\*(?P<count>\d+)\*\* annotated passage")
#: The narrative convention's banner, which spells its number.
NARRATIVE_BANNER = re.compile(r"⚠️ \*\*(?P<word>[A-Za-z]+) annotated source issues?\.\*\*")
#: The start of a blockquote callout, which is what the narrative convention annotates
#: with. The opening banner is one of them: it carries an issue of its own.
CALLOUT = re.compile(r"^>\s*⚠️", re.MULTILINE)
#: The census table's header and its rows.
CENSUS_HEADER = "| File stem | Annotated | Notes |"
CENSUS_ROW = re.compile(r"^\|\s*`(?P<stem>[^`]+)`\s*\|\s*(?P<count>\d+)\s*\|")

#: Spelled numbers a narrative banner may use. Small on purpose: a narrative banner is a
#: prose sentence, and a transcription needing more than this many annotations is one
#: that should be moved to the counted convention rather than spelled out.
WORDS: dict[str, int] = {
    "One": 1,
    "Two": 2,
    "Three": 3,
    "Four": 4,
    "Five": 5,
    "Six": 6,
    "Seven": 7,
    "Eight": 8,
    "Nine": 9,
    "Ten": 10,
}

#: Contributed-packet files that legitimately carry an annotation banner, each with the
#: reason. Repository-relative. A packet is retained as received, so one that reproduces
#: a transcription reproduces its banner too; what the guard below is for is a
#: transcription of this archive's own filed where the census does not look, and an
#: entry here that stops carrying a banner is itself a failure.
PACKET_BANNERS: dict[str, str] = {
    "packing/resources/papers/n11-complete-research-bundle-2026-09-07/source_packet/"
    "16-mathematical-background-and-literature.md": (
        "file 16 of the contributed n = 11 bundle reproduces this archive's own "
        "`stromquist-2003` transcription, banner and callouts included, inside a packet "
        "kept as received; it is a copy of a censused transcription rather than one "
        "filed outside the census"
    ),
}

#: Transcriptions whose annotations are not `GARBLED`/`NOTE` comments, each with the
#: reason its count is read the other way. The exception is checked, not trusted: a stem
#: here that grows an annotation comment, or loses its narrative banner, fails below
#: rather than quietly falling out of the census.
NARRATIVE: dict[str, str] = {
    "stromquist-2003-packing-10-or-11-unit-squares": (
        "its three annotated issues are blockquote callouts rather than comments, and "
        "the first of them -- Figure 13's four defining coordinates, read off rendered "
        "PDF page 9 -- is recorded in the opening banner itself rather than beside the "
        "text, so the banner block is one of the three it counts"
    ),
}


@dataclass(frozen=True)
class Transcription:
    """One archive transcription and the three counts that must agree about it."""

    path: Path
    stem: str
    narrative: bool
    #: What the bytes carry, re-derived by the convention the file declares.
    found: int
    #: `GARBLED`/`NOTE` comments, counted for every file so that a narrative-convention
    #: entry growing one is visible rather than silently uncounted.
    comments: int
    #: What the file's own banner says, or `None` where it carries no annotation banner.
    banner: int | None

    @property
    def annotated(self) -> bool:
        """Whether this file claims or carries any annotation at all."""
        return self.found > 0 or self.banner is not None


def _flattened(text: str) -> str:
    """`text` with blockquote continuations joined, so a wrapped banner reads as one line."""
    return re.sub(r"\n>\s*", " ", text)


def marker_count(text: str) -> int:
    """How many annotated passages `text` carries under the counted convention."""
    return len(MARKER.findall(text))


def callout_count(text: str) -> int:
    """How many blockquote callouts `text` carries under the narrative convention."""
    return len(CALLOUT.findall(text))


def banner_count(text: str) -> int | None:
    """The count a file's own annotation banner declares, or `None` if it has none.

    A `⚠️` banner that states a scope rather than a count -- "Partial transcription --
    front matter only", "Cleaned reading aid, not a transcription" -- is not an
    annotation banner and is not read as one.
    """
    flattened = _flattened(text)
    counted = COUNTED_BANNER.search(flattened)
    if counted is not None:
        return int(counted.group("count"))
    narrative = NARRATIVE_BANNER.search(flattened)
    if narrative is None:
        return None
    return WORDS.get(narrative.group("word").capitalize())


def _markdown(root: Path) -> list[Path]:
    """Every tracked Markdown file in the archive, or a bounded walk with no index here."""
    listed = tracked_files(root, ARCHIVE.as_posix())
    if listed is None:
        archive = root / ARCHIVE
        walked = archive.rglob("*.md") if archive.is_dir() else iter(())
        listed = sorted(path for path in walked if not SKIP & set(path.parts))
    return [path for path in listed if path.suffix == ".md"]


def _is_transcription(relative: Path) -> bool:
    """Whether a repository-relative archive path is one of the archive's transcriptions.

    One directory under the archive root, and not a `.raw.md` extraction or the README
    that holds the census. Anything deeper is a contributed packet.
    """
    if relative.name.endswith(".raw.md") or relative == CENSUS:
        return False
    return len(relative.relative_to(ARCHIVE).parts) == 2


def transcriptions(root: Path) -> list[Transcription]:
    """Every archive transcription, with its annotations re-derived from its bytes."""
    found: list[Transcription] = []
    for path in _markdown(root):
        relative = path.relative_to(root)
        if not _is_transcription(relative):
            continue
        text = path.read_text(encoding="utf-8")
        stem = relative.name.removesuffix(".md")
        narrative = stem in NARRATIVE
        comments = marker_count(text)
        found.append(
            Transcription(
                path=relative,
                stem=stem,
                narrative=narrative,
                found=callout_count(text) if narrative else comments,
                comments=comments,
                banner=banner_count(text),
            )
        )
    return found


def packet_banners(root: Path) -> list[str]:
    """Contributed-packet files carrying an annotation banner, repository-relative."""
    return [
        relative.as_posix()
        for path in _markdown(root)
        if not _is_transcription(relative := path.relative_to(root))
        and banner_count(path.read_text(encoding="utf-8")) is not None
    ]


def census(root: Path) -> dict[str, int]:
    """The `Annotated` column of the README census table, by file stem.

    An empty table is not distinguished from a missing one here; `check` reports the
    missing README itself, which is the more useful sentence.
    """
    path = root / CENSUS
    if not path.is_file():
        return {}
    rows: dict[str, int] = {}
    inside = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip() == CENSUS_HEADER:
            inside = True
            continue
        if not inside:
            continue
        if not line.startswith("|"):
            break
        row = CENSUS_ROW.match(line)
        if row is not None:
            rows[row.group("stem")] = int(row.group("count"))
    return rows


def _disagreements(entry: Transcription, declared: int | None) -> list[str]:
    """Every pair of `entry`'s three counts that disagree, named as a pair."""
    where = entry.path.as_posix()
    unit = "callouts" if entry.narrative else "annotation markers"
    lines: list[str] = []
    if entry.banner is not None and entry.banner != entry.found:
        lines.append(
            f"{entry.stem}: file/banner disagree -- {where} carries {entry.found} "
            f"{unit}, its banner declares {entry.banner}"
        )
    if declared is not None and declared != entry.found:
        lines.append(
            f"{entry.stem}: file/census disagree -- {where} carries {entry.found} "
            f"{unit}, the README census says {declared}"
        )
    if entry.banner is not None and declared is not None and entry.banner != declared:
        lines.append(
            f"{entry.stem}: banner/census disagree -- the banner declares "
            f"{entry.banner}, the README census says {declared}"
        )
    return lines


def _coverage(entry: Transcription, declared: int | None) -> list[str]:
    """Every way `entry` sits outside the census that is supposed to cover it."""
    where = entry.path.as_posix()
    lines: list[str] = []
    if declared is None and entry.annotated:
        lines.append(
            f"{entry.stem}: {where} is annotated but has no row in the census table of "
            f"{CENSUS.as_posix()}, whose closing sentence says files not listed carry "
            "no annotations"
        )
    if declared is not None and entry.banner is None:
        lines.append(
            f"{entry.stem}: the census counts {declared} annotations but {where} opens "
            "with no annotation banner, so a reader of the file is told nothing"
        )
    return lines


def _exception_lines(entry: Transcription) -> list[str]:
    """Whether a narrative-convention exception still has the shape it is written for.

    A stale exception is a failure, exactly as in `check_class_record_claims`: it must
    not outlive its reason and quietly leave a file counted the wrong way.
    """
    where = entry.path.as_posix()
    reason = NARRATIVE[entry.stem]
    lines: list[str] = []
    if entry.banner is None:
        lines.append(
            f"{entry.stem}: listed as a narrative-convention transcription ({reason}) "
            f"but {where} no longer carries a narrative banner; count it the counted "
            "way or drop the entry"
        )
    if entry.comments:
        lines.append(
            f"{entry.stem}: listed as a narrative-convention transcription but {where} "
            f"now carries {entry.comments} GARBLED/NOTE comments; count it the counted "
            "way and drop the entry"
        )
    return lines


def check(root: Path = REPO) -> list[str]:
    """Every disagreement, as a line naming the transcription and the pair."""
    if not (root / CENSUS).is_file():
        return [f"no census at {CENSUS.as_posix()}: the archive states its counts there"]

    declared = census(root)
    failures: list[str] = []
    seen: set[str] = set()
    for entry in sorted(transcriptions(root), key=lambda found: found.stem):
        row = declared.get(entry.stem)
        if row is not None:
            seen.add(entry.stem)
        if entry.narrative:
            failures.extend(_exception_lines(entry))
        failures.extend(_disagreements(entry, row))
        failures.extend(_coverage(entry, row))

    failures.extend(
        f"{stem}: the census table counts {declared[stem]} annotations for a stem "
        f"that names no tracked transcription under {ARCHIVE.as_posix()}"
        for stem in sorted(set(declared) - seen)
    )
    banners = packet_banners(root)
    for path in banners:
        if path in PACKET_BANNERS:
            continue
        failures.append(
            f"{path}: carries an annotation banner inside a contributed packet, where "
            "the census does not look; file it as a transcription"
        )
    for path, reason in PACKET_BANNERS.items():
        if path not in banners:
            failures.append(
                f"{path}: exempted from the packet guard for a shape it no longer has "
                f"({reason}); drop the exemption rather than leaving it to cover a "
                "later packet file"
            )
    return failures


def main() -> int:
    failures = check()
    for line in failures:
        print(f"FAIL {line}")
    entries = [entry for entry in transcriptions(REPO) if entry.annotated]
    annotations = sum(entry.found for entry in entries)
    print(
        f"archive annotation census: {len(entries)} annotated transcriptions, "
        f"{annotations} annotations, {len(NARRATIVE)} read the narrative way, "
        f"{len(failures)} failures"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
