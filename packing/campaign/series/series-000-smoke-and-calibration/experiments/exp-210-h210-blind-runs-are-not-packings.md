---
title: exp-210 — blind runs of the workbench's physics end with squares overlapping
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-210
  series: series-000
  title: Blind runs of the workbench's physics end with squares overlapping
  date: '2026-09-12'
  hypotheses:
  - H-210
  tier: exploratory
  subject:
    label: the workbench's contact simulation in blind mode, which withholds the destination poses
    engine: workbench page, build 4.4 MB, branch claude/annealing-search-benchmark
    engine_commit: d3c3a778
    assurance: numerically-checked
    method: numerical-f64
    tolerance: 1e-5 of a unit side of deepest pairwise overlap, taken from the snapped run's
      own float noise rather than chosen
    host_system: macOS on Apple silicon, one headless Chromium
    selftest_passed: true
    precision:
      binary_bits: 53
      rounding: nearest-even
    migration_annotation: '2026-09-13: source reference mapped from pre-purge ee27f8e3 to reachable
      d3c3a778; the retained harness and workbench source trees compare equal in Git. Original
      run provenance was not recaptured. The declared trial count does not match the recorded
      command, which requests 12,000, and no manifest was kept to reconcile them.'
  instance:
    axis: n
    point: 11
    role: target
  method:
    operator: claude-opus-5, unattended
    control: the snapped trajectory, which ends on the record's poses by construction
    candidate: the blind trajectory, which starts from the previous record and is not given the
      destination poses
    trials: 15000
    interleaved: false
    commit: d3c3a778
    entry_point: packing/devtools/bench_annealing.py
    command: python -m devtools.bench_annealing --n 5 10 11 17 26 29 --seeds 2000 --anneal 6
    record: packing/campaign/results/annealing/
  results:
  - shape: determination
    question: does any blind run end on an arrangement with no overlapping squares, checked
      by a separating-axis test over the final poses written in the harness rather than read
      off the simulation
    role: guard
    outcome: invalid
  - shape: conditions
    metric: deepest pairwise overlap in the final arrangement at n = 5, 11 and 17, unit sides
    control_median: 7.3e-07
    candidate_median: 0.084
    control_range:
    - 5.5e-07
    - 1.01e-06
    candidate_range:
    - 0.035146
    - 0.086189
    change_pct: 11506749.3
    overlapping: false
  complexity:
    lines_changed: 96
    new_failure_modes:
    - a trial can now be refused as invalid rather than recorded as poor
    notes: The check is the change; the simulation was not touched. It voided every result
      recorded before it.
  verdict:
    decision: unresolved
    primary_criterion: the deepest pairwise overlap in the final arrangement
    reason: Every blind run observed ended overlapping against a snapped control at float noise,
      but neither the trials nor their final poses were kept, so the observation cannot be
      re-checked from the repository.
    commit: d3c3a778
  effort:
    stopped_by: dependency
    wall_seconds: unrecorded-historical
    migration_annotation: '2026-09-13: no complete elapsed-time receipt was retained. Per-trial
      median milliseconds and approximate prose budgets cannot recover total wall or operator
      time. This marker records missing history and is unavailable to new experiments.'
---
# exp-210 — Blind Runs of the Workbench’s Physics End With Squares Overlapping

**Rewritten 2026-09-14** to remove superseded framing and layered corrections.
The previous text is at commit `a40d272c`.

## What Was Measured

A blind run starts from the known-best packing for `n - 1`, drops the new square into
the emptiest cell of a coarse grid, and runs contact forces, wall forces and a decaying
shake while the container contracts toward the known-best side for `n`. It is not given
the destination poses.

The measurement is the deepest overlap between any two squares in the arrangement the
run **ends on**. A separating-axis test computes it from the final poses, in the
harness, without using the simulation’s own bookkeeping.
The page’s `maxPenetration` is a running maximum over the whole trajectory and says
nothing about where the squares stopped.

## The Control Sets the Tolerance

| mode | n = 5 | n = 11 | n = 17 |
| --- | ---: | ---: | ---: |
| snap: ends on the record’s poses by construction | 5.5e-7 | 1.0e-6 | 7.3e-7 |
| free: pulled toward the destination poses, not snapped | 3.9e-5 | 4.5e-5 | 3.1e-2 |
| blind: not given the destination poses | 8.4e-2 | 3.5e-2 | 8.6e-2 |

The snapped row is the float noise the stored poses carry.
Two orders of magnitude separate it from the smallest real overlap, so a tolerance of
1e-5 refuses overlaps without refusing arithmetic.

## Result

Every blind run observed ended with at least one pair of squares overlapping, by 0.03 to
0.12 of a unit side.

## What It Means

- **Nothing measured before this check describes a packing.** A side read from the final
  arrangement was a bounding box around overlapping squares, and a bounding box shrinks
  when squares are allowed to intersect.
  That is why some early parameter cells reported a container below the known-best side.
  Those results are void and appear nowhere in the record.
- **Scoring needs a repair step.** The harness now separates overlapping squares,
  translation only with angles held, and scores the container that the repaired
  arrangement needs.
  [X-029](../../../explorations/X-029-the-workbench-physics-as-a-search.md) reports what
  repaired runs are worth.

## Why the Overlap Survives

The page’s own schedule allows it.
In blind mode the walls close toward the known-best side, and the contraction advances
whenever the deepest overlap is at most `BLIND.overlapTol`, which is 0.08 of a unit side
(`workbench.js`, the blind branch of the trajectory loop).
The walls stop at the known-best side and never go below it.

So a blind run is squeezed into the record’s own container while squares may overlap by
up to 0.08. The observed overlaps, 0.035 to 0.086, sit at that tolerance.
It also explains the early cells that reported a container below the known-best side:
squares compressed inside a record-sized box can have a smaller bounding box than the
box.

The snapped and free modes add target springs that pull each square toward its
destination. Blind mode has none, so nothing drives the overlap out.

## Evidence

The trials and their final poses were not retained, so this result cannot be re-checked
from the repository.
It is cheap to reproduce: from `packing/`, run
`uv run --frozen --all-extras --group dev python -m devtools.bench_annealing --n 5 11 17 --seeds 200`.
Each trial row it writes under `campaign/results/annealing/` carries `overlap`, the
deepest pairwise overlap before repair.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
