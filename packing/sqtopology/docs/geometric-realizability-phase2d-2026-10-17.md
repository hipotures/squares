# Geometric realizability, Phase-2d: the support decomposition theorem and the V+duplicate analysis (2026-10-17)

Branch `work/topology-phase1-native`, parent note
`docs/geometric-realizability-phase2c-2026-10-17.md`. This note (1) proves the
general support decomposition theorem behind the Phase-2c cross-tabs,
(2) corrects the `H_n` cache complexity statement, and (3) studies the
736-class wall-free V+duplicate question. The original revision incorrectly
described four tolerance-accepted, slightly overlapping scenes as geometrically
feasible. The erratum below supersedes that interpretation.

## Erratum (2026-10-18): strict packing geometry versus numerical tolerance

This section is authoritative and supersedes the affected claims in Sections 1,
4, 6-8, 10-11 of the original Phase-2d revision.

The campaign conflated two different notions:

1. **Strict geometric realizability** `R_strict(Sigma)`: every square is
   contained in the container and the interiors of distinct squares are
   disjoint. For the SAT separation value used by the verifier this requires

   ```
   slack >= 0.
   ```

2. **Tolerance acceptance** `R_tau(Sigma)`: the current numerical verifier
   accepts a pair whenever

   ```
   slack >= -overlap_tolerance,
   overlap_tolerance = 1e-6.
   ```

   In the implementation this is
   `SatResult::interior_disjoint = (slack >= -overlap_tolerance)`.

The second relation is useful for floating-point robustness, but it is a
*tolerance-expanded numerical acceptance relation*. It is not the mathematical
non-overlap condition of square packing when the reported slack is negative.

Consequently, the four crossed CS+CS V+duplicate scenes (classes 2585-2588)
with SAT slack about `-2e-8` are **not strict geometric realizations**. Their
interiors overlap by a small but positive amount. They must be described as
`TOLERANCE_ACCEPTED` (or historical software status
`VERIFIED_FEASIBLE` under the current verifier), not as counterexamples to
strict packing geometry. They refute only the statement that the numerical
tolerance verifier enforces strict non-overlap.

This also means that historical corpus rows labelled `VERIFIED_FEASIBLE`
should not automatically be read as strict packing certificates. A witness
with non-negative SAT slack for every square pair is compatible with strict
non-overlap; a witness with negative slack is not. A systematic strict-SAT
audit of all previously accepted witnesses has not yet been recorded here, so
this erratum does **not** silently relabel all earlier feasible counts.

### Stronger strict pair theorem

The original six-case theorem ("never exactly two pair contacts") is true for
strict non-overlap, but it is weaker and more complicated than necessary.

**Theorem.** Let `A` and `B` be two nondegenerate convex squares with
disjoint interiors. Under the normalized exact contact semantics
(CC/CS/positive-overlap SS with point events absorbed by an overlapping SS),
the number of contacts extracted between that square pair is at most one.

*Proof.* `A ∩ B` is convex because both squares are convex. Since their
interiors are disjoint, `A ∩ B` has empty planar interior, hence it is either
empty, one point, or one line segment.

- Empty intersection gives no contact.
- A one-point intersection gives one normalized point contact: CC if the point
  is a corner of both squares, otherwise CS when one corner lies in the
  relative interior of the other square's side. A transverse side-interior
  crossing would create interior overlap and therefore cannot occur.
- A nondegenerate segment contained in the boundary of a polygon lies in a
  side of that polygon. Thus a segment intersection is a positive-overlap
  side-side contact. Any endpoint CC/CS incidences on that same overlap are
  removed by the normalization/absorption rule, leaving one SS event.

Therefore every strictly non-overlapping square pair contributes 0 or 1
normalized pair contact. QED.

A direct corollary is stronger than the original V+duplicate statement:

```
for every square pair {i,j} in a strict packing:
    normalized_pair_contact_count(i,j) <= 1.
```

Hence **every V+duplicate class is strictly geometrically unrealizable**,
because its duplicated pair requires two normalized contacts. The four
crossed-pair scenes do not refute this theorem: their negative SAT slack means
they lie outside `R_strict`.

### Corrected support-theorem wording

