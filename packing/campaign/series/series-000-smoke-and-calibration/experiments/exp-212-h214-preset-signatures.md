---
title: exp-212 — the named Animate presets do not have one stable kinetic ordering
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-212
  series: series-000
  title: The named Animate presets do not have one stable kinetic ordering
  date: '2026-09-16'
  hypotheses: [H-214]
  tier: exploratory
  subject:
    label: >-
      deterministic 60 Hz kinetics for the balanced, rigid, soft and sticky Animate
      presets
    engine: committed workbench kinetics CLI
    engine_commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
    assurance: numerically-checked
    method: numerical-f64
    tolerance: >-
      non-overlapping min-to-max ranges over three seeds in the predicted direction,
      with the H-213 presentation limits as guards
    host_system: macOS on Apple silicon, Node.js deterministic command
    selftest_passed: true
    precision:
      binary_bits: 53
      rounding: nearest-even
  instance:
    axis: n
    point: 17
    role: target
  method:
    operator: Codex with delegated measurement agents
    control: balanced for sticky contact count; soft for rigid penetration
    candidate: sticky for contact count; rigid for penetration
    runs_per_condition: 3
    trials: 48
    interleaved: false
    commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
    dirty: false
    entry_point: packages/workbench/tools/measure-kinetics.ts
    command: >-
      For every retained solver, n, preset and seed cell, run `npm run
      measure:kinetics --workspace
      @squares/workbench -- --corpus PATH --solver SOLVER --instance N --law LAW
      --seed SEED` after generating the all-pairs workbench corpus.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/exp-212-h214-preset-signatures.json
  results:
  - shape: determination
    question: >-
      are rigid penetration and sticky contact signatures consistently ordered against
      soft and balanced with non-overlapping three-seed ranges at both transitions and
      in both solvers
    role: outcome
    outcome: criterion_missed
    checked_by: >-
      retained 48-row matrix from the shared trajectory CLI, grouped without dropping
      any seed; deterministic replay passed in every cell
  complexity:
    new_failure_modes:
    - a preset name can imply an ordering that reverses with solver or transition
    notes: >-
      Presets remain ordinary parameter bundles. The result rejects their behavioral
      names, not the usefulness of exposing those parameters for experiments.
  verdict:
    decision: rejected
    primary_criterion: >-
      rigid penetration is lower than soft and sticky contact count is higher than
      balanced in every solver-transition cell with non-overlapping three-seed ranges
    reason: >-
      Both predicted orders reverse in at least one transition: rigid exceeds soft
      penetration in Physics at n = 90, and sticky has fewer mean contacts than balanced
      at n = 90 in both solvers; continuity guards also fail at the frozen commit.
    commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
  effort:
    wall_seconds: 86.689334042
    pair_tests: 48
    stopped_by: criterion
---
# exp-212 — The Named Animate Presets Do Not Have One Stable Kinetic Ordering

## What Was Measured

The 48-cell matrix crosses four parameter presets, two solvers, two transitions and
three seeds. The instrument records maximum pair penetration, mean and final contact
count, mean nearest-neighbor gap, displacement, reversal ratio and deterministic replay
from the same positions the painter receives.

The retained result stores all 48 compact rows without discarding any seed.
It was measured from commit `9cca493c17ab61d5efb3e1032f32c54a9b87320e` with a clean
workbench tree. To regenerate the matrix, run
`uv run --frozen --all-extras --group dev python ../packages/workbench/tools/workbench_tools/build_candidate.py --all --out /tmp/squares-kinetics-corpus`
from `packing/`, then run the command template recorded in the frontmatter for every
matrix cell. The retained JSON contains every compact row and the exact engine commit;
full per-frame traces are intentionally omitted.

## Rigid Versus Soft Penetration

The prediction is lower rigid penetration than soft.
Each entry is median (minimum–maximum) over three seeds.

| solver | n | soft | rigid | disposition |
| --- | ---: | ---: | ---: | --- |
| Bodies | 17 | 0.23586 (0.21480–0.24236) | 0.24323 (0.22319–0.25143) | ranges overlap; median reverses |
| Bodies | 90 | 0.63579 (0.62397–0.63957) | 0.50155 (0.49151–0.50753) | predicted order, separated |
| Physics | 17 | 0.23490 (0.20651–0.24524) | 0.10146 (0.05112–0.12544) | predicted order, separated |
| Physics | 90 | 0.45005 (0.43090–0.51833) | 0.52285 (0.51928–0.53185) | reverse order, separated |

The order holds in two cells, overlaps and reverses in one, and reverses with separated
ranges in Physics at `n = 90`.

## Sticky Versus Balanced Contact Count

The prediction is a higher mean contact count for sticky.

| solver | n | balanced | sticky | disposition |
| --- | ---: | ---: | ---: | --- |
| Bodies | 17 | 22.71 (22.50–23.10) | 23.75 (23.36–23.96) | predicted order, separated |
| Bodies | 90 | 206.44 (204.38–208.30) | 185.25 (183.85–185.83) | reverse order, separated |
| Physics | 17 | 18.40 (18.27–18.57) | 19.75 (19.19–20.18) | predicted order, separated |
| Physics | 90 | 140.06 (139.58–141.82) | 132.58 (131.02–132.85) | reverse order, separated |

Sticky gathers more mean contacts at `n = 17` and fewer at `n = 90`, in both solvers.
Its mean nearest-neighbor gap is consistently less negative than balanced, which means
less average penetration in this trace rather than a smaller positive separation.
That metric does not rescue the claimed gathering order.

## Continuity Guards

Soft and sticky do not stay inside the default continuity limits.
For example, Physics soft at `n = 90` has maximum displacement
`0.19503 (0.18717–0.21647)` and reversal ratio `0.03201 (0.03136–0.03450)` against
limits `0.1` and `0.03`. Physics sticky at `n = 90` reaches maximum displacement
`0.18638 (0.15280–0.22344)` and reversal ratio `0.05409 (0.05213–0.05605)`. H-213
records the balanced and rigid guard failures.

## What the Prediction Got Wrong

One preset bundle does not have one solver-independent or density-independent physical
meaning.
Changing repulsion, attraction, contact give and the derived integration work at
once can reduce one penetration statistic while changing contact count in the opposite
direction at another transition.
The interface should describe these as parameter starting points, using literal labels
such as low give, gentle push and attractive, while retaining continuous controls for
experimentation.

## Limits

This experiment covers two transitions and three deterministic seeds.
It rejects the universal ordering stated by H-214; it does not prove that the parameter
bundles are indistinguishable or useless.
Mean contact count is an aggregate over frames rather than persistence of individual
contact identities. The full pose traces were temporary; the repository retains all 48
compact rows and the exact engine commit.
The rejected preset-tuning bead remains open.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
