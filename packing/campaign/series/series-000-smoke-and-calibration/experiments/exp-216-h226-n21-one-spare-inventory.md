---
title: exp-216 — Theorem 11 replay and the one-spare structure inventory at n=21
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-216
  series: series-000
  title: Theorem 11 replay and the one-spare structure inventory at n=21
  date: '2026-09-20'
  hypotheses: [H-226]
  tier: confirmatory
  subject:
    label: >-
      Bentz 2016's Theorem 11 replayed exactly at the printed constants, then the
      complete enumeration of exceptional structures for 21 boxes against the 22
      red and 23 blue points (one spare red, two spare blue), each classified as
      forced, needs-geometry, or kill on the two vertical wall lines under Theorem
      8's freezing rules and the paper's row and end-point moves
    engine: >-
      devtools.bentz2016.replay_theorem11 and devtools.bentz2016.one_spare_inventory,
      ported from the Session 144 mathematical lane's scratch under OR-1; exact
      Fraction and algebraic arithmetic
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 144; project Python 3.14.7
  instance: {axis: n, point: 21, role: target}
  method:
    control: >-
      The zero-spare n=22 case (--check): every one of the 73 blue structures must
      be reported forced, reproducing Theorem 11; and the 24-row replay of Theorem
      11 must pass at the printed constants (D-505, D-506, D-507)
    candidate: >-
      The n=21 inventory. Confirm H-226 only if every structure is forced under the
      modelled toolkit with each finish replayed exactly. A structure that leaves
      at most four charging boxes on every wall line with no forced partial-box
      point is H-226's registered kill for the proof strategy as stated; it does
      not refute s(21) = 5.
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-144 (Fable lane, Opus port, Fable review)
    entry_point: packing/devtools/bentz2016/one_spare_inventory.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.bentz2016.replay_theorem11 --json
      campaign/series/series-000-smoke-and-calibration/results/agenda-040/bentz2016-theorem11-replay.json
      && uv run --frozen --all-extras --group dev python -m
      devtools.bentz2016.one_spare_inventory --check --json
      campaign/series/series-000-smoke-and-calibration/results/agenda-040/one-spare-inventory-n22-check.json
      && uv run --frozen --all-extras --group dev python -m
      devtools.bentz2016.one_spare_inventory --n 21 --json
      campaign/series/series-000-smoke-and-calibration/results/agenda-040/one-spare-inventory-n21.json
    budget: >-
      The Session 144 mathematical lane (about two hours) plus the port and one
      Fable review; the enumeration itself runs in minutes.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  effort:
    timebox: One Fable lane, one Opus port, one Fable review
    wall_seconds: 39
    stopped_by: criterion
  results:
  - shape: determination
    role: outcome
    question: >-
      Does Theorem 11 replay at the printed constants, and does every exceptional
      structure at n=21 force five charging boxes on some wall line under Theorem 8
      with the paper's moves?
    outcome: criterion_missed
    checked_by: >-
      devtools.bentz2016.replay_theorem11: 24 of 24 rows hold (negative control at the
      old constant fails rows 11 and 15); devtools.bentz2016.one_spare_inventory --n
      21: 167,915 raw pairs, 42,124 D2 orbits, after the merge propagation 16,060
      forced, 22,603 needs-geometry, 3,461 kill (before propagation 11,483 / 26,908 /
      3,733); the Fable review re-implemented the enumeration independently and
      agreed on every orbit (receipt bentz2016-one-spare-receipt.md)
  - shape: record
    role: outcome
    metric: kill orbits at n=21 after propagation (structures leaving at most four charges on every vertical wall line with no forced partial-box point)
    direction: lower
    score: 3461
    standing_best: 0
    standing_best_source: H-226 criterion (confirm needs every structure forced)
    beat_record: false
    runs: 1
  verdict:
    decision: rejected
    primary_criterion: >-
      Confirm H-226 only when every exceptional structure is forced with each
      geometric step replayed exactly; kill the proof strategy as stated when a
      structure leaves at most four charges on every wall line with no forced
      partial-box point; a failed replay at the printed constants stops the lane.
    reason: >-
      The registered proof strategy cannot close n=21: 3,461 D2-orbits of exceptional structures (for example red (1, 9/10) uncovered with blue (1/2, 9/10) and (9/2, 9/10) uncovered) leave at most four charging boxes on each vertical wall line with no confined partial box, and the paper's toolkit has no further move or contradiction to apply; s(21) = 5 itself is untouched, and the 22,603 needs-geometry orbits name the claim Q(i, j) a stronger lemma would need.
---
# Exp-216: Theorem 11 Replay and the One-Spare Inventory at n=21

The first round of [H-226](../../../hypotheses/H-226-n21-one-spare-wall-charge-lemma.md)
under [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-362.
The mathematical lane’s scratch numbers become evidence only through the ported tool’s
run recorded here and the independent Fable review of its model.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
