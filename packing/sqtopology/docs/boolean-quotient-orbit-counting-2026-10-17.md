# Exact Burnside orbit counting for the Boolean-quotient topology space

Second topology-space research note on `work/topology-phase1-native`, following
`docs/topology-space-research-2026-10-17.md`. Starting HEAD for this campaign was
`92f86ce4`. The work was committed in focused steps: `c3c16905` (event-set /
group-action oracle), `c77521f3` (exact reference tests and Python differential),
`e22b058a` (depth-resolved geodesic-predecessor instrumentation), and the
documentation commit containing this file. Host: Ryzen 9 7950X3D guest, 16 vCPUs,
161 GiB RAM, nauty 2.9.3, g++ 15.2, CMake 4.2.3, Python 3.14.4. All runs use the
default Release `build/` tree (no PGO). The branch is not merged to `main`.

This note executes the counting and distance recommendations A-E of the first
note: formalize and test the quotient-hypercube model, compute exact Burnside
counts, extend them to `n = 2, 3, 4`, measure exact seed orbit-Hamming
distances, and reassess the need for large enumeration. It does not modify the
first note or its erratum; the numbering of its interpretations is preserved.

## Summary

- For fixed square count `n`, the semantic event set `Omega_n` has
  `E(n) = 64*C(n,2) + 32*n` elements; labeled topologies are subsets, one
  uncapped rewrite toggles one event, and the labeled rewrite graph is the
  Boolean hypercube `Q_E`. Canonical states are the orbits under
  `G_n = (D4^n semidirect S_n) x D4_container`, `|G_n| = n! * 8^n * 8`.
- An independent oracle (`sqtopology_orbit`, `include/sqtopology/orbit.hpp`,
  `src/orbit.cpp`) was implemented from that specification. It never calls
  canonicalization; canonicalization appears only as a cross-check.
- Exact integer Burnside/Polya counting gives `a_d` (orbit classes of weight `d`)
  and `N_n` (total classes) without any graph search. For `n = 1`:
  `a_0..a_32` below and `N_1 = 67,753,072`. This matches the first campaign's
  research traversal layer by layer through depth 10, and through depth 12 in
  this campaign.
- `n = 2`: `E = 128`, `|G| = 1024`, 26 distinct induced event cycle types,
  100 conjugacy classes, and a 36-digit total. Production BFS matches every
  Burnside layer through depth 5.
- `n = 3, 4`: `E = 288 / 512`, `|G| = 24,576 / 786,432`, 78 / 203 cycle types,
  325 / 950 conjugacy classes, exact totals computed in 0.06 s / 3.08 s with
  under 10 MiB of memory.
- Exact orbit-Hamming seed distances: all six `n = 2` seed pairs are within
  `delta <= 2`; for `n = 4`, `delta(line-4, grid-2x2) = 11` on a weight gap of
  only one, which fully explains the previously observed radius-3 zero overlap
  without any disconnected-basin interpretation.
- The depth-resolved predecessor metric replaces the raw multi-parent fraction:
  for the empty seed in the labeled hypercube a state at depth `d` has exactly
  `d` geodesic predecessors; the measured ratio `sum p / sum d` is `0.9896`,
  `0.9712`, `0.9733`, `0.9488` for `n = 1, 2, 3, 4` at the depths reached here.
  Same-level edges were exactly zero in every run, as the weight-parity
  argument requires.

## 1. Model (theorem)

For a fixed square count `n`:

- **Events.** `Omega_n` consists of `64 = 8*8` square-square feature pairs for
  each unordered pair of distinct squares, and `32 = 8*4` square-feature/wall
  pairs for each square, so `|Omega_n| = E(n) = 64*C(n,2) + 32*n`. Event IDs
  are deterministic: square-square events are
  `64*pair_index(i,j) + 8*a + b`; wall events are
  `64*C(n,2) + 32*i + 4*a + w`.
- **Labeled topologies.** A labeled topology on `n` squares is exactly a subset
  `S subseteq Omega_n`. Every subset is semantically valid: a contact exists or
  it does not.
- **Rewrites.** An uncapped rewrite removes one present event or adds one
  absent event, so it toggles one event and the labeled rewrite graph is the
  Boolean hypercube `Q_{E(n)}`. Labeled distance is Hamming distance.
