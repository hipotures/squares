---
title: H-230 — the A6 64-family violates a proved gap-g wall-wedge conflict edge
softschema:
  contract: packing.squares:Hypothesis/v1
  schema: ../schemas/hypothesis.schema.yaml
  envelope: hypothesis
  status: enforced
hypothesis:
  id: H-230
  kind: hypothesis
  claim: >-
    There is a proved wall-wedge conflict lemma for a tilted unit square at gap g
    from a wall, valid for some g >= 4/250, under which two placements of the
    retained A6 64-family at 153/40 that the family weights simultaneously cannot
    coexist in a physical packing, so a conflict-edge atom cuts that family.
  lane: proof
  derived_from: [X-040]
  strategy_refs: ['proof:12', 'proof:3']
  criterion:
    shape: determination
    metric: >-
      An exact check, on the retained family record, that a pair of placements with
      positive weight violates the lemma's conflict region, with the lemma's proof
      reviewed source-distinctly
    direction: >-
      Confirm when a reviewed gap-g lemma and an exact pair violation both exist.
      Kill when the best provable gap extension leaves every weighted pair of the
      family compatible, or when the lemma's wedge shrinks to zero at the family's
      7.11° tilt and 0.016 gap.
    threshold: null
  instrument: >-
    A derivation (Fable lane) of the gap-g extension of lane 2's wall-wedge lemma,
    then an exact pairwise check against
    campaign/series/series-000-smoke-and-calibration/results/agenda-034 family records;
    a conflict-edge atom class in the relational reader does not exist
  instrument_ready: false
  regime: n=11, side 153/40, the retained A6 64-family; exact arithmetic
  instance: {axis: n, point: 11}
  priority: 2
  cost_estimate: A Fable derivation lane of two to three hours, then an hour of exact checks
  prereqs: [think-z20r]
  replication: false
  registered: '2026-09-20'
  notes: >-
    Review R2 confirmed lane 2's wall-vertex wedge lemma (0.3203 protected area at
    40.18°, re-derived and brute-forced) and found the family's 7.11° orbit of mass
    3/4 at gap 0.016 from the top wall, so the lemma's kill condition is not met and
    a gap extension is the open question. R2 ranked this first among lane 2's
    mechanisms.
---
# H-230: The A6 Family Violates a Gap-g Wedge Conflict

Lane 2 turned waste lemmas into two-body conflict edges; review R2 verified the zero-gap
lemma and located the one orbit of the retained family the extension would have to
reach.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
