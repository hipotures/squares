---
title: H-161 — literal BC303 four-corner parent union exceeds its budget
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-161
  kind: hypothesis
  claim: >-
    In the frozen BC303 377-atom measure, the closed literal parent
    Q0=[0,1]^2 has integer mass N=4000000*mu(Q0) at least 4262074.
    Consequently the four specified D4 corner copies cannot all occur in an
    eleven-parent packing under the imported BC303 core floor.
  lane: proof
  derived_from: []
  criterion:
    shape: determination
    metric: Exact integer N=4000000*mu([0,1]^2) and the four-corner parent-union budget
    direction: N >= 4262074 accepts the literal four-corner nonextension claim
    threshold: 4262074
  instrument: packing/devtools/read_bc303_parent_union.py
  instrument_ready: true
  regime: >-
    Frozen BC303 source revision 39714308ce2081abbd76624387d134fee4be6deb,
    source SHA-256 c30b600d3d35f3851f0595e2c42962bf353721f9e72b0539bd691aec522e876f,
    377 rational point atoms in K=[0,96/25]^2, closed literal Q0 and its four
    separated D4 corner images; one source-bound exact reader invocation.
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: One exact 377-atom read and an independent source-atom replay
  prereqs:
  - The parent-union inequality and its strict-core premise pass independent review.
  - The source-bound reader, synthetic geometry, and forgery controls pass before the target.
  replication: true
  registered: '2026-09-13'
  notes: >-
    The companion one-parent comparison is frozen in exp-159: N>=5048249 excludes
    extension of this exact Q0 alone. If 4262074<=N<=5048248, only the literal
    four-corner tuple is excluded. Below 4262074 this necessary test survives,
    without proving an extension. Neither outcome excludes a pose cell, all
    eleven-parent packings, or changes the known bound on s(11).
---
# H-161: Literal BC303 Parent Union

The reviewed parent-union inequality is `mu(Q_I)-k+(11-k)g<=epsilon`, where `g=3/800000`
and `epsilon=524199/2000000`. The source scale is `W=4000000`, with `WM=45048398` and
`W(1+g)=4000015`. For one exact `Q0`, the necessary integer condition is `N<=5048248`.
For the four separated D4 corner copies, it is `4N<=17048293`, equivalently
`N<=4262073`. These are fixed before the
[exp-159 target read](../series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md).

The four-corner claim concerns that specified tuple only.
A pointwise result does not extend to nearby parent poses without a separate uniform
lower bound on their union mass.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
