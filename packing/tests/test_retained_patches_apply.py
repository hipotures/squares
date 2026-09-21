"""The two retained Session 148 partial diffs still apply to the base they name.

`h232-threshold-clip-partial.patch` and `h230-gap-wedge-port-partial.patch` are what two
stopped lanes delivered instead of a merge: 1,819 lines of diff kept as a receipt so the
resumption does not start from nothing. A retained diff whose applicability nothing
measures is the failure mode `OR-1` names -- the day `threshold.py` moves under it the
receipt becomes a fossil and the next session finds out by hand -- so each patch declares
its base revision in a header line above the diff, and this control replays
`git apply --check` against that revision.

The base is Session 148's opening commit. The check runs in a detached worktree of it
rather than against the working tree, which is the whole point: it measures the promise
the patch makes, not whatever HEAD happens to be. That needs the commit itself, so this
is marked slow and runs in the lane that checks out with `fetch-depth: 0`; it is
registered in `tests/test_module_boundaries.py` with the rest. Where the object is
genuinely absent -- a shallow clone that reached this test anyway -- it skips rather than
failing, because a missing object is a statement about the checkout and not about the
patch.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

PACKING = Path(__file__).resolve().parents[1]
REPO = PACKING.parent
RESULTS = (
    PACKING
    / "campaign"
    / "series"
    / "series-000-smoke-and-calibration"
    / "results"
    / "agenda-040"
)
#: Session 148's opening commit, which both patches were taken against and which each
#: one names in its own header line.
BASE = "19cdd4f8e21a28b058c21f04636dc6f6f82cb33c"
RETAINED_PATCHES = (
    RESULTS / "h232-threshold-clip-partial.patch",
    RESULTS / "h230-gap-wedge-port-partial.patch",
)


def _git(*args: str, cwd: Path = REPO) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


@pytest.mark.parametrize("patch", RETAINED_PATCHES, ids=lambda path: path.name)
def test_a_retained_patch_names_the_base_it_was_taken_against(patch: Path) -> None:
    """The header line is the promise; the test below is what measures it."""

    header = patch.read_text(encoding="utf-8").split("\n", 1)[0]
    assert BASE in header, f"{patch.name} does not name its base revision"
    assert header.startswith("Retained partial diff")


@pytest.mark.slow
def test_every_retained_patch_applies_to_its_declared_base(tmp_path: Path) -> None:
    """`git apply --check` in a worktree of the declared base, for both patches."""

    if _git("cat-file", "-e", f"{BASE}^{{commit}}").returncode != 0:
        pytest.skip(f"{BASE[:8]} is not in this checkout")

    worktree = tmp_path / "base"
    added = _git("worktree", "add", "--detach", str(worktree), BASE)
    assert added.returncode == 0, added.stderr
    try:
        for patch in RETAINED_PATCHES:
            checked = _git("apply", "--check", str(patch), cwd=worktree)
            assert checked.returncode == 0, (
                f"{patch.name} no longer applies to {BASE[:8]}: {checked.stderr}"
            )
    finally:
        _git("worktree", "remove", "--force", str(worktree))
