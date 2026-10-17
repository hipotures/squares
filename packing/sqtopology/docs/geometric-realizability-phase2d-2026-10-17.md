# Geometric realizability, Phase-2d: the support decomposition theorem and the V+duplicate analysis (2026-10-17)

Branch `work/topology-phase1-native`, parent note
`docs/geometric-realizability-phase2c-2026-10-17.md`. This note (1) proves the
general support decomposition theorem behind the Phase-2c cross-tabs,
(2) corrects the `H_n` cache complexity statement, and (3) resolves the
736-class wall-free V+duplicate question with an exact pair theorem, a
tolerance-boundary counterexample family, and four newly verified feasible
classes.

## 1. Scope and headline results

- **Support decomposition theorem** (Section 2): the number `f_d(k)` of
  canonical weight-`d` classes with support exactly `k` is `a_d(k) - a_d(k-1)`,
  independent of `n` for `n >= k`. The Phase-2c tables
  (`22/65/32`, `116/1295/1568`) are instances of one bijection, and the
  wreath note's stabilization theorem is an immediate corollary.
- **Corrected `H_n` cache asymptotics** (Section 3): memory
  `O(n! * 4^n * E(n))`, construction `O(n! * 8^n * E(n))`.
- **V+duplicate** (Sections 4-7): *at exact level (`tau = 0`) two unit squares
  can never have exactly two contact events between them* (case theorem over
  all six kind-pairs). Therefore every wall-free V+dup class is exactly
  impossible. At the production tolerance level the theorem is false by
  exactly one mechanism - the crossed antiparallel CS+CS pair, which lives on
  the absorption boundary with interior overlap at most the SAT tolerance -
  and four V+dup classes (2585-2588) are **verified feasible** with explicit
  witnesses. The corpus `NOT_FOUND` for those four is a demonstrated solver
  false negative; whole-family impossibility is refuted, and the remaining
  582 classes stay unresolved.

## 2. The support decomposition theorem

Let `E_n` be the event feature set on `n` squares (`|E_n| = 8n^2`), `G_n` the
full symmetry group (`n! * 8^n * 8` elements), `a_d(n)` the number of
`G_n`-orbits of weight-`d` subsets, and `support(X)` the set of square IDs
incident to at least one event of `X` (a wall event supports its square).

**Theorem.** For `d >= 1` and `1 <= k <= n`, the map

```
Phi: {G_k-orbits X of weight d with |support(X)| = k}
  -> {G_n-orbits Y of weight d with |support(Y)| = k}
     [X] |-> [iota(X)],   iota: add the squares k..n-1 with no events
```

is a well-defined bijection. Consequently, with `f_d(k)` denoting either
counted set,

```
a_d(n)  = sum_{k=1}^{min(n, 2d)} f_d(k),        f_d(k) = a_d(k) - a_d(k-1),
```

with `a_d(0) = 0`, and `f_d(k) = 0` for `k > 2d`.

*Proof.* Support is `G_n`-invariant because every group element permutes
squares bijectively and maps events to events preserving incidence, so `Phi`
is well defined; `iota` preserves support, and `X` has full support `k`, so
`iota(X)` has support `k`.

*Injective.* Let `g = (sigma, tau_0..tau_{n-1}, kappa) in G_n` with
`g . iota(X) = iota(Y)`. Take any square `s < k`. Since `X` has full support,
`s` is incident to some event `e in X`; then `g . e` is an event of `iota(Y)`,
which involves only squares `< k`; the squares of `g . e` are `sigma(s)` (and
`sigma(s')` for a square-square event with the other square also `< k`), so
`sigma(s) < k`. Hence `sigma` restricts to a permutation of `{0..k-1}`, and
`g' = (sigma|_k, tau_0..tau_{k-1}, kappa)` is an element of `G_k` with
`g' . X = Y`. Thus `[X] = [Y]`.

