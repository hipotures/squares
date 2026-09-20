---
title: "H-231 — open question: theta on a sound pose-cell graph at n=11"
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-231
  kind: open_question
  claim: >-
    Whether a Lovász theta certificate on a sound, non-uniform pose-cell conflict
    graph at n=11, verified by rational LDL^T or a verified Cholesky with directed
    rounding, can be built at a cell count whose coarseness loss leaves a side above
    3.826447, and whether the theta value at such a side lies below 11.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:17', 'proof:26']
  instrument: >-
    None. Review R2 measured 44% edge density among legal pose pairs at 3.83, so the
    dual matrix is dense and verification is cubic; the lane's own resolution
    arithmetic gives about 1.4e7 cells per D4 class, above its own kill line.
  instrument_ready: false
  regime: n=11, sides 3.83 to 3.86
  instance: {axis: n, point: 11}
  priority: 4
  cost_estimate: Unpriced; needs a non-uniform cell design before any producer
  prereqs: []
  replication: false
  registered: '2026-09-20'
  notes: >-
    X-037 retired M2 with the reopening condition of an exact PSD route that can
    reach C3; R2 judged that condition addressable but not met, and showed the
    proposed screen cannot discriminate because floor atoms already take the
    88-support to 10 and the 64-support's clique LP is already 9. Stays retired; no
    owner decision is requested.
---
# H-231: Theta on a Sound Pose-Cell Graph

Recorded as an open question so the reopening condition and the density measurement stay
findable. No lane or block is allocated.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
