# Geometric realizability, Phase-2c: corrected accounting, support analysis, and the n = 3 weight-3 census (2026-10-17)

Branch `work/topology-phase1-native`, parent note
`docs/geometric-realizability-phase2b-2026-10-17.md`. This note (1) corrects
two interpretation errors in the Phase-2b report, (2) completes the first
substantial `n = 3` weight-3 realizability census (all 2,979 canonical
classes), and (3) separates genuinely three-square geometry from two-square
configurations embedded with an unused square via a *support* classification.

Execution policy: production corpus runs use the deterministic bounded worker
pool with `--workers 16`; per-class seeds depend only on the sorted contact
keys, so results are independent of scheduling. Solver budgets are unchanged
from Phase-2b (`starts_per_rung = 32`, `max_solves = 400`, ladder
`{1, 2, 2.2, 2.5, 3, 4}`, 8 bisection steps) except where a sample study
explicitly raises them.

## 1. Corrected `a_3(3)` accounting

The Phase-2b note stated `a_3(3) = 1411` in two places. That is wrong: 1,411
is `a_3(2)`, the `n = 2` weight-3 count. The exact orbit table gives

```
E(3) = 288 event features at n = 3
labeled weight-3 event subsets:  C(288, 3) = 3,939,936
canonical full-G_3 classes:      a_3(3)   =     2,979
```

so the census target is **2,979 classes**, not 1,411. The Phase-2b text has
been corrected in place. The count is now a machine-checked regression:

- `sqtopology_realize corpus --n 3 --weight 3 --count-only` prints
  `{"schema":"sqtopology.realizability-count.v1",...,"class_count":2979}`
  (enumeration alone takes 13.4 s single-threaded);
- CTest target `sqtopology_realize_count_n3_w3` pins the string
  `"class_count":2979` without running any solver.

Every solver result in this note was produced against the 2,979-class
enumeration.

Contact keys throughout are `contact_key` strings:
`kind:square:featurekind:index|square2:featurekind2:index2` (wall contacts end
in `|w:wall`), with contact kind 0 = corner-corner, 1 = corner-side,
2 = side-side, 3 = wall, and feature kind 0 = corner, 1 = side.

## 2. Support classification

For a topology `Sigma`, define

```
support(Sigma) = number of square IDs appearing in at least one contact event
```

(a wall contact supports its square; a completely untouched square does not).
Support is invariant under `G_n` — a permutation of squares preserves the
number of used squares — so it is a property of the canonical class. The API
exposes `sqtopology::support_size(const Topology&)`, the corpus JSON records a
per-class `"support"` field (additive to schema `sqtopology.realizability.v2`;
regenerating the committed golden changed nothing but this field — all witness
digits are bit-identical), and a durable test checks `G_3`-invariance over all
24,576 elements.

The purpose is to separate genuinely `n`-square contact structures from
lower-`n` configurations embedded with unused squares. Two exact facts drive
the analysis:

1. **Deletion.** If an `n = 3` exact witness has a completely unsupported
   square, deleting that square leaves an exact witness (same container, same
   walls) for the corresponding `n = 2` topology. This direction is always
   valid.
2. **Embedding.** An `n = 2` witness embeds into `n = 3` by adding a free
   square *only when the container has room*. For wall-contact-free
   (square-square-only) classes this is automatic: keep the witness, enlarge
   the container to `L + 2`, and place the free square strictly inside the new
   margin. For classes with wall contacts on opposite walls the container side
   is pinned by the witness and enlargement destroys the wall events, so
   feasibility at `n = 2` does **not** automatically imply feasibility of the
   embedded `n = 3` class.

## 3. Corrected interpretation of `n = 3` weight 2

Support-resolved status of the final `n = 3` weight-2 corpus (119 classes,
workers=16, R1-R14, 5.3 s, 25,132 solves; totals 54/43/22, resolved 76/119 =
63.9%):

| support | classes | feasible | not found | proved |
| --- | --- | --- | --- | --- |
| 1 | 22 | 2 | 7 | 13 |
| 2 | 65 | 23 | 33 | 9 |
| 3 | 32 | 29 | 3 | 0 |

The `n = 2` weight-2 corpus has exactly the same support-resolved vectors
(support 1: 2/7/13; support 2: 23/33/9 over 87 classes). Combined with the
embedding bijection of Section 5, the precise statement replaces the Phase-2b
prose:

- The `n = 3` weight-2 corpus is the **disjoint union** of the 87 embedded
  `n = 2` classes (statuses identical) and **32 genuinely new support-3
  classes** (29 feasible, 3 not found, 0 proved).