- **Symmetry.** `G_n` acts by a square permutation `sigma`, a local `D4`
  transform at each square, and a container `D4` transform; `|G_n| = n!*8^n*8`.
  The action is weight-preserving because it permutes events.
- **Canonical space.** Canonical states are the orbits `[S]` of `G_n`; the
  canonical graph is `Q_E / G_n`. Graph distance on it is the orbit-Hamming
  distance `delta([A],[B]) = min_{g in G_n} |A symmetric_difference g(B)|`.
- **Counting.** Burnside/Polya gives, for the number of canonical classes of
  weight `d`,
  `a_d = (1/|G_n|) * sum_g [x^d] product_cycles (1 + x^|cycle|)`,
  and for the total number of classes
  `N_n = (1/|G_n|) * sum_g 2^{c(g)}`, where `c(g)` is the number of cycles of
  `g` on `Omega_n`. The complement map `S -> Omega_n \ S` commutes with `G_n`,
  which forces the exact complement symmetry `a_d = a_{E-d}`.

For the empty seed, discovery depth in the research traversal equals contact
count (weight), so the depth-`d` new-class count must equal `a_d` exactly. This
is the theorem that makes the research traversal an independent validator of the
counts, and vice versa.

## 2. Implementation and validation harness

`src/orbit.cpp` builds `Omega_n`, decodes group elements from a mixed-radix
index (container `D4` least significant, then local `D4`s, then the Lehmer rank
of the square permutation), composes/inverts/conjugates elements, applies them to
events, computes induced event cycle types, aggregates identical cycle types (one
Polya product per distinct type, not per element), and performs all arithmetic
on an exact base-10^9 big integer. Distances scan the whole group with an
early-exit popcount and keep the first best witness.

The oracle never canonicalizes. It is cross-checked through four independent
paths:

1. **Structural tests** (`tests/test_orbit.cpp`): event-layout round trips,
   group laws (identity, inverse, associativity, conjugation), kind
   preservation (square-square events stay square-square, wall events stay
   wall), event-action bijectivity, factor-wise agreement with the production
   transforms `relabel_square`, `relabel_container`, and `permute_squares`,
   canonical-key preservation under sampled group elements, and bitset
   round-trips between topologies and event subsets.
2. **Production research traversal**: layer-by-layer equality of `new_unique(d)`
   with `a_d` for empty seeds at available depths, plus totals equality.
3. **Independent Python re-implementation** (`tools/orbit_reference.py`),
   written from the same specification with a different conjugacy-generator set.
   CTest runs it for `n = 1..3` (coefficients, cycle-type multisets, totals,
   conjugacy classes) and additionally brute-forces small hypercube layers
   directly from the action without Burnside.
4. **Exact reference JSON** in `tests/data/`: counts for `n = 1` (including the
   full per-cycle-type contribution decomposition), `n = 2, 3, 4`, and the
   `n = 2` / `n = 4` seed-distance matrices; the tests parse these files, so
   either side drifting fails CI.

The distance tool re-verifies every reported witness through the production
transformations (`witness_symmetric_difference == distance`).

## 3. Exact `n = 1` orbit polynomial

`E(1) = 32` (all events are wall events; there is no square pair). `G_1` has
`8*8 = 64` elements, all of which are products of a ring transform (local `D4`
of the single square) and a wall transform (container `D4`). Exactly six induced
cycle types occur:

| cycle type | elements | `c(g)` | `2^c(g)` | Polya factor |
|---|---:|---:|---:|---|
| `4^8` | 28 | 8 | 256 | `(1+x^4)^8` |
| `2^16` | 21 | 16 | 65,536 | `(1+x^2)^16` |
| `1^4 2^14` | 8 | 18 | 262,144 | `(1+x)^4 (1+x^2)^14` |
| `1^8 2^12` | 4 | 20 | 1,048,576 | `(1+x)^8 (1+x^2)^12` |
| `1^16 2^8` | 2 | 24 | 16,777,216 | `(1+x)^16 (1+x^2)^8` |
| `1^32` | 1 | 32 | 4,294,967,296 | `(1+x)^32` |

