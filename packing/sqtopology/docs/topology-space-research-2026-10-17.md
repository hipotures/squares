# Discrete topology-space research, 2026-10-17

First topology-space research campaign on `work/topology-phase1-native`.

Starting HEAD: `93c262bf`. The instrumentation and tooling used here were
committed as `7f41a95c` (research mode) and `362b6d6e` (campaign driver and
analysis tooling); this note is the third commit. Host: Ryzen 9 7950X3D guest,
16 vCPUs, 161 GiB RAM, nauty 2.9.3. Production runs use the PGO build
(`tools/pgo_train.sh build-pgo`); the default `build/` tree is used only for the
native tests. All code, data, and prose are in English. Unrelated work outside
this directory is preserved, and this branch is not merged to `main`.

## Question

The engine's rewrite surface is mechanical: a rewrite removes one existing
contact or adds one semantically valid contact, with no realizability claim. The
question for this campaign is whether exact canonical quotienting plus rewrite
convergence collapses the combinatorial branching of that surface into a
tractable, structured space of reachable **topology classes**, or whether the
space still explodes.

This is a statement about the classes reachable under the current rewrite system
from a given seed, not about all possible topologies, and it deliberately excludes
geometry, continuous coordinates, and SAT/SMT reasoning.

## Method

`sqtopology research FIXTURE` (`7f41a95c`) runs the exact production rewrite and
canonicalization semantics but adds research-only aggregation:

- **Exactness.** Every child is validated and canonicalized with the same code
  path the search uses, and the emitted `SQK5HEX` key set is byte-identical to the
  production search on the same seed and depth (differential test in
  `tests/test_sqtopology.cpp`).
- **Counting scope.** Each run is a single process, so the reported counts are
  global-unique counts for the whole reachable set. This is recorded in every JSON
  as `"counts_scope": "global-unique-single-process"`. Multi-worker searches are
  exploratory only, because states shared across shard boundaries are re-expanded
  once per shard; the width-1 count is the true global count.
- **Memory.** Research state is compact fixed-width counters indexed by canonical
  id (discovery depth, incoming-event count, distinct-parent count). No full
  `Topology`, parent pointer, or variable-length metadata is retained per state.
  The dominant memory is the exact-key store, roughly `unique_classes *
  exact_key_size`.
- **Two regimes.** `--additions uncapped` enumerates the full event neighborhood
  `E(n)` and is the scientific core; `--additions 256` reproduces the production
  cap for contrast and audit cross-checking.

The campaign driver `tools/research_campaign.sh` (`362b6d6e`) runs a fixed list of
seeds and depths and writes one JSON per run plus exact key files for the
same-square-count overlap study. Plots and tables come from
`tools/research_analyze.py`, which is stdlib-only (no matplotlib).

### The reachable-set model

A rewrite toggles exactly one contact event, and the full event set is

```
E(n) = 64 * C(n, 2) + 32 * n      (square-square feature pairs + square-wall pairs)
```

because each of the 8 feature pairs across two squares admits two orientations
(64 per pair) and each of a square's 4 features against a wall admits two
orientations (32 per square). If additions are uncapped, each step flips one bit of
a `{0,1}^E` vector, so the depth-`d` reachable **labeled** set is the Hamming ball
`sum_{i<=d} C(E, i)`. The scientific object is the number of **canonical orbits**
of that ball. If the orbit count tracks the ball closely, its per-depth ratio
obeys `(E - d + 1) / d`; that ratio is the growth-law prediction this campaign
tests. It is subexponential and, once `d > E/2`, eventually drops below one, so the
space would stop growing and terminate — the opposite of an exponential explosion
in the depth at fixed `n`.

## Result 1: exact branching identity, `raw = frontier * E(n)`

Every experiment confirms that the raw candidate count at depth `d` is exactly

```
raw_candidates(d) = parents_expanded(d-1) * E(n)
```

with no exceptions across all seeds and both regimes. From any state, a rewrite
removes each present contact or adds each absent event, so the per-parent rewrite
count is exactly `E(n)`: for `grid-4x4-minus-one` (`E = 7200`), depth 2 has
`3630 * 7200 = 26,136,000` raw candidates. The branching factor per parent is
therefore a constant `E(n)`; all growth lives in the frontier size.

## Result 2: the space is subexponential, not exponential

Table 2 lists, for the uncapped runs, the new-class count per depth and the
observed ratio against the Hamming-ball prediction `(E - d + 1) / d`. The
prediction is an upper bound; the gap is canonical collapse of symmetric classes,
which is largest at small `E`/`d` and narrows as `d` grows (clearly for
`isolated-1`).

Table 2: uncapped growth-law check.

