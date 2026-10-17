# Discrete topology-space research, 2026-10-17

First topology-space research campaign on `work/topology-phase1-native`.

Starting HEAD: `93c262bf`. The instrumentation and tooling used here were
committed as `7f41a95c` (research mode) and `362b6d6e` (campaign driver and
analysis tooling); this note is the third commit. Host: Ryzen 9 7950X3D guest,
16 vCPUs, 161 GiB RAM, nauty 2.9.3. Production runs use the PGO build
(`tools/pgo_train.sh build-pgo`); the default `build/` tree is used only for the
native tests. All code, data, and prose are in English. Unrelated work outside
this directory is preserved, and this branch is not merged to `main`.

## Erratum and corrected mathematical interpretation

The first campaign measured the engine correctly, but several interpretations in the
original write-up were too strong. This section supersedes the affected conclusions below
and the corresponding wording in the campaign commit message.

The uncapped rewrite system has a much more explicit combinatorial description than the
first report stated. For fixed square count `n`, let `Omega_n` be the finite set of all
semantic contact events. Its size is

```
E(n) = |Omega_n| = 64*C(n,2) + 32*n,
```

where `64 = 8*8` square-feature pairs for each unordered square pair and
`32 = 8*4` square-feature/wall pairs for each square. A labeled topology is exactly a
subset `S subseteq Omega_n`, and an uncapped rewrite toggles one event. The labeled
rewrite graph is therefore the Boolean hypercube `Q_E`, not an empirically discovered
generic branching process.

Under the audited symmetry contract, canonical states are the orbits of these subsets under

```
G_n = (D4^n semidirect S_n) x D4_container,
```

so the uncapped canonical state graph is the quotient `Q_E / G_n`. For two canonical
classes the natural graph distance is the orbit-Hamming distance

```
delta([A],[B]) = min_{g in G_n} |A symmetric_difference g(B)|.
```

A depth-`d` research run from a seed therefore enumerates orbit classes intersecting the
Hamming ball of radius `d` around that seed.

This changes four interpretations from the original report:

1. **The global space is not "subexponential rather than exponential".** The labeled
   distance-`d` layer has exactly `C(E,d)` states. For fixed `d`, this is polynomial
   in `E` (`Theta(E^d)`), but for `d = alpha*E` it is exponential in `E`,
   asymptotically `2^(E*H_2(alpha)+o(E))`. The observed ratios are comparisons with this
   exact binomial baseline, not evidence of a globally subexponential state space.
2. **Crossing `E/2` is not termination.** The labeled layer ratio
   `C(E,d)/C(E,d-1) = (E-d+1)/d` falls below one after the midpoint, which only means
   successive layers shrink. The full labeled ball reaches all states only at depth `E`.
   For an empty seed, the group preserves contact count, so quotient layers of every weight
   `0..E` are non-empty and the uncapped traversal likewise cannot terminate at `E/2`.
3. **Near-universal multiple-parent counts are not, by themselves, evidence of exceptional
   quotient convergence.** Even the unquotiented hypercube gives a state at exact Hamming
   distance `d` exactly `d` geodesic predecessors. Moreover, the current
   `distinct_parents` instrumentation counts any expanded canonical state that later
   generates a child, including back-edges from deeper layers, not only geodesic
   predecessors. Quotient-specific convergence needs a depth-resolved comparison against
   the hypercube baseline.
4. **The same-`n` zero-overlap observations are shallow-ball separation, not distinct
   global basins.** `Q_E` is connected, and so is its quotient. All same-`n` seeds
   eventually reach the same uncapped canonical state space. Two radius-`r` balls being
   disjoint means their orbit-Hamming centers are farther than `2r`; it does not define
   separate components.

A further consequence is that exact orbit counting can often replace brute-force traversal.
For an empty seed, if `g in G_n` acts on `Omega_n` with event-cycle lengths
`l_1,...,l_k`, Burnside/Pólya gives the exact number of canonical classes of contact
weight `d` as

```
a_d = (1/|G_n|) * sum_g [x^d] product_i (1 + x^(l_i)),
```

and the total number of canonical states as

```
N_n = (1/|G_n|) * sum_g 2^(c(g)),
```

where `c(g)` is the number of cycles of `g` on the event set. For `n=1`, the group has
only `8*8 = 64` elements, so the next campaign should compute the exact orbit polynomial
directly and use search as an independent validation rather than enumerate the whole space
first.

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

For fixed `n`, let `Omega_n` be the complete semantic event set. The generator contains

```
E(n) = 64 * C(n, 2) + 32 * n
```

events: `8*8 = 64` feature pairs for each unordered square pair and `8*4 = 32`
feature/wall pairs for each square. A labeled topology is a subset
`S subseteq Omega_n`. With uncapped additions and removals, every rewrite toggles exactly
one event, so the labeled rewrite graph is exactly the Boolean hypercube `Q_E`.

