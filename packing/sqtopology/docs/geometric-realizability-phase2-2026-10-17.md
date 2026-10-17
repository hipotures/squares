# Geometric realizability of contact topologies (Phase 2)

Branch `work/topology-phase1-native`, starting HEAD `46ed8229` (Part A: the
`n = 12` low-weight closure). This note records the first Phase-2 experiment:
a geometric layer `Sigma -> R(Sigma)` with an independent verifier, solver
provenance rules, a validated scene action for the symmetry group, positive and
negative fixtures, and an `n = 2` class corpus at contact weights 1, 2 and 3.
All code, data and prose are in English. Nothing here is merged to `main`, and
no unrelated working-tree state is touched.

## 1. Question and answer format

For a fixed square count `n` a *contact topology* is a set `Sigma` of semantic
contact events (the same event set `Omega_n` used by the orbit oracle, with
`E(n) = 64*C(n,2) + 32*n`). Phase 1 counted the orbit classes `[Sigma]` under
`G_n`. Phase 2 asks which `Sigma` actually occur as contact sets of unit
squares packed in a square container.

Three statuses are allowed and nothing else:

| status | meaning |
| --- | --- |
| `VERIFIED_FEASIBLE` | an explicit scene was checked by the independent verifier and its exact contact set equals `Sigma` |
| `NOT_FOUND` | the deterministic solver budget produced no witness; this is **not** a statement of impossibility |
| `PROVED_INFEASIBLE` | a static filter proves that no scene can have `Sigma` as its exact contact set |

A weak (closure-stratum) witness is reported separately through the booleans
`exact_witness` / `weak_witness` and is never promoted to a top-level status.

## 2. Geometry and conventions

Unit squares are posed by center `(x_i, y_i)`, orientation `theta_i`
(radians, counterclockwise), and a boolean `frame_reflected` (the parity of
the semantic feature frame; see Section 7). In the body frame

- corner `c` sits at angle `135 - 90c` degrees at distance `sqrt(2)/2`;
- side `s` is the segment from corner `s` to corner `s+1`, so side 0 is the
  top edge, 1 right, 2 bottom, 3 left;
- `ring r = 2*index + (side ? 1 : 0)`, matching `feature_ring_index`;
- when `frame_reflected` is set, the label offsets are mapped through the
  body reflection `(x, y) -> (-y, -x)` (ring map `r -> 8 - r`); the occupied
  point set is unchanged.

The container is the axis-aligned square `[0, L]^2`. Wall 0 is `y = L` (top),
1 is `x = L` (right), 2 is `y = 0` (bottom), 3 is `x = 0` (left). Side `w`
faces wall `w` at `theta = 0`, which is the convention already used by the
fixtures and by the orbit module.

## 3. Contact semantics: exact and weak strata

The extraction below is implemented in `src/geometry.cpp` and documented in
`include/sqtopology/geometry.hpp`. It is written directly from the geometric
predicates and shares no code with the solver.

### 3.1 Exact stratum

| kind | rule |
| --- | --- |
| corner-corner (CC) | two corner points at distance `<= contact = 1e-7` |
| corner-side (CS) | corner point at distance `<= 1e-7` from the side segment, with segment parameter in `[interior, 1 - interior]`, `interior = 1e-6` |
| side-side (SS) | supporting lines collinear within `1e-7` and overlap length `>= overlap = 1e-6` |
| wall-corner | corner point at distance `<= 1e-7` from the closed wall segment |
| wall-side | both side endpoints at distance `<= 1e-7` from the closed wall segment |

### 3.2 Absorption

Absorption keeps the contact set canonical:

- a positive-overlap SS contact absorbs the CC and CS contacts at points that
  lie on both of its sides (the overlap endpoints);
- a wall-side contact absorbs the wall-corner contacts of its own two
  endpoints on the same wall.

"Positive overlap" means `overlap > 1e-9` (`kOverlapSlack`). The slack was
needed because raw projections of exactly touching segments can differ from
zero by a few ulps (`1.11e-16`); treating such noise as positive overlap
wrongly absorbed a genuine corner contact in the 2x2 grid scene.

Formally, let `I(P)` be the set of primitive incidences of a scene (CC, CS,
SS, wall-corner, wall-side, using the tolerances above) and let

```text
O(P) = { (i, s, j, t) in SS(P) : overlap(i, s, j, t) > 1e-9 }
```

be its positive-overlap side pairs. The exact contact set is the *normalized*
set

```text
E(P) = I(P) \ A(P),
A(P) = { CC/CS contacts at a point lying on both segments of a pair in O(P) }
     ∪ { wall-corner(i, c, w) : side c or side c-1 of square i is on wall w }.
```

