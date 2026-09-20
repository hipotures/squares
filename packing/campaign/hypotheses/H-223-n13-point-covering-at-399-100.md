---
title: H-223 — a first-party point certificate at n=13, side 399/100
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-223
  kind: hypothesis
  claim: >-
    A point-atom certificate exists for n=13 at container side 399/100 with
    B = 9977/10000 on the 181-direction net, on a named site set that includes the
    ceiling-window lattice, so s(13) >= 399/100 has a first-party structure-free
    fractional proof.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:22', 'proof:2']
  criterion:
    shape: determination
    metric: >-
      The covering value of a rows-complete point-atom LP on a named site set at
      (n, L, B, net) = (13, 399/100, 9977/10000, 181 directions), decided by both
      routes of decide_certificate on the frozen candidate
    direction: >-
      Confirm only when decide_certificate prints RETAINABLE on a freeze of mass
      strictly below 13. A converged restricted optimum at or above 13 refutes the
      site set only; an exact depth-one family of total at least 13 accepted by both
      ceiling readers refutes the claim at this scope. Unconverged or float values
      decide nothing.
    threshold: 13
  instrument: >-
    devtools.run_fractional_colgen with --seed-windows and auto grids at 399/100;
    declare_least_cell_mass; both routes of decide_certificate; on a converged
    value at or above 13, --freeze-family then polish_ceiling_family and both
    ceiling readers
  instrument_ready: true
  regime: >-
    n=13, side 399/100, shrink 9977/10000, 181-direction net, point atoms only,
    D4-symmetric nonnegative weights, exact rational freeze; the shrunk grid ceiling
    3.9908 clears the side by 0.0008
  instance: {axis: n, point: 13}
  priority: 2
  cost_estimate: One 1200 s to 3600 s run and the gate; Session 144
  prereqs: []
  replication: true
  registered: '2026-09-20'
  notes: >-
    s(13) = 4 is Bentz 2010's theorem, so a confirm is calibration of the
    integer-endpoint mechanism, not a new bound. Review R2 named this the cheapest
    decisive measurement in lane 2's slate: the side sits inside the window where a
    shrunk certificate is still possible, and a kill family would say the endpoint
    cases need structure even one hundredth below the integer.
---
# H-223: A First-Party Point Certificate at n=13, 399/100

Lane 2 asked whether the integer-endpoint cases admit a structure-free fractional proof
one hundredth below the integer.
Only `m = 4` can be tested in the shrunk language, because `3.99` lies below the grid
ceiling `3.9908` while `4.99` and `5.99` do not.

A retained certificate here is a calibration rung under a proved value.
A depth-one family of total at least 13 is the informative negative.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