Canonicalization quotients that hypercube by the established symmetry action

```
G_n = (D4^n semidirect S_n) x D4_container.
```

Consequently, the scientific object measured by the uncapped research traversal is the
orbit graph `Q_E / G_n`. From seed `S_0`, discovery depth is the orbit-Hamming distance

```
delta([S_0],[S]) = min_{g in G_n} |S_0 symmetric_difference g(S)|,
```

and depth `d` enumerates the canonical orbits that intersect that Hamming ball.

Before quotienting, the exact distance-`d` layer has `C(E,d)` labeled states and the
ball has `sum_{i<=d} C(E,i)`. The labeled layer ratio is exactly

```
C(E,d) / C(E,d-1) = (E-d+1)/d.
```

This ratio decreases through one near `E/2`, but that is the turnover of the binomial
layers, not termination of the state space. The layers continue through depth `E`.
For fixed small `d`, `C(E,d) = Theta(E^d)`; for `d = alpha*E`, the middle layers are
exponential in `E`, approximately `2^(E*H_2(alpha))`. Canonical orbit counts can be
much smaller, but their asymptotics are a separate group-action question.

For empty seeds, contact count equals Hamming weight and is invariant under `G_n`. This
makes the weight layers amenable to exact Burnside/Pólya orbit counting, which is the
preferred next step for the smallest `n`.

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

## Result 2: orbit-layer growth follows the exact binomial baseline at shallow depth

Table 2 compares the number of newly discovered canonical classes with the exact labeled
hypercube layer ratio `(E-d+1)/d`. The numerical agreement is real, but its interpretation
is narrower than in the original report: the formula is an exact property of the labeled
hypercube, while the canonical counts are orbit counts. The labeled count `C(E,d)` is an
upper bound on the number of canonical classes in layer `d`; the *ratio* of successive
canonical layers is not, in general, bounded by the labeled ratio because the symmetry
compression factor can vary with depth.

Table 2: uncapped orbit-layer growth compared with the labeled hypercube baseline.

| fixture | E | d | new | obs ratio | labeled ratio (E-d+1)/d |
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

For `isolated-1`, the canonical ratios approach the labeled ratios closely by the sampled
depths. This suggests that the depth-dependent orbit-compression factor is becoming locally
stable there; it does **not** establish a globally subexponential state space. At fixed
depth the labeled problem is polynomial in `E`, while around the middle layers it is
exponential in `E`. The correct next question is the exact orbit-layer count under
`G_n`, not whether the hypercube itself has an unknown growth law.

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

## Result 4: high path multiplicity is observed, but it is not yet quotient-specific convergence

The raw measurements in Table 4 are correct, but the original interpretation overstated
what they prove.

Table 4: generation-parent multiplicity at the final depth (uncapped).

| fixture | unique | multi-parent | single-parent | multi / unique | max distinct parents |
|---|---:|---:|---:|---:|---:|
| isolated-1 | 1,720,035 | 1,720,035 | 0 | 1.00000 | 32 |
| corner-side-2 | 7,284,478 | 7,284,440 | 38 | 0.99999 | 128 |
| grid-2x2 | 2,798,982 | 2,798,611 | 371 | 0.99987 | 511 |
| line-4 | 5,596,566 | 5,596,200 | 366 | 0.99993 | 512 |
| grid-4x4-minus-one | 12,964,500 | 12,957,300 | 7,200 | 0.99944 | 3630 |
| disjoint-4 | 3,691 | 3,617 | 74 | 0.980 | 57 |

Multiple generation paths are expected even before quotienting: in `Q_E`, a labeled state
at exact distance `d` from a fixed seed has exactly `d` geodesic predecessors obtained
by undoing one of the `d` toggles. In addition, the current research implementation's
`distinct_parents` counter is an all-run generation-neighbor count: a canonical state can
accrue another "parent" when a later/deeper frontier state generates a back-edge to it.
Therefore the near-one multi-parent fractions above are not a clean measurement of
additional convergence introduced by canonical quotienting.

The useful follow-up metric is depth-resolved: for a state first discovered at depth `d`,
count distinct canonical neighbors from depth `d-1` separately from same-level and
depth-`d+1` back-edges, then compare the `d-1` predecessor-orbit count with the labeled
baseline `d`. A deficit from `d` measures predecessor merging under symmetry; excess path
multiplicity elsewhere measures cycles/backtracking in the quotient graph.

## Result 5: contact count gives an exact layer law only for empty seeds