- **All 23 feasible square-square-only classes have support 3.** The third
  square is not "moved away"; it participates, typically as the hub of a
  two-contact V of CC/CS/SS contacts (e.g. `SS(sq0, sq2) + SS(sq1, sq2)`,
  keys `2:0:1:0|2:1:0` and `2:1:1:0|2:1:0`). These are new three-square
  contact structures.
- The three unresolved support-3 classes are V patterns with hub square 2:
  `CC(sq0,sq2) + CC(sq1,sq2)`
  (`["0:0:0:0|2:0:0","0:1:0:0|2:0:0"]`),
  `CC(sq0,sq2) + CS(sq2,sq1)`
  (`["0:0:0:0|2:0:0","1:1:1:0|2:0:0"]`), and
  `CS(sq2,sq0) + CS(sq2,sq1)`
  (`["1:0:1:0|2:0:0","1:1:1:0|2:0:0"]`).
- The identical `n = 2`/`n = 3` wall-contact cross-tab is **evidence
  consistent with predominantly local wall obstructions**, not a theorem. The
  support decomposition is the precise statement: every support < 3 class is
  an embedded lower-`n` class, and no new *proved* obstruction appears in the
  support-3 set.

Feasible `n = 3` weight-2 witnesses use branch 0 in 52 cases and branch 4 in 2
(`frame_reflected` on one square), unchanged from Phase-2b.

## 4. Complete `n = 3` weight-3 census

Target: all `a_3(3) = 2,979` canonical classes, default Phase-2b budget,
workers=16.

| quantity | value |
| --- | --- |
| classes | 2,979 |
| VERIFIED_FEASIBLE | 356 |
| NOT_FOUND | 1,798 |
| PROVED_INFEASIBLE | 825 |
| resolved | 1,181 (39.6%) |
| unknown | 1,798 (60.4%) |
| solves | 667,758 |
| wall time | 130.0 s |
| CPU time | 1,818.9 s |
| effective cores | 14.0 |
| branch solves attempted | 3,345 over 2,154 unfiltered classes (mean 1.55) |

First-rule attribution of the 825 proofs:

| rule | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | R9 | R10 | R11 | R12 | R13 | R14 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| count | 51 | 98 | 40 | 41 | 28 | 19 | 21 | 33 | 42 | 125 | 96 | 93 | 72 | 66 |

Feasible witnesses use frame branch 0 in 291 cases, 1 in 13, 2 in 34, and 4 in
18, so 65/356 = 18.3% require a non-standard feature-frame parity. Reported
container sides range 2.0023 to 3.8867 (median 2.1531).

Support-resolved totals (full-support = support 3):

| support | classes | feasible | not found | proved | resolved |
| --- | --- | --- | --- | --- | --- |
| 1 | 116 | 0 | 13 | 103 | 103 (88.8%) |
| 2 | 1,295 | 47 | 764 | 484 | 531 (41.0%) |
| 3 | 1,568 | 309 | 1,021 | 238 | 547 (34.9%) |

The support-1 and support-2 parts are exactly the embedded `n = 2` weight-3
corpus (116 + 1,295 = 1,411 classes; Section 5). The headline corrected
conclusion is therefore: **309 full-support three-square topologies are
verified feasible, 238 full-support classes are proved infeasible, and 1,021
full-support classes remain unresolved**; the aggregate 39.6% resolved
fraction mixes these with the embedded two-square corpus, whose own resolved
fraction is 45.0%.

## 5. The `n = 2` -> `n = 3` embedding map

For every `n = 2` weight-3 class: embed (add an untouched square), canonicalize
the event bitset under all 24,576 elements of `G_3`, and look the result up in
the `n = 3` weight-3 corpus. All 1,411 embeddings land on a class
(0 missing), the map is injective, and supports match; the image is exactly
the 1,411 support <= 2 classes. The status transition table (final corpora,
R1-R14 on both sides):

| n = 2 status | -> feasible | -> not found | -> proved |
| --- | --- | --- | --- |
| feasible (48) | 45 | 3 | 0 |
| not found (776) | 2 | 774 | 0 |
| proved (587) | 0 | 0 | 587 |

Five off-diagonal entries, all understood:

- **2 false negatives at `n = 2`** (`NOT_FOUND -> VERIFIED_FEASIBLE`). The
  `n = 3` witnesses for classes 767/768 have an untouched square; deleting it
  and re-verifying produced **exact `n = 2` witnesses** for the `n = 2`
  classes 599/600: both are `CS(sq0,sq1) + CS(sq1,sq0)` plus
  `wall-side(sq0, side2, w0)` (class 599) or `wall-corner(sq0, corner3, w0)`
  (class 600). These are solver discovery differences, not geometric
  differences: at `n = 2` the same classes convert with 64 starts (class 599,
  505 solves, L = 2.0859) and 128 starts (class 600, L = 4) at the same
  1,600-solve budget. The durable test suite now includes the deletion
  transfer for this class shape.
- **3 capacity-obstructed embeddings** (`VERIFIED_FEASIBLE -> NOT_FOUND`).
  Classes 321/463/765 have wall contacts on **opposite** walls (0 and 2) with
  witnesses at L in [2.0000, 2.0047]; the two squares span the container, and
  a grid search (0.05 spacing x 8 orientations) found no placement of a third
  unit square in the same container. Enlarging the container destroys the
  opposite-wall events. These are consistent with a genuine capacity
  obstruction for the embedded class; they are *not* counted as solver
  failures, and infeasibility is not proved either.

The embedding direction that is always valid geometrically — wall-contact-free
witnesses into a larger container — is a durable test: the verified `n = 2`
side-side witness embeds into `n = 3` at container `L + 2` with the free
square at `(L + 0.6, L + 0.6)` and re-verifies exactly.

## 6. Contact-graph and wall cross-tabs at `n = 3`, weight 3

For full-support classes, classify by wall-contact count and the multigraph on
the three squares (edges = square-square contacts; `V` = two distinct pairs
sharing a square, `triangle` = three distinct pairs, `pair+1dup` = two
contacts on one pair plus one linking edge, `0edges` = wall contacts only):

| walls | graph | classes | feasible | not found | proved |
| --- | --- | --- | --- | --- | --- |
| 0 | V + 1 dup | 736 | **0** | 586 | 150 |
| 0 | triangle | 200 | 18 | 175 | 7 |
| 1 | V | 352 | 180 | 152 | 20 |
| 1 | pair + 1 dup | 72 | **0** | 56 | 16 |
| 2 | pair | 186 | 89 | 52 | 45 |
| 3 | 0 edges | 22 | 22 | 0 | 0 |

Overall wall-count cross-tab (all 2,979 classes):

| wall contacts | feasible | not found | proved | resolved |
| --- | --- | --- | --- | --- |
| 0 | 18 | 1,023 | 313 | 24.7% |
| 1 | 182 | 479 | 131 | 39.5% |
| 2 | 126 | 245 | 212 | 58.0% |
| 3 | 30 | 51 | 169 | 79.5% |

Two structural observations:

- The **wall-free V-with-duplicate family (736 classes) contains no feasible
  class at all** (150 proved, 586 unresolved). Two contacts between one pair
  plus one contact to the third square appear to over-constrain the triple.
  This is the single largest unresolved family (586 classes) and the clearest
  target for the next proof rule. The same pattern with one wall contact
  (`pair + 1 dup`, 72 classes) is also feasible-free.

  **Phase-2d update.** The zero-feasible observation is now explained: at
  exact level two unit squares can never carry exactly two contact events
  (pair theorem), so the family is exactly impossible; at production
  tolerance the crossed antiparallel CS+CS pair evades absorption and four
  V+dup classes (2585-2588) are verified feasible with explicit witnesses -
  solver false negatives, not infeasible classes. See
  `docs/geometric-realizability-phase2d-2026-10-17.md`.
- Resolvedness rises monotonically with wall-contact count (24.7% -> 79.5%):
  wall events are what the current filter set can reason about; purely
  square-square triples dominate the unknown set.

## 7. Frame-branch orbit statistics at `n = 3`, weight 3

Over all 2,979 classes (naive 8 branches per class; distinct contact sets;
distinct `H_3`-orbits of those sets, `|H_3| = 3,072`):

| quantity | naive | distinct sets | `H_3` orbits |
| --- | --- | --- | --- |
| total | 23,832 | 12,391 | **4,423** |
| mean | 8 | 4.16 | **1.48** |
| median | 8 | 4 | 1 |
| max | 8 | 8 | 4 |

The strong collapse persists at weight 3 (81.5% reduction against naive,
64.3% against equality) but is weaker than at weight 2, where the totals were
952 -> 357 -> **136** (mean 1.14). Weight-3 contact sets pin down more of the
frame gauge, so fewer branches remain equivalent. The corpus actually
attempted 3,345 branch solves over the 2,154 classes that survived the static
filters (mean 1.55 per solved class).

