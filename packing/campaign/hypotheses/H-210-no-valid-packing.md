---
title: H-210 — the blind physics never settles to a valid packing
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-210
  kind: hypothesis
  claim: >-
    No blind run of the workbench's physics ends on a valid packing. At every n and every
    parameter setting the squares come to rest overlapping, so every side it reports is a
    bounding box around an invalid arrangement rather than a container a packing needs.
  lane: search
  derived_from: [X-029]
  criterion:
    shape: determination
    metric: the deepest pairwise overlap in the final arrangement, by separating axis
    direction: above tolerance in every trial
    threshold: 0.00001
  instrument: packing/devtools/bench_annealing.py
  instrument_ready: true
  regime: >-
    the workbench's simulation in blind mode; the snapped mode is valid by construction and
    is the control that sets the tolerance
  instance: {axis: n, point: 11}
  sweep: {axis: n, points: [5, 10, 11, 17, 26, 29]}
  priority: 1
  cost_estimate: seconds
  registered: '2026-09-12'
---
# H-210 — the blind physics never settles to a valid packing

**Registered so the claim can be tested rather than assumed.**

Every blind run observed ended with squares overlapping by 0.03 to 0.12 of a unit side.
A separating-axis test measured it over the final poses, with a tolerance taken from the
snapped control
([exp-210](../series/series-000-smoke-and-calibration/experiments/exp-210-h210-blind-runs-are-not-packings.md)).
The trials were not kept, so this is an observation to re-measure rather than a result.

**Why it happens.** The page’s blind contraction advances whenever the deepest overlap
is at most 0.08 of a unit side, and closes the walls onto the known-best side
(`BLIND.overlapTol` in `workbench.js`). The runs are squeezed into the record’s own
container with that much overlap allowed, and nothing afterwards drives it out.

**What would refute it.** One blind run, at any n and any parameters, whose deepest
final overlap is under 1e-5. That is the same falsifier as H-209’s and a cheaper one to
check, which is why it is worth having both.

**What follows if it stands.** Every side the instrument reads directly is a bounding
box rather than a container, so scoring needs a repair first.
The harness has one: it separates overlapping squares and scores the container the
repaired arrangement needs.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
