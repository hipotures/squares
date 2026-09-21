---
title: H-229 — the tilted-anchor case containing the ceiling family's 29° slot
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-229
  kind: hypothesis
  claim: >-
    At n=11, side 96/25, B = 9977/10000, in the anchor case whose centre box of
    half-width 3/20 contains (2.495, 1.387) and whose folded angle bin is (25°, 35°],
    the restricted fractional packing value of the other ten cores on the domain that
    excludes every core overlapping every unit square of the anchor cell is strictly
    below 10.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:10', 'proof:22']
  criterion:
    shape: determination
    metric: >-
      The covering value of a rows-complete point-atom LP on the anchor-cell residual
      domain at (11, 96/25, 9977/10000, unfolded 181-direction net), against the
      exact total of a depth-one family feasible on that domain
    direction: >-
      Confirm with a frozen covering below 10 on the residual domain that both gate
      routes accept with the cell predicate admitted. Kill with an exact depth-one
      family of total at least 10 on the residual domain accepted by both ceiling
      readers.
    threshold: 10
  instrument: >-
    A non-convex box-avoidance domain predicate (the BC-204 instrument) and the
    anchor cell's forbidden-set construction per net direction; neither exists
  instrument_ready: false
  regime: >-
    n=11, side 96/25, shrink 9977/10000, unfolded net (off-diagonal cells break the
    folded reflection), point atoms, exact arithmetic; completeness needs the lowest
    angle bin edge at the cell-24 boundary 6.4537°, not 6.585°
  instance: {axis: n, point: 11}
  priority: 2
  cost_estimate: Eight to twelve hours to the first number after the domain instrument exists
  prereqs: [think-z20r]
  replication: true
  registered: '2026-09-20'
  notes: >-
    Review R1 corrected lane 1: the 33/8 removal is a single-pose number; priced
    over the whole cell the removal is at most 5/2 at 96/25, so the honest gain per
    case is at most 1.5 and the residual is at least 8.5 against 10. The tree is
    complete only with the corrected bin edge. Registered so the case is on the
    record; it is not the first spend.
---
# H-229: The Tilted-Anchor Case Containing the 29° Slot

Lane 1’s second mechanism after review R1’s corrections.
The gain is real but smaller than first measured, and the domain predicate it needs is
non-convex, so it waits behind H-222.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
