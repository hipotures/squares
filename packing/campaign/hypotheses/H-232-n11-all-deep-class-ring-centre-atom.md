---
title: H-232 — the all-deep corner class at n=11, side 96/25, under the ring-centre 2-of-3 atom
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-232
  kind: hypothesis
  claim: >-
    At n=11, side 96/25, B = 9977/10000 on the 181-direction net, the restricted
    covering value (the infimum over finite point-plus-threshold certificates) of the
    all-deep corner class (bin vector f = 0 of the
    corner tree at d = 1/2: every corner has a core with penetration below 1/2, so
    four banked occupants whose cores contain X' = [1 - beta/2, (1 + beta)/2]^2 with
    beta = B/(1 + D) = 89793000/90207107, and seven cores avoiding the four open
    boxes (1/2, 1)^2) is strictly below 7 once the D4 orbit of the ring-centre
    2-of-3 threshold atom on the sites (101/100, 367/200), (34/25, 19/10),
    (101/100, 401/200), and further 2-of-3 atoms separated from the same domain,
    are admitted beside point atoms; so a point-plus-threshold certificate on the
    box-cut domain with budget minus refund below 7 exists on some named site set.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:10', 'proof:22']
  criterion:
    shape: determination
    metric: >-
      The covering value of a rows-complete point-plus-threshold LP whose row domain
      is the box-cut admissible core domain (every core meeting an open banked box
      (1/2, 1)^2 at any of the four corners removed), on a named site set at
      (n, L, B, net) = (11, 96/25, 9977/10000, 181 directions), with 2-of-3 atoms
      admitted and the exact refund sum over corners of the point mass in X'_j
      subtracted, against the requirement 7 and against the exact total of a
      depth-one family on the box-cut domain feasible for every point and 2-of-3 atom
    direction: >-
      Confirm only with a frozen certificate whose budget minus refund is strictly
      below 7, whose Condition 5' both routes of decide_threshold_certificate accept
      with the box cut admitted as a domain predicate, and whose record carries the
      class claim string and corner_bins (all four deep). Kill with an exact
      depth-one family on the box-cut domain of total at least 7 that
      independent_ceiling_reader and verify_ceiling accept with a K4-box condition
      and that an exact 2-of-3 reader (the arrangement-vertex scan: the maximum
      2-of-3 charge over triples of inclusion-maximal vertex traces is at most 1,
      which by the domination lemma bounds every site triple in the plane; a devtool
      to be retained beside its lemma) also accepts; that kills the
      point-plus-2-of-3 language on the all-deep class at this B and net for every
      site set. The ceiling readers alone do not decide the 2-of-3 condition: the
      transported 88-family passes both while paying 5/4 on the named atom, so it
      does not kill. A float value, an unconverged row loop, or a scratch number
      decides neither.
    threshold: 7
  instrument: >-
    At HEAD neither threshold route takes any domain cut. Needed:
    sqpack.fractional.threshold and threshold_interval with a non-convex box cut
    (per-cell exclusion in the exact sweep, since the convex per-slab range cannot
    express the kept domain; provable-inside exclusion in the interval branch and
    bound), the refund written as a subtraction of the point mass in X' per corner
    (exact and idle on the kill side, since X' lies strictly inside the open box),
    class claim strings and corner_bins under variant class;
    devtools.produce_threshold_certificate and threshold_separation reading the
    box-cut row set; devtools.decide_threshold_certificate with the cut admitted on
    both routes; verify_ceiling and independent_ceiling_reader with K4-box and count
    credit 7; and the exact 2-of-3 reader of the kill rule
  instrument_ready: false
  regime: >-
    n=11, side 96/25, shrink 9977/10000, 181-direction net, point atoms plus all-ones
    2-of-3 threshold atoms, D4-symmetric nonnegative weights, exact rational
    arithmetic, row domain the admissible cores avoiding the four open boxes
    (1/2, 1)^2 at the container corners, four banked occupants refunded through
    X' = [45310607/90207107, 180000107/180414214]^2
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: >-
    Seconds for the fixed-support screen, which is decisive on the kill side; eight
    to twelve hours to admit the box cut and the refund on both threshold routes
    with an independent reader and the 2-of-3 reader; then about thirty minutes per
    run at 96/25
  prereqs: [think-b7pr]
  replication: true
  registered: '2026-09-20'
  notes: >-
    Session 148 (chunk 5): the all-deep class is where the transported 88-family lives
    (four flush corner slots of mass 1 each, residual 7 = requirement, BC-366), so no
    point covering excludes it on any site set. The ring-centre relation X-040 names
    is billed by a 2-of-3 atom on one mid-wall core and two tilted central cores that
    pairwise overlap through three sites with no common point: the family pays 5/4
    against budget 1 on each of the eight D4 images, and 5/4 is the exact maximum any
    2-of-3 atom collects from the residual family (3-of-4 atoms collect at most 1, so
    they cut nothing). The counting proof needs only lane-a Lemmas 2-4 and
    threshold.py's budget theorem; the sweep decides the covering condition (C)
    one-sidedly, accepting only. First experiment: the fixed-support LP on the 56
    residual cores with depth at most 1 on the 125 maximal vertex traces and the
    2-of-3 charge at most 1 on every triple of them; by weak duality and the
    domination lemma a value at least 7 is the full kill for every site set, and a
    value below 7 decides nothing. The chunk-5 derivation and its adversarial review
    (ADMIT WITH CORRECTIONS, applied here) are retained under results/agenda-040 as
    h232-ring-centre-derivation.md and h232-ring-centre-review.md; the review found
    Theorems 1 to 3 and Corollary 4 sound (one unused chord-formula sentence
    corrected there), reproduced every family number independently, and proved the
    5/4 maximality by the domination lemma.
---
# H-232: The All-Deep Corner Class at n=11, 96/25, Under the Ring-Centre Atom

Session 146’s registration review left the all-deep class as the hard one: the one-body
extremal family is an all-deep configuration with residual exactly 7 against a
requirement of 7, so the corner tree cannot close at 96/25 by clipping alone.
Chunk 5 made the second stage precise: the four occupants are pinned (cores containing
X'), at least three non-occupants sit at depth at least sqrt 2 - 1 from every wall, at
most one of them fits in the 1.84 central box, and the relation the family never pays
for is priced by a 2-of-3 atom on three named sites in a wall gap strip, where the
family pays 5/4 against a budget of 1.

This claim is that the class’s restricted covering value in the point-plus-2-of-3
language is below 7. It needs the box cut and the refund admitted on both threshold
routes, and an exact 2-of-3 reader, before any number counts; the fixed-support screen
comes first and is decisive on the kill side.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
