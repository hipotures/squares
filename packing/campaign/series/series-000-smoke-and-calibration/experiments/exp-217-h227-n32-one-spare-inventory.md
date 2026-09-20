---
title: exp-217 — the one-spare structure inventory at n=32
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-217
  series: series-000
  title: The one-spare structure inventory at n=32
  date: '2026-09-20'
  hypotheses: [H-227]
  tier: confirmatory
  subject:
    label: >-
      The complete enumeration of exceptional structures for 32 boxes against Bentz
      2016's m = 6 red and blue configurations (one spare per colour), classified
      under Theorem 9's vertical row moves with the frozen-row budget
    engine: >-
      devtools.bentz2016.one_spare_inventory --n 32, ported from the Session 144
      mathematical lane's m6 model under OR-1; exact and 50-digit difference
      constraints
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 144; project Python 3.14.7
  instance: {axis: n, point: 32, role: target}
  method:
    control: >-
      The zero-spare n=33 case must be reported forced on both lines, reproducing
      Theorem 9; the Theorem 9 budget 2(sqrt 2 - 1/2) + 1.6 + 3 sqrt 3 / 2 = 6.0265
      at the printed constant (D-507)
    candidate: >-
      The n=32 inventory. Confirm H-227 only if every structure is forced; a
      structure with at most five charging boxes on every wall line and no forced
      partial-box point is H-227's registered kill for the proof strategy as stated.
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-144 (Fable lane, Opus port, Fable review)
    entry_point: packing/devtools/bentz2016/one_spare_inventory.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.bentz2016.one_spare_inventory --n 32 --json
      campaign/series/series-000-smoke-and-calibration/results/agenda-040/one-spare-inventory-n32.json
    budget: Runs beside exp-216 on the same tool; minutes.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  effort:
    timebox: Runs beside exp-216 on the same tool
    wall_seconds: 16
    stopped_by: criterion
  results:
  - shape: determination
    role: outcome
    question: >-
      Does every exceptional structure at n=32 force six charging boxes on some wall
      line under Theorem 9's vertical moves with the frozen-row budget?
    outcome: criterion_missed
    checked_by: >-
      devtools.bentz2016.one_spare_inventory --n 32: 12,100 raw pairs, 4,146 orbits at
      the record's decimal keys (3,089 at exact integer keys), 401 raw forced (352
      Theorem 8, 49 six distinct full), 11,699 raw kill, 0 needs-geometry; the
      zero-spare n=33 control is forced on both lines; the Fable review reproduced the
      survival table and the 0.0265 budget (receipt bentz2016-one-spare-receipt.md)
  - shape: record
    role: outcome
    metric: raw kill pairs at n=32 (wall-line count alone; the merge propagation is not carried by the m=6 model)
    direction: lower
    score: 11699
    standing_best: 0
    standing_best_source: H-227 criterion (confirm needs every structure forced)
    beat_record: false
    runs: 1
  verdict:
    decision: rejected
    primary_criterion: >-
      Confirm H-227 only when every exceptional structure is forced; kill the proof
      strategy as stated when a structure leaves at most five charges on every wall
      line with no forced partial-box point.
    reason: >-
      With the m=6 vertical budget 2(sqrt 2 - 1/2) + 1.6 + 3 sqrt 3 / 2 - 6 = 0.0265, any frozen row above a six-point row kills that row's shift and end-point move, so every structure whose red spare lies outside red row 1 or blue spare outside blue row 6 leaves at most five charges on every wall line and no shorter slide recovers a sixth; s(32) = 6 itself is untouched.
---
# Exp-217: The One-Spare Inventory at n=32

The first round of [H-227](../../../hypotheses/H-227-n32-one-spare-wall-charge-lemma.md)
under [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-362, on
the same tool as exp-216.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
