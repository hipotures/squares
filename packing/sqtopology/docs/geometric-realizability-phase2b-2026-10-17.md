# Phase-2b: parallel corpus, n = 3 weight 2, and distance/orientation filters

Branch `work/topology-phase1-native`, parent commit `d1c8e89d` (the full-G_n
symmetry repair). The code for this note is commit `7dd3c19e`; the note itself
is the following commit on the same branch. This note records the second Phase-2 campaign: deterministic
16-worker corpus execution, the complete `n = 3`, weight-2 corpus, the
orientation/coincidence filter family R7-R13, and the exact frame-branch
reduction. All code, data and prose are in English. The branch is not merged to
`main`, and no unrelated working-tree state is touched.

The historical tables in `geometric-realizability-phase2-2026-10-17.md` remain
as the `d1c8e89d` record. The tables below are the later, parallel/proof-
filtered results; the configuration is stated with each table.

## 1. Parallel corpus execution

`run_corpus()` now uses a native bounded worker pool in `src/realize.cpp`:

- one work item per canonical class;
- a single atomic next-index queue (dynamic scheduling, not static
  partitioning);
- one preallocated result slot per class, written only by its worker, so report
  order is the class index order regardless of completion order;
- per-class solver seeds derived only from the sorted contact keys, never from
  a worker number or scheduling decision;
- per-class `realize_topology()` is single-threaded, so `--workers 16` means 16
  concurrent single-threaded solvers (no nested oversubscription);
- the first exception stops the queue, is stored under a mutex, and is
  rethrown after every worker has joined;
- worker count 0 is rejected; worker count 1 is the old sequential loop;
- the JSON `config.workers` field records the setting.

CLI: `sqtopology_realize corpus ... --workers N` (default 1; campaign runs use
16).

### 1.1 Determinism

`tests/test_realize.cpp` runs the full `n = 2` weight-1 corpus at 1 and 4
workers and compares class representatives, status, exact/weak flags, filter
reason, frame branch, branch count, solve count, container side and the full
witness JSON (including coordinates). They are identical. The research check
below repeats this at every worker count on `n = 2` weight 2 and requires
semantic identity after removing the `workers` field.

## 2. Scaling

Fixed workload: `n = 2`, weight 2, the final configuration (R1-R13 filters and
H_n branch reduction), 87 classes, 15,346 deterministic solves.

| workers | wall (s) | user (s) | speedup | efficiency | classes/s | solves/s |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 13.02 | 13.02 | 1.00x | 100% | 6.7 | 1,179 |
| 2 | 6.20 | 12.26 | 2.10x | 105% | 14.0 | 2,476 |
| 4 | 3.18 | 12.40 | 4.09x | 102% | 27.4 | 4,825 |
| 8 | 1.66 | 12.56 | 7.86x | 98% | 52.4 | 9,244 |
| 16 | 1.03 | 13.28 | 12.6x | 79% | 84.5 | 14,900 |

The 16-worker run uses about 12.9 cores on average; the short
one-second wall time makes thread start-up and the tail visible. On the much
larger weight-3 corpus the utilization is 15.5 cores (see Section 4).

Semantic identity: the `workers = 1, 2, 4, 8, 16` runs produce identical
class representatives, statuses, witnesses and branch choices after excluding
the recorded worker count. Per-class seeds are independent of the worker
count; only completion order changes.

Load balance: per-class solve counts have median 192 and maximum 384 at weight
2 (0 for classes resolved by a filter). The atomic queue absorbs the tail; the
longest class is a few tenths of a second, far below the total wall time.

## 3. Long-run control

The long research runs were started as background processes in the agent
runtime and the agent resumed on their completion notification; no sleep/poll
loop was used. Each job wrote its stdout/stderr to separate files and the exit
status/time was recorded:

```text
n=2 weight=3, workers=16, no new filters: 57.7 s, 750,464 solves
n=2 weight=3, workers=16, final:          21.9 s, 281,212 solves
n=3 weight=2, workers=16, final:           4.3 s,  25,324 solves
```

## 4. n = 2 baseline reruns and the parallel speedup

Historical (serial, `d1c8e89d`, no new filters): **790.5 s**, 750,464 solves,
48 feasible / 1128 not found / 235 proved.

Parallel-only (same semantic configuration, 16 workers): **57.7 s**, same
750,464 solves and the same 48/1128/235 statuses. Speedup **13.7x**,
15.6 cores utilized.