The exact topology is therefore a normalized maximal-stratum description after
deterministic absorption, not the primitive incidence set. Sections 7.2 and
7.5 prove and machine-check that `E(psi_g(P)) = g . E(P)` for every `g in
G_n`; the same holds for the weak normalization, whose only differences are
the closed CS parameter range and the `overlap >= -1e-9` SS threshold, both of
which are isometry-invariant.

### 3.3 Weak stratum

The weak stratum closes the relations:

- CS uses the closed side segment (no interior margin);
- SS holds for collinear sides with `overlap >= -1e-9` (zero-length overlap
  counts);
- absorption still requires *strictly* positive overlap, so a point contact at
  a segment endpoint remains a CC contact.

Consequently the extracted exact set is always a subset of the extracted weak
set (`exact_contacts(P) subseteq weak_contacts(P)` for every scene `P`). The
diagonal corner-corner fixture demonstrates the difference: exact = 1 CC,
weak = 1 CC + 4 CS + 2 zero-overlap SS = 7 contacts.

A weak witness for `Sigma` is a scene whose weak extraction *contains*
`Sigma`. This is a containment certificate in the relaxed relation; it is not
a proof that `Sigma` is the limit of exact contact sets along a continuous
path, and it is reported as a flag, never as `VERIFIED_FEASIBLE`.

## 4. Independent verification

`verify_witness(scene, sigma)` in `src/realize.cpp`:

1. checks every corner of every square against `[0, L]^2` with tolerance
   `1e-9`;
2. checks every square pair with a separating-axis test (the same predicate
   family used by the extraction) and records the minimum slack;
3. extracts the exact and weak contact sets and compares them with `Sigma`:
   - exact acceptance requires `extracted_exact == Sigma` (no missing and no
     extra keys);
   - weak acceptance requires `Sigma subseteq extracted_weak`;
4. records diagnostics: missing/extra keys, minimum pair separation slack, and
   the smallest margin over exact relations that are present but not required
   (absorption already discounted).

The verifier is used on every solver candidate and on every fixture, and the
test suite re-verifies every returned witness.

## 5. Static impossibility filters

Only these filters may produce `PROVED_INFEASIBLE`:

- **R1** — one side feature is required on two distinct wall lines. A unit
  segment cannot lie on two different lines.
- **R2** — a corner class linked by CC contacts (union-find) is required on
  two opposite walls `w` and `w+2`, directly or through the endpoints of a
  wall-side contact. This puts one point on two parallel lines.
- **R3** — one corner is required on both members of an opposite side pair
  `s`, `s+2` of one square, again putting one point on two parallel lines.
- **R4** — a wall-side contact and a wall-corner contact of one of its own two
  endpoints on the same wall. The wall-side event absorbs the corner event in
  the exact stratum, so the two required events cannot both be exact.
- **R5** — two adjacent corners of one square required on the same wall. Both
  endpoints of the connecting side are then on the wall, so that side-wall
  event is extracted and absorbs both corner events.
- **R6** — two opposite corners of one square required on the same wall. The
  other two corners sit at distance `1/sqrt(2)` on either side of the wall
  line, so one of them is outside `[0, L]^2`. The violation is macroscopic
  (`1/sqrt(2)`), hence far above the `1e-7` contact tolerance.

R4 and R5 are absorption rules of the exact stratum; R6 is a containment rule.
All six predicates are invariants of the labelled incidence structure:
endpoint, adjacency and opposite-pair relations are D4 relations, and wall
distinctness is preserved by the container D4 element. A proof on the class
representative therefore lifts to every gauge branch and to the whole orbit.
The filter suite is tested exhaustively under all `G_n` transforms for `n <= 2`
and on synthetic positive controls.

The filters are deliberately conservative; many infeasible classes are not
caught by them and stay `NOT_FOUND`. In particular, a *label-sensitive*
corner/wall assignment is **not** a valid filter: the assignment that looks
impossible in one feature frame is realized in the reflected frame (Section
7.2). The two weight-2 classes converted by the symmetry repair are exactly
this case.

## 6. Solver

`realize_topology(Sigma, config)` uses a fixed-`L` Levenberg-Marquardt
minimizer over `3n` pose variables plus one parameter `tau in [0.05, 0.95]`
for every CS contact. Residuals (all soft inputs to the optimizer):

- CC / CS: 2 point-coincidence residuals each;
- SS: 2 collinearity residuals (parallel directions and common line) plus a
  hinge keeping the common overlap within `1 - 5e-6`;
- wall-side: 2 signed wall distances (no end-margin hinge: side contacts may
  legitimately span wall endpoint to wall endpoint in tight packings);
- wall-corner: 1 signed distance plus 2 end-margin hinges (`1e-3`) keeping the
  corner off the wall ends;
- containment: 16 hinge residuals per square;
- non-overlap: 4 residuals per pair, where only the largest separating-axis
  gap carries a penalty (`max(0, -gap)`). Penalizing every axis separately is
  wrong: two squares that touch along one axis are disjoint even though other
  axis projections overlap, and the per-axis version exerts a fictitious
  repulsion that prevented tight packings (the 2x2 grid) from converging;
