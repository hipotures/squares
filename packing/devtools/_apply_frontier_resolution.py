"""One-time, guarded patch preparation. It never updates a repository ref."""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = "5a03d67252c42729a445a4e349fe9412c70d7419"
BASE_TREE = "10ab1770d3eb645113a6acae5ddb14e45d1b7639"
ROOT = Path(__file__).resolve().parents[2]
POLICY = "packing/devtools/frontier_policy.py"
RUNNER = "packing/devtools/run_n12_frontier.py"
FILES = [POLICY, RUNNER, "packing/devtools/frontier_resolution.py",
         "packing/tests/test_frontier_resolution.py",
         "Experiments/n12-frontier-resolution/README.md",
         ".github/workflows/frontier-autonomy.yml", ".github/workflows/native-ab.yml",
         ".github/workflows/frontier-utilization.yml"]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def replace_once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f"ambiguous patch anchor: {before[:120]!r}")
    return text.replace(before, after, 1)


def apply():
    for path, expected in [(POLICY, "d5926ca9f2234aefa3a3cee88edb3596b40c0327"),
                           (RUNNER, "62fcd2c55e9a86df077f13741c847d4de6826a2f")]:
        if git("hash-object", path) != expected:
            raise RuntimeError(f"base source changed: {path}")
    path = ROOT / POLICY
    content = path.read_text()
    first = content.index("def search_resolution(")
    last = content.index("\n\ndef _enabled", first)
    content = content[:first] + '''def search_resolution(state: dict[str, Any]) -> Fraction:
    """Effective persisted search grid; never the verifier's precision."""
    from devtools.frontier_resolution import effective_resolution
    return effective_resolution(state)
''' + content[last:]
    path.write_text(content)

    path = ROOT / RUNNER
    content = path.read_text()
    content = replace_once(content, "from devtools import frontier_policy, frontier_runtime\n",
                           "from devtools import frontier_policy, frontier_runtime, frontier_resolution\n")
    first = content.index("def choose_work(")
    last = content.index("\n\ndef main(", first)
    choice = content[first:last]
    choice = replace_once(choice, "    return frontier_policy.plan(\n", "    work = frontier_policy.plan(\n")
    choice = choice.rstrip() + '''
    if work["kind"] == "idle":
        refinement = frontier_resolution.refinement_proposal(state)
        if refinement is not None:
            return refinement
        if frontier_policy.search_resolution(state) == frontier_resolution.numerical_floor(state):
            work = {**work, "reason": work["reason"] + "; 32-ULP search-grid floor reached"}
    return work
'''
    content = content[:first] + choice + content[last:]
    content = replace_once(content,
        '                work = choose_work(state)\n                if work["kind"] == "idle":',
        '''                work = choose_work(state)
                if work["kind"] == "refine-resolution":
                    poll_stop()
                    if not frontier_resolution.apply_refinement(root, state, work, sys.modules[__name__]):
                        break
                    idle_since = None
                    idle_message_at = 0.0
                    continue
                if work["kind"] == "idle":''')
    content = replace_once(content,
        '            f"mode: {state.get(\'mode\', \'FRONTIER\')}",',
        '''            f"search grid: {frontier_policy.search_resolution(state)} "
            f"(requested start: {frontier_resolution.requested_width(state)}; "
            f"numeric floor: {frontier_resolution.numerical_floor(state)})",
            f"mode: {state.get('mode', 'FRONTIER')}",''')
    content = replace_once(content,
        '''                 f"native={'+'.join(native_profile['kernels']) or 'reference-none'}")''',
        '''                 f"native={'+'.join(native_profile['kernels']) or 'reference-none'} "
                 f"resolution={frontier_policy.search_resolution(state)}")''')
    content = replace_once(content,
        '''On configured portfolio exhaustion the runner idles visibly without busy-looping.
--stop-when-exhausted exits instead. Neither state means mathematical impossibility.''',
        '''When observed strategy brackets exhaust the current search grid, the runner
reduces the effective strategy-width by a decade automatically, checkpoints the
change and replans in the same session. The configured width remains the initial
setting; resume preserves the effective width. The lower limit is 32 ULPs of the
float64 lower endpoint, not a verifier tolerance. --status is read-only.
Only exhaustion with no remaining refinement enters IDLE; --stop-when-exhausted
exits instead. Neither state means mathematical impossibility.''')
    path.write_text(content)
    for name, needle in [("frontier-autonomy.yml", "pytest tests/test_exact_slabs.py"),
                         ("native-ab.yml", "pytest tests/test_run_n12_frontier.py"),
                         ("frontier-utilization.yml", "pytest tests/test_frontier_utilization.py")]:
        path = ROOT / ".github/workflows" / name
        path.write_text(replace_once(path.read_text(), needle,
                                    needle.replace("pytest ", "pytest tests/test_frontier_resolution.py ", 1)))
    path = ROOT / "packing/devtools/frontier_resolution.py"
    path.write_text(replace_once(path.read_text(), '    result = {\n        "kind": "refine-resolution",',
                                 '    result: dict[str, Any] = {\n        "kind": "refine-resolution",'))


def publish():
    if os.environ.get("GITHUB_REPOSITORY") != "hipotures/squares":
        raise RuntimeError("unexpected repository")
    if os.environ.get("GITHUB_REF") != "refs/heads/work/frontier-resolution-build-20260927":
        raise RuntimeError("unexpected preparation branch")
    # Export blobs only. The authorized connector creates the final tree and
    # commit, including workflow changes, after reviewing these identities.
    def post_blob(payload):
        request = urllib.request.Request(
            "https://api.github.com/repos/hipotures/squares/git/blobs",
            data=json.dumps(payload).encode(), method="POST", headers={
                "Authorization": "Bearer " + os.environ["GITHUB_TOKEN"],
                "Accept": "application/vnd.github+json", "Content-Type": "application/json",
            })
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    entries = []
    for name in FILES:
        blob = post_blob({"content": (ROOT / name).read_text(), "encoding": "utf-8"})
        entries.append({"path": name, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    record = {"base_commit": BASE, "base_tree": BASE_TREE, "tree": entries}
    print("TESTED_TREE_ENTRIES=" + json.dumps(record), flush=True)
    (ROOT / "resolution-artifacts/candidate-sha.txt").write_text(json.dumps(record, indent=2) + "\n")


if __name__ == "__main__":
    if sys.argv[1:] == ["apply"]:
        apply()
    elif sys.argv[1:] == ["publish"]:
        publish()
    else:
        raise SystemExit("expected apply or publish")