Final (16 workers, R7-R13, H_n branch reduction): **21.9 s**, 281,212 solves,
48 feasible / 816 not found / 547 proved. The additional speedup over the
parallel-only run comes from (a) 312 classes proved before any solve and (b)
the H_n branch-orbit reduction (Section 7). Parallelism itself changes no
status: the parallel-only and serial status vectors are identical.

## 5. New proof filters

All seven rules are stated on the normalized exact contact set, are invariant
under the full `G_n` action, and are tested on all `G_n` transforms for
`n <= 2` plus synthetic positive controls and 3,000 extracted random scenes.

Let `tau = 1e-7` be the contact tolerance and `iota = 1e-6` the strict CS
interior margin.

### R7: one corner on two distinct walls

**Statement.** If a corner feature is required on walls `w != w'`, no exact
scene exists.

**Proof.** Opposite walls are disjoint segments, so no point lies on both.
Adjacent walls meet at a container corner. Put that corner at `(L, L)`, with
walls `y = L` and `x = L`, and let the corner be `p = (L - a, L - b)` with
`0 <= a, b <= tau`. Containment puts the square's 90-degree interior wedge in
the container quadrant; parameterize the two incident unit edge directions as
`u = (-cos alpha, -sin alpha)`, `v = (sin alpha, -cos alpha)`,
`alpha in [0, pi/2]`. The far endpoint `p + v` must satisfy `x <= L`, which
gives `sin alpha <= a`. Then the side along `v` has both endpoints within
`tau` of `x = L`: `p` is at distance `a <= tau` and `p + v` at distance
`a - sin alpha <= a <= tau`. That side-wall event absorbs the corner-wall
contact on `x = L`, so the exact set cannot contain it. Contradiction.

**Tolerance.** The absorbed side's endpoints are bounded by the *same* `tau`;
no chain of tolerances is used.

### R8: corner and non-incident side of one square on one wall

**Statement.** If corner `c` and side `s` of the same square are required on
the same wall and `c` is not an endpoint of `s`, no exact scene exists.

**Proof.** The distance from a unit-square corner to the supporting line of a
non-incident side is exactly `1` (the corner lies on the lines of its two
incident sides and at distance 1 from the other two). Both features are within
`tau` of the wall line, so the corner-to-side-line distance is at most
`2 tau = 2e-7`, a contradiction.

**Tolerance.** Margin `1 - 2e-7`.

### R9: two distinct sides of one square on one wall

**Statement.** If two distinct sides of one square are required on the same
wall, no exact scene exists.

**Proof.** Adjacent sides are perpendicular (90 degrees) while both are within
`2 tau` of the wall direction; opposite sides are parallel at distance 1 while
both are within `tau` of the same wall line, so the distance between them is at
most `2 tau`. Both cases contradict a fixed 1 or 90-degree separation.

**Tolerance.** Margins `90 degrees` and `1 - 2e-7`.

### R10: orientation / parallelism cycle

**Statement.** Build a `Z_2` axis assignment for every side and wall: SS sides
are parallel, a wall-side side is parallel to its wall, adjacent sides of a
square are perpendicular, opposite sides are parallel, walls 0 and 2 are
parallel, 1 and 3 are parallel, and 0 is perpendicular to 1. If the required
relations are inconsistent, no exact scene exists.

**Proof.** Each relation is a consequence of a required contact (collinearity
for SS, both endpoints on the wall line for wall-side) or of the unit-square
geometry, with error `O(tau)` radians. A `Z_2` inconsistency forces two
required directions to differ by 90 degrees while every relation is within
`O(tau)` of its claim. Contradiction.

**Tolerance.** Angular margin 90 degrees versus `O(1e-7)` radians.

### R11: two corners of one square forced to coincide

**Statement.** If one CC class contains two distinct corners of the same
square, no exact scene exists.

**Proof.** CC contacts chain corner points within `k tau` (`k` at most the
number of corners). Two distinct corners of a unit square are at distance 1 or
`sqrt(2)`. For the supported square counts (`k <= 48`), `k tau <= 4.8e-6`,
far below 1.

### R12: two corners of one square on one side feature

**Statement.** If two corners of the same square are both CS-required on the
same side feature, no exact scene exists.

