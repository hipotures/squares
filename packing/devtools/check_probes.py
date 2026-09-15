#!/usr/bin/env python3
"""Every probe tree in the repository: each probe parses as a function, and is used.

    uv run --frozen --all-extras --group dev python -m devtools.check_probes

A probe is a `.js` file under a directory named `probes`, holding one JavaScript expression
that a Python tool loads through `sqpack.probes` and hands to a page. Moving browser code
out of Python strings bought one thing above all: the text can be read by something other
than a browser. This is that something, and it asks three questions of every probe tree:

1. **Does each probe parse, and is it a function?** A probe that does not parse used to
   reach the page as a runtime error at the far end of a slow browser check. One that
   evaluates to a string or an object is handed to `page.evaluate` and silently returned
   unevaluated. `devtools/node/inspect-probes.mjs` answers both, in Node, without running
   any probe's body.
2. **Is each probe named by a caller?** A probe nothing names is dead weight that someone
   will edit believing it runs.
3. **Does every name a caller uses have a file?** A name no file answers is a
   `FileNotFoundError` at the far end of that same slow check.

A tree's callers are the Python files beside its `probes` directory, at any depth: for
`packing/devtools/probes` that is `packing/devtools/`, and for the workbench package's
`packages/workbench/probes` it is the package. Names are read from string literals rather
than from calls, so a helper that wraps the loader -- the workbench checkers' `look` --
still counts. That is also why a probe name is always written out whole: a name assembled
at run time is one this cannot see, and the probe it names reads as dead.

A string counts as a *missing* probe only when it looks like one and is written where probes
are used: it contains a `/`, its first segment is a group directory the tree already has, and
the file it is in imports the probe loader. A bare word in a checker is far more often a
label than a probe, and a build script beside the workbench's probes names
`atlas/known-best/...` paths that are files, not probes.

This supersedes `packages/workbench/tools/workbench_tools/check_probes.py`, which asked the
same three questions of the workbench tree alone, named its callers by hand, and was run by
no gate. It remains until `think-xvjf` removes it with the package's other JavaScript
strings.
"""

from __future__ import annotations

import ast
import json
import sys
from collections.abc import Iterable
from pathlib import Path, PurePosixPath

from nodejs_wheel import node as run_node

from devtools.check_no_embedded_js import LOADER_MODULES, repository_files

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
INSPECTOR = ROOT / "devtools" / "node" / "inspect-probes.mjs"
DIRECTORY = "probes"
SUFFIX = ".js"


def probe_trees(files: Iterable[str]) -> dict[str, list[str]]:
    """Each probe root, repository-relative, with the probe files under it.

    The root is the path through the first `probes` segment, so
    `packing/devtools/probes/tool/name.js` belongs to `packing/devtools/probes`.
    """
    trees: dict[str, list[str]] = {}
    for path in files:
        parts = PurePosixPath(path).parts
        if DIRECTORY not in parts[:-1]:
            continue
        cut = parts.index(DIRECTORY) + 1
        trees.setdefault(PurePosixPath(*parts[:cut]).as_posix(), []).append(path)
    return trees


def probe_name(root: str, path: str) -> str:
    return PurePosixPath(path).relative_to(root).with_suffix("").as_posix()


def callers(root: str, python: Iterable[str]) -> list[str]:
    """The Python files beside a probe root, at any depth."""
    base = PurePosixPath(root).parent
    return [path for path in python if PurePosixPath(path).is_relative_to(base)]


def strings(repo: Path, paths: Iterable[str]) -> tuple[set[str], set[str]]:
    """Every string literal in the named Python files, and those in files using the loader.

    Parsed rather than grepped, so a name inside a comment does not count as a use and a
    name split across an implicit concatenation still does.
    """
    everywhere: set[str] = set()
    in_loader_users: set[str] = set()
    for path in paths:
        tree = ast.parse((repo / path).read_text(encoding="utf-8"), filename=path)
        literals: set[str] = set()
        uses_loader = False
        for node in ast.walk(tree):
            match node:
                case ast.Constant(value=str() as value):
                    literals.add(value)
                case ast.ImportFrom(module=str() as module) if module in LOADER_MODULES:
                    uses_loader = True
                case ast.Import(names=names) if any(a.name in LOADER_MODULES for a in names):
                    uses_loader = True
                case _:
                    pass
        everywhere |= literals
        if uses_loader:
            in_loader_users |= literals
    return everywhere, in_loader_users


def inspect(repo: Path, paths: list[str]) -> dict[str, dict[str, str]]:
    """What Node makes of each file: `{"type": ...}` or `{"error": ...}`, by path."""
    if not paths:
        return {}
    done = run_node(
        [str(INSPECTOR), *paths],
        return_completed_process=True,
        capture_output=True,
        text=True,
        cwd=repo,
        check=False,
    )
    if done.returncode != 0:
        stderr = str(done.stderr).strip() or "(no stderr)"
        raise RuntimeError(f"node exited {done.returncode}: {stderr}")
    verdicts = json.loads(str(done.stdout))
    if not isinstance(verdicts, dict) or set(verdicts) != set(paths):
        # A partial answer would let an unread probe pass as a clean one.
        raise RuntimeError("the probe inspector did not report on every probe it was given")
    return verdicts


def faults(repo: Path) -> tuple[list[str], int, int]:
    """Every fault, the number of probes read, and the number of trees they are in."""
    trees = probe_trees(repository_files(repo, SUFFIX))
    python = repository_files(repo, ".py")
    found: list[str] = []
    count = 0
    for root, files in sorted(trees.items()):
        count += len(files)
        for path, verdict in sorted(inspect(repo, files).items()):
            if "error" in verdict:
                found.append(f"{path}: does not evaluate -- {verdict['error']}")
            elif verdict.get("type") != "function":
                found.append(f"{path}: evaluates to a {verdict.get('type')}, not a function")
        have = {probe_name(root, path) for path in files}
        groups = {name.split("/")[0] for name in have if "/" in name}
        used, named = strings(repo, callers(root, python))
        missing = {
            text
            for text in named
            if "/" in text and text not in have and text.split("/")[0] in groups
        }
        found.extend(
            f"{root}/{name}{SUFFIX}: named by a Python file beside {root}, and no such file"
            for name in sorted(missing)
        )
        found.extend(
            f"{root}/{name}{SUFFIX}: no Python file beside {root} names it"
            for name in sorted(have - used)
        )
    return found, count, len(trees)


def main() -> int:
    found, count, trees = faults(REPO)
    if count == 0:
        # The repository has probes by construction; finding none means the scan broke.
        found.append(f"no probe files found under {REPO}")
    for fault in found:
        print(f"FAIL  {fault}")
    if found:
        print(f"\n{len(found)} fault(s) over {count} probes in {trees} tree(s)")
        return 1
    print(
        f"OK: {count} probes in {trees} tree(s), every one a function that evaluates and is "
        "named by a Python file beside it"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
