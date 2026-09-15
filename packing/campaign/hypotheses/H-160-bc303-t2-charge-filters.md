---
title: H-160 — BC303 C and S first-owner charge filters
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-160
  kind: hypothesis
  claim: >-
    On the frozen BC293 377-atom measure and every one of the 182 eligible closed
    source charts, every forced-0 C core has integer charge at least 4524200,
    and every S first-owner strip core has integer charge at least 4524185.
  lane: proof
  derived_from: [X-029]
  criterion:
    shape: determination
    metric: Exact minimum integer C charge and exact minimum integer S first-owner charge over all eligible charts
    direction: both at or above their stated thresholds
    threshold: C >= 4524200 and S first owner >= 4524185
  instrument: packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py
  instrument_ready: false
  regime: >-
    q=96/25, h=9977/20000, W=4000000, closed symmetric source equipment;
    182 source charts including both axis aliases, 181 distinct bin-0 orientations;
    closed core membership; exact rational event sweep and parent-wall oracle.
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: One source-bound all-chart invocation with a 30-minute wall allowance after controls
  prereqs:
  - Source rows, complete chart manifest, and executing checkout revision authenticated.
  - Adversarial synthetic all-strata controls admitted before target charge evaluation.
  replication: false
  registered: '2026-09-13'
  notes: >-
    This is a sufficient route to the combined opposite-corner T2 helper, not its
    definition. A C value <=4524199 is a T2 refuter only after rational core and
    physical-parent replay. An S first-owner value <=4524184 rejects only this
    sufficient filter, leaving actual S pairing and T2 undecided. No global
    availability, selection routing, or stronger s(11) bound follows from either
    positive local filter alone.
---
# H-160: Exact BC303 Charge Filters

The accepted [T2 geometry](../explorations/X-029-bc303-t2-exact-geometry-draft.md) and
[charge bridge](../../../docs/project/research/research-2026-09-13-bc303-t2-charge-bridge.md)
reduce C to feasible open atom cells and S to a sufficient first-owner strip test.
The two minimum charges above are the complete measured outcomes.
A low S strip charge leaves the second owner and simultaneous physical parents untested.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
