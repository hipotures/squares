# Bentz 2016 Replay and One-Spare Inventory Receipt (exp-216, exp-217)

Status: **replay holds at the printed constants; both one-spare cases leave structures
the paper’s toolkit does not close**. The 24-row replay of Theorem 11 passes 24 of 24 at
the printed constants and fails at the pre-`D-505` line, so the lane’s stop condition
was not triggered. The `n = 22` control reproduces Theorem 11 on all 73 blue structures,
and the `n = 33` zero-spare control of the side-6 model is forced by six distinct full
boxes on both wall lines.
At `n = 21` the inventory reports 3,461 kill orbits and 22,603 needs-geometry orbits
after the merge propagation the review of the model added; at `n = 32`, 3,997 kill
orbits and no needs-geometry.
Under `H-226`’s and `H-227`’s own registered kill criteria those are kills of the proof
strategy as stated.
**They produce no packing and say nothing about `s(21)` or `s(32)`.**

Session-144 BC-362, Fable mathematical lane, ported to `devtools/bentz2016/` under
`OR-1` and re-run here.
Every count below is this port’s own output.
The wall-line counts match the mathematical lane’s scratch record exactly, pair for
pair, and the propagated counts match the reviewer’s independent `merge_check.py` orbit
for orbit; both cross-checks are recorded under Agreement with the scratch record and
the review.

The transcription defect the replay turned up, `D-507`, is filed and fixed: the Theorem
9 budget line had lost its leading factor 2.

## Commands

From `packing/`, project Python 3.14.7, four-cpu box, 2026-09-20:

```bash
uv run --frozen --all-extras --group dev python -m devtools.bentz2016.replay_theorem11 \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/bentz2016-theorem11-replay.json

uv run --frozen --all-extras --group dev python -m devtools.bentz2016.one_spare_inventory \
  --check \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/one-spare-inventory-n22-check.json

uv run --frozen --all-extras --group dev python -m devtools.bentz2016.one_spare_inventory \
  --n 21 --json <inventory>

uv run --frozen --all-extras --group dev python -m devtools.bentz2016.one_spare_inventory \
  --n 32 \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/one-spare-inventory-n32.json
```

The negative control, which must exit non-zero:

```bash
uv run --frozen --all-extras --group dev python -m devtools.bentz2016.replay_theorem11 \
  --negative-control
```

Wall times: replay 15.1 s, `--check` 0.7 s, `--n 21` 39.3 s, `--n 32` 15.8 s. The
negative control is 15.0 s and exits 1. The `n = 21` run was 6.6 s before the merge
propagation, which runs on each of the 122,323 pairs the wall-line count leaves
non-forced.

**How `--n 21`’s output is stored.** The per-orbit inventory is 22.4 MB, over the 5 MB
this directory keeps inline, so it is split: `one-spare-inventory-n21.json` carries
every count, reason table and pattern table with an `orbit_records` stanza in place of
the records, and `one-spare-inventory-n21-orbits.json.gz` (0.33 MB) carries the 42,124
records themselves, each with both its class and its `class_before_propagation`. Nothing
is dropped. The other three files are written by the tool unaltered;
`one-spare-inventory-n32.json` is 3.3 MB and stays whole.

## Replay of Theorem 11

| Quantity | Value |
| --- | --- |
| Rows | 24 |
| Rows that hold | 24 |
| Finishing line `l` | `sqrt(2) - 1/2` = 0.914214 (`D-505`) |
| Lemma 5 on the wall and `l` (row 11) | `1` exactly |
| Chord infimum over `[0.4, 1] x {y}` (row 15) | `1` |
| Chord infimum over `[0.5, 1] x {y}` (row 16) | `2 sqrt(2) - 2` = 0.828427 |
| Case 1 sup, target `(3/2, 5/2)` (row 21) | 0.381333 < 1/2 |
| Case 2 sup, target `(c, 1)` at `y_1 = 0.9` (row 23) | 0.497328 < 1/2 |
| Case 2 sup at the PDF’s own end point (row 24) | 0.484441 < 1/2 |
| Configurations tiled exactly in row 3 | 619 |
| Negative control at `(sqrt(2)-1)/2` | 12 of 24 hold; rows 11 and 15 fail; exit 1 |

## The `n = 22` control (`--check`)