For an empty seed, discovery depth equals contact count exactly. The seed is the empty
subset of `Omega_n`, the group action preserves subset cardinality, and orbit-Hamming
distance from the empty set is therefore exactly the number of contacts. The observed
`isolated-1`, `disjoint-2`, and `disjoint-4` diagonal contact bands are a theorem of the
model, not merely an empirical trend.

For a non-empty seed with `k_0` contacts, a class first discovered at orbit distance
`d` only satisfies the general constraints

```
|k-k_0| <= d
(k-k_0) mod 2 = d mod 2
```

for a representative realizing the minimum Hamming distance. The measured means near
`k_0+d` -- for example `grid-4x4-minus-one` `50, 50.76, 51.44, 52.11` for
`d=0..3` -- show that these shallow frontiers are addition-dominated. They are not a
general identity `mean contacts = seed_contacts + d`.

Contact count still gives a useful lower bound on orbit distance:

```
delta([A],[B]) >= ||A|-|B||.
```

Therefore non-overlapping contact-count bands can certify shallow-ball separation, but
overlapping bands cannot certify intersection. The latter requires the full orbit-Hamming
distance or exact key-set overlap. The existing `contacts-*.svg` plots remain valid
descriptive measurements under this corrected interpretation.

## Result 6: same-square-count shallow balls can be far apart

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

These are measurements of finite-radius balls in one connected quotient graph, not evidence
for separate global basins. The uncapped labeled hypercube `Q_E` is connected, and taking
a group quotient preserves connectivity, so every same-`n` seed eventually reaches the
same complete canonical state space.

For graph balls, `B_r(A)` and `B_s(B)` intersect iff the center distance is at most
`r+s`. Thus the pairwise-disjoint radius-3 `n=4` balls imply pairwise orbit-Hamming
seed distances greater than 6. For `disjoint-4` versus the 13/14-contact seeds this already
follows from the contact-count lower bound. The zero overlap between `line-4` and
`grid-2x2`, whose contact counts differ by only one, contains additional structural
information and motivates computing their exact orbit-Hamming distance directly.

The substantial `n=2` overlaps likewise measure local distances between seed orbits; they
do not indicate that the same-`n` state space decomposes into persistent components.

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

1. What is the exact weight enumerator of `2^Omega_n / G_n`? For `n=1`, Burnside/Pólya
   requires only 64 group elements and should give every layer count and the total number of
   canonical states without exhaustive BFS.
2. Do the existing `isolated-1` depth-0..10 counts exactly match the first coefficients of
   that Burnside orbit polynomial? This is the cleanest independent validation of both the
   group-action model and the research traversal.
3. How do exact orbit counts scale for `n=2,3,4`? Direct group enumeration is still
   plausible at small `n`; beyond that, conjugacy classes / cycle-index methods should
   replace element-by-element enumeration.
4. What are the exact orbit-Hamming distances between the same-`n` fixture seeds? These
   distances should explain the observed shallow-ball intersections and non-intersections
   more directly than contact-count bands.
5. For large `n` and fixed small depth, can the number of canonical classes be derived or
   tightly bounded from the group action without enumerating the frontier?
6. Once the discrete orbit structure is understood, which canonical classes are
   geometrically realizable as square packings? That remains a separate Phase-2 geometry
   question.

## Corrected next-phase recommendation

The original recommendation to brute-force `isolated-1` to depth 32 is superseded. The
hypercube/quotient model exposes an exact counting route that is both cheaper and
mathematically stronger.

Recommended order:

- **A — Formalize and test the quotient-hypercube model.** Add a small, independent group
  action implementation for the semantic event set and state explicitly that uncapped
  sqtopology is `Q_E / G_n`.
- **B — Compute the exact `n=1` orbit polynomial with Burnside/Pólya.** Enumerate the 64
  elements of `D4_local x D4_container`, compute their cycle decompositions on the 32
  events, and evaluate
  `(1/|G|) sum_g product_cycles (1+x^|cycle|)`. Compare every available coefficient
  against the existing exact research counts, then obtain the full layer sequence and total
  class count without BFS.
- **C — Extend exact orbit counting to `n=2,3,4`.** Start with direct group enumeration
  where practical, then move to conjugacy-class / cycle-index aggregation when the group
  size makes element enumeration wasteful. Record complexity in `n`.
- **D — Measure orbit-Hamming seed distances.** Compute exact distances among the same-`n`
  fixture seeds and verify that they predict the observed ball-overlap thresholds.
- **E — Reassess the need for large enumeration.** Use BFS only where it measures something
  not already available analytically (for example local quotient-graph structure or later
  realizability filters). Do not add an external key store merely to enumerate a space that
  Burnside can count directly.

Only after these steps should the project decide whether the next major engineering phase is
canonical augmentation, larger-`n` combinatorial counting, or geometric realizability
`R(Sigma)`.
