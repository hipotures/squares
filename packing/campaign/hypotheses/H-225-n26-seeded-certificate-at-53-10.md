---
title: H-225 — a seeded point certificate at n=26, side 53/10
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-225
  kind: hypothesis
  claim: >-
    A point-atom certificate exists for n=26 at container side 53/10 with
    B = 9977/10000 on the 181-direction net, on a named site set seeded with the
    ceiling-window lattice, so s(26) >= 53/10, above Nagamochi's floor and the only
    first-party value on the register.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:22']
  criterion:
    shape: determination
    metric: >-
      The covering value of a rows-complete point-atom LP on a named site set at
      (n, L, B, net) = (26, 53/10, 9977/10000, 181 directions), decided by both
      routes of decide_certificate on the frozen candidate
    direction: >-
      Confirm only when decide_certificate prints RETAINABLE on a freeze of mass
      strictly below 26. An unfinished loop, a float objective, or a restricted
      optimum at or above 26 on one site set is unresolved for the claim and refutes
      that site set only; two converged seeded site sets at or above 26 park the
      side.
    threshold: 26
  instrument: >-
    devtools.run_fractional_colgen with --grid-counts auto, --seed-windows, a 3600 s
    deadline and --support-cap 32; declare_least_cell_mass; both routes of
    decide_certificate
  instrument_ready: true
  regime: >-
    n=26, side 53/10, shrink 9977/10000, 181-direction net, point atoms only,
    D4-symmetric nonnegative weights, exact rational freeze
  instance: {axis: n, point: 26}
  sweep:
    axis: side
    points: ['53/10', '107/20', '27/5']
  priority: 1
  cost_estimate: One to three runs of up to 3600 s each and the gate; Sessions 144 to 146
  prereqs: []
  replication: true
  registered: '2026-09-20'
  notes: >-
    The verified floor at n=26 is Nagamochi's 5.0. Green's reported 5.51 (DS7
    Theorem 9) is unpublished and unrecovered. Session 140's only n=26 probe was
    unseeded and plateaued at the exact-integer artefact 25.000000 with rows still
    violated. A retain at 53/10 is worth about +0.30 and the recipe transfers to
    n = 37, 50, 65, 82.
---
# H-225: A Seeded Point Certificate at n=26, 53/10

Lane 3 ranked a first weighted certificate at n=26 as the largest single-step gain the
stock instrument can still make.
Review R3 verified Green’s numbers and corrected the reach ratio; the target side is
chosen below Green’s value so that a retain is a first-party floor, not a race.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
