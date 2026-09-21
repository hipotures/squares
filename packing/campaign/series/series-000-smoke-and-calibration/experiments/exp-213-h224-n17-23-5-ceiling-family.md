---
title: exp-213 — T-019-seeded ceiling family at n=17, 23/5
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-213
  series: series-000
  title: T-019-seeded ceiling family at n=17, 23/5
  date: '2026-09-20'
  hypotheses: [H-224]
  tier: confirmatory
  subject:
    label: >-
      The priced dual of the T-019-seeded column generation at n=17, side 23/5,
      B = 9977/10000, 181-direction net, polished to an exact vertex and read as a
      depth-one ceiling family
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen --freeze-family;
      devtools.polish_ceiling_family; devtools.independent_ceiling_reader;
      devtools.replay_ceiling_family --check (verify_ceiling)
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 144; project Python 3.14.7; four CPUs
  instance: {axis: n, point: 17, role: target}
  method:
    control: >-
      Session 140's T-019 four-grid plus windows 8 run at 23/5, which converged at
      17.120106 and retained no family; the H-216 n=6 recipe for polish and the two
      readers
    candidate: >-
      Freeze-family from a T-019-seeded auto plus windows 5 run at 23/5, polish to an
      exact vertex, then both readers. Confirm H-224 only when both accept maximum
      depth at most 1 and exact total at least 17.
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-144 Opus runner
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 17 --side 23/5 --shrink 9977/10000 --direction-steps 181
      --grid-counts auto --seed-windows 5
      --seed-certificate cases/n17_fractional_certificate/certificate.json
      --seed-map scale --support-cap 0 --column-rounds 1 --max-rounds 60
      --deadline-seconds 2400 --scale 4000000
      --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-213-n17-23-5-family.json
      --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-213-n17-23-5-covering.json
      --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-213-n17-23-5-run.json
      --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-213-n17-23-5-rows.jsonl
      --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-213-n17-23-5.log
    budget: >-
      One run of at most 2400 s, then polish and both readers; Session 144 wall.
      No second site set under this id.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  effort:
    timebox: 2400 s run plus polish and two readers
    wall_seconds: 1583.2
    stopped_by: error
  results:
  - shape: determination
    role: outcome
    question: >-
      Do both ceiling readers accept a polished family of maximum depth at most 1 and
      exact total at least 17 at n=17, 23/5?
    outcome: no_progress
    checked_by: >-
      The run's round 0 converged at objective 17.042346318 with least covered mass
      1.000000000 after 1583.2 s on 928 orbits over 7068 sites (row log), then the
      column round started and the process was lost when the container restarted
      before the 2400 s deadline; no run summary, freeze, or family file was written,
      so neither reader ran
  - shape: record
    role: outcome
    metric: restricted covering optimum at round 0 (float LP objective; not a bound)
    direction: lower
    score: 17.042346318
    standing_best: 17
    standing_best_source: H-224 criterion (a certificate needs mass strictly below 17)
    beat_record: false
    runs: 1
  verdict:
    decision: unresolved
    primary_criterion: >-
      Confirm H-224 only when independent_ceiling_reader and verify_ceiling both
      accept a family with maximum depth at most 1 and exact total at least 17;
      a covering freeze of mass below 17 accepted by both decide_certificate routes
      kills it and registers a rung; anything else is unresolved.
    reason: >-
      The restricted optimum on this site set sat above 17 at round 0, which refutes point certificates on this site set only, and the priced dual was never frozen because the container restarted mid-run, so no ceiling family exists to read; H-224 is undecided in both directions. Resume needs a new experiment id with a support cap, since keeping every dual row spent 1583 s on round 0 alone.
---
# Exp-213: T-019-Seeded Ceiling Family at n=17, 23/5

The first round of [H-224](../../../hypotheses/H-224-n17-ceiling-family-at-23-5.md),
registered by [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md)
BC-361 before any target ran.
A confirmed family closes the fixed-shrink point route at n=17 from `23/5` for every
site set; it moves no bound.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
