# Kleddamag n11: Local Replay Receipts

The complete source replay passed on 2026-09-22, establishing the certificate’s strict
bound `s(11) > 31/8`. The [launcher result](full-replay/RESULT.json) and
[independent audit](independent-audit.json) bind the replay to certificate SHA-256
`57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458` from commit
`6a733f339395c3514f2ab63d8c4aa64cf63c0b5a`, tag `v1.0.2`.

The
[mathematical review](../../../../../../docs/project/reviews/review-2026-09-22-kleddamag-n11-mathematics.md)
states the proof obligations and limits of the controls.
Both full scanners use the same event-cell method: their agreement supports V4/C3 and
does not supply C4 method diversity.

## Recorded Run

The runtime was CPython 3.14.7 on macOS 26.5.2 arm64, NumPy 2.3.5, Numba 0.67.0,
llvmlite 0.49.0 and Node.js 24.19.0. Python numerical dependencies were installed in a
separate environment without changing the project lockfile.
The JavaScript scanner was reconstructed offline from the retained R038 source, with
both upstream and resulting hashes checked by `prepare_secondary.py`.

The actual full-launcher command was run from the repository root:

```shell
/private/tmp/squares-frontier-20260922/n11-venv/bin/python \
  /private/tmp/squares-frontier-20260922/kleddamag-11/verify.py \
  --output-dir /Users/levy/.codex/worktrees/116b/squares/packing/resources/web/external-square-certificates-2026-09-22/receipts/n11/full-replay
```

Its stdout and stderr were redirected to
[full-replay-launcher.log](full-replay-launcher.log).
It exited zero. The launcher retained each phase log, complete Python row results, three
JavaScript range results and their stderr, and exact boundary controls under
[`full-replay/`](full-replay/). The recorded phase times were 1,501.120 seconds for
Python, 1,790.011 seconds for JavaScript and 277.972 seconds for the final controls,
under concurrent research and validation work.

The first-party auditor then verified all 54 files against the pinned release manifest,
reran its independent premise and adverse controls, and reconciled every complete
receipt. That final run passed in 27.626 seconds; its output is
[independent-audit.log](independent-audit.log).
`premise-audit.json` retains the earlier complete premise-only pass.
The integrity and exhaustive threshold-algebra logs are separate receipts.

## Reproduce in a Fresh Writable Directory

Run these commands from the repository root with `uv` and Node.js available.
The original run used Node.js 24.19.0. The source archive stays immutable; the checker
writes its reconstructed JavaScript cache only in the writable copy.

```shell
N11_WORKSPACE=$(mktemp -d "${TMPDIR:-/tmp}/n11-replay.XXXXXX")
N11_SOURCE_TREE="$N11_WORKSPACE/source"
N11_UPSTREAM_PYTHON="$N11_WORKSPACE/runtime/bin/python"
N11_REPLAY_OUTPUT="$N11_WORKSPACE/full-replay"

uv venv --python 3.14.7 "$N11_WORKSPACE/runtime"
uv pip install --python "$N11_UPSTREAM_PYTHON" \
  numpy==2.3.5 numba==0.67.0 llvmlite==0.49.0
cp -R packing/resources/web/external-square-certificates-2026-09-22/kleddamag-11 \
  "$N11_SOURCE_TREE"
"$N11_UPSTREAM_PYTHON" "$N11_SOURCE_TREE/prepare_secondary.py" \
  --source packing/resources/web/external-square-certificates-2026-09-22/dependencies/guzhou-r038/certificates/R038/src/exact_parent_side_scan.js
"$N11_UPSTREAM_PYTHON" "$N11_SOURCE_TREE/verify.py" \
  --output-dir "$N11_REPLAY_OUTPUT" \
  > "$N11_WORKSPACE/full-replay-launcher.log" 2>&1
```

The output directory must not already exist.
After that command succeeds, reconcile it and run the first-party controls:

```shell
packing/.venv/bin/python3 packing/devtools/audit_kleddamag_n11.py \
  packing/resources/web/external-square-certificates-2026-09-22/kleddamag-11/global-certificate.json \
  --upstream-tree "$N11_SOURCE_TREE" \
  --upstream-python "$N11_UPSTREAM_PYTHON" \
  --full-replay "$N11_REPLAY_OUTPUT" \
  --output "$N11_WORKSPACE/independent-audit.json"
```

The auditor checks all premises and selected scanner controls, then reconciles the full
source receipts. It does not replace the preceding complete launcher run.
The reproducible command uses fresh directory variables; the literal historical command
above records the paths used for the retained run.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
