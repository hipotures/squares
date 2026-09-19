---
title: H-220 — seedless colgen raises a Nagamochi-only floor
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-220
  kind: hypothesis
  claim: >-
    A rows-complete covering of mass strictly below n exists at a container side
    strictly above the Nagamochi floor for at least one n in
    {32, 31, 30, 26, 27, 29, 45, 44}, on a named seedless site set built by the
    stock colgen (auto grids, optional windows), and both routes of
    decide_certificate accept the freeze.
  lane: proof
  derived_from: [X-039]
  strategy_refs: ['proof:22']
  criterion:
    shape: determination
    metric: >-
      decide_certificate on a freeze whose total_mass is strictly below n at a
      queued Nagamochi-only side
    direction: >-
      Confirm only when decide_certificate prints RETAINABLE. A restricted optimum
      above n, an unconverged loop, or a freeze above n refutes that site set only.
    threshold: 1
  instrument: >-
    devtools.run_fractional_colgen with --freeze and no --seed-certificate;
    declare_least_cell_mass; then both routes of decide_certificate. No
    packing-campaign runner.
  instrument_ready: true
  regime: >-
    B = 9977/10000, 181-direction net, D4-symmetric nonnegative point-atom weights,
    exact rational freeze; no first-party certificate seed
  instance: {axis: n, point: 32}
  sweep:
    axis: n
    points: [32, 31, 30, 26, 27, 29, 45, 44]
  priority: 2
  cost_estimate: >-
    Sequential 1200 s probes on the eight queued sides after H-219 and the H-218
    n=20 new-site probe
  prereqs: []
  replication: true
  registered: '2026-09-19'
  notes: >-
    Session-140 second-wave queue never started. n=28, n=61, and n=78 stay
    deferred. Calibration: no seed, larger placement sets. Different n and
    construction class from H-218. Session-141 claimed exp-166 after exp-165
    stopped at 19.887914 unconverged. First probe is n=32 29/5 auto plus
    windows 5. Confirm only on RETAINABLE.
---
# H-220: Seedless Colgen Raises a Nagamochi-Only Floor

[X-039](../explorations/X-039-n100-re-rank-after-session-140.md) keeps the eight
Nagamochi sides Session-140 queued and did not start.

The first probe is n=32 at `29/5`, auto plus windows 5, no certificate seed. A float
LP above `n` refutes that site set only.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