## 8. New proof rule R14; R15 stays deferred

**R14 (adopted).** *A corner-side contact whose side feature is itself a
wall-side contact is infeasible.*

*Proof.* The CS point `p` lies in the relative interior of side `s` of square
`B` (parameter margin `iota`), and `s` lies within `tau` of wall `w`. Since
`B` is contained in the container, `B`'s interior occupies the inward
half-neighbourhood of `s` near `p`. `A`'s 90-degree interior wedge at `p` must
avoid it. If the wedge points inward it overlaps `B`. If it points outward it
crosses the container wall, since the unit side length is vastly larger than
`2 tau`. If it is tangent, one of `A`'s incident sides lies on `s` and the
wall, and both squares' interiors lie on the same side of the wall with a
shared boundary segment - again an interior overlap. Every case violates
containment or non-overlap by a macroscopic margin (size 1 or a boundary
crossing), never an `O(tau)` one, so the rule is tolerance-safe: no chain of
tolerances is accumulated, and the CS parameter margin keeps `p` away from the
side endpoints. The rule is manifestly `G_n`-invariant (it speaks only of the
incidence between one CS contact and one wall-side contact on the same side
feature). *QED*

This replaces the Phase-2b "forced wall event" formulation, which failed
because the forced point is only within `2 tau` of the wall. The strengthened
statement needs no forced-event bookkeeping at all: the pattern is impossible
outright, including the variants that *do* contain the corner-wall event or an
absorbing side (both were checked and are also infeasible).

Yield (first-rule attribution; no feasible class rejected in any corpus, and
the 3,000-random-scene soundness test still passes):

| corpus | new proofs |
| --- | --- |
| n = 2 weight 2 | +1 (25/40/22) |
| n = 2 weight 3 | +40 (48/776/587) |
| n = 3 weight 2 | +1 (54/43/22) |
| n = 3 weight 3 | +66 (356/1798/825), of which 26 full-support |

**R15 (CC forced wall-corner; still deferred).** For a CC-coincident corner
pair with one corner on a wall, the local half-plane argument fails: both
squares' wedges face *inward*, and with vertices within `tau` of each other
and `1.5 tau` from the wall, the SAT penetration of two inward 90-degree
wedges is `O(tau)` - inside the non-overlap tolerance. A valid scene with the
second corner at distance in `(tau, 2 tau]` from the wall cannot be excluded
by containment + SAT alone, and no tolerance-safe proof was found. The rule is
**not implemented**; closing it requires coupling the contact tolerance and
the SAT tolerance in a single certified argument, which the current
fixed-tolerance extraction does not express.

## 9. Solver-artifact sample study

A fixed deterministic sample of `NOT_FOUND` classes - the first two (in
canonical order) of every stratum defined by (support size, wall-contact
count, contact-kind multiset), capped at 24 per corpus - was re-solved at 4x
budget (`starts_per_rung = 64`, `max_solves = 1,600`, same ladder):

| corpus | sampled | conversions |
| --- | --- | --- |
| n = 2 weight 3 | 24 | 0 |
| n = 3 weight 3 | 24 | 1 |

The conversion is `n = 3` class 486,
`CS(1,2) + wall-side(0, side0, w0) + wall-side(2, side1, w0)`
(feasible at L = 3.21875, 778 solves): two squares on one wall with a rotated
third square between them. Combined with the two `n = 2` false negatives of
Section 5 (which convert at 64/128 starts), the picture is consistent: the
remaining `NOT_FOUND` set contains solver artifacts of the *start-coverage*
kind - more starts find them - rather than evidence of a missing structural
start family. The successful witnesses use the existing axis/diagonal start
geometry; no new deterministic start family was implemented, and the default
budget was left unchanged.

## 10. Corrected totals across all corpora (R1-R14, workers=16)

| n | w | classes | feasible | not found | proved | resolved | full-support (feasible/NF/proved) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 1 | 5 | 5 | 0 | 0 | 100% | - |
| 2 | 2 | 87 | 25 | 40 | 22 | 54.0% | 23/33/9 (support 2) |
| 2 | 3 | 1,411 | 48 | 776 | 587 | 45.0% | 48/763/484 (support 2) |
| 3 | 1 | 5 | 5 | 0 | 0 | 100% | - |
| 3 | 2 | 119 | 54 | 43 | 22 | 63.9% | 29/3/0 (support 3) |
| 3 | 3 | 2,979 | 356 | 1,798 | 825 | 39.6% | 309/1,021/238 (support 3) |