The original Section 2 also contained a separate wording error. At support
`2d`, full support forces all `d` events to be **square-square events on
pairwise disjoint square pairs**. It does *not* force them all to be side-side
events. The three single-event orbit types are the three unordered feature-kind
(or ring-parity) types CC, CS, and SS. The resulting count

```
f_d(2d) = C(d+2,2)
```

is unchanged.

## 1. Scope and headline results

- **Support decomposition theorem** (Section 2): the number `f_d(k)` of
  canonical weight-`d` classes with support exactly `k` is
  `a_d(k) - a_d(k-1)`, independent of `n` for `n >= k`. The Phase-2c
  tables (`22/65/32`, `116/1295/1568`) are instances of one bijection, and
  the wreath note's stabilization theorem is an immediate corollary.
- **Corrected `H_n` cache asymptotics** (Section 3): memory
  `O(n! * 4^n * E(n))`, construction `O(n! * 8^n * E(n))`.
- **Strict pair geometry** (Sections 4-6, corrected by the erratum): convexity
  implies that two squares with disjoint interiors have at most one normalized
  contact event between them. Therefore every V+duplicate class is strictly
  unrealizable.
- **Numerical tolerance artifact:** the current SAT verifier accepts
  `slack >= -1e-6`. Four crossed CS+CS scenes have slack about `-2e-8` and
  were historically reported as `VERIFIED_FEASIBLE`; they are
  `TOLERANCE_ACCEPTED`, not strict packing realizations.

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
square-square events on pairwise disjoint square pairs, classified by the
multiset of the three unordered feature-kind/ring-parity types CC, CS, and SS).

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

## 4. The V+duplicate family: corrected strict/tolerance status

A **V+duplicate** class is an `n = 3`, weight-3, support-3, wall-free class
whose three square-square contacts occupy exactly two unordered square pairs
sharing one square (the hub), with one pair carrying two contacts (the
duplicated pair). There are exactly 736 such canonical classes.

The original Phase-2d table mixed strict geometry with tolerance acceptance.
The corrected interpretation is:

| duplicated pair | classes | strict realizable | tolerance-only witnesses found | production-filter proved | production NOT_FOUND after template |
| --- | ---: | ---: | ---: | ---: | ---: |
| CC+CC | 68 | 0 | 0 | 36 | 32 |
| CC+CS | 168 | 0 | 0 | 26 | 142 |
| CC+SS | 64 | 0 | 0 | 0 | 64 |
| CS+CS | 200 | 0 | 4 | 52 | 144 |
| CS+SS | 168 | 0 | 0 | 0 | 168 |
| SS+SS | 68 | 0 | 0 | 36 | 32 |
| **total** | **736** | **0** | **4** | **150** | **582** |

The strict-realizable column is a theorem (Section 5), not a solver result.
The last two columns retain the historical production-pipeline accounting:
before the strict theorem was used as a general proof rule, only 150 classes
were rejected by R1-R14 and 582 remained numerically unresolved. The four
crossed CS+CS scenes are accepted only by the tolerance-expanded verifier and
must not be counted as geometric counterexamples.

## 5. Strict pair-contact theorem (strengthened by convexity)

The original revision proved by six contact-kind cases that two
strictly non-overlapping unit squares cannot extract *exactly two* contacts.
That statement is correct but unnecessarily weak.

Work in strict packing geometry: closed unit squares may touch, but their
interiors are disjoint. Use the normalized exact contact semantics: CC and CS
for point intersections, positive-overlap SS for segment intersections, with
CC/CS endpoint incidences absorbed when they lie on the positive SS overlap.

**Theorem.** For any pair of strictly non-overlapping squares, the normalized
pair-resolved contact set has cardinality at most one.

*Proof.* Let the two closed squares be `A` and `B`. Their intersection
`A ∩ B` is convex. Because their interiors are disjoint, this convex
intersection has empty two-dimensional interior, so it can only be empty, a
single point, or a line segment.

- If it is empty, the pair has no contact.
- If it is one point, the normalized geometry yields one point event. It is CC
  when the point is a corner of both squares, otherwise CS when a corner lies
  in the relative interior of the other square's side. Two side interiors
  cannot cross transversely at that point without creating an open
  neighbourhood of interior overlap.
