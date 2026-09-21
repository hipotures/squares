"""The archive annotation census is gated, and the gate can fail.

`bentz-2016-optimal-packings-22-and-33.md` declared seven annotated passages while
carrying nine and while the README census said nine, for the width of one commit inside
one stack, with nothing in the repository able to notice. The control that notices is
`devtools.check_archive_annotations`; these tests are what say it is not vacuous.

The demonstration is the defect itself: a temporary copy of the real archive files, the
banner mutated back to `**7**`, and the check must name the file and the disagreeing
pair. Restoring the byte must make it pass again. A control that cannot fail is not a
control, so every coverage rule below is exercised in both directions.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from devtools.check_archive_annotations import (
    ARCHIVE,
    CENSUS,
    NARRATIVE,
    PACKET_BANNERS,
    banner_count,
    callout_count,
    census,
    check,
    marker_count,
    transcriptions,
)

REPO = Path(__file__).resolve().parents[2]
BENTZ2016 = ARCHIVE / "papers/bentz-2016-optimal-packings-22-and-33.md"
#: The stale banner the repository carried, and the corrected one.
STALE = "> This transcription contains **7** annotated passage(s)"
CORRECT = "> This transcription contains **9** annotated passage(s)"


def _git(directory: Path, *arguments: str) -> None:
    subprocess.run(("git", "-C", str(directory), *arguments), check=True, capture_output=True)


@pytest.fixture
def archive(tmp_path: Path) -> Path:
    """A copy of every tracked archive file the check reads, in a fresh git checkout.

    Only the Markdown matters -- the PDFs and the `.raw.md` extractions are megabytes the
    check never opens -- and it is a real checkout because the sweep reads the tracked
    tree rather than the working directory.
    """
    listed = subprocess.run(
        ("git", "-C", str(REPO), "ls-files", "--", ARCHIVE.as_posix()),
        check=True,
        capture_output=True,
        text=True,
    ).stdout.split()
    root = tmp_path / "checkout"
    root.mkdir()
    _git(root, "init", "-q")
    for name in listed:
        relative = Path(name)
        if relative.suffix != ".md" or relative.name.endswith(".raw.md"):
            continue
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO / relative, destination)
    _git(root, "add", "-A")
    return root


def test_the_repository_as_it_stands_passes() -> None:
    assert check() == []


def test_the_copied_archive_passes_before_anything_is_touched(archive: Path) -> None:
    """The fixture is faithful: whatever the check says below is about the mutation."""
    assert check(archive) == []


def test_a_stale_banner_fails_and_restoring_it_passes(archive: Path) -> None:
    """The defect, reproduced: the banner says seven where the file carries nine.

    This is the non-vacuity demonstration. The mutation is the exact byte that drifted at
    `2aef9421`, and the check has to name the file and say which two of the three numbers
    disagree -- file/banner and banner/census, with file/census still agreeing, which is
    what says the repair belongs in the banner and not in the census.
    """
    path = archive / BENTZ2016
    original = path.read_text(encoding="utf-8")
    assert CORRECT in original

    path.write_text(original.replace(CORRECT, STALE), encoding="utf-8")
    failures = check(archive)
    stem = BENTZ2016.name.removesuffix(".md")
    assert [line for line in failures if stem in line] == failures
    assert any("file/banner disagree" in line for line in failures)
    assert any("banner/census disagree" in line for line in failures)
    assert not any("file/census disagree" in line for line in failures)
    assert any(BENTZ2016.as_posix() in line for line in failures)
    assert any(
        "carries 9 annotation markers, its banner declares 7" in line for line in failures
    )

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_a_stale_census_cell_fails_and_restoring_it_passes(archive: Path) -> None:
    """The other direction: the file and its banner agree and the README does not."""
    path = archive / CENSUS
    original = path.read_text(encoding="utf-8")
    row = "| `bentz-2016-optimal-packings-22-and-33` | 9 |"
    assert row in original

    path.write_text(original.replace(row, row.replace("| 9 |", "| 7 |")), encoding="utf-8")
    failures = check(archive)
    assert any("file/census disagree" in line for line in failures)
    assert any("banner/census disagree" in line for line in failures)
    assert not any("file/banner disagree" in line for line in failures)

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_an_added_annotation_that_updates_nothing_fails(archive: Path) -> None:
    """The drift as it actually happens: a tenth annotation, neither count moved."""
    path = archive / BENTZ2016
    original = path.read_text(encoding="utf-8")
    path.write_text(f"{original}\n<!-- NOTE: a tenth annotation. -->\n", encoding="utf-8")

    failures = check(archive)
    assert any(
        "carries 10 annotation markers, its banner declares 9" in line for line in failures
    )
    assert any("the README census says 9" in line for line in failures)

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_an_annotated_transcription_missing_from_the_census_fails(archive: Path) -> None:
    """The README's closing sentence is a claim about every file it does not list."""
    path = archive / ARCHIVE / "papers/newly-annotated-source.md"
    path.write_text(
        "# A new transcription\n\n"
        "> ⚠️ **Contains reconstructed passages.**\n"
        "> This transcription contains **1** annotated passage(s) where the PDF "
        "extraction was damaged.\n\n"
        "<!-- NOTE: reconstructed. -->\n",
        encoding="utf-8",
    )
    _git(archive, "add", "-A")

    failures = check(archive)
    assert any(
        "newly-annotated-source" in line and "no row in the census" in line for line in failures
    )

    path.unlink()
    _git(archive, "add", "-A")
    assert check(archive) == []