**Proof.** The open side parameters lie in `[iota, 1 - iota]`, so two points of
that side are at distance at most `1 - 2 iota = 1 - 2e-6`; each corner may be
up to `tau` off the side, so the corner-to-corner distance is below
`1 - 2e-6 + 2e-7 < 1`. The actual distance between two distinct corners is 1 or
`sqrt(2)`. Contradiction.

### R13: a CC class puts a non-endpoint corner of the side's square on that side

**Statement.** If a corner `p` is CS-required on side `s` of square `B`, and
the CC class of `p` contains a corner `c` of `B` that is not an endpoint of
`s`, no exact scene exists.

**Proof.** `c` coincides with `p` within `k tau`, and `p` is within `tau` of
side `s`, so `c` is within `(k+1) tau <= 5e-6` of the side line. But a
non-incident corner of a unit square is at distance exactly 1 from that line.
Contradiction.

### 5.1 Investigated but not adopted

**Forced wall events (R14/R15).** A CC-coincident corner of a corner that is on
a wall, or a CS point on a side that is on a wall, *suggests* a forced
wall-corner event. The forced point is only within `2 tau` of the wall, which
can exceed the `1e-7` corner-wall tolerance; the correct proof has to couple
the SAT (non-overlap) tolerance as well. Near-tolerance constructions show the
naive forced-event argument is not valid as stated, so these rules are **not**
implemented. They are a target for a future tolerance-aware analysis.

**Phase-2c update.** The CS case was later salvaged with a different, local
half-plane argument: a corner lying in the relative interior of a side that is
itself on a wall cannot avoid overlapping that side's square or leaving the
container, so the *whole pattern* is impossible (no forced-event bookkeeping
is needed). It is implemented as **R14** in Phase-2c. The CC case remains
deferred: both corner wedges face inward, and the SAT tolerance admits
`O(tau)`-penetration configurations, so the naive argument is still not
tolerance-safe.

**Label-sensitive impossibility (rule C of the previous review).** Not a valid
filter: the reflected feature frame realizes the assignment (the two weight-2
classes flipped by the symmetry repair).

## 6. n = 2 corrected totals

Baseline (parent `d1c8e89d`): weight 2 = 25/53/9; weight 3 = 48/1128/235.

Final (this note, workers=16, R1-R13, H_n branch reduction):

| weight | classes | feasible | not found | proved infeasible | resolved | resolved fraction |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 5 | 5 | 0 | 0 | 5 | 100% |
| 2 | 87 | 25 | 41 | 21 | 46 | 52.9% |
| 3 | 1411 | 48 | 816 | 547 | 595 | 42.2% |

**Superseded by Phase-2c** (filter R14 adds 1 proved class at weight 2 and 40
at weight 3, giving 25/40/22 and 48/776/587; no feasible class changed). The
table above is kept as the `a36aa2f3` record.

Transition from `d1c8e89d` (no feasible class changed; no old proof was
invalidated):

| weight | old status | -> feasible | -> not found | -> proved |
| --- | --- | --- | --- | --- |
| 2 | feasible 25 | 25 | 0 | 0 |
| 2 | not found 53 | 0 | 41 | 12 |
| 2 | proved 9 | 0 | 0 | 9 |
| 3 | feasible 48 | 48 | 0 | 0 |
| 3 | not found 1128 | 0 | 816 | 312 |
| 3 | proved 235 | 0 | 0 | 235 |

New proofs by first rule (the rule that fires first, in R1..R13 order):

| rule | weight 2 | weight 3 |
| --- | --- | --- |
| R1 | 0 | 0 |
| R2 | 0 | 0 |
| R3 | 0 | 0 |
| R4 | 0 | 0 |
| R5 | 0 | 0 |
| R6 | 0 | 0 |
| R7 | 1 | 18 |
| R8 | 1 | 30 |
| R9 | 2 | 36 |
| R10 | 3 | 78 |
| R11 | 2 | 54 |
| R12 | 2 | 53 |
| R13 | 1 | 43 |
| **new total** | **12** | **312** |

Raw overlaps exist (for example, R10 and R9 both match some two-side-on-one-
wall classes); the first-rule attribution above counts every class exactly
once. The new rules prove 142 square-square-only classes at weight 3 (out of 418
such classes; 14 more are proved by the older R3) and 7 at weight 2 (out of
36; 1 more by R3). No feasible class is rejected
by any filter: the 25/48 feasible vectors are unchanged, and 3,000 contact-rich
extracted scenes pass all filters.