| fixture | E | d | new | obs ratio | (E-d+1)/d |
|---|---:|---:|---:|---:|---:|
| isolated-1 | 32 | 6 | 15,454 | 4.33 | 4.50 |
| isolated-1 | 32 | 7 | 55,170 | 3.57 | 3.71 |
| isolated-1 | 32 | 8 | 170,302 | 3.09 | 3.12 |
| isolated-1 | 32 | 9 | 448,254 | 2.63 | 2.67 |
| isolated-1 | 32 | 10 | 1,026,402 | 2.29 | 2.30 |
| grid-2x2 | 512 | 2 | 16,571 | 227.00 | 255.50 |
| grid-2x2 | 512 | 3 | 2,782,337 | 167.90 | 170.00 |
| line-4 | 512 | 3 | 5,563,281 | 167.88 | 170.00 |
| grid-3x3 | 2592 | 2 | 421,045 | 1206.43 | 1295.50 |
| grid-4x4-minus-one | 7200 | 2 | 12,960,869 | 3570.49 | 3599.50 |

For `isolated-1` (`E = 32`) the observed ratios converge onto the prediction
almost exactly by depth 6 and continue to fall (`4.33, 3.57, 3.09, 2.63, 2.29`).
This is the signature of binomial growth with a decreasing ratio, not exponential
growth. For the larger seeds the depth-2 ratios are also within ~10% of
prediction (`3570.49` vs `3599.50` for `grid-4x4-minus-one`).

The absolute sizes are still large because `E(n)` grows as `O(n^2)` with a large
constant: `E(15) = 7200`, so even at depth 2 the labeled ball is ~`2.6e7`. The
space is structured but its scale is set by `E(n)`, not by depth.

## Result 3: canonical quotienting and residual symmetry

The number of canonical classes is far below the labeled ball, and the
compression deepens with depth. Table 3 gives the cumulative unique count at the
final depth against the labeled ball at that depth.

Table 3: canonical compression (uncapped, final depth).

| fixture | E | depth | unique | labeled ball | unique / ball |
|---|---:|---:|---:|---:|---:|
| isolated-1 | 32 | 10 | 1,720,035 | 1.08e8 | 0.016 |
| corner-corner-2 | 128 | 4 | 263,953 | 1.10e7 | 0.024 |
| corner-side-2 | 128 | 5 | 7,284,478 | 2.76e8 | 0.026 |
| disjoint-2 | 128 | 5 | 509,250 | 2.76e8 | 0.002 |
| disjoint-4 | 512 | 3 | 3,691 | 2.24e7 | 0.0002 |
| grid-2x2 | 512 | 3 | 2,798,982 | 2.24e7 | 0.125 |
| line-4 | 512 | 3 | 5,596,566 | 2.24e7 | 0.250 |
| grid-3x3 | 2592 | 2 | 421,395 | 3.36e6 | 0.125 |
| grid-4x4-minus-one | 7200 | 2 | 12,964,500 | 2.59e7 | 0.500 |

The residual symmetry is exposed directly by `CanonicalSymmetry` (nauty group
size and orbit count), not inferred from duplicates. Seed automorphism groups vary
by seed and control the early compression: `disjoint-4` has group size ~`10^5.9`
(square permutations and per-square D4), `isolated-1` `10^1.8` (=64), `grid-2x2`
and `grid-3x3` `10^0.9` (=8), and `grid-4x4-minus-one` `10^0.3` (the reflection
through the removed square). Deep classes are almost all trivial: among the 12,960,869 classes first
discovered at `grid-4x4-minus-one` depth 2, 12,955,525 have a trivial
automorphism group. The heavy compression for `disjoint-4` and `disjoint-2` at low
depth comes from their large symmetric seed groups collapsing many early
configurations into few orbits; by the depths shown here the deep classes are
mostly rigid.

A clean structural surprise: `corner-corner-2` and `side-side-2` have exactly equal
class counts (263,953 at depth 4) and equal counts of contact kinds up to the
corner-corner/side-side swap. They are the two `n = 2` seeds related by exchanging
the two "internal" contact kinds, and they generate equal-cardinality sets.

## Result 4: strong many-path convergence

Table 4: convergence at the final depth (uncapped).

| fixture | unique | multi-parent | single-parent | multi / unique | max distinct parents |
|---|---:|---:|---:|---:|---:|
| isolated-1 | 1,720,035 | 1,720,035 | 0 | 1.00000 | 32 |
| corner-side-2 | 7,284,478 | 7,284,440 | 38 | 0.99999 | 128 |
| grid-2x2 | 2,798,982 | 2,798,611 | 371 | 0.99987 | 511 |
| line-4 | 5,596,566 | 5,596,200 | 366 | 0.99993 | 512 |
| grid-4x4-minus-one | 12,964,500 | 12,957,300 | 7,200 | 0.99944 | 3630 |
| disjoint-4 | 3,691 | 3,617 | 74 | 0.980 | 57 |