- stray pressures: 32 residuals per square (`0.25 * max(0, 2e-3 - d)`) push
  features that are not required contacts off wall lines, so accidental extra
  wall contacts are avoided.

Starts are deterministic (splitmix64 seeded from the contact keys): five
families — required-driven construction, axis-aligned random, diagonal,
lattice/grid, free random — with 32 starts per container rung. The optimizer
searches one *standard-frame* representative at a time; `realize_topology`
drives it over the `2^n` gauge branches of Section 7.3 and transports the
witness back with `psi_g`. The container
ladder is `{1, 2, 2.2, 2.5, 3, 4}` followed by an 8-step bisection inside the
bracket of the last failed and first successful rung. The default budget is
400 solves per class; the budget is a deterministic solve count, not wall
clock.

Acceptance is never decided by residuals: a candidate is handed to the
verifier when its contact residual is at most `1e-6`. That gate is only a
runtime filter — some gated candidates still fail the `1e-7` extraction test —
and the verifier alone decides. A class is `VERIFIED_FEASIBLE` only if a
verified exact witness exists. Otherwise it is `NOT_FOUND`, with the best
rejected candidate kept for diagnostics.

## 7. Symmetry contract: from `H_n` to `G_n`

### 7.1 Audit: why `(x, y, theta)` cannot carry an independent local reflection

Four objects have to be kept apart.

**A. Physical square.** Square `i` occupies the point set
`Q_i = C_i + R(theta_i) [-1/2, 1/2]^2`. A square is achiral: every reflection
of `Q_i` is another square. All contact predicates (coincidence, distance,
collinearity, containment, separation) are statements about occupied point
sets and are invariant under rigid motions of the plane.

**B. Feature-label frame.** The extractor assigns corner `c` the point
`C_i + F_i u_c`, where `u_c` has body angle `135 - 90c` and `F_i` is an
orthogonal 2x2 matrix. The canonical pose stores `F_i = R(theta_i)`, whose
determinant is `+1`. This frame is a *convention*: it decides which physical
corner is called 0, 1, 2, 3. It is not a physical object.

**C. Container isometry.** The container D4 element `(k, b)` acts by
`Q_g = R(-90k) M_y^b`, with `M_y: (x, y) -> (L - x, y)`. This is a rigid
motion of `[0, L]^2` and realizes the production wall map
`w -> (4 - w) mod 4` then `+ k`.

**D. Local frame reflection.** The engine's local reflection (rotation 0,
reflected) maps ring labels by `r -> (8 - r) mod 8`; on corners this is
`c -> -c (mod 4)`, so corners 0 and 2 are fixed and corners 1 and 3 swap. Its
body-direction map is a reflection `L = R(90) M_y` acting on the feature
frame. It changes `det(F_i)`.

For a mixed-parity group element, the local reflection parity differs from the
container parity. Starting from `F_i = R(theta_i)`, the new frame required by
the label action is `Q_g F_i L_i^{-1}`, whose determinant is

```text
det(Q_g) det(F_i) det(L_i)^{-1} = (-1)^b * (+1) * (-1)^{r_i} = (-1)^(b + r_i).
```

When the parities differ this is `-1`, and no rotation `R(theta')` has
determinant `-1`. This is the precise reason for the old `H_n` restriction:
the scene action existed only on

```text
H_n = { g in G_n : local[i].reflected == container.reflected for all i },
```

where every determinant is `+1`. It was a representation/gauge limitation, not
a property of the geometry: a physical square does not know which way its
labels were reflected.

### 7.2 The missing construction: per-square feature-frame parity

Extend the pose with a boolean `frame_reflected` and set

```text
F_i = R(theta_i) M^{b_i},    M: (x, y) -> (-y, -x),
```

where `M` is the body reflection with ring map `r -> 8 - r` (it fixes corners
0 and 2 and swaps 1 and 3). The occupied set is unchanged:

```text
F_i {u_c} = R(theta_i) M^{b_i} {u_c} = R(theta_i) {u_c},
```

because `{u_c}` is invariant under `M`. Only the labelling changes; this is a
gauge bit, not a mirror-image square.

For every `g in G_n` with container `(k, b)` and local elements
`(k_i, r_i)`, define

```text
Q_g       = R(-90k) M_y^b                      (container isometry)
L_i       = R(-90 k_i)                if r_i = 0
L_i       = R(90 - 90 k_i) M_y        if r_i = 1
F'_sigma(i) = Q_g F_i L_i^{-1}
C'_sigma(i) = Cc + Q_g (C_i - Cc),             Cc = (L/2, L/2)
theta'    = atan2(F'.e1_y, F'.e1_x) + (det(F') < 0 ? 90 : 0)
b'        = det(F') < 0
new_pose[sigma(i)] = (C'_sigma(i), theta', b')
```

