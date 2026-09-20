---
title: exp-219 — the all-free corner class at n=11, 96/25, on the corner-clipped domain
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-219
  series: series-000
  title: The all-free corner class at n=11, 96/25, on the corner-clipped domain
  date: '2026-09-20'
  hypotheses: [H-222]
  tier: confirmatory
  subject:
    label: >-
      Restricted covering optimum at n=11, side 96/25, B = 9977/10000, the 181
      half-tangent folded net (direction_steps 180), on auto grids plus a 5-per-window
      lattice, with every core meeting a corner triangle x + y <= 1/2 (or a D4 image)
      removed from the row domain by the admitted convex corner clip; freeze-then-decide
      under the corner class hypothesis, and freeze-family for the ceiling readers
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen --corner-clip 1/2;
      declare_least_cell_mass; both routes of decide_certificate --corner-clip 1/2;
      polish_ceiling_family, independent_ceiling_reader --corner-clip 1/2 and
      replay_ceiling_family --corner-clip 1/2 (condition K4)
    assurance: verified
    method: exact-algebraic
    host_system: Claude cloud session 145; project Python 3.14.7; four CPUs
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      The retained 88-family transported to 96/25 keeps mass exactly 7 on the clipped
      domain (K4 false, residual kept 7 removed 4), reproduced by the instrument's
      test, by verify_ceiling, and by the stdlib-only independent reader; the
      unclipped run at the same site set is the byte-for-byte baseline
    candidate: >-
      The clipped covering at 96/25. Confirm H-222 only when decide_certificate
      --corner-clip 1/2 prints RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS on a freeze
      of mass strictly below 11. Kill with a polished depth-one family that both readers
      accept with K4 true and exact total at least 11.
    runs_per_condition: 1
    interleaved: false
    operator: Claude session-145 coordinator
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 11 --side 96/25 --shrink 9977/10000 --direction-steps 180 --corner-clip 1/2
      --grid-counts auto --seed-windows 5 --support-cap 32 --column-rounds 1
      --max-rounds 60 --deadline-seconds 2400 --scale 4000000 --verify-serial
      --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip-covering.json
      --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip-family.json
      --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip-run.json
      --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip-rows.jsonl
      --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip.log
    budget: One run of at most 2400 s, then the gate or the readers; Session 145 wall.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/
  lease:
    expires: '2026-09-20T14:00:00Z'
    host: claude-session-145
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-222 only on RETAINABLE UNDER THE CORNER CLASS HYPOTHESIS from both
      routes on a freeze below 11; kill only with a K4-accepted depth-one family of
      total at least 11 on the clipped domain; a converged value at or above 11 refutes
      this site set only.
    reason: Registered before the run, after the Fable review admitted the instrument.
---
# Exp-219: The All-Free Corner Class at n=11, 96/25

The first round of [H-222](../../../hypotheses/H-222-n11-octagon-class-at-96-25.md)
under [agenda-040](../../../agendas/agenda-040-overnight-lower-bound-loop.md) BC-363, on
the convex corner-clip instrument admitted by the Session 145 review.
A confirm is a conditional exclusion at `3.84` for the octagon class only.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