The multiplicities sum to 64, and
`sum over types: m * 2^c(g) = 4,336,196,608 = 64 * 67,753,072 = |G_1| * N_1`.
The multiplicity table is a consequence of the 25 `(ring class, wall class)`
pairs: each pair contributes `|R|*|W|` elements with one of the six cycle
types. Class sizes are identity 1, rotation180 1, rotation90 2,
corner-axis reflection 2, side-axis reflection 2. The full 5x5 relation:

| ring \ wall | identity | rot180 | rot90 | refl corner | refl side |
|---|---|---|---|---|---|
| identity | `1^32` | `2^16` | `4^8` | `1^16 2^8` | `2^16` |
| rot180 | `2^16` | `2^16` | `4^8` | `2^16` | `2^16` |
| rot90 | `4^8` | `4^8` | `4^8` | `4^8` | `4^8` |
| refl corner | `1^8 2^12` | `2^16` | `4^8` | `1^4 2^14` | `2^16` |
| refl side | `1^8 2^12` | `2^16` | `4^8` | `1^4 2^14` | `2^16` |

Weighted by cell sizes, this table reproduces the six multiplicities above
(28, 21, 8, 4, 2, 1). `tests/test_orbit.cpp` pins all 25 cells.

Exact coefficients `a_0 .. a_32`:

```
1, 2, 22, 116, 744, 3568, 15454, 55170, 170302, 448254, 1026402,
2042344, 3568192, 5476980, 7429674, 8906430, 9465762, 8906430,
7429674, 5476980, 3568192, 2042344, 1026402, 448254, 170302, 55170,
15454, 3568, 744, 116, 22, 2, 1
```

`N_1 = 67,753,072`. All Burnside numerators are divisible by 64, the sequence is
exactly complement-symmetric, `a_0 = a_32 = 1`, and both totals (coefficient sum
and `(1/64) * sum_g 2^c(g)`) agree. The complete numerator and contribution
tables are in `tests/data/orbit-count-n1.json`.

**Empirical validation.** The production research traversal for `isolated-1`
reaches depth 10 with per-layer counts equal to `a_d` for every `d = 0..10`:

| depth d | `new_unique(d)` | `a_d` | cumulative |
|---:|---:|---:|---:|
| 0 | 1 | 1 | 1 |
| 1 | 2 | 2 | 3 |
| 2 | 22 | 22 | 25 |
| 3 | 116 | 116 | 141 |
| 4 | 744 | 744 | 885 |
| 5 | 3,568 | 3,568 | 4,453 |
| 6 | 15,454 | 15,454 | 19,907 |
| 7 | 55,170 | 55,170 | 75,077 |
| 8 | 170,302 | 170,302 | 245,379 |
| 9 | 448,254 | 448,254 | 693,633 |
| 10 | 1,026,402 | 1,026,402 | 1,720,035 |

The depth-6..10 layers are exactly the values recorded in Table 2 of the first
note, and the final total equals its depth-10 total, `1,720,035`. A deeper run
through depth 12 also confirms layers 11 and 12 exactly (`2,042,344` and
`3,568,192`; cumulative `7,330,571`), taking 280 s wall and 2.74 GiB peak RSS.
In this campaign the depth-10 run took 43.3 s wall and 0.45 GiB peak RSS.

## 4. `n = 2`

`E(2) = 128` (64 square-square + 64 wall events), `|G_2| = 2 * 8^2 * 8 = 1024`.
The 1024 elements induce only 26 distinct cycle types, and the group has 100
conjugacy classes (computed independently: `20 * 5` by the wreath-product
class structure).

- `a_0..a_5 = 1, 5, 87, 1411, 26620, 481126`
- `a_64 = 23,390,428,548,642,033,510,637,858,756,581,126` (center of the
  complement-symmetric polynomial)
- `N_2 = 332,317,140,421,910,940,456,278,459,867,471,872` (36 digits)

**Empirical validation.** The `disjoint-2` research traversal (empty seed)
matches `a_d` for `d = 0..5`; cumulative `1 + 5 + 87 + 1411 + 26620 + 481126
= 509,250`, exactly the first campaign's depth-5 total for this seed. The first
campaign's depth-4 diagonal entry for `disjoint-2` was `28,124`, which equals
`a_0 + a_1 + a_2 + a_3 + a_4 = 1 + 5 + 87 + 1411 + 26620` exactly. Both were
counted before these polynomials existed and are now explained by them.