Then

```text
extraction(psi_g(P)) = g . extraction(P)
```

for both the exact and the weak stratum, and for every `g in G_n`.

*Proof sketch.* `L_i` sends body direction `u_r` to `u_{transform_ring(r, local_i)}`.
Therefore `F' u_{g(r)} = Q_g F_i u_r`: the physical feature that carried label
`r` is moved by `Q_g` and now carries label `g(r)`. Every contact predicate is
a distance, collinearity, segment-parameter or containment statement about
these physical features, so it is preserved by the rigid motion and the label
map. The absorption triggers are the same predicates (a point lies on both
segments of a positive-overlap SS pair; both endpoints of a side lie on a
wall), so absorption commutes as well. `psi_{g^{-1}}` inverts the action, so
`psi` is a bijection on scenes and realizability is `G_n`-invariant.

Consequences:

- exact and weak realizability are well-defined properties of a full `G_n`
  orbit; Phase 1's quotient is **not** too coarse for geometry;
- the old failure was a coordinate/gauge representation problem, exactly the
  hypothesis stated in the audit brief;
- a label-sensitive corner/wall assignment that is impossible in the standard
  frame can be realized in the reflected frame. This actually happens in the
  `n = 2` corpus (Section 9.2).

### 7.3 Completeness of the `2^n` gauge branches

Let `tau_b` be the group element with container identity and
`tau_b.local[i] = (0, true)` exactly on the squares selected by the bit vector
`b`. Changing only the parity of square `i` relabels that square by `tau_i`, so
for any scene `P`

```text
extraction(P, b) = tau_b . extraction(P, 0).
```

Hence a labelling `Sigma` is realizable with some frame parities iff one of
the `2^n` standard-frame labellings `tau_b Sigma` is realizable with all
parities zero. The `tau_b` are coset representatives of `H_n`:

```text
|G_n| = n! 8^(n+1),   |H_n| = n! 8 4^n,   [G_n : H_n] = 2^n.
```

`realize_topology` enumerates the `2^n` branches in increasing mask order,
deduplicates branches that coincide as contact sets, stops at the first
verified exact witness, and transports the witness back with `psi_{tau_b}`.
The transported scene is re-verified against the input `Sigma`; branch `0`
reproduces the previous standard-frame solver exactly, so old feasible
witnesses remain valid. Weak witnesses are transported the same way and are
reported separately. The per-branch solve budget is `max_solves`; a class may
therefore spend up to `2^n * max_solves` deterministic solves.

### 7.4 What a corpus row means

For a canonical class `[Sigma]_G` with representative `Sigma`:

- `VERIFIED_FEASIBLE`: some gauge branch `tau_b Sigma` has a verified exact
  witness. By `G_n` invariance this is equivalent to every representative in
  the orbit being realizable; the reported witness is the `psi_{tau_b}` image
  for `Sigma` and verifies against `Sigma` directly.
- `PROVED_INFEASIBLE`: a `G_n`-invariant filter (Section 5) proves that no
  exact scene exists. Equivalently, every gauge branch is infeasible.
- `NOT_FOUND`: no branch produced a witness within budget and at least one
  branch remains unresolved. It is never a proof of impossibility.

The statuses are therefore statements about the same full canonical `G_n`
classes that Phase 1 counts.

### 7.5 Covariance evidence

The covariance identity is tested against the production
`relabel_square` / `relabel_container` / `permute_squares` transformations, on
both strata:

- `n = 1`: all 64 elements of `G_1` on wall-side, wall-corner and
  mixed-frame single-square scenes;
- `n = 2`: all 1024 elements of `G_2` on the corner-corner, corner-side,
  side-side, wall-side+SS multi-contact and mixed-frame scenes;
- `n = 3`: all 24,576 elements of `G_3` on a compact three-square L-scene with
  wall, SS and CC contacts.

Absorption is covered by the side-side and grid scenes, where endpoint corner
contacts are absorbed by positive-overlap side contacts, and by the multi-
contact wall scene, where wall-side events absorb endpoint corner-wall events.
The wall-only checks pin the container convention: container rotation `k` maps
wall `w` to `w + k`; the vertical mirror maps `w` to `4 - w`.

## 8. Fixtures

Positive fixtures (`scene_fixtures()`), all extracted exactly:

| name | n | exact contacts | weak contacts |
| --- | --- | --- | --- |
| isolated-1 | 1 | 0 | 0 |
| disjoint-2 | 2 | 0 | 0 |
| corner-corner-2 | 2 | 1 CC | 7 |
| corner-side-2 | 2 | 1 CS | 1 |
| side-side-2 | 2 | 1 SS (endpoint CCs absorbed) | 3 |
| wall-corner | 1 | 1 wall-corner | 1 |
| wall-side | 1 | 1 wall-side | 1 |
| grid-2x2 | 4 | 14 | 34 |
| grid-3x3 | 9 | 32 | 124 |
| grid-4x4 | 16 | 58 | 298 |

