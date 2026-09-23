# Tokoharu Density Replay Receipts

The retained [audit record](audit.json) contains exact preflight results and complete
201-direction interval replays for the `n = 11`, `n = 26`, and `n = 29`
rectangle-density certificates.
The adjacent case directories retain the upstream standard output, standard error,
verification summary, and per-angle records from that run.

The replay ran from `packing/` with the project CPython 3.14 environment, four workers,
and a 900-second ceiling per certificate.
It requires a C++17-capable `g++` on `PATH`. The audit tool checks the compiler before
processing certificates and copies each retained certificate into a temporary writable
directory before compiling and running the upstream verifier.

## Reproduce the Coverage Replay

Run the following from `packing/`:

```bash
density_replay_output="$(mktemp -d "${TMPDIR:-/tmp}/tokoharu-density-replay.XXXXXX")" &&
.venv/bin/python3 -m devtools.audit_tokoharu_density \
  --out "$density_replay_output" \
  --n 26 --n 29 --n 11 --replay --workers 4 --timeout 900
```

The output parent may exist, but its per-certificate child directories must not.
The `mktemp` command creates an empty parent so every run uses fresh output.
The audit fails rather than merging a replay into an existing certificate directory.

The
[mathematical review](../../../../../../docs/project/reviews/review-2026-09-22-tokoharu-density-mathematics.md)
records the theorem correspondence, exact premise checks, independent sampled controls,
and assurance limits.
The exact coverage decision remains the retained upstream C++ implementation; the
sampled controls are not a second global coverage method.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
