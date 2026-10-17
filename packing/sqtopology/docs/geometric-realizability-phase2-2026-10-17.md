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

Unit squares are posed by center `(x_i, y_i)` and orientation `theta_i`
(radians, counterclockwise). In the body frame

- corner `c` sits at angle `135 - 90c` degrees at distance `sqrt(2)/2`;
- side `s` is the segment from corner `s` to corner `s+1`, so side 0 is the
  top edge, 1 right, 2 bottom, 3 left;
- `ring r = 2*index + (side ? 1 : 0)`, matching `feature_ring_index`.

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

The filters are deliberately conservative; many infeasible classes are not
caught by them and stay `NOT_FOUND`.

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
lattice/grid, free random — with 32 starts per container rung. The container
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

## 7. Scene action `psi_g`

The event action of a group element is a label relabeling: square features use
the local D4 element, wall labels use the container element. A *geometric*
scene action exists only on the subgroup where every local element has the
same reflection parity as the container element:

```text
H_n = { g in G_n : local[i].reflected == container.reflected for all i },
index [G_n : H_n] = 2^n.
```

For `g in H_n` with container rotation `k`, container reflection `b`, and
local rotation `k_tau(i)`, the action on a scene is

```text
C'_i = R(-90k) ( M_b (C_i - Cc) ) + Cc,      Cc = (L/2, L/2)
theta'_i = theta_i + 90 (k_tau(i) - k)                if b = 0
theta'_i = -theta_i + 90 (k_tau(i) - k) - 90          if b = 1
new_pose[sigma(i)] = pose'_i
```

where `M_b` is the vertical mirror `x -> L - x`. Elements outside `H_n` throw
`std::invalid_argument`: no standard-labeled scene can carry a mixed-parity
feature relabeling.

Validation against the production `relabel_square` / `relabel_container` /
`permute_squares` transformations (tests in `tests/test_realize.cpp`):

- `n = 2`, corner-corner scene: all 256 elements of `H_2`
  (`extraction(psi_g(P)) == g . extraction(P)`), 768 mixed-parity elements
  rejected;
- `n = 2`, side-side scene (positive-overlap SS with absorbed endpoint CCs):
  all 256 elements of `H_2`;
- `n = 3`, three-square L-scene with wall contacts: all 3072 elements of
  `H_3`.

The wall-only checks pin the container convention: a pure container rotation
by `k` quarters maps wall `w` to `w + k`, and the vertical mirror maps wall
`w` to `4 - w`; the corresponding corner map is `c -> 1 - c` (mod 4).

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

## 9. The `n = 2` corpus

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

### 9.1 Results

| weight | classes | feasible | not found | proved infeasible | exact witnesses | weak-only | solves | time |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 5 | 0 | 0 | 5 | 0 | 921 | 0.54 s |
| 2 | 87 | 23 | 58 | 6 | 23 | 0 | 15,045 | 11.1 s |
| 3 | 1411 | 15 | 1240 | 156 | 15 | 0 | 240,654 | 226.5 s |

Host: 16 vCPU Linux guest, Release build, single-threaded. Runtime scales with
the solve count, not with enumeration (enumeration of 1411 classes takes
0.12 s).

Filter breakdown at weight 3: R1 = 45, R2 = 89, R3 = 22 (156 total); at
weight 2: R1 = 2, R2 = 3, R3 = 1 (6 total).

### 9.2 Container sides of feasible classes

| weight | feasible | smallest `L` | largest `L` | notes |
| --- | --- | --- | --- | --- |
| 1 | 5 | 2.0023 | 2.0133 | all five single-contact classes |
| 2 | 23 | 2.0008 | 3.0859 | 21 of 23 below 2.03; two outliers at 2.10 and 3.09 |
| 3 | 15 | 2.0000 | 2.2012 | 14 below 2.02 |

The gap above 2 is not numerical noise: the two-square minimum-`L` problem has
infimum 2, but at `L = 2` two unit squares fill the container exactly, so any
placement that uses the whole side length forces extra wall contacts. The
bisection therefore converges to a slightly larger `L` where the required
contact set is exact and no extra contact appears. The reported value is a heuristic
infimum bracketed between `bisection_lower` and `container_side`; it is not a
proof that no witness exists inside the bracket.

A concrete tight example from weight 3 is exactly realizable at `L = 2`:

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

### 9.3 Reading the `NOT_FOUND` set

`NOT_FOUND` is not evidence of impossibility, but several families in the
corpus *are* infeasible by local reasoning that the current filters do not
implement. Three examples:

- a corner that is an endpoint of a side required on a wall cannot also carry
  a required corner-only wall contact on the same wall: the wall-side
  absorption removes it (e.g. `3:0:0:0|w:0` + `3:0:1:0|w:0`);
- two corners of one square on the same wall force the whole side onto the
  wall, again by absorption;
- label-sensitive corner/wall assignments: corner 0 on the right wall and
  corner 1 on the top wall is impossible for the standard labeling, because
  the interior side of the labeled side would fall outside the container.

These are the natural home of a future `R4`/`R5` filter family (Section 11).

### 9.4 Determinism and robustness

- Two independent runs at weight 1 produce byte-identical JSON.
- Doubling the weight-2 budget (`--starts 64 --max-solves 1500`) changes no
  status (still 23/58/6) and costs 29,190 solves instead of 15,045, but 9 of
  the 23 feasible classes report a different `L`, always smaller or within the
  bisection resolution: for example 3.0859 -> 2.1133 and 2.1016 -> 2.0086.
  The statuses are budget-stable; the reported `L` is an upper bound from the
  heuristic search, not a certified infimum.
- No weak-only certificate occurs in any of the three corpora. The weak
  stratum is exercised by the fixtures, not by the corpus.