Every fixture is contained and interior-disjoint, and its exact extraction
equals the committed fixture topology (`sqtopology_realize fixtures` checks
all of them and exits non-zero on any mismatch).

Negative fixtures (`negative_fixtures()`):

| name | n | expected status | reason |
| --- | --- | --- | --- |
| N1-side-two-walls | 1 | `PROVED_INFEASIBLE` | R1 (one side on two walls) |
| N2-cc-opposite-walls | 2 | `PROVED_INFEASIBLE` | R2 (coincident corners on opposite walls) |
| N3-corner-opposite-sides | 2 | `PROVED_INFEASIBLE` | R3 (one corner on opposite sides) |
| N4-corner-opposite-walls | 1 | `NOT_FOUND` | containment forces centering, which adds side-wall contacts; no static filter proves it |

N4 is deliberately a negative fixture that the filters cannot prove; it pins
the rule that solver failure never becomes a proof.

## 9. The corpus (`n = 2` weights 1-3, `n = 3` weight 1)

`corpus_classes(n, w)` enumerates canonical classes exactly: start from the
empty class, expand the previous level by one event, and keep the orbit-minimal
event bitset under all `|G_n|` event permutations. The counts reproduce the
Burnside coefficients exactly:

| weight | classes | Burnside `a_w(2)` |
| --- | --- | --- |
| 1 | 5 | 5 |
| 2 | 87 | 87 |
| 3 | 1411 | 1411 |

(`n = 1`: weights 1/2/3 give 2/22/116 classes, consistent with
`G_1 = D4_ring x D4_wall`.)

Each class is then solved with the default budget (`32` starts, `400` solves,
8 bisection steps) and the seed derived from its contact keys, so the run is
reproducible.

### 9.1 Superseded standard-frame results

The first revision of this note reported the following corpus totals, computed
with the **standard-frame solver only**:

| weight | classes | feasible | not found | proved infeasible |
| --- | --- | --- | --- | --- |
| 1 | 5 | 5 | 0 | 0 |
| 2 | 87 | 23 | 58 | 6 |
| 3 | 1411 | 15 | 1240 | 156 |

These geometric status tables are **superseded**: they were not valid as
full-`G_n` class statements, because the solver only tried the canonical
standard-frame representative. The pure orbit counts (5/87/1411) are
unaffected and remain exact Burnside coefficients. The corrected results
follow.

### 9.2 Results under full-`G_n` semantics

Each class is solved with the default budget (`32` starts, `400` solves per
branch, 8 bisection steps) and a per-class seed derived from its contact keys;
the solver enumerates the `2^n` gauge branches (Section 7.3).

| weight | classes | feasible | not found | proved infeasible | exact witnesses | weak-only | solves | time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 5 | 0 | 0 | 5 | 0 | 921 | 0.68 s |
| 2 | 87 | 25 | 53 | 9 | 25 | 0 | 33,394 | 28.2 s |
| 3 | 1411 | 48 | 1128 | 235 | 48 | 0 | 750,464 | 790.5 s |

Host: 16 vCPU Linux guest, Release build, single-threaded. Runtime scales with
the solve count, not with enumeration (enumeration of 1411 classes takes
0.12 s). The weight-3 solve count and time are from the filtered run; the
symmetry-only run (before R4-R6) used 787,328 solves in 822.6 s.

Filter attribution order R1, R2, R3, R4, R5, R6 (the first rule that fires):
weight 3 = 45 / 89 / 22 / 38 / 25 / 16 (235 total); weight 2 = 2 / 3 / 1 /
1 / 1 / 1 (9 total). Counting overlaps, the 79 classes newly proved at weight
3 are hit by R4 = 38, R5 = 27 and R6 = 18.

### 9.3 Old -> new status transitions

The transition is reported in two stages so the effect of the symmetry repair
and of the new filters are not hidden.

**Stage 1: symmetry repair only (frame-parity branches, no R4-R6).**

| weight | old status | new feasible | new not found | new proved |
| --- | --- | --- | --- | --- |
| 1 | feasible (5) | 5 | 0 | 0 |
| 1 | not found (0) | 0 | 0 | 0 |
| 1 | proved (0) | 0 | 0 | 0 |
| 2 | feasible (23) | 23 | 0 | 0 |
| 2 | not found (58) | 2 | 56 | 0 |
| 2 | proved (6) | 0 | 0 | 6 |
| 3 | feasible (15) | 15 | 0 | 0 |
| 3 | not found (1240) | 33 | 1207 | 0 |
| 3 | proved (156) | 0 | 0 | 156 |

**Stage 2: adding R4-R6.**

