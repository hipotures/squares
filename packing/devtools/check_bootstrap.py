#!/usr/bin/env python3
"""Report the five setup facts a fresh clone needs before any gate can run.

A remote-session clone of this repository could not run `packing-validate --edit` at
all on 2026-09-22, and none of the five reasons was a bug in the gate. Each was a fact
about the checkout that no tool asked about, so every one of them surfaced as a
confusing failure somewhere downstream:

1. the image shipped `uv 0.8.17`, whose compiled-in interpreter index stops at
   `cpython-3.14.0rc2`. `uv python install 3.14.7` answered "No download found for
   request", and `uv sync` then answered "No interpreter found for Python 3.14.7" --
   a message about this checkout for a defect in the tool reading it;
2. `.python-version` pins `3.14.7` and nothing had installed it;
3. the clone was shallow, so `check_provenance` refused recorded engine commits that
   are in the history this clone did not fetch;
4. `vendor/kpress` was an empty directory, so `uv sync` reported that a declared
   workspace member "does not appear to be a Python project";
5. `npm ci` had never run, so the browser floor had no pinned Biome, ESLint or `tsc`.

None of those is slow to ask and none of them changes while a session runs, which is
why they are a check a session runs once rather than a tier step. `OR-14` keeps the
edit cycle quick, and adding six subprocess calls to every edit loop to re-establish
facts that were settled at clone time is exactly the artificial slowness it names.

This reports and never repairs. Installing a toolchain, fetching history, or running
`npm ci` behind a check is a mutation nobody asked for, and the remedy is one line the
reader can see before it runs. Every failure prints the exact command that fixes it.

It runs with nothing installed and no virtual environment, because the bootstrap
failure it diagnoses is the one where the project interpreter does not exist yet. It
imports only the standard library, and nothing from `sqpack` or the rest of `devtools`,
both of which are written in the project's 3.14; it was run on every CPython from 3.10
to 3.14 on the machine that produced it. From `packing/`, either of these works:

    python3 -m devtools.check_bootstrap
    uv run --frozen --all-extras --group dev python -m devtools.check_bootstrap
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
PIN = ROOT / ".python-version"

TOOL_TIMEOUT_SECONDS = 120.0
"""How long `uv`, `git` or a filesystem walk gets before its answer is unavailable.

Generous: `uv python list` reads a compiled-in index and returns in milliseconds, and
the ceiling exists only so a wedged subprocess cannot hang the bootstrap report that a
session runs before anything else.
"""

UV_INSTALL = 'curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR="$HOME/.local/bin" sh'
"""How to get a current `uv`, and deliberately not `uv self update`.

`uv self update` asks the GitHub releases API, which a session behind a shared proxy
hits already rate-limited; it failed that way on the clone that produced this check,
while the install script succeeded. A remedy that does not work on the machine the
check runs on is worse than no remedy.
"""

UNAVAILABLE: tuple[type[BaseException], ...] = (OSError, subprocess.SubprocessError)
"""The two ways a subprocess tells this check nothing: it did not start, or it hung.

