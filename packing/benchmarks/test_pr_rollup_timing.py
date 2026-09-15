"""Opt-in workload for timing the cumulative pull-request rollup renderer."""

from __future__ import annotations

import re
import subprocess
import sys


def test_complete_rollup_corpus_renders() -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "devtools.render_pr_rollup", "--check"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0
    match = re.fullmatch(
        r"  the branch cost rollup renders for ([0-9]+) branches, and for none\n",
        completed.stdout,
    )
    assert match is not None
    assert int(match.group(1)) > 0
    assert completed.stderr == ""