| weight | stage-1 not found | -> feasible | -> not found | -> proved |
| --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 0 | 0 |
| 2 | 56 | 0 | 53 | 3 |
| 3 | 1207 | 0 | 1128 | 79 |

No old `VERIFIED_FEASIBLE` class became unfeasible, and **no old
`PROVED_INFEASIBLE` class became feasible**. The filters were sound before and
after the symmetry repair. The 35 classes that changed from `NOT_FOUND` to
`VERIFIED_FEASIBLE` (2 at weight 2, 33 at weight 3) are the correctness
finding of this audit: they are realizable only in a reflected feature frame.

### 9.4 The reflected-frame classes

The two weight-2 classes are exactly the "label-sensitive" cases that the
first campaign misclassified as impossible:

```text
3:0:0:0|w:1  +  3:0:0:1|w:0     corner 0 on the right wall, corner 1 on the top wall
3:0:1:0|w:1  +  3:0:1:1|w:0     side 0 on the right wall, side 1 on the top wall
```

Both are realized with `frame_reflected = true` on square 0 and a rotation
that makes the labelled interior point into the container. For example, the
first witness has `L = 2.00703125` and square 0 at
`(1.48526, 1.48526)`, `theta = 4.66784` with the reflected frame; its corner 0
lies on `x = L` and its corner 1 on `y = L`, with the other two corners
inside and no side-wall contacts. The standard-frame representative of the
same class cannot realize it, which is why the old run reported `NOT_FOUND`.

The general lesson is that a corner/wall assignment that forces the labelled
interior outside the container in one feature frame is **not** a proof of
infeasibility: the reflected frame relabels the square and can make the same
physical assignment valid. A rule of type C from the review brief therefore
must not be added as a filter.

At weight 3 the 33 newly feasible classes split into 20 branch 1 and 13
branch 2 witnesses (bit masks over two squares); with three squares, the
third square's parity is not needed for any of them. All 48 feasible weight-3
classes now verify against their canonical representatives.

The three weight-2 classes that R4-R6 convert from `NOT_FOUND` to
`PROVED_INFEASIBLE` are:

| rule | contacts |
| --- | --- |
| R4 | `3:0:0:0|w:0` + `3:0:1:0|w:0` |
| R5 | `3:0:0:0|w:0` + `3:0:0:1|w:0` |
| R6 | `3:0:0:0|w:0` + `3:0:0:2|w:0` |

### 9.5 Container sides of feasible classes

| weight | feasible | smallest `L` | largest `L` | notes |
| --- | --- | --- | --- | --- |
| 1 | 5 | 2.0023 | 2.0133 | all five single-contact classes, branch 0 |
| 2 | 25 | 2.0008 | 3.0859 | 23 of 25 below 2.03; two outliers at 2.10 and 3.09 |
| 3 | 48 | 2.0000 | 2.2012 | 44 below 2.02 |

The gap above 2 is **not** an area-filling argument: two unit squares have
total area 2 while a `2 x 2` container has area 4, so they do not fill the box.
What is true is the classical packing bound `s(2) = 2`: the container cannot be
smaller than 2 for two disjoint unit squares, and `L = 2` is the infimum of the
ladder. The solver finds sides slightly above 2 for many minimal-contact
classes because at `L = 2` the required contact set and the no-extra-contact
condition were not met by a verified witness; this campaign has **not** proved
a topology-specific minimum-`L` theorem. The reported value is a heuristic
infimum bracketed between `bisection_lower` and `container_side`, and it
depends on the start budget (Section 9.6).

A concrete tight example from weight 3 is exactly realizable at `L = 2`
(branch 0, so it was already feasible before the symmetry repair):

```text
contacts: 2:0:1:0|1:1:0    (SS, side 0 of square 0 and square 1)
          3:0:1:2|w:2      (side 2 of square 0 on wall 2)
          3:1:1:2|w:0      (side 2 of square 1 on wall 0)
witness:  L = 2
          square 0: (0.86247, 0.5),        theta = 2*pi
          square 1: (1.46453, 1.5),        theta = 3*pi
```

The two squares touch along the line `y = 1` with an overlap of about `0.40`
and rest on opposite walls; the exact contact set is exactly the three listed
events.

### 9.6 Determinism and robustness

- Two independent runs at weight 1 produce byte-identical JSON.
- The weight-2 status totals are stable under a double budget: no status
  changes, but 9 of the feasible classes report a different `L`, always
  smaller or within the bisection resolution (for example 3.0859 -> 2.1133 and
  2.1016 -> 2.0086). The statuses are budget-stable; the reported `L` is an
  upper bound from the heuristic search, not a certified infimum.
- The branch enumeration is deterministic: branch order and per-class seeds
  are fixed, and the transported witnesses re-verify against the canonical
  representatives.
- No weak-only certificate occurs in any of the three corpora. The weak
  stratum is exercised by the fixtures, not by the corpus.

### 9.7 `n = 3` weight 1