Hand check for the first nontrivial coefficient: a single contact at `n = 2`
is either a square-square event or a wall event. `D4` preserves ring parity
(rotations shift by even amounts, reflections negate), so up to square
permutation, local `D4`, and container `D4`, square-square feature pairs split
into three orbits by the unordered pair of ring parities, and wall events into
two orbits by ring parity, giving `a_1 = 5`, agreeing with the counter.

## 5. `n = 3` and `n = 4`

| n | E(n) | `\|G_n\|` | distinct cycle types | conjugacy classes | count runtime | peak RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 3 | 288 | 24,576 | 78 | 325 | 0.06 s | 4.5 MiB |
| 4 | 512 | 786,432 | 203 | 950 | 3.08 s | 9.5 MiB |

Head coefficients and totals (exact; full coefficient arrays are in
`tests/data/orbit-count-n3.json` and `orbit-count-n4.json`):

- `n = 3`: `a_0..a_6 = 1, 5, 119, 2979, 92770, 2985882, 94975858`;
  `N_3 = 20,236,136,706,353,419,489,706,614,231,386,596,117,233,454,241,731,617,570,180,889,797,386,693,542,586,351,616`
  (83 digits).
- `n = 4`: `a_0..a_8 = 1, 5, 125, 3560, 137549, 5938772, 268405879,
  12147272864, 537727714799`;
  `N_4 = 17,048,909,424,064,756,014,997,528,997,896,117,216,728,519,458,537,695,747,220,991,249,823,019,341,285,095,045,438,875,118,761,109,179,823,766,174,041,404,699,896,022,692,907,418,854,640,880,451,584`
  (149 digits).

Runtime is dominated by group enumeration (2.88 s of the 3.08 s for `n = 4`,
including the conjugacy-class BFS); the polynomial step takes 0.035 s. Cycle
types compress the per-element sum by 3,874x at `n = 4` (786,432 elements to
203 types). All checks (divisibility by `|G_n|` for every coefficient,
complement symmetry, endpoints, positivity, and equality of the two totals)
hold.

**Empirical validation.** New empty-seed traversals in this campaign:

| seed | depth | total classes | equals | wall s | peak RSS |
|---|---:|---:|---|---:|---:|
| disjoint-3 | 5 | 3,081,756 | `a_0 + ... + a_5` (n = 3) | 66.6 | 706 MiB |
| disjoint-4 | 4 | 141,240 | `a_0 + ... + a_4` (n = 4) | 5.6 | 44 MiB |

`disjoint-4` depth 3 was already in the first campaign (`3,691` classes); the
new depth-4 total extends it and agrees with the Burnside sum. The two large
`n = 4` campaign runs were also re-executed with the new instrumentation:
`line-4` depth 3 gives 5,596,566 and `grid-2x2` depth 3 gives 2,798,982, both
exactly the first campaign's totals.

**Scaling wall.** Direct element enumeration is comfortable through `n = 4`.
`n = 5` would have `|G_5| = 39,321,600` elements and `E(5) = 800`; naive
per-element cycle decomposition is about `3 * 10^10` event steps. Further
extension needs conjugacy-class / cycle-index aggregation of the wreath product,
not a larger search.

## 6. Exact seed orbit-Hamming distances

`delta([A],[B]) = min_{g in G_n} |A symmetric_difference g(B)|` is the graph
distance in `Q_E / G_n`. It is computed here by an exact scan over the full
group with early exit; the witness is re-verified through the production
transforms. Contact counts give the lower bound
`delta >= abs(|A| - |B|)`; the excess over the weight gap is structural.

`n = 2`, fixtures in order `disjoint-2, corner-corner-2, corner-side-2,
side-side-2` (contact counts 0, 1, 1, 1):

```
delta = [ 0 1 1 1 ]
        [ 1 0 2 2 ]
        [ 1 2 0 2 ]
        [ 1 2 2 0 ]
```

All seed pairs are within two toggles up to symmetry; `disjoint-2` is within
one toggle of each of the other three.

