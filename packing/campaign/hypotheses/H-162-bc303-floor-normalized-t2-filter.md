---
title: H-162 — floor-normalized BC303 C and S first-owner filter
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-162
  kind: hypothesis
  claim: >-
    On the frozen BC293 377-atom measure and every one of the 182 eligible closed
    source charts, the exact forced-0 C minimum and exact S first-owner strip
    minimum are both at least 4524132 integer mass units.
  lane: proof
  derived_from: [X-031]
  criterion:
    shape: determination
    metric: Complete exact integer C and S first-owner strip minima over all eligible charts
    direction: Both minima at or above 4524132
    threshold: C >= 4524132 and S first owner >= 4524132
  instrument: packing/devtools/analyze_bc303_h162_receipt.py
  instrument_ready: true
  regime: >-
    q=96/25, h=9977/20000, W=4000000; frozen 377-atom BC293 measure and closed
    symmetric BC303 source equipment; 182 eligible C and S first-owner charts
    including both axis aliases and 181 distinct bin-0 orientations; exact rational
    event sweep, closed core membership, complete signed-frame labels, and rational
    physical-parent replay.
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: One receipt-only comparison of the single admitted exp-158 target run; no second target invocation
  prereqs:
  - Authenticate all frozen source rows and blobs, the complete first-owner manifest, and the executing checkout revision.
  - Admit exp-158 source, adversarial controls, complete target coverage, and attaining-cell replay before reading its retained exact minima.
  replication: false
  registered: '2026-09-13'
  notes: >-
    This is a sufficient filter for the normalized opposite-corner helper, not the
    complete actual-S criterion. A replayed C value <=4524131 rejects both H-162
    and that helper, regardless of S. If C passes but an admitted S strip minimum
    is <=4524131, reject only H-162; actual S and the helper remain unresolved.
    Both passing minima accept H-162 and establish the helper under X-031's
    imported BC303 floor. A later actual-S registration cannot reverse H-162's
    filter verdict. The H-162 instrument compares a retained receipt only; the
    exp-158 charge reader is its upstream source, not a second H-162 target.
    H-160 and exp-158 retain their separate frozen criteria.
---
# H-162: Floor-Normalized First-Owner Filter

The [X-031 derivation](../explorations/X-031-bc303-floor-normalized-t2-helper-draft.md)
proves the integer cutoffs conditional on the imported BC303 strict-core floor.
The numerical minima are unmeasured at registration.
The
[source-distinct mathematical audit](../../../docs/project/reviews/review-2026-09-13-bc303-h162-preregistration-math.md)
checks the quantifiers and verdict order.

The sole future input is the retained exact C and S first-owner minima from the
[single exp-158 invocation](../series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md),
after its own source, revision, control, completeness, and replay admission.
[Exp-160](../series/series-000-smoke-and-calibration/experiments/exp-160-bc303-floor-normalized-t2-filter-analysis.md)
owns the separate H-162 comparison.
Its thresholds do not change H-160’s C `4524200` or S strip `4524185` thresholds, and
this registration authorizes no new target invocation.

An incomplete run, source mismatch, failed control, or refused replay yields an
unresolved instrument outcome.
A low C witness needs exact closed atom membership, complete labels, and a rational
contained physical parent before it rejects the normalized local helper.
A low S strip rejects only this sufficient filter.
The complete actual-S condition in X-031 requires simultaneous physical parents and an S
second owner drawn from every compatible admitted chart, beyond the 182-chart
first-owner manifest.
Neither filter acceptance nor H-161 local stability establishes global owner selection,
an eleven-parent packing exclusion, or a stronger bound on `s(11)`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