| Quantity | Value |
| --- | --- |
| Blue structures (one spare) | 73 (23 uncovered, 50 doubles) |
| Raw pairs | 73 |
| `D2` orbits | 22 |
| Forced | 73 raw, 22 orbits |
| By Theorem 8 | 4 |
| By five full boxes | 10 |
| By the paper’s finish | 59 |
| By the derived finish | 0 |
| By the merge propagation | 0 |
| Verdict | SELF-TEST PASSED |

Every structure is forced by the wall-line count alone, so the propagation never runs
here, and none of them is forced by the red-row finish this port derives rather than
reads off the paper.
That is what the control is for.

## The merge propagation

The review of the model found the lane’s immediate contradiction too weak: it fired only
on a trajectory through an uncovered point of the other colour, where Theorem 8,
convexity and the 1.01-diagonal bound give more.
Two swept segments that meet cannot lie in two boxes of a packing, so their boxes merge,
and a merged box is refused when it sweeps an uncovered point, when it holds a singly
covered point of one colour beside another point of that colour, or when the points it
must contain do not fit in a square of side 1.01. The pass runs by default on every
non-forced pair and can only add contradictions.
Both readings are reported everywhere, in the tool’s output and in the JSON
(`classes_raw_before_propagation`, `classes_orbits_before_propagation`,
`orbits_converted_by_propagation`).

It is carried at side 5 only; the `n = 32` side-6 model does not have it, so that case’s
counts below are wall-line counts alone.

## `n = 21` (red one spare, blue two spares)

Orbits, before and after the propagation:

| Class | Orbits before | Converted | Orbits after |
| --- | --- | --- | --- |
| forced | 11,483 | +4,577 | 16,060 |
| needs-geometry | 26,908 | −4,305 | 22,603 |
| kill | 3,733 | −272 | 3,461 |
| total | 42,124 |  | 42,124 |

Raw pairs, 167,915 in all (71 x 2,365):

| Class | Raw before | Raw after |
| --- | --- | --- |
| forced | 45,592 | 63,842 |
| needs-geometry | 107,479 | 90,309 |
| kill | 14,844 | 13,764 |

Forced by mechanism, raw, after the propagation:

| Mechanism | Raw pairs |
| --- | --- |
| Theorem 8, trajectory through an uncovered point | 28,936 |
| Theorem 8 propagated through merged boxes | 18,250 |
| Four full + partial, the paper’s finish (blue heights 1, 3, 5) | 14,367 |
| Four full + partial, the derived finish (red heights 2, 4) | 1,794 |
| Five full boxes on one line | 495 |

The largest surviving non-forced patterns, as `(left full, left partial), (right full,
right partial)`, by raw pairs:

| Pattern | Class | Raw pairs |
| --- | --- | --- |
| (2, 2), (2, 3) | needs-geometry | 16,468 |
| (2, 3), (2, 3) | needs-geometry | 16,150 |
| (3, 1), (3, 2) | needs-geometry | 15,956 |
| (3, 2), (3, 2) | needs-geometry | 15,653 |
| (2, 2), (2, 2) | kill | 6,276 |
| (3, 1), (3, 1) | kill | 4,990 |
| (2, 1), (2, 2) | kill | 1,056 |
| (4, 0), (4, 0) | kill | 402 |

The class is `D2`-invariant on every one of the 167,915 pairs (`invariance_ok: true`),
propagation included.

## `n = 32` (side 6, one spare in each colour)

| Quantity | Raw pairs | Orbits |
| --- | --- | --- |
| Total | 12,100 (110 x 110) | 4,146 |
| forced | 401 | 149 |
| needs-geometry | 0 | 0 |
| kill | 11,699 | 3,997 |

Forced by mechanism: 352 raw by Theorem 8, 49 raw by six distinct full boxes.

| Control or constant | Value |
| --- | --- |
| `n = 33`, zero spares | forced, six distinct full boxes on both lines |
| Theorem 9 budget over the side 6 | 0.0265033361 (`D-507`) |
| Numeric finish against the exact `m = 5` table | agrees to 1e-18 |
| Orbit count at the reported 25-digit decimal keys | 4,146 |
| Orbit count on exact integer keys | 3,089 |

Two things about that last pair, because the record states 4,146. A point key is a
decimal string, so the double mirror `x -> 6 - x -> x` re-rounds twice and does not
return the identical string at 5 of the 33 heights; the canonical form therefore splits
a few true orbits, and 4,146 is an upper bound on the number of orbits.
The tool prints both counts on every run.
No verdict depends on either: the classification never compares points across a mirror,
so all 12,100 raw pairs and every class above are independent of the key precision.