Virtually every non-seed class is reachable from at least two distinct canonical
parents; `isolated-1` reaches all 1,720,035 classes by multiple parents and the
`grid-4x4-minus-one` maximum distinct-parent count equals its whole depth-1
frontier (3630). Duplicate candidate fractions rise with depth (up to ~0.93 for
`isolated-1` at depth 10), so the exact-key dedup is doing most of the compression.
This is the rewrite system converging on a small set of classes through a very
large number of distinct rewrite paths.

## Result 5: contact layering controls overlap

Mean contact count of the classes first discovered at depth `d`:

- empty seeds satisfy an exact law: mean contacts `= d` (`isolated-1`: `1..10`
  exactly; `disjoint-2`: `1..5`; `disjoint-4`: `1..3`). Discovery depth literally
  equals contact count, because a minimum-distance-`d` state from the empty seed
  has exactly `d` contacts.
- non-empty seeds satisfy `mean contacts ~= seed_contacts + d`: `grid-4x4-minus-one`
  `50, 50.76, 51.44, 52.11` for `d = 0..3`; `line-4` `13, 13.93, 14.90, 15.85`;
  `grid-3x3` `32, 32.97, 33.95`.

So classes are stratified by contact count into a narrow band around
`seed_contacts + d`. `docs/research-plots/contacts-*.svg` show the contact-count
distribution by discovery depth (the diagonal band).

This predicts that seeds with different contact counts reach largely disjoint sets
at shallow depth, which the overlap study confirms.

## Result 6: same-square-count seed overlap

Exact `SQK5HEX` key-set overlap (counts are class counts, entries on the diagonal).

`n = 2`, depth 4:

| A \ B | disjoint-2 | corner-corner-2 | corner-side-2 | side-side-2 |
|---|---:|---:|---:|---:|
| disjoint-2 | (28,124) | 13,206 | 20,180 | 13,206 |
| corner-corner-2 | 13,206 | (263,953) | 201,922 | 127,833 |
| corner-side-2 | 20,180 | 201,922 | (399,494) | 201,922 |
| side-side-2 | 13,206 | 127,833 | 201,922 | (263,953) |

`n = 4`, depth 3:

| A \ B | disjoint-4 | line-4 | grid-2x2 |
|---|---:|---:|---:|
| disjoint-4 | (3,691) | 0 | 0 |
| line-4 | 0 | (5,596,566) | 0 |
| grid-2x2 | 0 | 0 | (2,798,982) |

Two findings:

- **Different contact counts do not overlap much.** `disjoint-2` (empty seed)
  shares only ~5% (Jaccard) with the other `n = 2` seeds, consistent with the
  contact-band separation.
- **Same square count does not imply shared classes.** The three `n = 4` seeds at
  depth 3 are pairwise disjoint, even though `line-4` (`seed_contacts = 13`) and
  `grid-2x2` (`seed_contacts = 14`) have overlapping contact bands. Their reachable
  regions do not meet within three rewrites. The reachable space is therefore not
  a single object indexed by `n`: it partitions into largely disjoint seed-centred
  regions.

The remaining `n = 2` pairs overlap substantially because they are shallow in
contact count (one seed contact) and close under the kind swap; the corner/side
family shares most of its classes.

## Result 7: capped vs uncapped, and the audit cross-check

The production cap of 256 additions truncates each parent's neighborhood, so the
capped space is a subset of the uncapped space at the same depth but reaches
deeper for the same cost.

Table 5: capped regime (256 additions).

| fixture | depth | unique | wall s | peak GiB |
|---|---:|---:|---:|---:|
| grid-2x2 | 3 | 897,475 | 6.1 | 0.34 |
| grid-3x3 | 3 | 2,835,105 | 35.9 | 1.40 |
| grid-4x4-minus-one | 3 | **4,392,083** | 85.7 | 3.23 |

The capped `grid-4x4-minus-one` depth-3 count of **4,392,083** matches the earlier
audit's width-1 global count (`docs/performance-2026-10-16.md`, "Audit follow-up")
exactly. That is an independent cross-check that the research traversal reproduces
the production reachable set, not just its key set. Capped runs stay well within
memory (3.2 GiB peak at ~4.4M classes), so the cap is a practical exploration
regime, while the uncapped regime is the scientific one.

## Result 8: differential validation

