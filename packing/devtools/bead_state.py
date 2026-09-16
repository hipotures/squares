#!/usr/bin/env python3
"""Whether a `think-xxxx` alias still tracks work, read straight from the bead store.

A gate that names a bead is making a claim: this relaxation, this allowlist entry, this
exception is temporary, and something is tracking its removal. A closed bead tracks
nothing, and a bead that does not exist never did -- which is how the `tsconfig`
relaxations came to name the closed `think-4cwy` with every check green (#160 R24), and
how a four-character name that matched the shape would have widened the embedded-JavaScript
allowlist (#175 R2).

Read from the store rather than through the `tbd` binary, which CI does not install. Every
CI job that clones full history fetches `origin/tbd-sync`, which is where the store lives
when no local sync worktree has been materialized.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path

from devtools.check_bead_tree import ISSUES, MAPPINGS, REFS, parse_aliases
from sqpack.yamlio import safe_load

REPO = Path(__file__).resolve().parent.parent.parent

#: The bead states that still track work.
LIVE = frozenset({"open", "in_progress", "blocked"})

#: Reads one repository-relative path from the bead store, or None when it is absent.
Reader = Callable[[str], str | None]


class UnavailableError(RuntimeError):
    """No bead store is reachable, so no tracker can be resolved either way."""


def _git(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(REPO), *arguments], check=False, capture_output=True, text=True
    )


def store() -> Reader | None:
    """A reader over the bead store: the local sync worktree, else the sync branch."""
    common = _git("rev-parse", "--path-format=absolute", "--git-common-dir")
    if common.returncode == 0:
        worktree = Path(common.stdout.strip()) / "tbd" / "data-sync-worktree"
        if (worktree / MAPPINGS).is_file():

            def from_worktree(path: str) -> str | None:
                target = worktree / path
                return target.read_text(encoding="utf-8") if target.is_file() else None

            return from_worktree
    for ref in REFS:
        if _git("cat-file", "-e", f"{ref}:{MAPPINGS}").returncode == 0:

            def from_ref(path: str, ref: str = ref) -> str | None:
                shown = _git("show", f"{ref}:{path}")
                return shown.stdout if shown.returncode == 0 else None

            return from_ref
    return None


def require_store() -> Reader:
    """The reader, or `Unavailable` naming what is missing."""
    read = store()
    if read is None:
        raise UnavailableError(
            "no bead store is reachable (no tbd sync worktree, no tbd-sync branch)"
        )
    return read


def state(alias: str, read: Reader) -> str | None:
    """The status of the bead a `think-xxxx` alias names, or None if there is no such bead."""
    tail = parse_aliases(read(MAPPINGS) or "").get(alias.removeprefix("think-"))
    if tail is None:
        return None
    text = read(f"{ISSUES}/is-{tail}.md")
    if text is None or not text.startswith("---\n"):
        return None
    front = safe_load(text[4 : text.index("\n---", 4)])
    return str(front.get("status")) if isinstance(front, dict) else None


def dead_trackers(aliases: Iterable[str], read: Reader) -> list[str]:
    """Each named tracker that is not a live bead, with what it is instead."""
    faults: list[str] = []
    for alias in sorted(set(aliases)):
        found = state(alias, read)
        if found is None:
            faults.append(f"{alias}: no such bead")
        elif found not in LIVE:
            faults.append(f"{alias}: {found}")
    return faults


def fixture_store(states: Mapping[str, str]) -> Reader:
    """A bead store holding one bead per alias, in the given state.

    Here rather than in a test file because both contract files that resolve trackers need
    the negative control, and a control written twice drifts once.
    """
    files = {MAPPINGS: "".join(f"{alias}: tail{alias}\n" for alias in states)}
    for alias, status in states.items():
        files[f"{ISSUES}/is-tail{alias}.md"] = (
            f"---\nid: is-tail{alias}\nstatus: {status}\n---\n"
        )
    return files.get