No feasible class was lost anywhere; R14 only moved `NOT_FOUND` classes to
`PROVED_INFEASIBLE`. Runtime at workers=16: 1.1 s (n2 w2), 21.6 s (n2 w3),
5.3 s (n3 w2), 130.0 s (n3 w3, 14.0 effective cores).

## 11. Code, CLI, and schema changes

- `support_size(const Topology&)` in `realize.hpp`/`realize.cpp`.
- Corpus JSON gains a per-class `"support"` field (additive; schema string
  unchanged at `sqtopology.realizability.v2`). The committed golden
  `tests/data/realizability-n2-w1.json` was regenerated and differs only by
  these fields.
- `corpus --count-only` prints the enumeration count without solving
  (`sqtopology.realizability-count.v1`).
- Filter **R14** (Section 8) appended to `static_infeasibility_filters`;
  R1-R13 unchanged.
- Tests: `support and embedding` (support basics, `G_3`-invariance over all
  24,576 elements, the 87-class embedding bijection into the `n = 3` weight-2
  corpus, deletion transfer of a verified `n = 3` support-2 witness to an
  exact `n = 2` witness, explicit `n = 2` -> `n = 3` witness embedding with a
  free square); R14 negative + two positive controls; CTest target
  `sqtopology_realize_count_n3_w3` pinning 2,979. The full `n = 3` weight-3
  solve remains outside CI.

## 12. Strongest corrected conclusions

1. The `n = 3` weight-2 corpus is exactly the embedded `n = 2` corpus (87
   classes, identical statuses) plus **32 genuinely new support-3 classes**
   (29 feasible). Every feasible square-square-only class at `n = 3` uses all
   three squares; the third square is a structural participant (V-hub), not
   free space.
2. The first full `n = 3` weight-3 census is complete: **2,979 canonical
   classes, 356 feasible / 1,798 not found / 825 proved (39.6% resolved)**.
   Of the 1,568 full-support classes, **309 are verified feasible, 238 proved
   infeasible, 1,021 unresolved (34.9% resolved)**.
3. The `n = 2` -> `n = 3` embedding is a support-preserving bijection onto the
   support <= 2 classes with exactly five status disagreements: two are
   demonstrated `n = 2` solver false negatives (recovered by witness
   deletion), three are capacity-obstructed embeddings on opposite-wall
   classes where the implication is not geometrically automatic.
4. R14 (CS on a wall-side is impossible) is a sound, tolerance-safe,
   `G_n`-invariant rule worth 108 proofs across the four corpora; the CC
   analogue (R15) provably resists the same local argument and stays open.
5. The dominant unresolved structure is wall-free: the full-support
   V-with-duplicate family (736 classes, zero feasible, 586 unresolved) and
   the wall-free triangle family (175 unresolved). Wall-contact classes are
   resolved far more often (79.5% at three wall contacts).

## 13. Limitations

- `NOT_FOUND` remains non-certainty: 60.4% of the `n = 3` weight-3 corpus is
  unresolved, and the sample study shows the solver is materially incomplete
  at the default budget.
- The embedding implication for opposite-wall classes is only tested by a
  discretized placement search; the three capacity cases are not proved
  infeasible.
- `L` values remain certified *upper* bounds from the ladder + bisection, not
  infima.
- The support analysis is exact but does not by itself classify *why* a
  support-3 class is hard; the graph cross-tab is descriptive.
- R14's proof uses the fixed extraction tolerances as ground truth; a
  tolerance-free formulation would state it with explicit margins.

## 14. Next recommendations

1. **Wall-free triple rules.** The V-with-duplicate family (zero feasible out
   of 736) invites a metric rigidity proof: two contacts between one pair plus
   one contact to the third square. A line/axis relation analysis (Section 7
   candidate abstraction B of Phase-2b) is the natural setting.
2. **R15 via certified tolerance coupling.** Only worth pursuing with a
   formal `tau`-vs-`SAT-tau` coupling; the local geometry alone is exhausted.
3. **Budget-tiered re-run of the unknown set.** The sample study suggests a
   cheap 2x-start tier would convert a small fraction of `NOT_FOUND`; a
   stratified 2x pass over the 1,021 unresolved full-support classes is the
   empirical next step.
4. **Weight 4 at `n = 2`** (`C(128, 4) = 10,668,000` labeled; the Burnside
   coefficient gives the canonical count) as the next census frontier, using
   the same machinery.