def test_a_census_row_naming_no_transcription_fails(archive: Path) -> None:
    path = archive / CENSUS
    original = path.read_text(encoding="utf-8")
    row = "| `bentz-2016-optimal-packings-22-and-33` | 9 |"
    path.write_text(
        original.replace(row, f"| `no-such-paper` | 4 | Invented. |\n{row}"), "utf-8"
    )

    failures = check(archive)
    assert any(
        "no-such-paper" in line and "names no tracked transcription" in line
        for line in failures
    )

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_a_censused_file_that_loses_its_banner_fails(archive: Path) -> None:
    """A reader who opens the file must be told, not only a reader of the README."""
    path = archive / BENTZ2016
    original = path.read_text(encoding="utf-8")
    path.write_text(
        original.replace(CORRECT, "> This transcription is clean"), encoding="utf-8"
    )

    failures = check(archive)
    assert any("opens with no annotation banner" in line for line in failures)

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_the_narrative_exception_still_has_the_shape_it_is_written_for() -> None:
    """A stale exception cannot outlive its reason and leave a file counted wrongly."""
    for stem in NARRATIVE:
        path = REPO / ARCHIVE / "papers" / f"{stem}.md"
        text = path.read_text(encoding="utf-8")
        assert marker_count(text) == 0
        assert banner_count(text) == callout_count(text)


def test_the_narrative_exception_fails_when_the_file_changes_convention(
    archive: Path,
) -> None:
    (stem,) = NARRATIVE
    path = archive / ARCHIVE / "papers" / f"{stem}.md"
    original = path.read_text(encoding="utf-8")
    path.write_text(f"{original}\n<!-- GARBLED: counted the other way now. -->\n", "utf-8")

    failures = check(archive)
    assert any("GARBLED/NOTE comments" in line and stem in line for line in failures)

    path.write_text(original, encoding="utf-8")
    assert check(archive) == []


def test_the_packet_exemption_still_has_the_shape_it_is_written_for() -> None:
    for relative in PACKET_BANNERS:
        assert banner_count((REPO / relative).read_text(encoding="utf-8")) is not None


def test_an_unexempted_packet_banner_fails(archive: Path) -> None:
    """A transcription filed where the census does not look is not silently out of scope."""
    packet = archive / ARCHIVE / "papers/n11-complete-research-bundle-2026-09-07/hidden.md"
    packet.write_text(
        "> ⚠️ **Contains reconstructed passages.**\n"
        "> This transcription contains **2** annotated passage(s).\n",
        encoding="utf-8",
    )
    _git(archive, "add", "-A")

    failures = check(archive)
    assert any("hidden.md" in line and "contributed packet" in line for line in failures)

    packet.unlink()
    _git(archive, "add", "-A")
    assert check(archive) == []


def test_the_sweep_reads_the_tracked_tree_and_not_the_working_directory(
    archive: Path,
) -> None:
    """A scratch transcription nobody asked the repository to keep cannot fail the gate."""
    scratch = archive / ARCHIVE / "papers/scratch-draft.md"
    scratch.write_text(
        "> ⚠️ **Contains reconstructed passages.**\n"
        "> This transcription contains **3** annotated passage(s).\n"
        "<!-- NOTE: one. -->\n",
        encoding="utf-8",
    )
    assert check(archive) == []

    _git(archive, "add", "-A")
    assert any("scratch-draft" in line for line in check(archive))


def test_several_markers_on_one_line_are_several_annotations() -> None:
    """`friedman-ds7`'s Roth-Vaughan sentence carries two, and a line count misses one."""
    line = "if <!-- GARBLED: a --> then <!-- GARBLED: b --> holds"
    assert marker_count(line) == 2


def test_a_combined_marker_is_one_annotation() -> None:
    assert marker_count("<!-- GARBLED/NOTE: one passage, two readings -->") == 1


def test_a_scope_banner_is_not_an_annotation_banner() -> None:
    """`roth-vaughan` and the three 1984 memoranda state a scope, not a count."""
    assert banner_count("> ⚠️ **Partial transcription — front matter only.**\n") is None
    assert banner_count("> ⚠️ **Cleaned reading aid, not a transcription.**\n") is None


def test_a_wrapped_banner_is_read_wherever_the_wrap_puts_the_number() -> None:
    assert banner_count("> This transcription\n> contains **12** annotated passage(s)") == 12


def test_the_census_is_read_as_the_table_and_stops_at_its_end() -> None:
    rows = census(REPO)
    assert rows["bentz-2016-optimal-packings-22-and-33"] == 9
    assert set(rows) == {entry.stem for entry in transcriptions(REPO) if entry.annotated}
