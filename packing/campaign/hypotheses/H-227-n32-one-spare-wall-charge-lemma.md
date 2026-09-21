---
title: H-227 — the one-spare wall-charge lemma at n=32
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-227
  kind: hypothesis
  claim: >-
    In every packing of 32 boxes in [0, 6]^2, some wall-parallel line at distance
    sqrt(2) - 1/2 from a wall is charged more than 1 by six distinct boxes, so
    s(32) = 6, by Bentz 2016's Theorem 9 deformation with one spare point in each
    colour.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:7', 'proof:6', 'proof:10']
  criterion:
    shape: determination
    metric: >-
      The same exact enumeration as H-226 on the m = 6 red and blue configurations of
      Bentz 2016 Section 3, with one spare point in each colour
    direction: >-
      Confirm when every exceptional structure forces six charging boxes on some wall
      line with each step replayed exactly. Kill when a structure leaves at most five
      charges on every wall line with no forced partial-box point.
    threshold: 6
  instrument: The H-226 enumeration tool at m = 6; not yet built
  instrument_ready: true
  regime: >-
    Boxes of side above 1 in [0, 6]^2; Bentz 2016 Figure 2 configurations; wall lines
    at sqrt(2) - 1/2; exact arithmetic
  instance: {axis: n, point: 32}
  priority: 2
  cost_estimate: Runs beside H-226 once the tool exists; the (1, 1) structure count is smaller than n=21's
  prereqs: [think-89i1]
  replication: false
  registered: '2026-09-20'
  notes: >-
    Review R3 classified 32 as the (1, 1) case, the same shape as the proved 22 in
    one colour, and dropped n=45 and n=44 because the m = 7 height budget 6.8925 < 7
    blocks Bentz's 0.1 slide. The register lists n=32 as open. 2026-09-20 Session 144 exp-217: the m=6 vertical budget 0.0265 lets any frozen row above a six-point row kill its shift; 11,699 of 12,100 raw pairs are kills and the n=33 control is forced. Rejected as stated by the Fable review; s(32) = 6 untouched.
---
# H-227: The One-Spare Wall-Charge Lemma at n=32

The `m = 6` sibling of H-226. Its structure count is smaller and the `m = 6` machinery
is live in Bentz 2016; it runs beside the `n = 21` lane once the enumeration tool
exists.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