`n = 4`, fixtures `disjoint-4, line-4, grid-2x2` (contact counts 0, 13, 14):

```
delta = [  0 13 14 ]
        [ 13  0 11 ]
        [ 14 11  0 ]
```

For `disjoint-4` versus the others the distance equals the weight gap exactly
(13 and 14, structural excess 0). For `line-4` versus `grid-2x2` the weight gap
is only 1, while `delta = 11`: ten of the eleven toggles are structural. This is
the quantity the first note asked for when it observed that this pair's radius-3
zero overlap "contains additional structural information."

## 7. The ball criterion and the previous overlap data

In any graph, balls around centers `A` and `B` with radii `r` and `s` intersect
iff the center distance is at most `r + s`:

- if `delta(A,B) <= r+s`, take a geodesic from `A` to `B`; the point at distance
  `min(r, delta)` from `A` lies in both balls;
- if a common point `C` exists, `delta(A,B) <= delta(A,C) + delta(C,B) <= r+s`.

For the quotient, `delta` is exactly quotient graph distance, so the criterion
applies verbatim. This resolves the first campaign's overlap observations
without any basin interpretation:

- **`n = 2`, depth 4 (`r = s = 4`).** The criterion requires intersection iff
  `delta <= 8`. All six pairs have `delta <= 2`, so all off-diagonal overlaps
  must be positive; the measured values (13,206 / 20,180 / 13,206 / 201,922 /
  201,922 / 127,833) are all nonzero. Overlap *sizes* are not determined by
  `delta` alone: `corner-corner-2` vs `side-side-2` and `corner-side-2` vs
  `side-side-2` both have `delta = 2` but overlap `127,833` and `201,922`.
  The criterion predicts thresholds, not volumes.
- **`n = 4`, depth 3 (`r = s = 3`).** The criterion requires intersection iff
  `delta <= 6`; the measured distances are 11, 13, and 14, so all three
  pairwise overlaps are forced to be zero. For `disjoint-4` pairs the weight
  bound would already forbid intersection (gaps 13 and 14); for
  `line-4` vs `grid-2x2` only the exact `delta = 11` explains the observed
  zero beyond the weak `delta >= 1` bound. Zero overlap at radius 3 is a
  statement about distances, not about separate components: `Q_E` is connected,
  quotients of connected graphs are connected, and all same-`n` seeds
  eventually reach the same canonical space.
- **New direct check.** `tests/test_orbit.cpp` enumerates explicit quotient
  balls for the four `n = 2` seeds at radii 0, 1, 2 (all labeled toggle sets of
  size at most `r` relative to the seed, collapsed to canonical keys; up to
  8,257 labeled points per radius-2 ball) and verifies
  `B_r(A) intersect B_s(B) != empty iff delta(A,B) <= r+s` for all 54
  pair/radius combinations. As a second consistency check, the radius-0/1/2
  ball sizes of the empty `disjoint-2` seed are 1, 6, 93, exactly
  `a_0 + ... + a_r` for `r = 0, 1, 2`.

## 8. Depth-resolved geodesic predecessors (replaces raw multi-parent counts)

The first campaign's `distinct_parents` counter counts any expanded state that
generates a child, including back-edges from deeper layers; the erratum already
marked its near-one multi-parent fractions as *not* a convergence measurement.
The instrumentation now separates, for every state first discovered at depth
`d`:

- `p` = number of distinct canonical neighbors first discovered at depth
  `d - 1` (geodesic predecessors);
- same-level edges (child first discovered at equal depth), which must not
  occur: an edge toggles one event, so contact-weight parity flips, while the
  weight of a canonical class is fixed by `G_n`. Recorded: **zero in every
  run**, including all empty-seed and seeded runs above.
- backward edges to states discovered at depth `<= d - 2`.

On the labeled hypercube an empty-seed state at depth `d` has exactly `d`
geodesic predecessors, and forming the quotient can only merge some of those
classes, so `1 <= p <= d`; the aggregate `sum p / sum d` lies in `(0, 1]` and
equals 1 iff the quotient introduces no predecessor merging. Raw multi-parent
counts remain in the report as diagnostics only.

`isolated-1` through depth 10 (empty seed, 1,720,034 non-seed states):