*Surjective.* Let `Y subset E_n` have weight `d` and support `S` with
`|S| = k`. Choose `sigma in S_n` with `sigma(S) = {0..k-1}`. Then
`sigma . Y = iota(X)` where `X` is the restriction of `sigma . Y` to the
first `k` squares (full support by construction), and
`Phi([X]) = [iota(X)] = [sigma . Y] = [Y]`.

The two constructions are inverse (restricting an embedded set recovers it),
so `Phi` is a bijection. Summing over `k <= min(n, 2d)` gives the partial-sum
identity; telescoping gives `f_d(k) = a_d(k) - a_d(k-1)`; and `d` events touch
at most `2d` squares, so `f_d(k) = 0` for `k > 2d`. *QED*

**Corollary (stabilization).** `a_d(n) = a_d(2d)` for all `n >= 2d` - the
Proposition of the wreath note, section 5.3, now as an immediate consequence
of a stronger statement. The increment identity
`f_d(2d) = a_d(2d) - a_d(2d-1) = C(d+2, 2)` is the wreath note's proved
classification of full-support classes at `n = 2d` (all `d` events are
side-side events on disjoint pairs, classified by the multiset of three
ring-parity types).

**Data.** The theorem reproduces every Phase-2c cross-tab exactly:

```
f_2 = (22, 65, 32, 6, 0, ...)        a_2 = (22, 87, 119, 125, 125, ...)
f_3 = (116, 1295, 1568, 581, 90, 10, 0, ...)
```

and the n=3 weight-2/weight-3 corpora (`22/65/32`, `116/1295/1568`).

**Tests.** `test_support_decomposition` (orbit suite) checks non-negative
differences, partial sums, `f_d(k) = 0` for `k > 2d`, and
`f_d(2d) = C(d+2,2)` against the committed exact table for `d <= 6`,
`n <= 12`. `test_support_histograms_and_crossed_pair` (realize suite)
recomputes support histograms by enumeration for `(n,d) in {(2,1),(3,1),
(2,2),(3,2),(2,3)}` and matches the differences. `corpus --count-only` now
emits `"support_histogram"`, and the CTest target
`sqtopology_realize_count_n3_w3` pins
`"class_count":2979,"support_histogram":[116,1295,1568]`.

## 3. Corrected H_n cache complexity

`h_n_event_permutations` stores one `E(n)`-entry event permutation per
parity-consistent group element. The parity-consistent subgroup is

```
|H_n| = |G_n| / 2^n = n! * 4^n * 8,
```

so the cache memory is `O(n! * 4^n * E(n)) = O(n! * 4^n * n^2)`, not
`O(4^n * E(n))` as first written in the Phase-2b limitations (corrected in
place there). Construction is worse: the current build scans all
`|G_n| = n! * 8^n * 8` elements and filters, i.e. `O(n! * 8^n * E(n))` time.
Two documented, unimplemented fixes (no current run needs `n > 3`): enumerate
`H_n` directly as `S_n x C4^n x D4_container`, and stream permutations (the
canonical branch key needs only a running minimum, not storage).

## 4. The V+duplicate family: definition and census status

A **V+duplicate** class is an `n = 3`, weight-3, support-3, wall-free class
whose three square-square contacts occupy exactly two unordered square pairs
sharing one square (the hub), with one pair carrying two contacts (the
duplicated pair). Census (from the Phase-2c corpus, 736 classes):

| duplicated pair | classes | feasible | proved | not found |
| --- | --- | --- | --- | --- |
| CC+CC | 68 | 0 | 36 | 32 |
| CC+CS | 168 | 0 | 26 | 142 |
| CC+SS | 64 | 0 | 0 | 64 |
| CS+CS | 200 | 0 -> **4** | 52 | 148 -> **144** |
| CS+SS | 168 | 0 | 0 | 168 |
| SS+SS | 68 | 0 | 36 | 32 |
| total | 736 | **4** | 150 | **582** |

The feasible column reflects this note: classes 2585-2588 verified feasible
with explicit witnesses (Section 6); they were `NOT_FOUND` in the corpus.

## 5. The exact pair theorem