- If it is a nondegenerate segment, that segment lies in the boundary of each
  square. A nondegenerate segment contained in the boundary of a square lies
  in one of its sides, so the pair has one positive-overlap SS event. Any CC or
  CS endpoint incidences on that same overlap are removed by the established
  absorption normalization.

Thus there are 0 or 1 normalized pair contacts. QED.

**Corollary.** Any topology requiring two or more normalized contacts between
the same unordered square pair is strictly unrealizable.

This immediately proves strict unrealizability of all 736 V+duplicate classes:
their duplicated pair has multiplicity two.

The earlier brute-force 2,752-feature classifier remains a useful numerical
cross-check of the exact contact implementation, but it is no longer the
mathematical proof and should not be described as needed to establish the
theorem.

## 6. The crossed antiparallel CS+CS window is a tolerance artifact

The production verifier does not implement strict pairwise non-overlap. Its SAT
test accepts

```
slack >= -overlap_tolerance
```

with `overlap_tolerance = 1e-6`. Therefore scenes with a small *negative*
separating-axis gap can pass `verify_witness`.

The crossed antiparallel construction found in this campaign does exactly that.
Two squares are placed at relative orientation `pi + eps`
(`|eps| ~ 7e-7`) so that each contributes a CS contact to the other while
the otherwise collinear SS contact falls outside the extraction test. The
reported SAT slack is approximately `-2e-8`: the interiors overlap slightly,
although the overlap is below the numerical tolerance.

At `eps = 0` the sides are collinear, SS is extracted, and its positive
overlap absorbs the point events. At small nonzero `eps`, the tolerant
extractor can keep both CS events while the tolerant SAT check still accepts
the small interior penetration.

The four constructed V+duplicate scenes (classes 2585-2588) should therefore
be recorded as:

```
TOLERANCE_ACCEPTED
```

not as strict `VERIFIED_FEASIBLE` packing realizations. They are regression
cases demonstrating that the numerical verifier's tolerance-expanded relation
`R_tau` is strictly larger than the intended strict packing relation
`R_strict`.

The same warning applies to two earlier crossed CS+CS corpus witnesses
(classes 767/768): their SAT slack is also negative (about `-2.1e-8`), so
they are numerical-tolerance witnesses, not strict packing certificates.

This is a semantics/certification issue, not a solver-discovery issue. The
strict convexity theorem of Section 5 remains valid and is not refuted.

## 7. Numerical counterexample search and analytic starts

The campaign's search data remain useful, but they must be interpreted as
search inside the tolerance-expanded verifier semantics rather than strict
packing geometry.

- **4x budget sweep** over the 586 production-`NOT_FOUND` V+duplicate
  classes: 359,424 solves, 83 s wall at 16 workers, **0 additional tolerance
  acceptances**.
