# Exp-222 Re-pricing the n=17 Kleddamag Measure on Its Own Catalogue

Status: **bounded-negative, with a number.** Re-pricing this measure on this support at
this `(L, A)` is worth **at most `0.0252` of mass**, and by a stated sensitivity
heuristic at most about `+0.0034` in the bound — about `4.6232` against the artifact’s
`4.619791`, and very likely much less, because the floor that produces `0.0252` had not
converged when its deadline hit.
No bound moved, nothing was registered, and no certificate was produced.

The pre-declared discriminator in
[X-042](../../../../explorations/X-042-what-is-left-at-low-n.md)’s `A2` row — *the LP
value on 1,387 orbit variables against 16.99* — reads `16.776137532` and so “confirms”
on its face. **That reading is wrong, and the run says why**: the measure that value
belongs to charges `0.608365` at one of the 415 rows the separation probe looks at, and
would need mass `27.58` to be a certificate.
The discriminator was written for a number that the one-cell relaxation does not
produce.

This is the `A2` cell of `X-042`, hypothesis `H-233`.

## The three numbers, in order of what they are worth

| Number | Exact | Float | What it is |
| --- | --- | --- | --- |
| The artifact’s own normalised mass | `16998427356/1000020517` | `16.998078606` | an exactly feasible point of every program below |
| **A rigorous floor under any re-priced measure on this support** | `33945829752/2000000005` | **`16.972914834`** | 32 rounds of row generation on a 415-row sub-catalogue, dual-feasible in integers |
| The one-cell relaxation’s optimum | in `[6710455004/400000001, 4194034383/250000000]` | `[16.776137468, 16.776137532]` | a relaxation of a relaxation; a lower bound on the answer and not the answer |

The middle row is the lane’s result.
The difference between it and the first is
`50328578403114996/2000041039000102585 = 0.025163773`, and that is the whole of what a
re-pricing at fixed `(L, A)` on this support can still buy — **an upper bound on the
prize, not the prize.**

## The instrument

[`devtools/reprice_kleddamag_measure.py`](../../../../../devtools/reprice_kleddamag_measure.py)
reads the retained
[`global-certificate.json`](../../../../../resources/web/n17-kleddamag-certified-bound-2026-09-21/kleddamag-17-squares-certified-bound/global-certificate.json)
(`sha256 0288aaac…d69cec`) through `devtools.translate_kleddamag_certificate`’s own
`read_source` and `expand`, so the translation and its nine controls are neither re-done
nor re-decided here.
What is new is the **argmin**: the artifact’s checker reports each catalogue row’s least
charge and discards the cell it was attained at; this sweep keeps the cell, reads the
capture set off the rotated site frame there, and folds it onto the orbits that own the
sites.

| Piece | Value |
| --- | --- |
| Variables | 1,134 point-orbit weights + 253 two-of-three orbit weights = 1,387, non-negative |
| Constraint | one per catalogue row, at its minimising cell: `sum_o a_o w_o + sum_s b_s w_s >= 1` |
| `a_o` | how many of orbit `o`’s sites the row’s core captures at that centre |
| `b_s` | how many of orbit `s`’s triples have at least two of three captured |
| Objective | `sum_o |orbit_o| w_o + sum_s |triples_s| w_s`, the artifact’s own `budget_units` arithmetic |
| Program | 7,853 × 1,387 with 3,248,096 nonzeros |

The baseline is `budget_units / minimum_units` and not `budget_units`, because both
conditions are homogeneous in the weights: a measure of budget `B` whose least charge is
`G` rescales to one charging at least 1 everywhere at mass `B / G`. The artifact is
therefore an exactly feasible point of this program at `16.998078606`, which `K4`
re-derives rather than assumes.

## Controls

Every one exact; the tool refuses to emit if `K1`–`K5` fail.

| Control | What it decides | Result |
| --- | --- | --- |
| `K1` | this sweep’s per-row minimum against the artifact’s own retained Python replay | **all 7,853 rows, zero mismatches** |
| `K2` | this sweep’s per-row slab and cell counts against the same replay | **all 7,853 rows, zero mismatches** |
| `K3` | this sweep against `translate_kleddamag_certificate.restricted_row_minimum` on `(units, slabs, cells)` | 24 rows, exact |
| `K4` | the artifact’s own weights read back through the emitted matrix | objective `16998427356` = `budget_units`; **every one of 7,853 constraints returns its own swept minimum**; the least returns `1000020517` = `minimum_units` |
| `K5` | each minimising cell clipped against its own row’s parent-centre envelope | **0 rows detached** — every constraint sits at a legal centre; 4,761 of 7,853 cell *midpoints* lie outside it, which is why the clip exists |
| `K6` | the primal rationalised on the artifact’s `1e-9` grid and re-verified in integers | mass reported as `objective / least charge`, exact |
| `K7` | the dual rationalised the same way and scaled until `A^T y <= c` holds in integers | the exact floor, by weak duality |

