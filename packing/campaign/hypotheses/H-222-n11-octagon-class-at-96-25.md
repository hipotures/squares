---
title: H-222 — the all-free corner class at n=11, side 96/25
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-222
  kind: hypothesis
  claim: >-
    At n=11, side 96/25, B = 9977/10000 on the 181-direction net, the restricted
    fractional packing value of the all-free corner class of lane-a Theorem B at
    threshold d = 1/2 (no admissible core meets any corner triangle x + y <= 1/2 or
    its D4 images) is strictly below 11, so a point-atom certificate conditioned on
    that class exists on some named site set.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:10', 'proof:22']
  criterion:
    shape: determination
    metric: >-
      The covering value of a rows-complete point-atom LP whose row domain is the
      D4-symmetric convex clip of the admissible core domain by the four corner
      triangles at d = 1/2, on a named site set at (n, L, B, net) = (11, 96/25,
      9977/10000, 181 directions), against the exact total of a depth-one family
      feasible for every point atom on that clipped domain
    direction: >-
      Confirm only with a frozen covering of value strictly below 11 on the clipped
      domain that both routes of decide_certificate accept with the clip admitted as
      a domain predicate. Kill with an exact depth-one family of total at least 11
      whose every core avoids all four corner triangles and that
      independent_ceiling_reader and verify_ceiling both accept; that kills every
      corner-conditioned point route at this B and net for every site set. A float
      value, an unconverged row loop, or a scratch number decides neither.
    threshold: 11
  instrument: >-
    devtools.run_fractional_colgen with a convex corner-clip domain predicate in the
    event-cell sweep (to be built under think-ni3v with an independent reader and a
    T-023-branch replay control); --freeze-family, devtools.polish_ceiling_family,
    devtools.independent_ceiling_reader, sqpack.fractional.ceiling.verify_ceiling;
    devtools.decide_certificate with the clip predicate admitted on both routes
  instrument_ready: false
  regime: >-
    n=11, side 96/25, shrink 9977/10000, 181-direction net, point atoms only,
    D4-symmetric nonnegative weights, exact rational arithmetic, row domain
    clipped by x + y <= 1/2 at each corner
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: >-
    Six to ten hours to admit the domain predicate with an independent reader, then
    about thirty minutes per run of the existing loop at 96/25
  prereqs: [think-ni3v]
  replication: true
  registered: '2026-09-20'
  notes: >-
    Session 143 (X-040): review R1 showed that transported to 96/25 the retained
    88-family makes Theorem B's deep branch exactly neutral, so the all-four-deep
    class is obstructed for every site set; the all-free class is the only branch
    with headroom (the family's residual there is 7 against a requirement of 11).
    A kill here is a structural negative about corner conditioning in the point
    language; a confirm is a conditional exclusion at 3.84 that still needs the
    other fifteen bin classes before it is a bound.
---
# H-222: The All-Free Corner Class at n=11, 96/25

X-040’s lane 1 measured the retained ceiling family against lane-a Theorem B’s
corner-penetration cases; its reviewer transported the family to the target side and
found every deep branch neutral.
The all-free class, in which no core meets a corner triangle of penetration `1/2`, is
the one branch where the family loses mass at no count cost.

This claim is that branch’s restricted covering value is below 11. It needs the convex
clip admitted as a domain predicate on both gate routes before any number counts.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