## 7. Frame-branch orbit reduction

The solver used to deduplicate branches by equality of their contact sets. The
correct equivalence is smaller: if two gauge branches are in the same `H_n`
orbit, they are the same standard-frame problem, because standard-frame
realizability is `H_n`-invariant (`psi_h` maps standard frames to standard
frames for `h in H_n`). Solving one representative per `H_n` orbit is exact;
the witness is still transported to the canonical class with `psi_{tau_b}`.

Measured on all 119 `n = 3` weight-2 classes:

| measure | naive | distinct contact sets | `H_n` orbits |
| --- | --- | --- | --- |
| mean branches | 8 | 3.00 | **1.14** |
| median | 8 | 2 | **1** |
| max | 8 | 8 | **2** |
| total branch attempts | 952 | 357 | **136** |

The reduction is 85.7% versus the naive 8 and 62% versus equality dedup. It is
implemented in `canonical_branch_key()` with a per-`n` cache of the `H_n` event
permutations. Effects:

- `n = 3` weight 2: 38,764 -> 25,324 solves, 8.6 s -> 4.3 s;
- `n = 2` weight 2: solves 28,018 -> 15,346 (filters also change this number);
- `n = 2` weight 3: 563,456 -> 281,212 solves.

Statuses are unchanged; the reduction only removes redundant searches.

## 8. n = 3 weight-2 corpus

`a_2(3) = 119` canonical `G_3` classes; naive 8 branches, `H_3` orbit mean
1.14. Run with the final configuration and 16 workers:

| classes | feasible | not found | proved | resolved | resolved fraction | solves | wall |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 119 | 54 | 44 | 21 | 75 | 63.0% | 25,324 | 4.3 s |

Comparison with `n = 2` weight 2:

| quantity | n = 2 | n = 3 |
| --- | --- | --- |
| classes | 87 | 119 |
| feasible | 25 (28.7%) | 54 (45.4%) |
| proved | 21 (24.1%) | 21 (17.6%) |
| not found | 41 (47.1%) | 44 (37.0%) |
| square-square-only classes | 36 (0 feasible) | 62 (23 feasible) |
| wall-only classes | 31 (11 feasible) | 31 (11 feasible) |
| classes with 2 wall contacts | 31 | 31 (same status split) |

**Correction (Phase-2c).** The original interpretation above over-read the
aggregate comparison. Classify each class by its *support*, the number of
square IDs that appear in at least one contact event (a wall contact supports
its square; an untouched square does not):

| support | classes | feasible | not found | proved |
| --- | --- | --- | --- | --- |
| 1 | 22 | 2 | 7 | 13 |
| 2 | 65 | 23 | 34 | 8 |
| 3 | 32 | 29 | 3 | 0 |

The support-1 and support-2 status vectors are **identical** to the `n = 2`
weight-2 corpus (22 and 65 classes respectively). The `n = 3` corpus is
therefore the disjoint union of the embedded `n = 2` classes and **32
genuinely new support-3 classes** (29 feasible, 3 not found, 0 proved). In
particular, every one of the 23 feasible square-square-only classes has
support 3: the third square participates in the contact graph (typically as
the hub of a two-contact V), so these are new three-square structures, not
two-square configurations with a square moved away.

The identical wall-contact cross-tab is **evidence consistent with**
predominantly local wall obstructions, not a theorem; the support decomposition
is the precise statement. No new obstruction family appears at `n = 3` in the
support-3 set (0 proved there, 3 unresolved).

Feasible `n = 3` weight-2 classes use branch 0 in 52 cases and branch 4 in 2
cases (`frame_reflected` on square 2), so 3.7% require a non-standard frame
parity. For comparison, at `n = 2` weight 2 it is 2 of 25 (8%) and at
`n = 2` weight 3 it is 33 of 48 (68.75%). Reported container sides range from 2.0055 to 3.0273 (median 2.1387).

Contact-kind cross-tabs (status counts by multiset of contact kinds; 0 = CC,
1 = CS, 2 = SS, 3 = wall):

```text
feasible:  (3,3) 11, (1,3) 9, (2,3) 6, (0,3) 5, (1,1) 7,
           (1,2) 5, (0,1) 4, (2,2) 3, (0,0) 2, (0,2) 2
proved:    (3,3) 13, (1,1) 3, (0,0) 2, (2,2) 2, (0,1) 1
not found: (1,1) 9, (3,3) 7, (0,1) 6, (1,2) 6, (0,0) 4,
           (1,3) 3, (0,2) 3, (2,2) 3, (0,3) 2, (2,3) 1
```