Work at exact level (`tau = 0`): CC = exact corner coincidence, CS = corner
in the open side, SS = exactly collinear sides with positive overlap, under
the canonical convention that a point lying on both overlapping sides of a
positive-overlap SS contact is absorbed by it (the production extractor's
`absorbed_by_side_overlap`).

**Theorem.** Let `A` and `B` be unit squares with disjoint interiors. The
extracted contact set between `A` and `B` never has exactly two events.

*Proof by kind-pair.* Write `l_i` / `m_j` for sides, `p_i` / `q_j` for
corners of `A` / `B`.

- **SS+SS.** The two `A`-sides are distinct (a side cannot be collinear with
  two distinct `B`-side lines) and likewise for `B`. If both pairs are
  opposite sides, the two line pairs coincide, so `A = B` - interiors
  coincide, excluded. If both pairs are adjacent, the two line intersections
  give `p_i = q_j` - a CC event, so the set has at least three events
  (CC + SS + SS). Mixed adjacency is impossible (perpendicular vs parallel
  lines).
- **CC+CC.** Coincident corner pairs have equal separations (`1` or `sqrt 2`).
  Adjacent-adjacent: the two shared corners are the endpoints of one side of
  `A` and one side of `B`, so those sides are collinear with overlap `1` - an
  SS event whose absorption convention removes the two CC points, leaving one
  event, never two. Diagonal-diagonal: the centers coincide, `A = B`,
  excluded. Mixed separations are impossible.
- **CC+SS.** If the CC corner `p_i` is not on the SS side `l_a`, then `p_i`
  has distance `1` or `sqrt 2` from the line of `l_a` = line of `m_b`, but
  `p_i = q_j` lies on that line: contradiction. So `p_i` is an endpoint of
  `l_a`. Positive overlap then forces one of: `A`'s side covers `B`'s side
  (the other endpoint is also a `B` corner - a second CC event), `A` extends
  away from the segment (overlap zero, no SS), or `A`'s endpoint enters the
  side interior (a CS event). In all cases the set is not `{CC, SS}`; the
  same-side interior case additionally overlaps interiors.
- **CS+CS.** If both `A`-corners lie on one `B`-side: adjacent corners at
  distance `1` inside a unit segment must be its endpoints (two CC events);
  diagonal distance `sqrt 2` cannot fit. On two distinct `B`-sides: adjacent
  sides - the segment between the two contact points is a chord of `B`
  through its interior; `A`'s interior lies on one side of the chord and
  meets `B`'s interior on that side (both interiors occupy a one-sided
  neighbourhood of the chord), an overlap; diagonal corners on adjacent sides
  are at distance `sqrt 2` only at the far endpoints, giving CC events.
  Opposite sides - the chord is perpendicular to both, and `A` either lies
  inside `B` (overlap) or crosses it (overlap). The mixed orientation (an
  `A`-corner on a `B`-side and a `B`-corner on an `A`-side) reduces to the
  same alternatives: if the two points are distinct and on a common line the
  sides are collinear (SS forced, then absorption or overlap); otherwise the
  chord argument applies.
- **CS+SS.** A CS corner on the SS side's own line is absorbed (it lies on
  both overlapping sides) or produces a CC point; a CS corner on a different
  `B`-side `m` has distance `0` or `1` from the SS line, and the case
  analysis above forces either collinearity (absorption) or a coincident
  corner (CC). No scene extracts exactly `{CS, SS}`.
- **CC+CS.** The CC corner `p = q` is a `B` corner. A CS `A`-corner `r` on a
  `B`-side: `|p - r|` is `1` (adjacent) or `sqrt 2` (diagonal). On the side
  opposite `q` no point of `A` reaches at distance `1` in the interior
  parameter range; on a side incident to `q`, the chord `p r` cuts the corner
  triangle of `B`, and `A`'s interior, on either side of the chord line,
  overlaps `B`'s interior. A CS `B`-corner on an `A`-side is symmetric.
  Degenerate placements put `r` at a `B` corner (CC, absorbed by the SS that
  the collinear sides create). *QED*