- **Crossed-pair analytic initializer:** scanning the 148 unresolved CS+CS-dup
  classes found the four tolerance-accepted scenes described in Section 6.
  The initializer is effective at reaching the approximately `1e-6)-wide
  numerical boundary window that generic starts miss.
- For the other duplicated kinds no analogous tolerance window was found.
  This is irrelevant to strict geometry (Section 5 already proves all
  duplicated-pair topologies impossible there), but it remains relevant if the
  tolerance-expanded numerical relation is studied as a software robustness
  problem.

The analytic initializer should therefore not be described as finding a new
physical realization family. It finds verifier boundary cases. Integrating it
into the production solver is unnecessary for strict packing research unless
the purpose is specifically to stress-test numerical tolerance semantics.

## 8. Accounting after the erratum

The following table is retained as **historical software output** from the
tolerance-based verifier. In these rows, `VERIFIED_FEASIBLE` means
"accepted by `verify_witness` under its configured tolerances"; it does not,
by itself, certify strict non-overlap.

| n | w | classes | verifier-accepted | not found | production-filter proved | historical resolved |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2 | 2 | 87 | 25 | 40 | 22 | 54.0% |
| 2 | 3 | 1,411 | 48 | 776 | 587 | 45.0% |
| 3 | 2 | 119 | 54 | 43 | 22 | 63.9% |
| 3 | 3 | 2,979 | 356 | 1,798 | 825 | 39.6% |

The four additional crossed V+duplicate constructions are *not* added to a
strict-feasible count. They are tolerance-only regression witnesses.

For strict geometry, the pair-contact theorem immediately upgrades the
V+duplicate family:

```
736 / 736 V+duplicate classes: strictly PROVED_INFEASIBLE.
```

Only 150 of those 736 had already been counted by the production filters, so
the theorem adds 586 strict impossibility results beyond the historical corpus
filter output. Consequently, for `n=3, weight=3` there are at least

```
825 + 586 = 1,411
```

strictly proved-infeasible classes. In the full-support slice the corresponding
strict proved count is at least

```
238 + 586 = 824  out of 1,568.
```

No global strict-feasible count is asserted here. The 356 historical
verifier-accepted `n=3,w=3` witnesses (and analogous accepted witnesses in
other corpora) require a systematic audit of the sign of every pairwise SAT
slack before they can be reported as strict packing certificates.

Thus the original "knowledge layer" values `360 feasible` and `313
full-support feasible` are **superseded as strict-geometric claims**. They
remain valid only as tolerance-verifier accounting.

## 9. Tests, CI, runtime

- The support-decomposition and orbit-count tests remain valid and unaffected
  by this erratum.
- The crossed-pair durable test is now interpreted as a **numerical-tolerance
  regression test**: it demonstrates that the current verifier accepts a
  slightly overlapping scene. It is not evidence of strict realizability.
- The existing CTest result recorded by the campaign remains historical:
  12 targets green.
- Runtime measurements are unchanged: pair classifier 101 s single-core; 4x
  V+duplicate sweep 83 s at 16 workers; constructive tolerance-window scan
  20 s single-core; `--count-only` with histogram 13.4 s.

A future correctness pass should add an explicit strict verifier/check
(`SAT slack >= 0`, with a separately documented floating-point certification
policy) and audit every previously accepted witness.

## 10. Limitations after correction

- The current `VERIFIED_FEASIBLE` software status uses tolerance-expanded SAT
  acceptance and therefore is not, by itself, a strict packing certificate.
- The four V+duplicate boundary scenes and the earlier crossed CS+CS witnesses
  are known examples with negative SAT slack. They must not be counted as
  strict realizations.
- The strict pair-contact theorem settles the duplicated-pair question
  mathematically, but the production filter layer does not yet encode this
  general theorem.
- A systematic strict-SAT audit of all historical accepted witnesses has not
  yet been performed, so this report intentionally does not publish a corrected
  global strict-feasible total.
- Floating-point strict certification itself needs a policy: a tiny positive
  computed slack is not automatically a formal exact-arithmetic proof. At
  minimum, numerical witnesses should distinguish positive-margin,
  near-boundary, and negative-slack cases.
- The support decomposition theorem and the orbit-counting results are purely
  combinatorial and unaffected by these geometric tolerance corrections.

## 11. Corrected recommendation

1. **Separate strict geometry from tolerance diagnostics in code and schema.**
   Introduce an explicit strict witness audit and stop using one
   `VERIFIED_FEASIBLE` label for both `R_strict` and `R_tau`. A practical
   schema could distinguish `STRICT_FEASIBLE`, `TOLERANCE_ACCEPTED`,
   `NOT_FOUND`, and `PROVED_INFEASIBLE`.
2. **Encode the convex pair-contact theorem as a general strict infeasibility
   rule.** Any topology containing at least two normalized contacts between one
   unordered square pair is strictly impossible. This subsumes the whole
   V+duplicate strict-impossibility result and should be reusable at higher
   weights.
3. **Audit all historical accepted witnesses by SAT-slack sign** before using
   feasible percentages as statements about physical square packings. Record
   minimum pairwise slack and a near-boundary category.
4. Treat tolerance-window classification (crossed CS+CS, endpoint/collinearity
   windows) as a **numerical robustness study**, not as the main geometric
   realizability program.
5. Continue using the all-canonical/full-support decomposition for future
   censuses; that combinatorial result is unaffected by the erratum.