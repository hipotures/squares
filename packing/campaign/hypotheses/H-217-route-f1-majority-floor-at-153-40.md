---
title: H-217 — Route F1 majority, k-of-S, and floor covering at 153/40
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-217
  kind: hypothesis
  claim: >-
    The rows-complete covering LP with weighted-majority, k-of-S, and floor atoms on
    arrangement-vertex sites has value strictly below 11 at container side 153/40 with
    B = 9977/10000 on the 181-direction net, and that covering freezes to a certificate
    of total budget strictly below 11 with least charge at least 1.
  lane: proof
  derived_from: [X-037]
  strategy_refs: ['proof:22', 'proof:23']
  criterion:
    shape: determination
    metric: >-
      The covering value of the rows-complete majority, k-of-S, and floor LP at
      (n, L, B, net) = (11, 153/40, 9977/10000, 181 directions) on arrangement-vertex
      sites, against a depth-one family feasible for every admitted majority, k-of-S,
      and floor atom
    direction: >-
      Confirm only with a frozen certificate of total budget strictly below 11 and
      least charge at least 1 that both routes of decide_threshold_certificate accept,
      or both routes of the think-g3j7 successor that admits these classes. Kill, and
      refute the claim at this scope, with an exact depth-one family of total at least
      11 that is feasible for every admitted majority, k-of-S, and floor atom on its
      own vertices. Column-generation values on incomplete rows, clique-LP numbers on
      a fixed catalogue, and the attic replacement-support chase decide neither
      direction.
    threshold: 11
  instrument: >-
    A checkpointed column-generation loop that prices weighted-majority, k-of-S, and
    floor atoms and hands a terminal family to an independent reader and then to
    devtools.decide_threshold_certificate, or to the think-g3j7 successor that admits
    these classes (think-gyzw). The sites-1 arrangement-vertex checkpoint must be
    retained or regenerated (think-3xbr). The retained threshold verifier must accept
    those atom classes without mutating T-025 or T-026 (think-g3j7). None of those
    three exists yet. This hypothesis allocates no experiment id; exp-161 remains
    Route S.
  instrument_ready: false
  regime: >-
    n=11, side 153/40, shrink 9977/10000, 181-direction net, arrangement-vertex sites,
    weighted-majority, k-of-S, and floor atoms with D4-symmetric nonnegative weights,
    exact rational arithmetic
  instance: {axis: n, point: 11}
  priority: 1
  cost_estimate: >-
    About a day to land the three missing tools, then several checkpointed hours for a
    convergence run to one of the two terminal states
  prereqs:
  - >-
    think-g3j7: new reader accepts weighted-majority, k-of-S, and floor atoms without
    mutating T-025 or T-026
  - 'think-3xbr: sites-1 checkpoint retained or regenerated'
  - >-
    think-gyzw: guarded colgen with independent family reader and threshold-gate
    hand-off
  replication: true
  registered: '2026-09-18'
  notes: >-
    X-037 admitted this language as a certificate class and did not measure a covering
    value. The overnight loop rebuilt a mass-11 family after every cut and never reached
    a terminal state; surviving both informal kill criteria is not evidence that the
    covering LP is below 11. Format admission is not this claim. decide_certificate is
    the point two-route gate and is not this instrument.
---
# H-217: Route F1 at 153/40

T-025 already prices a relation: a 2-of-3 atom is `(S, k, w)` with `|S| = 3` and
`k = 2`. X-037’s adversarial review kept that route as F1 and widened the admitted
classes to weighted-majority, k-of-S, and floor atoms.
The scientific claim is not that those classes are sound.
It is that, at `153/40` with the retained shrink and net, the rows-complete covering in
that language falls below 11 and freezes to a certificate whose total budget is strictly
below 11 and whose least charge is at least 1.

The kill is the dual of that claim.
A depth-one family of total at least 11 that is feasible for every admitted majority,
k-of-S, and floor atom on its own vertices shows the language is capped at 11 at this
scope, the way the point-atom ceiling caps the one-body method at `191/50`. Killing only
majority and floor leaves k-of-S open.

`devtools.decide_certificate` decides point certificates.
The confirm gate here is `devtools.decide_threshold_certificate`, or the `think-g3j7`
successor that admits these classes: budget `< 11` and least charge `>= 1`, both routes
agreeing. A dual with “no cell below 1” is not that gate.

Nothing in the attic chase is this measurement.
Fixed-support values (9, 54/5, 76/7, 296/27) are not covering values.
Column generation that refills to 11 with rows still open has not terminated.
The `sites-1` LP did not run.

The format decision in X-037 admits the language.
This hypothesis stays blocked until the new reader, the site checkpoint, and the
convergence tool exist.
Do not mutate T-025’s or T-026’s embedded `verify_claim.py`. A later certificate in a
new class needs two-route C4 before it can carry a T-id.
T-025 and T-026 remain 2-of-3 (+ point) certificates; their bytes are not reread as
majority or floor atoms.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