`K1` and `K2` together are the control the lane stands on.
Agreeing with the artifact’s retained replay on the **cell counts** as well as the
minima, row by row over the whole catalogue, is what says this sweep partitions the
event grid the way the artifact’s does; `K4` then says the capture set read off the
argmin cell carries exactly the charge the sweep found.
A capture set off by one site fails `K4`.

## What was extracted

7,853 minimising cells, one per catalogue row, in 1,363.7 s of sweep on two contended
workers.
The catalogue was swept twice, before and after the centre defect below, and the
second pass reproduced `K1`–`K5` and both linear-program brackets to every printed
digit. Each carries the row’s `(t, B)`, its minimum in units, the centre, the
captured-site count and the folded orbit counts.

| Quantity | Value |
| --- | --- |
| Rows | 7,853 of 7,853 |
| Captured sites at the minimising cell | 267 (row 0) to 998 |
| Cell midpoints outside the strict parent-centre envelope | 4,761 |
| Cells meeting the envelope only in measure zero | **0** |
| Global minimum | `1000020517` units, row 6237 alone, core `38.065°` |

The high midpoint-outside count is not a defect and not a surprise: a row’s charge is
least where its core is pushed hardest against a wall, so the argmin lands on a boundary
cell, and the artifact’s own sweep window takes a boundary cell whole.
The charge is constant on the open cell, so clipping the cell to the envelope and taking
the intersection’s centroid moves the reported centre without moving the constraint.
Row 0 is axis-aligned, and its extracted centre comes out at `(0.4992654, 0.4992650)`
against that row’s own envelope corner `r = A/2 = 0.4992650` — the sharpest single check
that the geometry is being read right, and the cell’s own width is the whole difference.

### The slack distribution, recomputed

`X-042` reports this from one-off code and classes the reading `V0/C0`. It is the whole
argument for the lane, so the tool re-measures it from the swept minima that `K1` has
already matched to the artifact’s replay:

| Reading | This run | `X-042` |
| --- | --- | --- |
| rows within `1e-3` of the global minimum | 729 | 729 |
| within `5e-4` | 255 | 255 |
| within `1e-4` | 26 | 26 |
| within `1e-5` | 13 | 13 |
| attaining it | 1 (row 6237) | 1 |
| the plateau `1002070341` | 2,140 rows | 2,140 |
| the second plateau `1002070393` | 1,361 rows | 1,361 |
| rows at `minimum_units >= 1002040000` | 5,026 | 5,222 at slack `>= 2.04e-3` |

Every figure reproduces except the last, where the two readings use different cuts;
`5,026` is the count at the predicate this tool states.
The top three minima alone carry 48.5% of the catalogue.

## The linear program

| Program | Variables | Exact bracket | Support |
| --- | --- | --- | --- |
| All 1,387 orbits | 1,387 | `[16.776137468, 16.776137532]` | 93 orbits |
| Only the 1,105 orbits the artifact prices above zero | 1,105 | `[16.811458499, 16.811458570]` | 102 orbits |

The bracket is exact on both ends and `6.4e-8` wide: the upper end is the mass of an
exactly primal-feasible rational measure on the artifact’s own `1e-9` weight grid, the
lower end the mass of an exactly dual-feasible `y`, and no float lies between them.
Turning the 282 zero-weight orbits on is worth `0.035321` of the relaxation’s value.

**The support is 93 orbits of 1,387.** That is the tell.
A measure supported on 93 orbits cannot cover the continuum of 7,853 rows, and the next
section measures by how much it fails.

## What the value is, and is not

Three statements, in decreasing strength, and the order matters.

1. `floor <= OPT_cells <= mass`, both ends exact rationals, decided by `K6` and `K7`.
2. `OPT_cells <= OPT_catalogue`, because the constraint set is *one cell per row* and a
   re-priced measure has to hold on **every** cell of every row.
   Dropping constraints enlarges the feasible set, so the optimum can only fall.
   Therefore **`floor` is a rigorous lower bound on the mass of any re-priced measure on
   this support at this `(L, A)`, and `mass` bounds nothing at all.**
3. `OPT_catalogue < 17` is *necessary* for a re-priced certificate and not sufficient.
   The artifact’s own verifier also checks the row-wise core selection, the strict-core
   margins and the parent-envelope inclusion, none of which a change of weights touches
   but all of which a change of `A` would.

So **a value below `16.99` says only that the relaxation has room.
It does not say a certificate exists at `4.619791` with a smaller budget, and it must
not be read that way.** This is the single easiest thing in this lane to get wrong, and
the pre-declared `A2` discriminator gets it wrong: it reads a confirm off a number that
is a lower bound on the quantity it names.