A brute-force classifier over all 2,752 feature combinations and all six
kind-pairs (analytic solution of the contact equations in the translation,
dense theta scans, production extractor as ground truth) confirms: **no
feature combination realizes an exact two-event pair set with disjoint
interiors** (`CC+CC 0/240, CC+CS 0/512, CC+SS 0/256, CS+CS 0/992, CS+SS
0/512, SS+SS 0/240`).

Because extraction between two squares depends only on their two poses, the
theorem transfers verbatim to `n`-square scenes: *in every exact scene, the
pair-resolved contact set of any square pair has size different from 2.*
Hence **no wall-free V+dup class is exactly realizable** - the duplicated
pair would need exactly two events.

## 6. The tolerance loophole: the crossed antiparallel pair

At production tolerances (contact `1e-7`, CS interior margin `1e-6`, SAT
overlap tolerance `1e-6`) the theorem fails in exactly one observed way. Take
two squares with relative orientation `theta = pi + eps` (`|eps| ~ 7e-7`)
positioned so that corner `p_0` of `A` lies within `1e-7` of side `m_0` of
`B` and corner `q_0` of `B` lies within `1e-7` of side `l_0` of `A`, with
interior overlap `~2e-8` (inside the SAT tolerance). At `eps = 0` the sides
are collinear: SS fires and absorbs both corner events (one event). For
`0 < |eps| less than the SS parallelism window but within the CS distance
tolerance`, SS does not fire and both CS events survive: the pair extracts
exactly `{CS, CS}`.

This is not a curiosity: the Phase-2c corpus already contains two
`VERIFIED_FEASIBLE` classes of this shape (`CS+CS` pair plus one wall event,
classes 767/768 - the deletion-test witnesses, SAT slack `-2.1e-8`).

**V+dup counterexamples.** Attaching a third square `C` to such a pair by an
SS contact with partial overlap yields a full V+dup witness: the SS endpoint
events are absorbed by the very same convention, and `C` clears the other
pair square. Constructively (witness pair above, `C` placed on side 2 of the
second square with shift `0.45` and zero gap):

```
class 2585  CS(0,1)+CS(1,0)+SS   VERIFIED_FEASIBLE (was NOT_FOUND)
class 2586  CS(0,1)+CS(1,0)+SS   VERIFIED_FEASIBLE (was NOT_FOUND)
class 2587  CS(0,1)+CS(1,0)+SS   VERIFIED_FEASIBLE (was NOT_FOUND)
class 2588  CS(0,1)+CS(1,0)+SS   VERIFIED_FEASIBLE (was NOT_FOUND)
```

Each scene is contained in a container of side `< 2.9` with all three square
pairs SAT-disjoint (within tolerance) and extracts exactly the class's three
events; `verify_witness` accepts. The durable test
`test_support_histograms_and_crossed_pair` pins the class-2587 witness.

Consequences: (a) whole-family impossibility is **refuted**; (b) the four
classes are **solver false negatives** - the production solver's generic
starts never reach the `1e-6`-wide angular window; (c) among third-contact
kinds, only SS is demonstrated feasible - the constructive search over CS and
CC third-contact placements (all sides, both normals, corner and side
interior attachments, all body spins and frame parities) found no witness for
the remaining 144 unresolved CS+CS-dup classes.

## 7. Solver counterexample search and analytic starts

- **4x budget sweep** (all 586 unresolved V+dup classes, `starts = 64`,
  `max_solves = 1600`, 16 workers): **0 conversions**, 359,424 solves,
  83 s wall / 16.8 min CPU. The generic solver cannot reach the boundary
  family even with quadrupled effort.