Before the campaign, the research key set was compared to the production search:
`isolated-1` depth 4 (885 classes), `disjoint-2` depth 3 (1504),
`corner-side-2` depth 3 (19,584), and `grid-2x2` depth 2 all match byte-for-byte on
the sorted `SQK5HEX` keys and on raw/unique counts. The capped `grid-4x4-minus-one`
depth-3 count additionally matches the audit. The research traversal therefore
measures the same object the production engine builds.

## Memory and runtime

Peak RSS tracks the exact-key store plus the current frontier, consistent with
`unique_classes * exact_key_size`. Key size grows with `n`: the exact key is
643–646 bytes at `n = 15` but far smaller at `n = 1`, so per-class memory ranges
from ~0.26 GiB/Mclass (`isolated-1`) to ~0.69 GiB/Mclass
(`grid-4x4-minus-one`).

| fixture | unique | wall s | peak GiB | GiB / Mclass |
|---|---:|---:|---:|---:|
| isolated-1 d10 | 1,720,035 | 59.1 | 0.44 | 0.26 |
| grid-2x2 d3 | 2,798,982 | 31.4 | 0.83 | 0.30 |
| line-4 d3 | 5,596,566 | 66.2 | 1.64 | 0.29 |
| corner-side-2 d5 | 7,284,478 | 111.5 | 2.10 | 0.29 |
| grid-4x4-minus-one d2 | 12,964,500 | 213.2 | 8.90 | 0.69 |

The `grid-4x4-minus-one` row is higher per class because its depth-1 frontier
(3630 full `Topology` objects) and larger average key are less amortized. Memory is
linear in the number of discovered classes, which is the practical wall for wide
runs; the PGO build kept runtime predictable (canonicalization dominates).

## Limitations

- Single-process counts only. Multi-worker runs would re-expand shared states and
  are not usable for authoritative counts.
- Reachability here is under the current mechanical rewrite system from one seed,
  not "all topologies" and not realizability-filtered.
- Uncapped exploration is feasible only up to `E(n)` and depth where the frontier
  fits memory; the largest uncapped run here is `grid-4x4-minus-one` depth 2
  (`E = 7200`, 12.96M classes, 8.90 GiB). Uncapped depth 3 there is out of reach
  (frontier ~12.9M parents, ~`9.3e10` raw candidates).
- The growth-law comparison is strongest where `d` is large relative to the
  residual symmetry; low-depth ratios are upper-bounded but not tight.
- Symmetry is reported from nauty per class and is exact; the "trivial group"
  tallies are exact counts, but no group-theoretic classification of the residual
  symmetry is attempted here.

## Open questions

1. Does the observed ratio follow `(E - d + 1)/d` through its turnover (ratio `< 1`
   near `d = E/2`) and then terminate? `isolated-1` (`E = 32`) can reach `d ~ 16`.
2. Is the compression factor `unique / ball` a function of the residual symmetry
   alone, and can it be predicted before enumeration?
3. How does the depth-1 and depth-2 class count scale with `n` (the `E(n)` constant
   64/32), and where is the practical frontier for realistic `n`?
4. Are the seed-centred regions of Result 6 disjoint for all same-`n` seeds, or do
   some pairs merge at greater depth?

## Phase-2 recommendation

Four options for the next campaign, in the order considered:

- **A — Complete the smallest space (`E = 32`).** The `isolated-1` space is finite
  and small enough to enumerate to completion: the labeled ball at `d = 32` is
  `2^32` subsets, which residual symmetry compresses to an estimated `10^7–10^8`
  classes (~10 GiB, a few hours). Completing it would directly confirm the ratio
  falling through 1 near `d ~ 16` and the space terminating — the decisive test
  that the subexponential reading is real rather than a small-`d` artifact.
  `disjoint-2` (`E = 128`) cannot be completed, but can be pushed a few more depths.
- **B — Chart the `n`-scaling frontier.** Measure `unique(1)` and `unique(2)` for a
  sweep of `n` (e.g. `grid-5x5`, `grid-4x4`, and a few non-grid arrangements) to
  quantify how the constant `64/32` in `E(n)` drives the practical limit.
- **C — Bounded-RAM key store.** Add a hash-partitioned external key store so deep
  or large-`n` runs are not memory-bound, unlocking uncapped depth 3 at
  `grid-4x4-minus-one` and similar.
- **D — Formalize the law.** Prove or bound the orbit count of the depth-`d` ball
  in terms of residual symmetry, making the compression factor a theorem.

**Recommendation: do A now, then B.** A is the decisive, cheap test of the central
claim and can be run in this campaign's harness without new code. B follows to turn
the `n = 1..2` observations into an `n`-scaling picture, which is what the
realizability layer will eventually need. C is the enabling engineering work only
if B shows the realistic-`n` frontier is memory-bound; D is worthwhile once A
confirms the law holds through turnover.
