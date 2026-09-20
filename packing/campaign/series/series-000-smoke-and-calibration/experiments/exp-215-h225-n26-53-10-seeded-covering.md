---
title: exp-215 — window-seeded point covering at n=26, 53/10
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-215
  series: series-000
  title: Window-seeded point covering at n=26, 53/10
  date: '2026-09-20'
  hypotheses: [H-225]
  tier: confirmatory
  subject:
    label: >-
      Restricted covering optimum at n=26, side 53/10, B = 9977/10000,
      181-direction net, on auto grids plus a 5-per-window ceiling lattice with a
      3600 s deadline; freeze-then-decide on convergence below 26
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 144; project Python 3.14.7; four CPUs
  instance: {axis: n, point: 26, role: target}
  method:
    control: >-
      Nagamochi's verified floor 5 at n=26 (E-nagamochi-lower) and Session 141's
      unseeded exp-169 probe at 513/100, which plateaued at the exact-integer
      artefact 25.000000 with rows still violated
    candidate: >-
      Auto grids plus windows 5 at 53/10 with support cap 32 and a 3600 s deadline;
      RETAINABLE below 26 confirms H-225 and registers s(26) >= 53/10
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-144 Opus runner
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 26 --side 53/10 --shrink 9977/10000 --direction-steps 181
      --grid-counts auto --seed-windows 5 --support-cap 32 --column-rounds 1
      --max-rounds 80 --deadline-seconds 3600 --scale 4000000
      --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-covering.json
      --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-family.json
      --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-run.json
      --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-rows.jsonl
      --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10.log
    budget: One run of at most 3600 s and the gate; Session 144 wall; one site set under this id.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  lease:
    expires: '2026-09-20T09:30:00Z'
    host: claude-session-144
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-225 only on RETAINABLE below 26 from both decide_certificate routes;
      an unfinished loop or a converged value at or above 26 is unresolved for the
      claim and refutes this site set only.
    reason: Registered before the run; no number yet.
---
# Exp-215: Window-Seeded Point Covering at n=26, 53/10

The first round of [H-225](../../../hypotheses/H-225-n26-seeded-certificate-at-53-10.md)
under [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-361.
The one chunk-1 item that can move a floor.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