After the symmetry repair, the cheap generalization requested by the review
brief:

| class (canonical keys) | status | branch | `L` |
| --- | --- | --- | --- |
| `3:2:0:0|w:0` (corner-wall) | feasible | 0 | 2.1070 |
| `3:2:1:0|w:0` (side-wall) | feasible | 0 | 2.0617 |
| `0:1:0:0|2:0:0` (CC) | feasible | 0 | 2.0508 |
| `1:1:0:0|2:1:0` (CS) | feasible | 0 | 2.2035 |
| `2:1:1:0|2:1:0` (SS) | feasible | 0 | 2.1773 |

All five single-contact classes are exactly realizable, matching the `n = 2`
pattern. The extra free square does not introduce unavoidable extra contacts
at these witnesses; it does raise the reported container sides above the
`n = 2` values (2.05-2.20 instead of 2.00-2.01), because the third square has
to fit without creating new contacts. All witnesses use the standard frame;
the branch machinery is still exercised at `n = 3` because the solver
enumerates up to eight branches before settling on branch 0.

### 9.8 What remains in `NOT_FOUND`

`NOT_FOUND` is not evidence of impossibility. After the symmetry repair and
R4-R6, the remaining families include:

- `NOT_FOUND` classes whose reflected-frame branches were not reached within
  the per-branch budget (the solver tries all `2^n` branches but each branch is
  budget-limited);
- three-or-more-contact patterns whose infeasibility is macroscopic but not
  covered by R1-R6 (for example combinations of wall distances that force a
  diagonal longer than the container);
- classes that are genuinely realizable but missed by every start family.

The weight-3 corpus leaves 1128 of 1411 classes unresolved; the number of
solved statuses is 283 (48 feasible + 235 proved), up from 171 before the
symmetry repair. This is the honest state of the classifier.

## 10. Machine-readable schema

Schema `sqtopology.realizability.v2` (`sqtopology_realize corpus --json FILE`):

```json
{
  "schema": "sqtopology.realizability.v2",
  "tool": "sqtopology_realize",
  "n": 2, "weight": 1, "class_count": 5, "gauge_branches": 4,
  "group_size": 1024, "event_count": 128,
  "config": { "ladder": [1, 2, 2.2, 2.5, 3, 4], "starts_per_rung": 32,
              "lm_max_iterations": 120, "max_solves": 400,
              "minimize_container": true, "minimization_steps": 8,
              "seed": "11400714819323198485" },
  "status_counts": { "VERIFIED_FEASIBLE": 5, "NOT_FOUND": 0,
                     "PROVED_INFEASIBLE": 0 },
  "exact_witnesses": 5, "weak_only": 0, "total_solves": 921,
  "classes": [
    { "weight": 1, "events": [0], "contacts": ["0:0:0:0|1:0:0"],
      "status": "VERIFIED_FEASIBLE", "exact_witness": true,
      "weak_witness": false, "filter_reason": "",
      "frame_branch": 0, "weak_frame_branch": 0, "branches_tried": 1,
      "container_side": 2.0046875, "bisection_lower": 2.00390625, "solves": 191,
      "witness": { "container_side": 2.0046875,
                   "squares": [
                     { "x": 1.502344, "y": 1.502687, "theta": 6.379e-07,
                       "frame_reflected": false },
                     { "x": 0.502344, "y": 1.502687, "theta": -1.570797,
                       "frame_reflected": false } ] } }
  ]
}
```

`events` are the canonical orbit-minimal event IDs (`EventSetLayout`),
`contacts` are the normalized `contact_key` strings, `frame_branch` is the
gauge-branch bitmask used by the exact witness (bit `i` = reflected feature
frame of square `i`), `weak_frame_branch` is the same for a weak-only witness,
and `branches_tried` counts distinct branches actually solved. `witness` /
`weak_scene` are present only when the corresponding flag is set. Every scene
square carries `frame_reflected`; older v1 reports lacked both the field and
the branch accounting and are superseded (Section 9).

Fixture and negative reports keep
`sqtopology.realizability-fixtures.v1` and
`sqtopology.realizability-negatives.v1`.

`tests/data/realizability-n2-w1.json` is a committed weight-1 record. The test
suite pins its schema, class accounting, status distribution, branch metadata
and that all five witnesses use branch 0; floating-point digits are not pinned
because they depend on the host's math library.

## 11. Reproducing

```bash
cmake -S packing/sqtopology -B packing/sqtopology/build -DCMAKE_BUILD_TYPE=Release
cmake --build packing/sqtopology/build -j
ctest --test-dir packing/sqtopology/build          # 10 targets; realize unit tests ~9 s,
                                                   # plus the n=12 and corpus targets
./packing/sqtopology/build/sqtopology_realize fixtures
./packing/sqtopology/build/sqtopology_realize negative
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 1
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 2 --json w2.json
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 3 --json w3.json
./packing/sqtopology/build/sqtopology_realize corpus --n 3 --weight 1 --json n3w1.json
```

