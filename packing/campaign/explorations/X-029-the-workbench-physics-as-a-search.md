---
title: X-029 — the workbench's blind physics, measured as a search
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-029
  title: The Workbench's Blind Physics, Measured as a Search
  date: '2026-09-12'
  author: Claude Opus 5, unattended
  campaign: packing.squares
  brief: >-
    The workbench animates each step from one known-best packing to the next with a contact
    simulation. In blind mode the run starts from the previous record and is not given the
    destination poses. This exploration measured that run as a search: whether it ends on a
    packing, and how close the best of many seeded runs gets to the known-best side.
  sources:
  - packing/atlas/known-best/video/spikes/v2-transitions/assets/workbench.js
    - packages/workbench/tools/workbench_tools/benchmark.py
  - packing/campaign/results/annealing/summaries.json
  - docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md
  proposes: [H-207, H-208, H-209, H-210, H-211]
---
# X-029: The Workbench’s Blind Physics, Measured as a Search

**Rewritten 2026-09-14.** This report keeps only what survived checking.
Earlier versions reported numbers from runs whose arrangements were never checked to be
packings, and from inline analyses whose code was not kept.
That text is recoverable at commit `a40d272c`; none of it is repeated here.

## Summary

- **A blind run is not blind.** It starts from the known-best packing for the previous
  `n`, closes its walls onto the known-best side, places the new square with a
  coarse-grid proposal, and in the style measured here welds squares into blocks chosen
  by matching the two records.
  Only the destination poses are withheld.
  It is one point on a range of how much of the answer a search is given.
- **The runs did not end on packings.** None of the 123,190 blind runs whose rows
  survive ended without overlapping squares; the median deepest overlap was 0.083 of a
  unit side. A container side read from such an arrangement is a bounding box around
  overlaps, so every number taken that way has been discarded.
- **Repaired to a packing, a single run is worse than the trivial grid.** At every `n`
  and every shake level measured, the median run needs a larger container than
  `ceil(sqrt(n))`.
- **The best of many runs sometimes comes close and never reaches a record.** At shake
  level 6 the best of the first 1,000 seeds was 0.28% above `s(5)` and 0.42% above
  `s(10)`. At `n = 17` and `n = 29` no run in 5,000 beat the grid.
- **Difficulty does not follow the number of squares.** `n = 26` did better than
  `n = 11` and `n = 17`. What does decide it is not established.
