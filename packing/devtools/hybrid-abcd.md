# Isolated hybrid experiments

Base: `0ff6c5274fcf0751a2883cb49915fbff66376725` on `work/frontier-native-ab`.
External source: `evand/square-packing` at `6aa82ba457e9eaeaaa3af0833600f27f91a2fce3`.
`prepare-external` clones that revision into
`Experiments/hybrid-dependencies/evand-square-packing`, preserving its MIT license.

## Variant A: exact support transfer and controls

Imports are exact source measures, explicitly `SEED_ONLY`, not accepted fixed-B
certificates. Repeat `--seed` to union the external and own supports. The existing
native generator, one-column pricing and full two-route gate are the control.
The original `native_ab` and `run_n12_frontier` commands remain unchanged; use the
new command below to exercise this branch's hybrid variant.

From the new worktree's `packing/` directory:

```bash
git submodule update --init --recursive
uv sync --frozen
uv run --frozen python -m devtools.frontier_hybrid prepare-external \
  --root ../Experiments/hybrid-a/external-build
uv run --frozen python -m devtools.frontier_hybrid check-external \
  --root ../Experiments/hybrid-a/external-check --workers 16
uv run --frozen python -m devtools.frontier_hybrid run \
  --root ../Experiments/hybrid-a/search --workers 16 --minutes 60
```

For a union, pass both paths explicitly:

```bash
uv run --frozen python -m devtools.frontier_hybrid run \
  --root ../Experiments/hybrid-a/union \
  --seed ../Experiments/hybrid-dependencies/evand-square-packing/s12/certificates/s12_lower_3.9686.txt \
  --seed /absolute/path/to/candidate.verified.json \
  --target 15680/3951 --workers 16 --minutes 60
```

The second path must identify an existing local certificate, not a decimal log.
`--target` and `--seed` may be repeated. Defaults are in `hybrid_profile.json`.
To resume, repeat the same arguments and add `--resume`; session minutes may change.
Changed code, settings or source bytes require a new root, never a state edit.

Each job uses the existing durable supervisor, process ownership, wall/RSS/disk
guards and receipts. Ctrl-C, SIGTERM, SIGHUP or the minute limit drains the current
bounded job and its required gate; no next target starts. There is no LP-internal
checkpoint claim. Errors and unresolved searches are different statuses. Preserve
error roots for inspection; rerun corrected work in a fresh root.

The external control uses Rust at N and 2N plus exhaustive independent Python at N.
Its receipt binds source revision, checker hashes, binary hash and candidate bytes.
It is a different proof contract from our fixed-B gate. Failure under the stronger
fixed-B instrument does not invalidate the external certificate. Never report L/B.

```bash
uv run --frozen pytest tests/test_hybrid_*.py -q
```

Four simultaneous experiments on a 16-core host should use four workers each,
not sixteen each. Compare accepted side, time to acceptance and phase times,
not counts of tiny VERIFIED increments. No new bound or speedup is claimed.
