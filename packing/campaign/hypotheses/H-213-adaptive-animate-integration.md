---
title: H-213 — adaptive Animate integration removes clamp ringing
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-213
  kind: hypothesis
  claim: >-
    Law-driven integration substeps remove Animate's cap-to-cap contact ringing at the
    16-to-17 and 89-to-90 transitions while retaining the current amount of mean motion.
  lane: search
  derived_from: [X-035]
  criterion:
    shape: conditions
    metric: deterministic 60 Hz displacement and direction-reversal ratio
    direction: adaptive integration lowers both while retaining mean displacement
    threshold: >-
      maximum displacement at most 0.1 and reversal ratio at most 0.03; the rigid preset
      may use 0.15 and 0.05; median mean displacement remains within 20 per cent of the
      one-step control
  instrument: >-
    packages/workbench/tools/measure-kinetics.ts over the package trajectory generator,
    comparing one-step and adaptive integration with at least three seeds per condition
  instrument_ready: true
  regime: >-
    deterministic Node runs of Animate physics and bodies, default timing and annealing,
    with snap excluded from the measured moving span
  instance: {axis: transition, point: 16-to-17}
  sweep: {axis: transition, points: [16-to-17, 89-to-90]}
  priority: 1
  cost_estimate: seconds
  registered: '2026-09-16'
---
# H-213 — adaptive Animate integration removes clamp ringing

The one-step diagnostic is identified by alternating speed-clamped moves, not by a
rendered impression.
The experiment records raw kernel states, corrected stored states and deterministic 60
Hz presentation samples, then derives every verdict metric from those positions.
The presentation layer decides the visible continuity criterion; the other two layers
locate its cause.

Finiteness, stable square identity, deterministic replay, endpoint agreement and
penetration are guards.
Integration work and elapsed runtime are costs.
Contact counts, gaps and acceleration explain the result but do not replace the
registered displacement and reversal criterion.

The earlier one-off measurements in X-035 motivated the claim but did not test it.
[Exp-211](../series/series-000-smoke-and-calibration/experiments/exp-211-h213-adaptive-animate-integration.md)
rejects the end-to-end claim at frozen commit
`9cca493c17ab61d5efb3e1032f32c54a9b87320e`: adaptive substeps reduce raw ringing, but
every solver-transition group misses at least one preregistered 60 Hz presentation
budget. The instrument is ready; the physical tuning work remains open.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
