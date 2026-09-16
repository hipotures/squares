---
title: exp-211 — adaptive integration does not yet meet the Animate presentation budgets
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-211
  series: series-000
  title: Adaptive integration does not yet meet the Animate presentation budgets
  date: '2026-09-16'
  hypotheses: [H-213]
  tier: exploratory
  subject:
    label: >-
      deterministic raw and 60 Hz presented Animate trajectories under adaptive
      force-law integration
    engine: committed workbench kinetics CLI
    engine_commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
    assurance: numerically-checked
    method: numerical-f64
    tolerance: >-
      balanced maximum displacement 0.1, reversal ratio 0.03 and mean displacement
      0.0136 to 0.0204; rigid limits 0.15, 0.05 and the same mean interval
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
    control: >-
      the preregistered one-step control was not retained; absolute presentation budgets
      remain sufficient to reject a candidate that breaches them
    candidate: >-
      adaptive substeps with balanced and rigid laws, physics and bodies solvers, and
      the default timing and annealing settings
    runs_per_condition: 3
    trials: 24
    interleaved: false
    commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
    dirty: false
    entry_point: packages/workbench/tools/measure-kinetics.ts
    command: >-
      For each retained solver, n, law and seed cell, run `npm run
      measure:kinetics --workspace
      @squares/workbench -- --corpus PATH --solver SOLVER --instance N --law LAW
      --seed SEED` after generating the all-pairs workbench corpus.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/exp-211-h213-animate-kinetics.json
  results:
  - shape: determination
    question: >-
      do adaptive balanced and rigid paths satisfy every preregistered 60 Hz
      displacement, reversal and mean-motion budget at n = 17 and n = 90
    role: outcome
    outcome: criterion_missed
    checked_by: >-
      all 24 retained committed-code rows from the shared trajectory CLI; deterministic
      replay was true in every cell
  complexity:
    new_failure_modes:
    - 60 Hz presentation can breach a motion budget even when the raw solver path passes
    notes: >-
      The instrument separates raw, corrected and presented motion, so a stable solver
      trace cannot conceal presentation discontinuity.
  verdict:
    decision: rejected
    primary_criterion: >-
      all balanced and rigid n = 17 and n = 90 cells satisfy their maximum displacement,
      reversal and mean-motion budgets over seeds 0 through 2
    reason: >-
      Every solver-transition group at the frozen commit misses at least one required 60
      Hz budget; the instrument is ready, but physical tuning remains open.
    commit: 9cca493c17ab61d5efb3e1032f32c54a9b87320e
  effort:
    wall_seconds: 0
    pair_tests: 24
    stopped_by: criterion
---
# exp-211 — Adaptive Integration Does Not Yet Meet the Animate Presentation Budgets

## What Was Measured

The command sampled the actual poses supplied to the painter at deterministic 60 Hz.
The frozen-commit matrix covers balanced and rigid laws, the physics and bodies solvers,
the `16 → 17` and `89 → 90` transitions, and seeds 0 through 2. It also retains the raw
solver metrics, endpoint landing, penetration, integration work and replay determinism.

The retained result stores the three seed values for every metric rather than only the
medians in this report.
It was measured from commit `9cca493c17ab61d5efb3e1032f32c54a9b87320e` with a clean
workbench tree. To regenerate the matrix, run
`uv run --frozen --all-extras --group dev python ../packages/workbench/tools/workbench_tools/build_candidate.py --all --out /tmp/squares-kinetics-corpus`
from `packing/`, then run the command template recorded in the frontmatter for every
matrix cell. The retained JSON contains all 24 compact rows and the exact engine commit;
full per-frame traces are intentionally omitted.

## Result

Each table entry is median (minimum–maximum) over three seeds.
Displacement units are one square side.

| solver | n | law | mean displacement | maximum displacement | reversal ratio |
| --- | ---: | --- | ---: | ---: | ---: |
| Bodies | 17 | balanced | 0.01480 (0.01348–0.01527) | 0.09477 (0.07652–0.09599) | 0.04378 (0.03967–0.04514) |
| Bodies | 17 | rigid | 0.01619 (0.01579–0.01639) | 0.14397 (0.14249–0.14605) | 0.05130 (0.04378–0.05540) |
| Bodies | 90 | balanced | 0.02195 (0.02143–0.02211) | 0.23095 (0.22682–0.24014) | 0.03656 (0.02868–0.04031) |
| Bodies | 90 | rigid | 0.02240 (0.02097–0.02267) | 0.21328 (0.21204–0.21695) | 0.04871 (0.04496–0.05181) |
| Physics | 17 | balanced | 0.01147 (0.01139–0.01191) | 0.08797 (0.08488–0.10184) | 0.04241 (0.03899–0.04309) |
| Physics | 17 | rigid | 0.01384 (0.01379–0.01407) | 0.14386 (0.14102–0.14787) | 0.06019 (0.04993–0.06224) |
| Physics | 90 | balanced | 0.01645 (0.01625–0.01671) | 0.20534 (0.20224–0.21740) | 0.04238 (0.03850–0.04625) |
| Physics | 90 | rigid | 0.01729 (0.01723–0.01764) | 0.20826 (0.20365–0.21146) | 0.05401 (0.04793–0.05969) |

Balanced requires maximum displacement at most `0.1`, reversal ratio at most `0.03` and
mean displacement from `0.0136` through `0.0204`. Rigid permits `0.15` and `0.05` for
the first two limits with the same mean interval.
No row satisfies every limit over all three seeds.

The raw adaptive path is materially smoother than its presented form.
For example, balanced Physics at `n = 90` has raw maximum displacement
`0.092485 (0.092485–0.092486)` and raw reversal ratio `0.013980 (0.013653–0.015809)`,
both inside the declared limits.
The presented path reaches maximum displacement `0.205341 (0.202237–0.217397)` and
reversal ratio `0.041808 (0.038281–0.045989)`.

## Screening Sweeps

Earlier dirty-worktree screening sweeps located possible controls but were not carried
into this verdict. The frozen 24-cell committed-code matrix above is the evidence for
rejection.

## What the Prediction Got Wrong

Adaptive substeps address the cap-to-cap motion in the raw numerical path, but raw
stability does not guarantee that the sampled presentation meets its kinetic budgets.
One set of global speed, damping, timing and annealing controls also cannot preserve the
declared mean motion at `n = 17` while bounding the largest `n = 90` Bodies motion.
The next experiment needs a rotational or Bodies-member response control, or normalized
perturbation torque and frequency, followed by the same frozen 24-cell matrix.
It must not use a smoothing filter to hide motion the solver produced.

## Limits

The original one-step control command was not retained, so this experiment cannot
measure the candidate’s mean-motion ratio against that control.
That gap does not change the rejection because the candidate independently breaches the
absolute presentation budgets.
The full pose traces were temporary; the repository retains every compact per-seed row
and the exact engine commit, not every frame.
Pair and wall penetration remain large and require separate geometry work before these
paths can support Search claims.
The rejected default and preset tuning beads remain open.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