- **Analytic pair initializer** (the crossed antiparallel template plus
  geometric third-square placements, all spins/parities/mirror): 148 CS+CS-dup
  classes scanned in 20 s, **4 verified feasible**. As a deterministic start
  family this is exactly the missing seed class: the configurations form a
  `~1e-6`-wide neighbourhood of a collinear-degenerate pose, which random
  starts hit with probability essentially zero. Production integration into
  the solver's start generator is deferred (the constructive witnesses already
  settle feasibility; wiring pair-specific seeds into the branch machinery is
  a solver refactor with no further known conversions).
- **Other duplicated kinds**: no tolerance-boundary template was found for
  `CC+CC`, `CC+CS`, `CC+SS`, `CS+SS`, `SS+SS` duplicates; their forcing
  arguments in Section 5 involve macroscopic violations (interior overlap of
  fixed size, or events pinned at distance `>= 1 - O(tau)`), so no
  `O(tau)`-evasion mechanism analogous to the crossed pair is available.
  Empirically 0/536 feasible at 4x. This is evidence, not proof; no new
  production filter is claimed for them.

## 8. Corrected accounting (two layers, per the Phase-2d policy)

All-canonical layer (corpus solver output, unchanged):

| n | w | classes | feasible | not found | proved | resolved |
| --- | --- | --- | --- | --- | --- | --- |
| 2 | 2 | 87 | 25 | 40 | 22 | 54.0% |
| 2 | 3 | 1,411 | 48 | 776 | 587 | 45.0% |
| 3 | 2 | 119 | 54 | 43 | 22 | 63.9% |
| 3 | 3 | 2,979 | 356 | 1,798 | 825 | 39.6% |

Knowledge layer (adding the four constructive witnesses; the two n=2 false
negatives of Phase-2c remain `NOT_FOUND` in the n=2 corpus but are known
feasible):

| corpus | feasible (known) | unknown | proved |
| --- | --- | --- | --- |
| n=3 w3, all classes | 360 | 1,794 | 825 |
| n=3 w3, full support f_3(3)=1,568 | **313** | 1,017 | 238 |

Full-support resolved fraction: 551/1,568 = 35.1%.

## 9. Tests, CI, runtime

- New durable tests: support decomposition arithmetic (`d <= 6`, `n <= 12`);
  support histograms by enumeration for five small `(n, d)`; the crossed-pair
  V+dup witness; `support_histogram` pinned by the enumeration-only CTest
  target. No large campaign in CI.
- Full CTest suite: 12 targets green (Section 10 commit).
- Runtime: pair classifier 101 s single-core; 4x V+dup sweep 83 s at 16
  workers; constructive template scan 20 s single-core; `--count-only` with
  histogram 13.4 s.

## 10. Limitations

- The exact pair theorem is stated and proved at `tau = 0`; the tolerance
  theory is a single observed evasion family, not a classification. A full
  tolerance-level pair classification (which near-degenerate configurations
  survive extraction) remains open.
- 582 V+dup classes (and 1,017 full-support classes overall) are unresolved;
  the Section 5 forcing arguments for the five non-CS+CS kinds rule out exact
  scenes but not all tolerance-boundary scenes.
- The four new witnesses rely on interior overlap `~2e-8` accepted by the SAT
  tolerance; they are feasible by the campaign's definition (the verifier is
  the ground truth) but are geometrically degenerate. A stricter verifier
  (strict disjointness) would reject them - a definitional choice worth
  recording.
- The constructive template covers the crossed pattern and its D4/frame
  parities; other near-degenerate pair families (if any exist) would need
  their own templates.

## 11. Recommendation

1. **Tolerance-level pair classification.** Enumerate the near-degenerate
   extraction regimes (collinear-side windows, corner-near-endpoint windows)
   systematically; this is the exact boundary between the pair theorem and
   the verifier's acceptance semantics, and it decides whether the remaining
   582 V+dup classes contain more feasible members.
2. **Wire the crossed-pair start family into the solver** if further
   boundary-family censuses are planned (weight 4 at `n = 2`, `a_4(2) =
   26,620`, will contain duplicated-pair classes with the same issue).
3. **Adopt the two-layer accounting** (all-canonical vs full-support) in all
   future census reports, as mandated in the Phase-2d brief.
