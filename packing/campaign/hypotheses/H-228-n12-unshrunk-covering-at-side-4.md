---
title: H-228 — an unshrunk covering below 12 at n=12, side 4
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-228
  kind: hypothesis
  claim: >-
    A weighted measure on [0, 4]^2 of total mass strictly below 12 puts mass at least
    1 in every closed unit square at every orientation inside the container, so
    s(12) = 4 by the unshrunk obstruction lemma.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:22', 'proof:15']
  criterion:
    shape: determination
    metric: >-
      The covering value of an unshrunk covering LP at side exactly 4 with
      wall-offset and grid-line atoms, decided by an exact orientation partition and
      an interval route
    direction: >-
      Confirm with a frozen measure of mass below 12 that an unshrunk two-route
      verifier accepts at side 4. Kill with a certified fractional packing of value
      at least 12 at side 399/100 or any side below 4, which retires the one-body
      measure route at n=12 for good.
    threshold: 12
  instrument: >-
    An unshrunk exact-orientation verifier generalised from cases/green17/interval_audit.py
    and an unshrunk column generator; neither exists
  instrument_ready: false
  regime: Closed unit squares at every orientation in [0, 4]^2; exact arithmetic
  instance: {axis: n, point: 12}
  priority: 3
  cost_estimate: One to two weeks of tooling before the single decisive LP
  prereqs: [think-mmd5]
  replication: false
  registered: '2026-09-20'
  notes: >-
    Review R2 rejected lane 2's estimate that the fractional value at side 4 is
    12.3 to 12.6: certificate masses are upper bounds on covering values, and no
    depth-one family of total at least 12 is retained below 4. The claim is
    therefore open on the record, not out of reach; it is blocked on the verifier.
---
# H-228: An Unshrunk Covering Below 12 at n=12, Side 4

The only single-shot route to `s(12) = 4` on X-040’s slate.
It is blocked on an unshrunk verifier, and its kill is a certified dual, which the
existing ceiling readers can already produce below `3.9908`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