## What is not modelled

Two limits, both cutting against the kill class, stated rather than smoothed over:

- **The second point of a five-point row** can be moved within `[1.5, 1.6]` once that
  row’s end point sits at `x = 1`, which Lemma 1 allows.
  It is not modelled because it earns nothing: the segment it sweeps reaches neither
  wall line, so it adds no charge.
- **Every wall line means four lines, not two.** The two horizontal lines `y = c`,
  `y = 5 - c` cannot be charged by these row moves at all, because a column cannot move:
  displacing one point vertically stretches a triangle side to `sqrt(1 + delta^2)`. They
  are charged instead by the transposed configurations `R^T`, `B^T`, whose structures
  this toolkit cannot correlate with `(R, B)`. So a kill counted here is a kill on all
  four lines for the structure paired with its own transposed twin; for an arbitrary
  pair the transposed lines are an independent draw that doubles the chances and changes
  no per-structure verdict.

## Agreement with the scratch record and the review

The Session 144 mathematical lane’s `inventory_n21.json` holds one record per orbit.
Every record was expanded over its four `D2` images back to raw pairs -- 167,915 of
them, each orbit’s expansion matching its recorded size -- and each pair’s wall-line
class compared with this port’s. **Zero pairs differ.**

The reviewer’s independent `merge_check.py` converts 272 kill orbits and 4,305
needs-geometry orbits to forced.
This port converts **exactly those counts**, leaving 3,461 kill and 22,603
needs-geometry orbits, and it reaches them by a single interval sweep per row rather
than the reviewer’s fixed point over component pairs, which is the same transitive
closure at a fraction of the cost.

For `n = 32` the port reproduces the scratch file’s class counts, reason table and
orbit-size distribution exactly, including the 4,146 orbits.

`tests/test_bentz2016_tools.py` pins both sides: the red structure `U[(1/2,17/10)]`
against all 2,365 blue structures is 240 forced, 1,516 needs-geometry and 609 kill
before the propagation and 405, 1,381 and 579 after, and a slow-marked test pins the
whole inventory’s orbit counts on both sides.

## `D-507` and the source slip

Two findings against the archived transcription,
`packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md`:

- **Line 140, corrected.** The Theorem 9 budget lost its leading factor 2. PDF page 5
  prints `2(sqrt(2) - 1/2) + 2*0.8 + 3*(1/2)sqrt(3) > 6`, about 6.0265; the transcribed
  left side is about 5.1123, which does not exceed 6, so the inequality as transcribed
  is false. The factor 2 is the two wall gaps of the seven the sum counts.
  Filed as `D-507`, fixed in the file with an inline note.
- **Lines 191 to 194, not corrected.** The PDF itself names case 2’s end point
  `(0.5, sqrt(2) - 1/2)` where Figure 3 has `(0.5, 0.9)`. This is the source’s slip, not
  the transcription’s, so the text stands and only an inline note is added.
  Replay row 24 runs the step at the printed point: the region’s sup is 0.484441 there
  against 0.497328 at `y_1 = 0.9`, both under 1/2, so the step holds either way and no
  defect is filed against the source.

The archive annotation census for this file rises from seven to nine.

## Determination

What the tools decided, and nothing beyond it:

- Every quantitative step of Theorem 11 holds at the printed constants, and the table
  fails at the constant the transcription carried before `D-505`. The replay’s stop
  condition for the lane was not triggered.
- At `n = 22` and at `n = 33`, where the theorems are theorems, every structure is
  forced by the paper’s own mechanisms, with no help from the propagation.
- At `n = 21`, after the propagation, 3,461 of 42,124 orbits leave at most four counted
  boxes on both vertical wall lines with no forced partial-box point, which is `H-226`’s
  registered kill for the proof strategy as stated; 22,603 more need a geometric claim
  the paper does not make, stated per structure in each record’s reason.
- At `n = 32`, 3,997 of 4,146 orbits are the same kind of kill under `H-227`, and no
  structure reaches needs-geometry: with 0.0265 of vertical budget, one frozen row
  removes the shift of every interior six-point row on its side.
  The side-6 model does not carry the merge propagation, so that count is a wall-line
  count alone.
- A kill here names the case that would need new geometry.
  It exhibits no packing and bears on neither `s(21)` nor `s(32)`.

The Fable review verdict on the model, and the `H-226` and `H-227` verdicts it supports,
are recorded by the coordinator in `exp-216` and `exp-217`; this receipt records only
what the tools output.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