| d | new | full (`p = d`) | merged (`p < d`) | predecessor histogram | backward edges |
|---:|---:|---:|---:|---|---:|
| 1 | 2 | 2 | 0 | `1: 2` | 0 |
| 2 | 22 | 6 | 16 | `1: 16, 2: 6` | 2 |
| 3 | 116 | 82 | 34 | `2: 34, 3: 82` | 28 |
| 4 | 744 | 530 | 214 | `1: 32, 2: 82, 3: 100, 4: 530` | 314 |
| 5 | 3,568 | 3,020 | 548 | `2: 6, 3: 188, 4: 354, 5: 3,020` | 2,616 |
| 6 | 15,454 | 13,462 | 1,992 | `2: 90, 3: 444, 4: 504, 5: 954, 6: 13,462` | 17,092 |
| 7 | 55,170 | 50,792 | 4,378 | `3: 48, 4: 634, 5: 1,476, 6: 2,220, 7: 50,792` | 89,070 |
| 8 | 170,302 | 159,550 | 10,752 | see JSON | 378,924 |
| 9 | 448,254 | 429,188 | 19,066 | see JSON | 1,339,450 |
| 10 | 1,026,402 | 990,752 | 35,650 | see JSON | 3,994,486 |

Aggregates: `sum p = 15,993,488`, `sum d = 16,160,846`,
`sum p / sum d = 0.98964`; 72,650 of 1,720,034 non-seed states (4.22%) have at
least one merged geodesic predecessor. Predecessor merging is rare at `n = 1`,
but it grows with `n` for empty seeds at the depths reached here:

| run | depth | non-seed states | merged | mean `p/d` |
|---|---:|---:|---:|---:|
| isolated-1 | 10 | 1,720,034 | 4.22% | 0.9896 |
| isolated-1 | 12 | 7,330,570 | 2.78% | 0.9931 |
| disjoint-2 | 5 | 509,249 | 11.91% | 0.9712 |
| disjoint-3 | 5 | 3,081,755 | 11.65% | 0.9733 |
| disjoint-4 | 4 | 141,239 | 17.20% | 0.9488 |
| line-4 | 3 | 5,596,565 | 0.22% | 0.9999 |
| grid-2x2 | 3 | 2,798,981 | 0.18% | 0.9994 |

These are descriptive measurements of the quotient graph at finite depth, not
asymptotics; the `isolated-1` mean `p/d` is even non-monotone between depth 10
and depth 12. For non-empty seeds even the baseline interpretation differs: `p`
only counts distinct depth-`d-1` parent classes, which may already be fewer than
`d` after quotienting near the seed.

## 9. Reproducibility

Counts and distances (about 4 s total for all six committed artifacts):

~~~bash
./build/sqtopology_orbit count --n 1 --contributions --json tests/data/orbit-count-n1.json
./build/sqtopology_orbit count --n 2 --json tests/data/orbit-count-n2.json
./build/sqtopology_orbit count --n 3 --json tests/data/orbit-count-n3.json
./build/sqtopology_orbit count --n 4 --json tests/data/orbit-count-n4.json
./build/sqtopology_orbit matrix --fixtures disjoint-2,corner-corner-2,corner-side-2,side-side-2 \
  --json tests/data/seed-distances-n2.json
./build/sqtopology_orbit matrix --fixtures disjoint-4,line-4,grid-2x2 \
  --json tests/data/seed-distances-n4.json
~~~

Research validation runs (one JSON per run, written under `build/validation/`
and not committed):

~~~bash
./build/sqtopology research isolated-1 --max-depth 10 --json build/validation/isolated-1-d10.json
./build/sqtopology research isolated-1 --max-depth 12 --json build/validation/isolated-1-d12.json
./build/sqtopology research disjoint-2 --max-depth 5  --json build/validation/disjoint-2-d5.json
./build/sqtopology research disjoint-3 --max-depth 5  --json build/validation/disjoint-3-d5.json
./build/sqtopology research disjoint-4 --max-depth 4  --json build/validation/disjoint-4-d4.json
./build/sqtopology research line-4     --max-depth 3  --json build/validation/line-4-d3.json
./build/sqtopology research grid-2x2   --max-depth 3  --json build/validation/grid-2x2-d3.json
~~~