## 9. Resolved vs unknown

| corpus | feasible | proved | not found | resolved | unknown |
| --- | --- | --- | --- | --- | --- |
| n = 2 w1 | 5 | 0 | 0 | 5/5 = 100% | 0% |
| n = 2 w2 | 25 | 21 | 41 | 46/87 = 52.9% | 47.1% |
| n = 2 w3 | 48 | 547 | 816 | 595/1411 = 42.2% | 57.8% |
| n = 3 w1 | 5 | 0 | 0 | 5/5 = 100% | 0% |
| n = 3 w2 | 54 | 21 | 44 | 75/119 = 63.0% | 37.0% |

The `n = 2` weight-3 resolved fraction rose from 20.1% (`d1c8e89d`) to 31.5%
(symmetry repair only) to 42.2% (new filters). All new resolutions are proofs
or verified witnesses; no numerical failure is reported as impossibility.

## 10. Limitations

- `NOT_FOUND` is still not impossibility. The `n = 2` weight-3 corpus leaves
  816 of 1411 classes unresolved; the `n = 3` weight-2 corpus leaves 44 of 119.
- The new filters are sound but incomplete. R14/R15 were investigated and
  deliberately not adopted because their forced-event step is not
  tolerance-safe without an additional SAT-coupling proof. (Phase-2c adopted
  the CS case as R14 via a local half-plane proof; the CC case stays open.)
- The `H_n` branch reduction is exact but requires the per-`n` permutation
  cache; for very large `n` the cache grows as `4^n * E(n)` and should be
  built lazily or streamed.
- The solver remains a deterministic local optimizer. A class can be
  `NOT_FOUND` because its successful branch was not reached within the
  per-branch budget, not because it is unrealizable.
- The corpus solver budget was not increased for the parallel comparison; the
  results are comparable to the historical run.
- The `n = 3` corpus is measured at weight 2 only. Weight 3 has
  `C(288, 3) = 3,939,936` labeled event subsets and `a_3(3) = 2,979` canonical
  `G_3` classes (not 1,411, which is `a_3(2)`); it is not attempted here.
- `L` values remain heuristic upper bounds from the ladder/bisection, not
  certified infima.

## 11. Tests and CI

New durable tests:

- worker determinism: 1 vs 4 workers, identical semantics and witness JSON;
  no duplicate/missing classes; zero workers rejected;
- R7-R13 synthetic negatives (rule fires, `PROVED_INFEASIBLE`, all `G_n`
  transforms for `n <= 2`) and positive controls (near-boundary topologies
  remain feasible);
- 3,000 generated contact-rich scenes: every extracted exact contact set
  passes every filter (a direct soundness check);
- `n = 3` weight-2 class count = 119 and `n = 3` weight-1 corpus solve;
- existing full-`G_n` exact/weak covariance, frame-gauge, branch-lifting and
  golden checks.

CI targets: the existing 10 CTest targets plus a bounded `n = 3` weight-2
corpus target (`--workers 4`). The full `n = 2` weight-3 research run remains
outside CI (21.9 s at 16 workers is acceptable for a research job, not for the
default suite).

## 12. Next recommendation

1. **Tolerance-aware forced-event filters (R14/R15).** The largest remaining
   proof lane is the forced wall-corner event under CC/CS. It needs a proof
   that couples the contact tolerance with the SAT/non-overlap tolerance;
   the current naive version is not sound. (Phase-2c: the CS case is settled
   as R14; the CC case is still open.)
2. **n = 3 weight 3.** `C(288, 3) = 3,939,936` labeled event subsets reduce
   to `a_3(3) = 2,979` canonical `G_3` classes; the parallel/`H_n` machinery
   makes it a feasible one-off run. It would test whether the `n = 2`
   weight-3 picture (wall-local impossibility plus square-square
   realizability) persists.
3. **Small solver study.** A fixed stratified sample of the remaining
   `n = 2` weight-3 `NOT_FOUND` classes, with contact-pattern-aware starts and
   a 4x bounded budget, would quantify how much of the unknown set is a solver
   artifact rather than a geometric obstruction.
4. **Scale the proof lane, not the budget.** Every new resolution in this
   campaign came from a proof or a verified witness; keep that ratio.
