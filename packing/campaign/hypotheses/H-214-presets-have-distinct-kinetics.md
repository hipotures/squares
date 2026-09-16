---
title: H-214 — Animate presets have distinct, correctly ordered kinetics
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-214
  kind: hypothesis
  claim: >-
    On the stable physical solver, rigid produces less penetration than soft and sticky
    retains more contacts with smaller neighbour gaps than balanced, while every named
    preset stays inside its continuity budget.
  lane: search
  derived_from: [X-035]
  criterion:
    shape: conditions
    metric: preset penetration, contact persistence and neighbour-gap signature
    direction: rigid is harder than soft and sticky gathers more than balanced
    threshold: >-
      the predicted order has non-overlapping exploratory ranges at three or more seeds
      per condition, with the H-213 displacement and reversal limits as guards
  instrument: >-
    packages/workbench/tools/measure-kinetics.ts with the shared balanced, rigid, soft and
    sticky preset registry
  instrument_ready: true
  regime: >-
    deterministic Node runs of Animate physics and bodies at transitions 16-to-17 and
    89-to-90, default timing and annealing
  instance: {axis: transition, point: 16-to-17}
  sweep: {axis: transition, points: [16-to-17, 89-to-90]}
  priority: 1
  cost_estimate: seconds
  registered: '2026-09-16'
---
# H-214 — Animate presets have distinct, correctly ordered kinetics

Preset names are claims about behavior.
Each preset is an ordinary force-law configuration, and the CLI records the effective
values beside its trajectory.
A range that overlaps another range is no detectable distinction, not a small success.

This test does not require every metric to differ.
It requires the axis named by the preset to move in the predicted direction without
violating the motion and geometry guards.

[Exp-212](../series/series-000-smoke-and-calibration/experiments/exp-212-h214-preset-signatures.md)
rejects that universal ordering over the registered two-transition sweep.
Rigid penetration reverses against soft in Physics at `n = 90`, and sticky mean contact
count reverses against balanced at `n = 90` in both solvers.
The complete matrix was measured at frozen commit
`9cca493c17ab61d5efb3e1032f32c54a9b87320e` and retains all 48 rows.
The interface should treat the four bundles as parameter starting points rather than
promises of a stable physical effect.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