## One round of separation

The measurement that says what the LP value is worth.
The program’s own weights go back into the artifact’s sweep and the minimum is retaken
over the **whole continuum** of 415 stratified rows — every nineteenth row plus the
last, the same sample `exp-221`’s `H-235` screen used.

| Quantity | Exact | Float |
| --- | --- | --- |
| budget | `16776137532` units | 16.776138 |
| least charge over the 415 rows | `152091139/250000000` at row 6042 | 0.608365 |
| mass this measure would need | `4194034383/152091139` | **27.576** |

By homogeneity that `27.576` is a **lower** bound on the re-priced measure’s real mass,
so one row of a 5% sample refutes the one-cell program’s answer as a certificate without
sweeping the other 7,438. The one-cell relaxation is not nearly tight, and its `16.776`
carries no information about what a certificate could cost.

## Row generation on a sub-catalogue

The tight measurement.
The same 415-row sample, but each row kept **whole**: solve, put the weights back,
re-sweep the continuum, add the cells the sweep found, repeat.
Every round’s dual floor is a valid floor under the whole catalogue’s optimum, because
the cells held are a subset of its constraints.

| Round | Cells held | Exact dual floor | Swept mass of that round’s measure | Binding row |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 830 | 16.638514 | 70.357 | 6517 |
| 4 | 2,490 | 16.833460 | 19.862 | 0 |
| 9 | 4,565 | 16.912780 | 18.368 | 6764 |
| 14 | 6,640 | 16.942843 | 17.765 | 6897 |
| 19 | 8,715 | 16.958131 | 17.421 | 6992 |
| 24 | 10,770 | 16.966280 | 17.271 | 5548 |
| 28 | 12,382 | 16.971195 | 17.112 | 7638 |
| 30 | 13,110 | 16.972514 | 17.100 | 6783 |
| **31** | **13,484** | **16.972914834** | 17.395 | 1995 |

Stopped at `deadline reached` after 799.9 s and 32 rounds, **not converged**: round 31
still added 374 cells.
The floor is monotone and its increments were still `4e-4` a round when the clock ran
out, so `16.972915` is a floor that had not finished rising.

Two things follow.

- **The prize is at most `0.025164` of mass.** Any re-priced measure on this support at
  this `(L, A)` has mass at least `16.972915`; the artifact already achieves
  `16.998079`. What is left between them is all there is, and the true figure is
  smaller.
- **No re-priced certificate was produced.** After 32 rounds the loop’s own measure
  still charges below what it needs: its swept mass over those 415 rows is `17.395`,
  above 17. Row generation on a sub-catalogue of 5% of the rows has not yet reached a
  measure that would pass on that 5%.

### What it is worth in the bound

Converting mass into bound needs the catalogue regenerated at a smaller `A`, which this
lane did not do. What can be said is a sensitivity estimate with its assumption named.
The core side tracks the parent side (`B/A = 0.99984` at the tightest row), and at fixed
site density a core’s charge scales with its captured area, so a relative fall `e` in
`A` costs about `2e` of relative charge and buys `e` of relative bound.
Then

```
bound gain ~ (L/A) * (17 - mass) / (2 * 17) = 0.135876 * (17 - mass).
```

| Case | Mass | Estimated bound |
| --- | --- | --- |
| The artifact’s own unspent surplus | `16.998079` | `+0.000261` → `4.620052` |
| Everything re-pricing could add, at the floor | `16.972915` | `+0.003419` more → `4.623471` |

So this whole avenue is worth **at most about `+0.0037`**, taking the bound from
`4.619791` to no more than about `4.6232`, and the floor was still climbing.
The estimate is a heuristic, not a bound: it assumes uniform site density and ignores
that shrinking `A` also *enlarges* the legal-centre domain, which makes covering harder.
Both errors point the same way — the real figure is smaller.

## H-239: the dual by angle

| Quantity | Value |
| --- | --- |
| Total dual mass | 16.776138 |
| Rows carrying it | 99 of 7,853 |
| Within `0.5°` of a folded Bidwell class | 4.125673 |
| **Share** | **24.6%** |
| By class: `0°` / `36.62°` / `39.80°` | 3.808160 / 0.033860 / 0.283653 |

**`24.6%` is below `50%`, so the `X-014` cap signature is not present at `4.6198`** on
this dual. What mass there is sits almost entirely at `0°` rather than at either tilt,
which is the same reading `X-042` takes from the tight row being `1.44°` and `1.74°` off
Bidwell’s two tilts.

This is the weakest measurement in the receipt and should be read as a first look only:
it is the dual of the *one-cell relaxation*, whose primal the separation probe has just
refuted, and 99 rows is a thin support to bin.

