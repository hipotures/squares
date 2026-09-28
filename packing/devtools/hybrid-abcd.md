# Isolated hybrid experiments

Base: `0ff6c5274fcf0751a2883cb49915fbff66376725` on `work/frontier-native-ab`.
External source: `evand/square-packing` at `6aa82ba457e9eaeaaa3af0833600f27f91a2fce3`,
cloned by `prepare-external` into `Experiments/hybrid-dependencies/evand-square-packing`
at that exact revision, under its own MIT license.

The four requested branches are independent descendants of the same base. The
`hybrid_profile.json` file selects this branch's experiment. The original
`native_ab` and `run_n12_frontier` entry points are unchanged; run the new entry
point below to exercise the hybrid code. Never reuse the live frontier root.

## Variant A: support transfer and controls

Import the external integer certificate as exact rational source geometry. Duplicate
points are combined, all weights must be nonnegative, and malformed input or
conditional trailers are refused. Imports are explicitly `SEED_ONLY`; no fixed-B
proof metadata is invented. Repeat `--seed` to union the external and own supports.
The existing native generator, one-column pricing and full two-route gate remain
the control instrument. A rejection under that stronger instrument does not
invalidate the external closed-cover certificate.

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

For a union, pass both exact paths (the second path must point to an existing
local certificate, not a copied decimal log):

```bash
uv run --frozen python -m devtools.frontier_hybrid run \
  --root ../Experiments/hybrid-a/union \
  --seed ../Experiments/hybrid-dependencies/evand-square-packing/s12/certificates/s12_lower_3.9686.txt \
  --seed /absolute/path/to/candidate.verified.json \
  --target 15680/3951 --workers 16 --minutes 60
```

`--target` and `--seed` may be repeated. Defaults are recorded in the branch profile.
Budget/net/batch overrides are recorded in the immutable campaign configuration.
To resume, repeat the same arguments and add `--resume`; the session's `--minutes`
may change. Source or configuration changes require a new root, never state edits.

Each generation job and proof job runs through the existing durable supervisor,
process-ownership checks, wall/RSS/disk guards and completion receipts. Ctrl-C,
SIGTERM, SIGHUP or the minute limit drains the current bounded job and its required
proof gate; no next target starts. A crash can lose the active LP, not completed
job artifacts. The runner does not claim LP-internal checkpoint recovery. Errors
are recorded separately from unresolved mathematical searches. An error root is
preserved for inspection; start a new root to rerun failed work after fixing it.

The external control is checked on unchanged bytes by Rust at N and 2N and the
independent Python checker at all N bins. Its receipt records the source revision,
checker-source hashes and binary hash. That is a different certificate contract
from our fixed-B gate. `L/B` is never a reported bound.

## Tests and measurement

```bash
uv run --frozen pytest tests/test_hybrid_*.py -q
```

Use equal total CPU budgets when comparing branches. Four simultaneous experiments
with `--workers 16` oversubscribe a 16-core host; assign four workers each instead.
Compare accepted side, time to a full-gate acceptance, phase times and memory, not
counts of tiny VERIFIED increments. No new packing bound or speedup is claimed by
these branches merely existing.

## Branch-selected variants

The extension modules are shared so that parsing, scheduling, pricing and proof
boundaries do not diverge across forks. Each independent branch selects exactly
one implementation through its committed `hybrid_profile.json`:

| Variant | Mode | Main change |
| --- | --- | --- |
| A | control | External exact support with the original one-column fixed-B generator |
| B | batched | Full-dual broad pricing, 16 columns per round, 1800 steps and B=0.99976 |
| C | interleaved | Native cut batches interleaved with up to 32 columns; one append-only HiGHS model |
| D | bins | Per-bin cores and unit-square centre envelopes, pinned exact separator, persistent LP |

B and C include the repository's retained n=12 support by default. It is not the
user's latest private run. `--own-seed /absolute/path/candidate.verified.json`
adds that run's exact geometry without replacing the default external support.
A and D default to the external support alone. No seed import transfers proof
status. Only the appropriate gate can make the result VERIFIED.

C and D carry the preceding target's whole search support, including zero-weight
sites, to the next target as `SEED_ONLY`. Its file and hash are recorded in the
new job's immutable manifest. The carried geometry is never accepted as a bound.
There is a final cut-only tail in both interleaved loops.

All variants accept repeated `--target` options. A defaults to the published
record; B/C additionally test 3.9687, 3.9690, 3.9693 and 3.9696. D uses nearby
rational targets compatible with the external integer lattice. These are search
targets, not announced results. Budgets can expire before reaching any of them.

### B: pricing is still a search

The coarse D4 triangle survey and local refinements inspect the full positive
dual, with the same tiny-weight screening as the original solver. B/C also add
candidates from a bounded 16-row arrangement. Selected candidates are rechecked
by `PreparedDepth` on the full rationalized dual, then against the actual LP
column before insertion. No full all-pairs arrangement is constructed. A pricing
deadline or empty candidate list is never a method-ceiling certificate.

### C: model lifetime

`AppendOnlyLp` adds columns over existing rows first, then appends new rows over
all columns. It retains one HiGHS object and its simplex basis. Hash checks refuse
any alteration of already-installed coefficients or objective coefficients.
Persistent does not mean faster on every workload; hashing, matrix construction,
separation and pricing remain costs measured by the phase logs.

### D: a separate proof contract

D uses the pinned external `tighten.Model` for floating incidence construction and
its witness reader, not its optimizer. Our append-only model solves the LP and
our broad full-dual pricing selects columns. Rust separates the complete bin net
on every iteration. The final gate runs Rust at N and 2N and independent Python
at every bin of N; the two N minima must match exactly. Checkers, source revision,
binary and artifact bytes are all bound in the retained receipt.

D emits `hybrid-bin-cover/v1`, never a fake fixed-B certificate. The verified copy
preserves the original candidate bytes; `verification.json` is the proof-status
record. The old fixed-B gate remains unchanged. A claim is always about L, not L/B.

Imported coordinates are never silently snapped. The external adapter explicitly
refuses a common coordinate denominator above 1,000,000, rather than overflowing
its bounded integer implementation or damaging a precise seed. D therefore may
refuse the highly heterogeneous denominators from an own run that B/C can use.
Its default rational target ladder avoids this problem for the external seed.
Only newly proposed sites are searched on that exact integer lattice.

### Reproducible short controls

```bash
HYBRID_EXTERNAL_TESTS=1 uv run --frozen pytest tests/test_hybrid_*.py -q
```

Run `prepare-external` first for the opt-in real Rust/Python integration tests.
The tiny real controls use L=3/2 and N=12, not the n=12 record or production N=6000.
The dedicated `Hybrid experiment tests` workflow installs the locked environment,
builds the pinned external checker and runs these controls plus unchanged generator
regressions. The repository-wide validation is a separate, broader surface.
