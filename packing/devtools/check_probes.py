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
`packages/workbench/probes` it is the package. No list of callers is kept by hand, so a
new checker is covered the day it is written.

**Used** means any string literal in a caller equals the name, so a name that reaches the
loader through a tuple, a loop or a helper still counts. That is also why a probe name is
always written out whole: a name assembled at run time is one this cannot see, and the
probe it names reads as dead.

**Missing** is checked two ways, and a name either way catches fails:

- A string literal handed straight to a *loader* must name a file, whatever its group. A
  loader is `probe` as imported from `sqpack.probes` or `workbench_tools.probes`, or any
  function or method beside the tree that passes one of its own parameters straight to a
  loader -- the workbench checkers' `look` and `_look`, the Animate view's `session.look`.
  Before this rule a name was checked only when its first segment was an existing group,
  so `probe("newgroup/zz_missing")` passed (#125 F9, fixed in the workbench checker by
  #160 and applied here).
- A string that only *looks* like a probe -- it contains a `/` and its first segment is a
  group the tree has -- must name a file too, when it is in a file that uses a loader.
  This is how a name in a tuple is caught. A file that uses no loader is left out, because
  a build script beside the workbench's probes names `atlas/known-best/...` paths that are
  files, not probes.

This replaced `packages/workbench/tools/workbench_tools/check_probes.py`, which asked the
same questions of the workbench tree alone from a hand-kept list of fourteen callers.
"""

from __future__ import annotations

import ast
import json
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

from nodejs_wheel import node as run_node

from devtools.check_no_embedded_js import LOADER_MODULES, repository_files

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT.parent
INSPECTOR = ROOT / "devtools" / "node" / "inspect-probes.mjs"
DIRECTORY = "probes"
SUFFIX = ".js"
#: The loader's own name, in both modules that export it.
LOADER = "probe"
#: The keyword the loader itself takes the probe's name by. A name passed this way reached
#: neither branch of `name_faults` and failed in the browser instead (#175 R6). Only the
#: loader's own call is read this way: a wrapper takes the name positionally and forwards
#: `**argument` to the page, where `name=` is a value the probe reads, not a probe.
NAME_KEYWORD = "name"


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


def node_callers(root: str, scripts: Iterable[str]) -> list[str]:
    """The Node scripts beside a probe root, which name probes the way Python does.

    A probe a `.mjs` test exercises and no Python file mentions read as dead, because only
    `.py` was searched for its name (lane L4). This answers question 2 for those; questions
    1 and 3 are Python's, since only Python loads a probe into a page.
    """
    base = PurePosixPath(root).parent
    return [
        path
        for path in scripts
        if PurePosixPath(path).is_relative_to(base)
        and DIRECTORY not in PurePosixPath(path).parts
    ]


@dataclass
class Caller:
    """What one Python file says about probes."""

    #: Every string literal in the file.
    literals: set[str] = field(default_factory=set[str])
    #: The names the file imports the loader under: `probe`, an alias, or `module.probe`.
    imported: set[str] = field(default_factory=set[str])
    #: Every name the file calls, as `_called` spells it.
    called: set[str] = field(default_factory=set[str])
    #: Each call with string literals among its arguments: the name, the literals. Keyword
    #: arguments count -- `probe(ROOT, name="newgroup/absent")` reached neither branch of
    #: `name_faults` and failed at the far end of a browser run instead (#175 R6).
    literal_calls: list[tuple[str, tuple[str, ...]]] = field(
        default_factory=list[tuple[str, tuple[str, ...]]]
    )
    #: Each call that reaches a loader with no literal name in it, as `path:line`: the
    #: analysis could not read what it loads, which is not the same as clean (lane L1).
    unread_calls: list[tuple[str, int]] = field(default_factory=list[tuple[str, int]])
    #: Each function that passes one of its own parameters to a call: its name, the callee.
    forwards: set[tuple[str, str]] = field(default_factory=set[tuple[str, str]])


def read_caller(source: str, filename: str = "<caller>") -> Caller:
    """One parse of a caller: its literals, its loader imports, its calls and forwards."""
    tree = ast.parse(source, filename=filename)
    caller = Caller()
    for node in ast.walk(tree):
        match node:
            case ast.Constant(value=str() as value):
                caller.literals.add(value)
            case ast.ImportFrom(module=str() as module, names=names):
                for alias in names:
                    local = alias.asname or alias.name
                    if module in LOADER_MODULES and alias.name == LOADER:
                        caller.imported.add(local)
                    elif f"{module}.{alias.name}" in LOADER_MODULES:
                        caller.imported.add(f"{local}.{LOADER}")
            case ast.Import(names=names):
                caller.imported.update(
                    f"{alias.asname or alias.name}.{LOADER}"
                    for alias in names
                    if alias.name in LOADER_MODULES
                )
            case ast.FunctionDef() | ast.AsyncFunctionDef():
                parameters = {a.arg for a in (*node.args.posonlyargs, *node.args.args)}
                caller.forwards.update(
                    (node.name, _called(inner))
                    for inner in ast.walk(node)
                    if isinstance(inner, ast.Call)
                    and any(isinstance(a, ast.Name) and a.id in parameters for a in inner.args)
                )
            case ast.Call():
                name = _called(node)
                caller.called.add(name)
                named = [kw.value for kw in node.keywords if kw.arg == NAME_KEYWORD]
                arguments = [*node.args, *(named if name in caller.imported else [])]
                literals = tuple(
                    a.value
                    for a in arguments
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)
                )
                if literals:
                    caller.literal_calls.append((name, literals))
                elif any(
                    isinstance(a, ast.JoinedStr | ast.BinOp | ast.Call) for a in arguments
                ):
                    # A name assembled rather than written out, which leaves no literal
                    # for either branch of `name_faults` to check (lane L1). A plain name
                    # and a subscript of a literal table both leave one, so both stay quiet.
                    caller.unread_calls.append((name, node.lineno))
            case _:
                pass
    return caller


def _called(call: ast.Call) -> str:
    """The name a call reaches: `probe`, `look`, or `probes.probe` for a module alias."""
    match call.func:
        case ast.Name(id=name):
            return name
        case ast.Attribute(value=ast.Name(id=owner), attr=attr):
            return f"{owner}.{attr}"
        case ast.Attribute(attr=attr):
            return attr
        case _:
            return ""


def wrappers(files: Mapping[str, Caller]) -> set[str]:
    """Every function beside a tree that passes one of its parameters to a loader.

    Found to a fixed point, so a wrapper of a wrapper counts, and matched across the tree's
    files by bare name, so `session.look` in one file is the `look` another file's
    `Session` defines. The workbench's own `probe(name)`, which forwards to the shared
    loader, is one of these.
    """
    found: set[str] = set()
    while True:
        more = {
            function
            for caller in files.values()
            for function, callee in caller.forwards
            if _loads(callee, caller.imported | found)
        }
        if more <= found:
            return found
        found |= more


def _loads(called: str, loaders: set[str]) -> bool:
    """Whether a call reaches a loader: by its full name, or a method by its bare name."""
    return called in loaders or called.rsplit(".", 1)[-1] in loaders


def name_faults(
    files: Mapping[str, Caller], have: set[str], also_used: Iterable[str] = ()
) -> tuple[list[str], list[str], list[str]]:
    """Names a caller uses that no file answers, files no caller names, and calls that
    reach a loader with a name this cannot read.

    The third list is not a fault: a wrapper forwarding its own parameter is the supported
    way to load a probe. It is printed because an assembled name -- `probe(f"{group}/x")` --
    is invisible to the missing-name half of the check, so "could not read" has to look
    different from "clean" (lane L1).
    """
    forwarding = wrappers(files)
    groups = {name.split("/")[0] for name in have if "/" in name}
    wanted: set[str] = set()
    used: set[str] = set()
    unread: list[str] = []
    for path, caller in sorted(files.items()):
        used |= caller.literals
        loaders = caller.imported | forwarding
        # Handed straight to a loader: must resolve, whatever its group.
        wanted.update(
            literal
            for called, literals in caller.literal_calls
            if _loads(called, loaders)
            for literal in literals
        )
        # Looks like a probe, in a file that loads probes: must resolve too.
        if caller.imported or any(_loads(called, loaders) for called in caller.called):
            wanted.update(s for s in caller.literals if "/" in s and s.split("/")[0] in groups)
        unread.extend(
            f"{path}:{line}: {called}(...) loads a probe whose name this cannot read"
            for called, line in caller.unread_calls
            if _loads(called, loaders)
        )
    return sorted(wanted - have), sorted(have - used - set(also_used)), sorted(unread)


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


@dataclass(frozen=True)
class Report:
    """What the check found: faults, the notes beside them, and what it read."""

    faults: list[str]
    unread: list[str]
    probes: int
    trees: int


def faults(repo: Path) -> Report:
    """Every fault, every loader call whose name could not be read, and what was read."""
    trees = probe_trees(repository_files(repo, SUFFIX))
    python = repository_files(repo, ".py")
    scripts = [*repository_files(repo, ".mjs"), *repository_files(repo, ".cjs")]
    parsed: dict[str, Caller] = {}
    found: list[str] = []
    unread: list[str] = []
    count = 0
    for root, files in sorted(trees.items()):
        count += len(files)
        for path, verdict in sorted(inspect(repo, files).items()):
            if "error" in verdict:
                found.append(f"{path}: does not evaluate -- {verdict['error']}")
            elif verdict.get("type") != "function":
                found.append(f"{path}: evaluates to a {verdict.get('type')}, not a function")
        for path in callers(root, python):
            if path not in parsed:
                parsed[path] = read_caller((repo / path).read_text(encoding="utf-8"), path)
        beside = {path: parsed[path] for path in callers(root, python)}
        have = {probe_name(root, path) for path in files}
        named_in_node = _named_in_node(repo, node_callers(root, scripts), have)
        missing, unnamed, opaque = name_faults(beside, have, named_in_node)
        unread.extend(opaque)
        found.extend(
            f"{root}/{name}{SUFFIX}: named by a Python file beside {root}, and no such file"
            for name in missing
        )
        found.extend(
            f"{root}/{name}{SUFFIX}: no Python file beside {root} names it" for name in unnamed
        )
    return Report(faults=found, unread=unread, probes=count, trees=len(trees))


def _named_in_node(repo: Path, scripts: Iterable[str], have: set[str]) -> set[str]:
    """The probe names a Node script beside the tree writes out, read as text.

    Text rather than a parse: these are the same whole names Python writes, and a JavaScript
    parser here would be a second inspector to keep.
    """
    named: set[str] = set()
    for path in scripts:
        text = (repo / path).read_text(encoding="utf-8")
        named.update(name for name in have if name in text)
    return named


def main() -> int:
    report = faults(REPO)
    found = report.faults
    if report.probes == 0:
        # The repository has probes by construction; finding none means the scan broke.
        found.append(f"no probe files found under {REPO}")
    for note in report.unread:
        print(f"NOTE  {note}")
    for fault in found:
        print(f"FAIL  {fault}")
    read = f"{report.probes} probes in {report.trees} tree(s)"
    unread = (
        f"; {len(report.unread)} loader call(s) whose name could not be read"
        if report.unread
        else ""
    )
    if found:
        print(f"\n{len(found)} fault(s) over {read}{unread}")
        return 1
    print(
        f"OK: {read}, every one a function that evaluates and is named by a file beside "
        f"it{unread}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