A named tuple rather than the `except OSError, subprocess.SubprocessError:` this project
writes everywhere else. That spelling is PEP 758, valid only from 3.14, and this module
has to parse on the interpreter a fresh clone already has -- which is the interpreter
that is wrong, and the reason the module exists.
"""

#: One `uv python list` row: `cpython-3.14.7-linux-x86_64-gnu`, or the `+freethreaded`
#: variant, whose version field carries the `+` and must not match a bare pin.
_ENTRY = re.compile(r"^(?P<implementation>[a-z]+)-(?P<version>[^\s-]+)-\S+$")

#: The pinned browser tools `_browser_floor` asks for by path, kept identical to it: a
#: bootstrap check that agreed to a different set would pass a tree that step refuses.
NODE_TOOLS = ("biome", "eslint", "tsc")


class Fact(NamedTuple):
    """One setup fact, its verdict, and what to read when it is false."""

    name: str
    detail: str
    remedy: str | None

    @property
    def holds(self) -> bool:
        return self.remedy is None


def _output(*command: str) -> str | None:
    """A command's stdout, or None where it could not answer at all.

    Unavailable and failing are one case here on purpose. Both mean this check learned
    nothing from the tool, and both are reported against the fact the tool was asked
    about rather than as an error of their own.
    """
    try:
        finished = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=str(REPO),
            timeout=TOOL_TIMEOUT_SECONDS,
        )
    except UNAVAILABLE:
        return None
    return finished.stdout if finished.returncode == 0 else None


def _version_key(version: str) -> tuple[int, ...]:
    """Order versions numerically, so `3.14.0` sorts above `3.9.1` rather than below it.

    A prerelease suffix orders before the release it precedes, which is what makes the
    stalled index readable: an index whose newest 3.14 is `3.14.0rc2` says so.
    """
    release, _, suffix = version.partition("+")
    numbers = [int(part) for part in re.findall(r"\d+", release.split("rc")[0])]
    return (*numbers, 0 if "rc" in release or suffix else 1)


def pinned_version() -> str:
    """The interpreter `.python-version` pins, as `uv` spells it on the command line."""
    if not PIN.is_file():
        return ""
    for line in PIN.read_text(encoding="utf-8").splitlines():
        candidate = line.split("#", 1)[0].strip()
        if candidate:
            return candidate
    return ""


def listed_versions(*selector: str) -> frozenset[str] | None:
    """Every CPython version `uv python list` reports under `selector`.

    `--all-versions` because the pin is an exact patch and the default view shows only
    the newest patch of each minor. The free-threaded rows are excluded by the pattern
    rather than filtered after: `3.14.7+freethreaded` is a different interpreter from
    `3.14.7`, and counting it would answer yes to a question nobody asked.
    """
    listing = _output("uv", "python", "list", "--all-versions", *selector)
    if listing is None:
        return None
    found: set[str] = set()
    for line in listing.splitlines():
        fields = line.split()
        if not fields:
            continue
        entry = _ENTRY.match(fields[0])
        if entry is not None and entry["implementation"] == "cpython":
            found.add(entry["version"])
    return frozenset(found)


def uv_resolves_the_pin(pin: str) -> Fact:
    """Can the `uv` on PATH name the pinned interpreter at all?

    The measurement is uv's own index rather than a version floor, because a floor is a
    guess about which release first carried a given CPython build and this is the fact
    the floor would be standing in for. An index that cannot name the pin is an index
    too old to install it, whatever version string the binary reports.
    """
    if shutil.which("uv") is None:
        return Fact("uv is installed", "not on PATH", UV_INSTALL)
    reported = (_output("uv", "--version") or "unknown").strip()
    known = listed_versions()
    if known is None:
        return Fact(
            "uv resolves the pinned interpreter",
            f"{reported} could not list its interpreter index",
            f"reinstall uv and rerun: {UV_INSTALL}",
        )
    if pin in known:
        return Fact("uv resolves the pinned interpreter", f"{reported} knows {pin}", None)
    newest = max(known, key=_version_key, default="nothing")
    return Fact(
        "uv resolves the pinned interpreter",
        f"{reported} does not know CPython {pin}; its index stops at {newest}",
        f"install a current uv, which is not `uv self update` here: {UV_INSTALL}",
    )


def pin_is_installed(pin: str) -> Fact:
    """Is the pinned interpreter on this machine, by any route?

    `--only-installed` counts a system CPython as readily as a uv-managed one, which is
    the honest reading: `uv sync` needs an interpreter matching the pin and does not
    care who put it there.
    """
    installed = listed_versions("--only-installed")
    if installed is None:
        return Fact(
            f"CPython {pin} is installed",
            "uv could not list installed interpreters",
            f"uv python install {pin}",
        )
    if pin in installed:
        return Fact(f"CPython {pin} is installed", f"{PIN.name} pins {pin}", None)
    return Fact(
        f"CPython {pin} is installed",
        f"{PIN.name} pins {pin} and no installed CPython matches it",
        f"uv python install {pin}",
    )


def history_is_complete() -> Fact:
    """Is this clone deep enough to be asked about a commit?

    Two checks read the graph and both go wrong quietly on a truncated one:
    `check_provenance` refuses recorded engine commits it cannot find, and
    `check_session_gate` cannot decide the ancestry of a declared gate commit. Neither
    is a defect in the record.
    """
    shallow = _output("git", "rev-parse", "--is-shallow-repository")
    if shallow is None:
        return Fact("the clone is not shallow", "git could not answer", "install git")
    if shallow.strip() != "true":
        return Fact("the clone is not shallow", "complete history", None)
    return Fact(
        "the clone is not shallow",
        "shallow clone: recorded commits are unreachable and ancestry is undecidable",
        "git fetch --unshallow",
    )


def declared_submodules() -> list[str]:
    """Every submodule path `.gitmodules` declares, read by git rather than by a regex.

    `devtools.repo_scope` answers the same question for the sweeps, and this does not
    import it: `repo_scope` is written in the project's Python and uses PEP 758's
    unparenthesised `except A, B:`, which no interpreter before 3.14 parses. Importing
    it here would make the bootstrap check require the very interpreter whose absence
    it exists to diagnose. Asking `git config` is not a second implementation of that
    measurement -- it is the canonical reader of the file the regex approximates.
    """
    listing = _output("git", "config", "-f", ".gitmodules", "--get-regexp", r"\.path$")
    if listing is None:
        return []
    return sorted(line.split(maxsplit=1)[1] for line in listing.splitlines() if " " in line)


def submodules_are_present() -> Fact:
    """Is every submodule `.gitmodules` declares actually checked out?

    The declaration is what is asked, not the directory listing, for the reason
    `repo_scope` gives: a submodule that is not checked out is still this repository's
    to have. An empty `vendor/kpress` is a declared uv workspace member with no
    `pyproject.toml`, and `uv sync` reports it as not being a Python project.
    """
    declared = declared_submodules()
    if not declared:
        return Fact("submodules are checked out", "none declared", None)
    empty = [path for path in declared if not any((REPO / path).glob("*"))]
    if not empty:
        return Fact(
            "submodules are checked out", f"{len(declared)} declared, all populated", None
        )
    return Fact(
        "submodules are checked out",
        f"empty: {', '.join(empty)}",
        "git submodule update --init --recursive",
    )


def node_modules_are_installed() -> Fact:
    """Are the browser floor's pinned tools where that step looks for them?"""
    binaries = REPO / "node_modules" / ".bin"
    missing = [tool for tool in NODE_TOOLS if not (binaries / tool).is_file()]
    if not missing:
        return Fact(
            "the browser floor's tools are installed", f"{', '.join(NODE_TOOLS)} present", None
        )
    return Fact(
        "the browser floor's tools are installed",
        f"missing from node_modules/.bin: {', '.join(missing)}",
        "npm ci at the repository root, or make hooks-install, which also installs the hook",
    )