`sqtopology_realize_tests` runs in about 9 s (it includes all 24,576 elements
of `G_3` on a compact scene). `sqtopology_realize_corpus_w2` is the dedicated
full weight-2 CTest target (~30 s). The weight-3 run is not part of the
default suite (~13 min); the `n = 3` weight-1 run takes about 2 s.

## 12. Limitations

- `NOT_FOUND` means the per-branch budget found no witness; it is never
  reported as impossibility. The weight-3 corpus leaves 1128 of 1411 classes
  unresolved.
- The filters R1-R6 are sound but incomplete; no completeness claim is made.
  In particular, distance/containment rules that depend on `L` are not
  implemented, and the tolerance-scale status of some local arguments is
  delicate: a rule such as "one corner on two adjacent walls is impossible"
  is exact in the continuum picture but is not obviously sound for the
  `1e-7` extraction tolerance, so it is deliberately not a filter.
- Gauge branches multiply the solve budget by up to `2^n`. A class can be
  `NOT_FOUND` because the successful branch was not reached within its
  400-solve budget, even though another branch is easy.
- `L` minimization is a deterministic heuristic bisection between a failed and
  a successful rung, and the returned witness is re-verified, but the reported
  infimum is not certified: feasibility may be non-monotone in `L`, and the
  bracket is only sampled at 8 points. It is also branch- and
  budget-dependent; no topology-specific minimum-`L` theorem is claimed.
- Local minima are real: the solver's ability to find a witness depends on the
  start families (the lattice family was added after the 2x2 grid topology
  exposed a tight-packing failure). Doubling the budget at weight 2 changed no
  status, but this is evidence of stability, not completeness.
- The corpus is `n = 2` for weights 2 and 3; `n = 3` is covered at weight 1
  only. Higher weights need a different dispatch strategy for the per-class
  solver (see Section 13).
- The weak stratum is a relaxed containment relation, not a certified
  topological closure of the exact stratum.
- The line-4 fixture (a 1x4 strip) is still not realizable as an exact scene
  in a square container: each square would need side 0 on wall 0 and side 2 on
  wall 2 simultaneously, forcing `L = 1` for a chain of length 4. This is
  recorded as a candidate finding, not used as a test.
- The `psi_g` covariance is machine-checked for all `G_1`, `G_2` and `G_3`
  elements on representative scenes, not symbolically for all `n`; the proof
  in Section 7.2 is the general argument.
- The frame parity is a gauge bit. It must not be read as a physical chirality
  of the square (squares are achiral); it only records how the semantic corner
  and side labels are attached to the physical square.

## 13. Recommended next direction

The symmetry contract is now sound: geometric realizability is a property of
the same canonical `G_n` classes that Phase 1 counts, and the corpus statuses
are full-class statements. The next decisions are therefore about coverage and
proof strength, not about correctness of the quotient.

- **A. `n = 3` corpus at weight 2 (recommended next measurement).** The
  weight-1 run is cheap (5 classes, ~2 s, all feasible, `L` in
  `[2.0508, 2.2035]`). Weight 2 has `a_2(3) = 119` Burnside classes and would
  test whether the `n = 2` picture (most single contacts feasible, most mixed
  sets infeasible, frame branches matter) persists with a third square. It
  also stresses the `2^3 = 8` branch enumeration.
- **B. More `G_n`-invariant filters.** The R4-R6 family converted 79 classes
  in the weight-3 corpus with three local arguments. Distance-based rules
  (a chain of wall contacts longer than the container diagonal, two contacts
  whose required distance exceeds `sqrt(2)` or the diagonal of the wall
  rectangle) are the natural continuation; they must be stated in physical,
  frame-gauge terms and checked against the extraction tolerance.
- **C. Solver and branch-budget hardening.** A class may be `NOT_FOUND`
  because the successful branch was not reached within the per-branch budget.
  Analytic Jacobians, branch-specific starts, and a shared budget scheduler
  would raise the solved fraction without changing the geometry.
- **D. Weak-stratum study.** No weak-only certificate occurs in the corpus, so
  the weak stratum is currently untested as a classification tool. A targeted
  study of nearly-touching families (zero-overlap SS, endpoint CS) would
  decide whether it adds information or should be retired from the status
  story.
- **E. Freeze and publish.** The geometry, verifier, symmetry contract and
  corrected corpus are a coherent Phase-2 reference. This is the lowest-effort
  option and would leave the open questions explicitly labelled.

**Recommendation: A, with B as the parallel proof lane.** The symmetry repair
changed 35 corpus classes from `NOT_FOUND` to feasible and the absorption
filters proved 79 more; the natural next test is whether the three-square
corpus reproduces the same structural picture. B is the cheapest way to keep
raising the solved fraction while A runs.
