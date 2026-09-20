---
title: exp-214 — window-seeded point covering at n=13, 399/100
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-214
  series: series-000
  title: Window-seeded point covering at n=13, 399/100
  date: '2026-09-20'
  hypotheses: [H-223]
  tier: confirmatory
  subject:
    label: >-
      Restricted covering optimum at n=13, side 399/100, B = 9977/10000,
      181-direction net, on auto grids plus a 5-per-window ceiling lattice;
      freeze-then-decide on convergence below 13, freeze-family otherwise
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate; on a value at
      or above 13, polish_ceiling_family and both ceiling readers
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 144; project Python 3.14.7; four CPUs
  instance: {axis: n, point: 13, role: calibration}
  method:
    control: >-
      Bentz 2010's s(13) = 4 (T-006) and the shrunk grid ceiling 3.9908 at this B and
      net; no covering value at n=13 is on the register
    candidate: >-
      Auto grids plus windows 5 at 399/100; RETAINABLE below 13 confirms H-223; a
      depth-one family of total at least 13 accepted by both readers refutes it at
      this scope
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-144 Opus runner
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 13 --side 399/100 --shrink 9977/10000 --direction-steps 181
      --grid-counts auto --seed-windows 5 --support-cap 0 --column-rounds 1
      --max-rounds 60 --deadline-seconds 2400 --scale 4000000
      --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-covering.json
      --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-family.json
      --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-run.json
      --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-rows.jsonl
      --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100.log
    budget: One run of at most 2400 s and the gate or the readers; Session 144 wall.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  lease:
    expires: '2026-09-20T09:30:00Z'
    host: claude-session-144
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-223 only on RETAINABLE below 13 from both decide_certificate routes;
      refute at this scope only with a depth-one family of total at least 13 accepted
      by both ceiling readers.
    reason: Registered before the run; no number yet.
---
# Exp-214: Window-Seeded Point Covering at n=13, 399/100

The first round of [H-223](../../../hypotheses/H-223-n13-point-covering-at-399-100.md)
under [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-361.
Calibration under a proved value: `s(13) = 4` does not move.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