## 10. Machine-readable schema

Schema `sqtopology.realizability.v1` (`sqtopology_realize corpus --json FILE`):

```json
{
  "schema": "sqtopology.realizability.v1",
  "tool": "sqtopology_realize",
  "n": 2, "weight": 1, "class_count": 5,
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
      "container_side": 2.0046875, "bisection_lower": 2.00390625, "solves": 191,
      "witness": { "container_side": 2.0046875,
                   "squares": [
                     { "x": 1.502344, "y": 1.502687, "theta": 6.379e-07 },
                     { "x": 0.502344, "y": 1.502687, "theta": -1.570797 } ] } }
  ]
}
```

`events` are the canonical orbit-minimal event IDs (`EventSetLayout`),
`contacts` are the normalized `contact_key` strings, and `witness` /
`weak_scene` are present only when the corresponding flag is set.
Fixture and negative reports use
`sqtopology.realizability-fixtures.v1` and
`sqtopology.realizability-negatives.v1`.

`tests/data/realizability-n2-w1.json` is a committed weight-1 record. The test
suite pins its schema, class accounting and status distribution; floating
point digits are not pinned because they depend on the host's math library.

## 11. Reproducing

```bash
cmake -S packing/sqtopology -B packing/sqtopology/build -DCMAKE_BUILD_TYPE=Release
cmake --build packing/sqtopology/build -j
ctest --test-dir packing/sqtopology/build          # 10 targets; unit tests ~2.5 s,
                                                   # plus the n=12 and corpus targets
./packing/sqtopology/build/sqtopology_realize fixtures
./packing/sqtopology/build/sqtopology_realize negative
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 1
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 2 --json w2.json
./packing/sqtopology/build/sqtopology_realize corpus --n 2 --weight 3 --json w3.json
```

`sqtopology_realize_tests` runs in about 2.4 s; `sqtopology_realize_corpus_w2`
is the dedicated full weight-2 CTest target (~11 s). The weight-3 run is not
part of the default suite (~4 min).

## 12. Limitations

- `NOT_FOUND` means the fixed budget found no witness; it is never reported as
  impossibility. The weight-3 corpus leaves 1240 of 1411 classes unresolved.
- The filters R1–R3 are sound but incomplete; no completeness claim is made.
- `L` minimization is a deterministic heuristic bisection between a failed and
  a successful rung, and the returned witness is re-verified, but the reported
  infimum is not certified: feasibility may be non-monotone in `L`, and the
  bracket is only sampled at 8 points.
- Local minima are real: the solver's ability to find a witness depends on the
  start families (the lattice family was added after the 2x2 grid topology
  exposed a tight-packing failure). Doubling the budget at weight 2 changed no
  status, but this is evidence of stability, not completeness.
- The corpus is `n = 2` only. Weight 3 is the practical limit of the current
  per-class solver on this host; higher weights need a different dispatch
  strategy (see Section 13).
- The weak stratum is a relaxed containment relation, not a certified
  topological closure of the exact stratum.
- The line-4 fixture (a 1x4 strip) is still not realizable as an exact scene
  in a square container: each square would need side 0 on wall 0 and side 2 on
  wall 2 simultaneously, forcing `L = 1` for a chain of length 4. This is
  recorded as a candidate finding, not used as a test.
- The `psi_g` action is validated for `n <= 3` and for parity-consistent
  elements only; mixed-parity elements have no scene action by construction.

## 13. Recommended next direction

Five options, grounded in what the experiments actually showed:

- **A. Corpus widening at `n = 2`, all weights.** Weight 3 already runs in
  226 s, so weights 4–6 are feasible as one-off runs (the class counts grow as
  roughly `a_3 = 1411`, `a_4 = 26620`, ...). Cheap to execute, but the
  scientific return per class drops: most of the weight-3 mass is
  `NOT_FOUND`, and without new filters more classes do not become theorems.
- **B. Filter completeness (recommended).** The three local infeasibility
  arguments in Section 9.3, plus absorption-aware corner/wall conflicts,
  appear to cover large parts of the weight-3 `NOT_FOUND` set without any
  continuous search. This is the highest ratio of proved statements to compute
  in the entire campaign, and it composes with every later corpus run.
- **C. Solver hardening.** Improve the LM (analytic Jacobian, start
  diversification per contact pattern, a final polishing stage) and measure the
  conversion rate of a fixed `NOT_FOUND` sample. The weight-2 budget-doubling
  experiment suggests the current solver is stable, so the remaining gains are
  likely in the tight-packing and wall-alignment regimes rather than in more
  random starts.
- **D. `n = 3` corpus at low weight.** Enumerating `n = 3` weight-1 classes is
  cheap (288 events, `|G_3| = 24576`); solving them tests whether the `n = 2`
  picture (most single contacts feasible, most mixed sets infeasible) persists
  with a third square. It also exercises `psi_g` at the cube level.
- **E. Report layer only.** Freeze the current geometry + verifier as the
  Phase-2 reference, publish the corpus JSON, and defer further geometric work.
  This is the lowest-effort option and would leave the strong results
  (independent verification, `psi_g`, exact fixture agreement) documented and
  the open questions explicitly labelled.

**Recommendation: B, with D as the next measurement.** The largest concrete
gap exposed by these experiments is not solver throughput but the absence of
absorption-aware impossibility filters: 156 classes are proved by three rules,
and 1240 remain unresolved, many for reasons that are local and provable. B
turns those into `PROVED_INFEASIBLE` without touching the geometry, and D then
tests whether the resulting picture generalizes to `n = 3`. A is a run, not a
direction; C is worth doing only if B leaves a large residuum; E is the
fallback if Phase 2 is to be closed here.
