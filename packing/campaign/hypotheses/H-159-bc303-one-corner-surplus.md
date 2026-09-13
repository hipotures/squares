---
title: H-159 — bottom-left role-C surplus exceeds the shared allowance
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-159
  kind: hypothesis
  claim: >-
    For every admissible bottom-left one-corner role-C unit parent X with both local
    labels 0 and 15 absent, its selected-core surplus S(X) exceeds the BC303 shared
    allowance epsilon = 524199/2000000.
  lane: proof
  derived_from: []
  criterion:
    shape: determination
    metric: Exact selected-core mass minus one for one admissible bottom-left role-C
      parent with the complete closed label set excluding 0 and 15
    direction: Reject the universal inequality when a source-bound exact local witness
      has S(X) <= epsilon; otherwise this one-candidate replay leaves it unresolved.
    threshold: 524199/2000000
  instrument: packing/devtools/replay_bc303_t1_witness.py
  instrument_ready: true
  regime: >-
    BC303's frozen 377-atom rational measure on [0,96/25]^2; unit parent [0,1]^2,
    selected axis core [23/20000,19977/20000]^2, centre (1/2,1/2), axis (1,0),
    physical bottom-left marks and closed signed-frame labels.
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: One deterministic full-source replay of the already disclosed literal
    candidate, with independent source-atom and implementation identity review.
  prereqs:
  - Frozen BC303 source and exact local witness independently admitted at their original
    revisions; maintained reader and source/reader binding independently reviewed.
  replication: true
  registered: retroactive
  notes: >-
    Retrospective registration on 2026-09-13: the centre, axis, two marks, charge and
    rejecting comparison were disclosed and independently reviewed before this H-159
    artifact existed. Exp-157 tests that fixed candidate once; it is not a prospective
    search, a complete minimum, or a test of whether one parent extends to an eleven-parent
    packing. The broader seven-mark selection question remains in the accepted
    selection-routing analysis and separate T2 and global-routing work.
---
# H-159: One-Corner BC303 Surplus

The claim is the named universal bottom-left role-C inequality `S(X) > epsilon` on the
declared local domain with labels 0 and 15 absent.
A single admissible parent at or below the allowance rejects that statement.
The fixed candidate and its replay are recorded in
[exp-157](../series/series-000-smoke-and-calibration/experiments/exp-157-bc303-literal-t1-witness.md).

The registration is retrospective to the disclosed candidate.
The result has no full-packing extension, continuous-domain minimum, T2 forced-type
verdict, global owner-routing result, or new bound on `s(11)`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