- **The shake dial is a search parameter that the page sets for looks.** At levels 0 to
  4 no run in 3,000 beat the grid at `n = 5`, 10 or 11. At levels 6 to 10 the best run
  did, with one exception.
  The page shipped level 3 when these runs were measured; the owner’s defaults now ship
  9 on a 0–20 dial (#171).

## 1. What a Blind Run Is

The workbench draws the step from the packing of `n - 1` squares to the packing of `n`
by simulating it:

1. The squares start at the known-best poses for `n - 1`, centred in a container 12%
   larger than the known-best side for `n`.
2. The new square is dropped, upright, into the emptiest cell of a coarse grid.
3. Contact forces between squares, wall forces and a decaying shake act while the walls
   close onto the known-best side.
   The walls keep closing while the deepest overlap is at most 0.08 of a unit side, and
   they never go below the known-best side.
4. In the `bodies` style, which every run in this report used, squares are welded into
   rigid blocks in their starting arrangement.
   Which squares share a block comes from matching the record for `n - 1` against the
   record for `n`, so it is information about the destination.

The page has three ways to finish the step:

| mode | what the run is given about the destination |
| --- | --- |
| snap | the destination poses, and it ends on them by construction |
| free | the destination poses as a pull, without the snap |
| blind | no poses; still the known-best side, and in `bodies` style the matched blocks |

So “blind” is conditioned on a great deal: the previous record, the reference side, the
proposal and, in `bodies` style, which squares move together.
Any claim about it is a claim about improving a known packing toward a known side, not
about finding a packing from nothing.

## 2. One Trial Per `n`, Until Runs Were Seeded

Every generator on the page was seeded from `n` alone, so a given `n` and parameter set
had exactly one blind trial.
That is right for an animation, which must reproduce across builds, and it makes a
success rate meaningless.

`setSeed` folds a run seed into every generator.
Seed 0 reproduces the page exactly, so the existing checks pass unchanged.

## 3. The Runs Were Not Packings

The first two rounds of the benchmark scored the bounding box of each run’s final
arrangement and never checked that the squares were disjoint.
Some parameter cells reported a container below the known-best side, which no packing
can need. That was the signal that something was wrong, and it was missed.

The check that exposed it is a separating-axis test over the final poses, computed in
the harness rather than read from the simulation.
It reports the deepest overlap between any two squares.
The tolerance comes from a control: a snapped run ends on the record’s own poses, so
whatever it scores is float noise.

| mode | n = 5 | n = 11 | n = 17 |
| --- | ---: | ---: | ---: |
| snap | 5.5e-7 | 1.0e-6 | 7.3e-7 |
| free | 3.9e-5 | 4.5e-5 | 3.1e-2 |
| blind | 8.4e-2 | 3.5e-2 | 8.6e-2 |

Two orders of magnitude separate the control from the smallest real overlap, so the
harness uses 1e-5 of a unit side.
The snap and free rows came from a variant of the probe that was run once and not kept;
the committed harness runs blind only, so the control is a recorded observation rather
than a reproducible one.

Across the 123,190 runs of the later rounds, whose rows survive locally, no run ended
below 1e-5. The deepest overlap before repair ranged from 0.002 to 0.118 of a side, with
a median of 0.083.

The overlap is built into the blind schedule.
The walls close onto the known-best side while squares may overlap by up to 0.08, and
the observed overlaps sit at that tolerance.
Squares compressed inside a record-sized box can have a bounding box smaller than the
box, which is how a cell came to report a container below the known-best side.
The details are in
[exp-210](../series/series-000-smoke-and-calibration/experiments/exp-210-h210-blind-runs-are-not-packings.md).

**Everything measured before this check is void.** In `summaries.json` those cells are
the ones marked `resolved: false`: 243 cells across 49 run files.
No number from them appears in the record.

Since then the harness repairs every run before scoring it.
The repair moves squares apart along each overlapping pair’s minimum-penetration axis,
holding angles fixed, until no pair overlaps.
The score is the container that the repaired arrangement needs.

## 4. What a Repaired Run Is Worth

The score is `closed = (grid - side) / (grid - record)`, where `grid` is
`ceil(sqrt(n))`. One is the record, zero is the trivial grid, and a negative value is
worse than the grid.
Raw excess over the record cannot be compared across `n`, because the room between the
record and the grid ranges from 1.12% at `n = 29` to 10.82% at `n = 5`.

### Across `n`, at shake level 6

5,000 seeds per `n`, each run repaired and checked before scoring:

| n | gap to grid | median run | best of first 100 | best of first 1,000 | best of 5,000 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 5 | 10.82% | −0.074 | −0.015 | 0.974 | 0.977 |
| 10 | 7.90% | −0.099 | 0.874 | 0.947 | 0.974 |
| 11 | 3.17% | −0.107 | −0.035 | −0.012 | 0.476 |
| 17 | 6.94% | −0.104 | −0.062 | −0.062 | −0.061 |
| 26 | 6.74% | −0.101 | 0.120 | 0.212 | 0.230 |
| 29 | 1.12% | −0.857 | −0.370 | −0.193 | −0.110 |

What this shows:

- **One run is worse than doing nothing.** The median is below zero at every `n`.
- **A budget of runs is the method.** A run’s median wall time was 0.3 ms at `n = 5` and
  2.4 ms at `n = 29`, so the best of a thousand takes seconds.
  At `n = 5` the best of the first 1,000 is 0.28% above the record; at `n = 10` it is
  0.42%.
- **No run reached a record.** The closest is at `n = 5`: over 39,871 seeds the best is
  0.15% above `s(5)`.
- **Size does not order the results.** `n = 26` beats the grid in its first 100 seeds,
  while `n = 11` needed more than 1,000 and `n = 17` never did.
  `n = 11` and `n = 29` have the two smallest gaps, where `closed` is a harsh scale, but
  `n = 17`’s gap is ordinary.

### Across shake levels, at `n = 5`, 10 and 11

3,000 seeds per cell; each entry is the best of the first 1,000, then the median run:

| level | n = 5 | n = 10 | n = 11 |
| ---: | --- | --- | --- |
| 0 | −0.082 / −0.082 | −0.114 / −0.114 | −0.112 / −0.112 |
| 2 | −0.056 / −0.090 | −0.076 / −0.104 | −0.015 / −0.103 |
| 4 | −0.018 / −0.083 | −0.070 / −0.103 | −0.021 / −0.103 |
| 6 | 0.974 / −0.074 | 0.947 / −0.099 | −0.012 / −0.106 |
| 8 | 0.958 / −0.076 | 0.977 / −0.098 | 0.564 / −0.115 |
| 10 | 0.864 / −0.095 | 0.879 / −0.098 | 0.325 / −0.249 |

What this shows:

- **At level 0 every seed gives the same answer**, because the shake is the only
  randomness in the run.
- **At levels 0 to 4 no run beat the grid** in 3,000 seeds at any of the three `n`.
- **At levels 6 to 10 the best run beat it**, except `n = 11` at level 6. At level 8,
  `n = 11` reached 0.564 in the first 1,000 seeds and 0.616 over 16,319.
- **The median barely moves with the level**, except `n = 11` at level 10, so the dial
  acts on the best run rather than the typical one.
- **The page shipped level 3** when these runs were measured, chosen for how the
  animation looked. The owner’s defaults now ship level 9 on a dial widened to 0–20
  (#171); levels above 10 have not been measured.
  Level 3 was not measured after the repair existed.

## 5. What Is Not Established

- **No spread.** Every “best of the first k” is one observation from one ordered seed
  stream. None of these numbers carries a range or a confidence interval.
- **The runs cannot be re-checked.** Trials and final poses were not retained, so the
  validity of each repaired run rests on the check as it ran at the time.
- **Coverage is thin.** `n = 17`, 26 and 29 have repaired runs at level 6 only.
  Levels 3, 5, 7 and 9 were not measured.
- **The repair only translates.** Whether a repair that rotates changes the scores is
  untested. A compaction pass was tried and its code was not kept, so
  [exp-209](../series/series-000-smoke-and-calibration/experiments/exp-209-h211-an-unretained-compaction-pass.md)
  supports no conclusion.
- **The open hypotheses are untested:** whether restarts beat schedule tuning at equal
  cost (H-207), whether the drop decides the outcome (H-208), and whether any setting
  reaches a record (H-209).
- **One instrument.** These are the workbench’s simulation in one headless Chromium on
  one laptop. They say nothing about the campaign’s Rust engine.

## 6. What Follows

- **Re-measure before reusing any number here.** The package benchmark keeps each
  trial’s poses and reports disjoint seed blocks, which is what these observations lack.
- **Measure success against how much the run is given.** Blind is one level between
  nothing and the full answer.
  The
  [annealing plan](../../../docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md)
  lays out the levels in between, from the record’s connected components to its contact
  graph and rigid clusters.

## Evidence

- **Retained:** `packing/campaign/results/annealing/summaries.json`, which holds one
  median and one best-of-first-k ladder per cell, per run file.
  Cells marked `resolved: true` were repaired and checked before scoring.
  Several files replay the same seeds, so their trial counts overlap.
- **Not retained:** per-trial rows and final poses, which were removed from the branch
  at `6e191a35` to keep the diff reviewable.
- **Checked before this rewrite:** local copies of the rows behind every
  `resolved: true` cell, 59.7 MB and not in the repository.
  No run was refused, every repaired overlap is finite and at most 1e-9, seeds run
  contiguously from 0, and the counts match the summaries.
- **Instrument:** these runs used `packing/devtools/bench_annealing.py`, which now lives
  in the package as `squares-workbench-benchmark`
  (`packages/workbench/tools/workbench_tools/benchmark.py`).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
