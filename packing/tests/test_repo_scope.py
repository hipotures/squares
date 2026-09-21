"""Which trees the checkout is answerable for, answered once from `.gitmodules`.

Two sweeps asked that question separately and disagreed about the vendored tree in
opposite directions. `check_svg_rendering` swept it, which is D-455.
`check_documentation` did not sweep it, and excluded its prose through a document-map
pattern instead -- which fails on a plain `git clone`, because the map's loader requires
every exclusion to match a file and an unchecked-out submodule matches none (think-5e7k).

`devtools.repo_scope` is the one answer, and it comes from the declaration rather than
from the working tree, so it is the same on a clone with submodules and one without.

`tracked_files` is the same principle one level down: a sweep reads what the repository
holds, which is its index, not what the working directory happens to contain.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from devtools.repo_scope import REPO, is_vendored, tracked_files, vendored_directories
from sqpack.yamlio import safe_load


def _git(directory: Path, *arguments: str) -> None:
    subprocess.run(("git", "-C", str(directory), *arguments), check=True, capture_output=True)


def _repository(tmp_path: Path) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    return repository


def test_the_vendored_set_is_what_gitmodules_declares() -> None:
    """Read, not typed. A second submodule is excluded by being declared."""
    declared = vendored_directories()
    assert declared == {"vendor/kpress"}, sorted(declared)
    for path in declared:
        assert (REPO / path).is_dir(), f"{path} is declared but not a directory"


def test_a_path_inside_a_declared_submodule_is_vendored() -> None:
    assert is_vendored(REPO / "vendor" / "kpress" / "README.md")
    assert is_vendored(REPO / "vendor" / "kpress")


def test_a_sibling_sharing_a_prefix_is_not_vendored() -> None:
    """Compared on path parts, so `vendor/kpress-notes` is not `vendor/kpress`.

    A string prefix test would call it vendored and stop policing our own prose in it.
    """
    assert not is_vendored(REPO / "vendor" / "kpress-notes" / "README.md")
    assert not is_vendored(REPO / "README.md")
    assert not is_vendored(REPO / "packing" / "devtools" / "repo_scope.py")


def test_every_map_pattern_matches_a_file_no_submodule_supplies() -> None:
    """The regression: a map pattern satisfied only by vendored files fails a plain clone.

    The loader requires every collection and every exclusion to match at least one file,
    and reports `document exclusion is empty` when one does not. A pattern whose only
    matches live inside a submodule therefore passes with `submodules: true` -- which is
    what both workflows pass -- and fails a plain `git clone`. That is precisely what
    `vendor/**/*.md` did (think-5e7k).

    Checked by matching each pattern the way the loader does and then discarding the
    vendored files, rather than by reasoning about the pattern's prefix: `vendor/**/*.md`
    has the prefix `vendor`, which is not itself a declared submodule path, so prefix
    arithmetic reports it clean.
    """
    map_path = REPO / "docs" / "project" / "document-map.yaml"
    document_map = safe_load(map_path.read_text("utf-8"))
    patterns = [
        entry["pattern"] for key in ("collections", "exclusions") for entry in document_map[key]
    ]
    assert patterns, "the map declares no patterns; this check would pass vacuously"
    for pattern in patterns:
        without_submodules = [
            path for path in REPO.glob(pattern) if path.is_file() and not is_vendored(path)
        ]
        assert without_submodules, f"{pattern} matches only files a submodule supplies"


def test_only_what_the_index_holds_is_listed(tmp_path: Path) -> None:
    """Untracked and ignored files are not the repository's, whatever the disk says.

    This is the regression: a sweep that walked the filesystem read one JSON dropped into
    the gitignored `attic/` and failed on a record nobody had asked to keep (PR 207).
    """
    repository = _repository(tmp_path)
    (repository / ".gitignore").write_text("attic/\n", encoding="utf-8")
    (repository / "kept.json").write_text("{}\n", encoding="utf-8")
    (repository / "untracked.json").write_text("{}\n", encoding="utf-8")
    (repository / "attic").mkdir()
    (repository / "attic" / "scratch.json").write_text("{}\n", encoding="utf-8")
    _git(repository, "add", ".gitignore", "kept.json")
    assert tracked_files(repository, "*.json") == [repository / "kept.json"]


def test_a_pathspec_matches_at_any_depth_and_excludes_other_suffixes(tmp_path: Path) -> None:
    repository = _repository(tmp_path)
    (repository / "results").mkdir()
    (repository / "results" / "deep.json").write_text("{}\n", encoding="utf-8")
    (repository / "notes.md").write_text("read me\n", encoding="utf-8")
    _git(repository, "add", "-A")
    assert tracked_files(repository, "*.json") == [repository / "results" / "deep.json"]


def test_a_tracked_file_the_working_tree_no_longer_holds_is_dropped(tmp_path: Path) -> None:
    """The index still names it; a sweep that went on to read its bytes would raise."""
    repository = _repository(tmp_path)
    (repository / "gone.json").write_text("{}\n", encoding="utf-8")
    _git(repository, "add", "gone.json")
    (repository / "gone.json").unlink()
    assert tracked_files(repository, "*.json") == []


def test_a_directory_inside_a_checkout_is_not_a_repository_of_its_own(tmp_path: Path) -> None:
    """Otherwise a snapshot nested in someone else's checkout would sweep that checkout."""
    repository = _repository(tmp_path)
    nested = repository / "nested"
    nested.mkdir()
    (nested / "inside.json").write_text("{}\n", encoding="utf-8")
    _git(repository, "add", "-A")
    assert tracked_files(nested, "*.json") is None


def test_tracking_nothing_is_not_the_same_answer_as_having_no_index(tmp_path: Path) -> None:
    """`[]` and `None` are different answers, and the caller's fallback turns on which."""
    repository = _repository(tmp_path)
    assert tracked_files(repository, "*.json") == []
    assert tracked_files(tmp_path / "no-such-directory", "*.json") is None


def test_the_repository_itself_tracks_this_file() -> None:
    """The real checkout, not a fixture: the listing has to work where the sweeps run."""
    listed = tracked_files(REPO, "*.py")
    assert listed is not None
    assert Path(__file__).resolve() in {path.resolve() for path in listed}