`ctest --test-dir build` runs the production test suite (1.4 s), the new orbit
test suite (0.6 s), and the Python differential through `n = 3` with deep
brute-forced layers (9.4 s).

## 10. What is theorem, what is empirical

- **Theorem (specification-level):** the event set and its size `E(n)`; the
  subset/Hamming-hypercube representation of uncapped rewriting; the group
  action and `|G_n| = n!*8^n*8`; the Burnside/Polya formulas; complement
  symmetry; weight parity and the impossibility of same-level edges; the ball
  criterion; the weight lower bound; and "empty-seed research depth-`d` class
  count equals `a_d`" given an exact canonicalizer.
- **Exact arithmetic results:** all `a_d` and `N_n` for `n = 1..4` are computed
  with exact integers. Independent re-implementation checks cover `n = 1..3`
  fully (coefficients, cycle types, totals, conjugacy classes; plus Burnside-free
  brute-force layers at small depth/weight). The `n = 4` numbers rest on one
  implementation plus its internal exact checks (divisibility, symmetry,
  endpoints, two totals) and structural tests shared with `n <= 3`.
- **Empirical measurements:** the production traversal's layer-by-layer
  agreement at the depths actually run; runtimes and memory; the overlap
  matrices from the first campaign that the certified distances now explain;
  the finite-depth predecessor statistics in section 8.

## 11. Limitations

- Exact counting covers `n = 1..4` by direct group enumeration. `n = 5` needs
  conjugacy-class/cycle-index aggregation; no claim is made about asymptotics
  of `a_d` or `N_n` in `n` or `d`.
- The oracle models the audited symmetry contract exactly. It agrees with
  production canonicalization on sampled elements and keys, but it is not a
  second canonicalizer; if the production symmetry contract changes, both the
  contract tests and the oracle must be revisited.
- Research-traversal validation exists only at feasible depths: the deepest
  checks here are isolated-1 depth 12, disjoint-2/3 depth 5, disjoint-4 depth 4,
  and line-4/grid-2x2 depth 3. Nothing is claimed about deeper layers beyond the
  exact polynomials.
- The `n = 4` counts have not been re-derived by an independent implementation;
  they have passed every structural and exact-arithmetic check the smaller `n`
  also passed, plus the shared Python differential for the machinery.
- Shallow-ball separation is a distance statement at a fixed radius. It says
  nothing about connectivity or about components of the full quotient; both the
  labeled and the canonical spaces are connected and finite.

## 12. Recommended next direction

The counting model is now fully validated at `n <= 3` and computationally
cheap at `n = 4`. The options for the next phase:

- **A. Extend exact counting to `n = 5` (and possibly `n = 6`) via cycle-index /
  conjugacy-class aggregation.** This is the direct continuation of the proven
  route: replace per-element enumeration (about `3 * 10^10` event steps at
  `n = 5`) with the wreath-product cycle index, then evaluate the weight
  enumerator with exact arithmetic. Deliverable: `a_d` and `N_n` for larger `n`
  with the same check battery, cross-validated against brute force at `n <= 3`.
- **B. Quotient-graph structure at `n = 2`.** The full canonical space for
  `n = 2` has a 36-digit class count, so it is not enumerable, but representative
  sets, ball intersections, and local moments are computable with the exact
  oracle: measure distance distributions between orbit representatives, diameter
  growth, and local structure. Cheaper than A, answers how the quotient differs
  from the labeled cube.
- **C. Geometric realizability `R(Sigma)` (Phase 2).** Filter the orbit classes
  by which contacts are geometrically realizable as square packings. This is the
  strategic question the whole topology-space program is ultimately about, and
  it is orthogonal to counting.
- **D. Canonical augmentation / production engineering.** Use the quotient model
  as the specification for a faster canonical search. Least scientifically new;
  best deferred until A-C show where enumeration cost actually matters.

**Recommendation: A now.** It is cheap, directly extends the validated exact
method, and settles how the orbit counts scale before any further large
enumeration work. `B` is a natural small side study if quotient-local structure
matters for the traversal; `C` becomes the main Phase-2 program once the
discrete orbit structure is understood; `D` should wait.