## A defect found and fixed inside the lane

The first extraction’s reported centres were wrong by a factor of `norm = q^2 + p^2`.
The frame map is `(dx, dy) -> scale * (C dx + S dy, -S dx + C dy)`, whose inverse
divides by `scale * (C^2 + S^2) = scale * norm^2`; the code divided by `scale * norm`.
It was caught by reading the emitted JSONL rather than by a check, which is the lesson:
row 6237’s centre came out at `-1.04e17` against a container of side `4.613`.

Nothing else was affected — the constraint matrix, every control and every LP value are
computed in the frame and never through that inverse — but the extraction was re-run
rather than patched in place, and the tool now refuses any centre outside the container.
The re-run is its own evidence for that claim: both passes give `K1` and `K2` on all
7,853 rows with zero mismatches, the same `4,761` midpoints outside the envelope, the
same `0` detached, and the identical bracket `[16.776137468, 16.776137532]`. All 7,853
retained centres now lie inside the container, `x` in `[0.499265, 2.306202]` and `y` in
`[0.499265, 3.095368]` against `L = 4.613`.

## Commands and wall times

All from `packing/`, all `uv run --frozen --all-extras --group dev python -m …`, all on
two workers of a four-core box shared with four other lanes; every wall is a contended
wall and none is a cost measurement.

| Wall | Command |
| --- | --- |
| 21.6 s | `devtools.reprice_kleddamag_measure --stride 100 --workers 2 --control-rows 6 --report …-calibration.json` |
| 9.3 s | `devtools.reprice_kleddamag_measure --stride 500 --workers 1 --control-rows 4 --skip-lp --report …-sweep-control.json` |
| 2,097.3 s | `devtools.reprice_kleddamag_measure --stride 1 --workers 2 --control-rows 24 --quiet --cells …-cells.jsonl --matrix …/exp-222-matrix.npz --report …-lp.json` |
| 810.4 s | `devtools.reprice_kleddamag_measure --from-matrix …/exp-222-matrix.npz --separation-rows 413 --rowgen-rows 413 --rowgen-rounds 40 --rowgen-deadline 780 --workers 2 --quiet --report …-solve.json` |
| 1,376.5 s | the third command again, after the centre fix; this is the retained run |

Of the 810.4 s, the LP took 3.4 s, the second LP 2.2 s, the separation probe 4.4 s and
row generation 799.9 s.

Emitted beside this receipt:

| File | What |
| --- | --- |
| `exp-222-n17-repricing-cells.jsonl` | 7,853 minimising cells: row, minimum, slabs, cells, `t`, `B`, exact centre, captured sites, envelope flags |
| `exp-222-n17-repricing-lp.json` | the sweep, `K1`–`K5`, the slack distribution, both linear programs, the `H-239` histogram |
| `exp-222-n17-repricing-solve.json` | the same read back from the matrix, plus `K7`, the separation probe and the 32-round row-generation log |
| `exp-222-n17-repricing-calibration.json`, `…-sweep-control.json` | the two staged controls, at stride 100 and 500 |

The constraint matrix itself (`exp-222-matrix.npz`, 828 KB, 3,248,096 nonzeros) is in
the session scratchpad rather than the record; `--stride 1` regenerates it, and
`--from-matrix` re-derives every number above from it.

## What this did not establish

- **No certificate, and no bound.** An LP value is not a certificate.
  Nothing here was registered, no rung was claimed, and `T-032` and the retained
  Kleddamag value are untouched.
- **The row-generation floor is not converged.** `16.972915` is valid as a floor and is
  not the sub-catalogue’s optimum; a longer run raises it and shrinks the `0.025164`.
  The obvious next slice is the same command with a larger `--rowgen-deadline`, and the
  obvious one after that is `--rowgen-rows 7853`, which at these rates is hours.
- **415 rows is 5.3% of the catalogue.** The row-generation floor is valid for the whole
  catalogue — a subset of constraints can only lower an optimum — but its *tightness* is
  a statement about those 415 rows and nothing more.
- **The sensitivity estimate is not a bound.** It assumes uniform site density and holds
  `A` and `B` in lockstep.
  It is stated to one significant figure for a reason.
- **Nothing about a different support or a different `A`.** This lane varies weights and
  nothing else. Whether a *new* site set or a smaller `A` reaches past `4.6198` is a
  different question and the one the negative here points at.
- **Nothing about the unrestricted language.** This runs restricted, on the artifact’s
  own rows, exactly as `exp-221`’s row 6512 witness says it must.
- **`H-239` is a first look, not a decision.** 99 dual rows from a refuted primal.
- **The receipt is not in the document map.** `docs/project/document-map.yaml` is
  outside this lane’s write scope; the entry is the coordinator’s.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
