---
title: H-224 — a depth-one ceiling family of total 17 at n=17, side 23/5
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-224
  kind: hypothesis
  claim: >-
    At n=17, side 23/5, B = 9977/10000 on the 181-direction net, an exact depth-one
    family of admissible cores with total weight at least 17 exists, so no point-atom
    certificate at that side exists for any site set and the fixed-shrink point route
    at n=17 is closed at 23/5 and above.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:22']
  criterion:
    shape: determination
    metric: >-
      The exact total and maximum depth of a polished ceiling family frozen from the
      T-019-seeded column-generation dual at (n, L, B, net) = (17, 23/5, 9977/10000,
      181 directions), read by independent_ceiling_reader and verify_ceiling
    direction: >-
      Confirm only when both readers accept a family with maximum depth at most 1
      and exact total at least 17. Kill with a frozen covering of mass strictly below
      17 that both routes of decide_certificate accept, which would also register a
      new s(17) rung. A family of total below 17 or a stalled polish leaves the claim
      open.
    threshold: 17
  instrument: >-
    devtools.run_fractional_colgen --freeze-family seeded from
    cases/n17_fractional_certificate/certificate.json at 23/5; devtools.polish_ceiling_family;
    devtools.independent_ceiling_reader; devtools.replay_ceiling_family --check
  instrument_ready: true
  regime: >-
    n=17, side 23/5, shrink 9977/10000, 181-direction net, point atoms only,
    D4-symmetric weights, exact rational polish
  instance: {axis: n, point: 17}
  priority: 1
  cost_estimate: One run of about 1200 s plus polish and two readers; Session 144
  prereqs: []
  replication: true
  registered: '2026-09-20'
  notes: >-
    Session 140's T-019 four-grid plus windows 8 run converged at 17.120106 at 23/5,
    which refuted that site set only, and retained no family. A confirmed family
    bounds the whole fixed-shrink point method at n=17 from above at 4.60, against
    the 4.671 packing-side cap, and says an unshrunk or relational language is
    required for any material n=17 result. It moves no bound.
---
# H-224: A Depth-One Ceiling Family of Total 17 at n=17, 23/5

X-040’s lane 3 and review R3 agree that the fixed-shrink family cannot close n=17. This
claim asks where the point route actually stops.
The Session 140 run at `23/5` converged above 17 on one site set; a ceiling family of
total 17 would make that a statement about every site set.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