def facts() -> list[Fact]:
    """Every bootstrap fact, asked in the order a fresh clone has to satisfy them.

    An unreadable pin stops the report rather than colouring it: both interpreter facts
    are questions about a version, and asking them about an empty string would print two
    confident answers to a question nobody could state.
    """
    pin = pinned_version()
    if not pin:
        return [
            Fact(
                "the interpreter pin is readable",
                f"{PIN} is missing or names no version",
                "git checkout -- packing/.python-version, from the repository root",
            )
        ]
    return [
        uv_resolves_the_pin(pin),
        pin_is_installed(pin),
        history_is_complete(),
        submodules_are_present(),
        node_modules_are_installed(),
    ]


def main() -> int:
    """Print every bootstrap fact, and fail on the ones that do not hold."""
    checked = facts()
    for fact in checked:
        if fact.holds:
            print(f"  ok   {fact.name}: {fact.detail}")
    broken = [fact for fact in checked if not fact.holds]
    for fact in broken:
        print(f"FAIL {fact.name}: {fact.detail}", file=sys.stderr)
        print(f"     fix: {fact.remedy}", file=sys.stderr)
    if broken:
        print(
            f"{len(broken)} of {len(checked)} bootstrap facts do not hold; "
            "the gate cannot run until they do",
            file=sys.stderr,
        )
        return 1
    print(f"  all {len(checked)} bootstrap facts hold; this clone can run the gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
