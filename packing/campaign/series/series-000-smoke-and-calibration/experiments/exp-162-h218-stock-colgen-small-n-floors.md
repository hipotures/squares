---
title: exp-162 — stock colgen on the X-038 first-wave floors
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-162
  series: series-000
  title: Stock colgen on the X-038 first-wave floors
  date: '2026-09-19'
  hypotheses: [H-218]
  tier: exploratory
  subject:
    label: >-
      Restricted covering optima at n in {12, 17, 19, 20} on the 181-direction net at
      B = 9977/10000, at sides strictly above the current verified floors, on named
      site sets built by run_fractional_colgen
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate
    assurance: verified
    method: exact-algebraic
    host_system: Cursor cloud agent; project Python 3.14; no packing-campaign runner
  instance: {axis: n, point: 20, role: target}
  method:
    control: >-
      Standing verified floors T-017 99/25, T-019 459/100, T-020 24/5, T-021 97/20,
      and the covering-values rows already recorded for those n. H-062's wall at
      973/200 binds only the auto-grid and 97/20-seed constructions it named.
    candidate: >-
      New named site sets on the ranked sides in X-038: certificate seed plus a
      four-grid and/or --seed-windows, then freeze-then-decide if the row loop
      converges below n
    runs_per_condition: 1
    interleaved: false
    operator: Cursor session-140
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n N --side SIDE --shrink 9977/10000 --direction-steps 181 --grid-counts COUNTS
      --seed-windows W --seed-certificate CERT --seed-map scale --support-cap 32
      --column-rounds 1 --max-rounds 60 --deadline-seconds 1200 --scale 4000000
      --freeze results/agenda-038/...-certificate.json
      --json results/agenda-038/...-run.json
    budget: >-
      Session-140 research wall to 2026-09-19T06:42:00Z. One probe family per ranked
      n. No second attempt at a (n, side, site_set) already on covering-values.yaml.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
  lease:
    expires: '2026-09-19T07:02:00Z'
    host: cursor
    pid: 486108
  results:
  - shape: determination
    role: outcome
    question: >-
      Does any first-wave freeze have mass strictly below n at a side above the current
      verified floor and print RETAINABLE?
    outcome: no_progress
    checked_by: >-
      Round in progress; no freeze has been offered to decide_certificate under
      session-140
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-218 only when decide_certificate prints RETAINABLE on a freeze with
      mass < n at a side above the current floor for some n in {12, 17, 19, 20}
    reason: >-
      X-038 and the ranked queue are registered. The first probes have not finished.
    resume_from: >-
      Rank 5: n=18 at 4675/1000 with T-027 seed, auto grids, and windows 5.
      Then the n=20 2400 s follow-up and n=21 at 97/20. n=12, n=17, and n=19
      named first-wave site sets finished above n.
---
# Exp-162: First-Wave Stock Colgen

This is the first scientific round of
[H-218](../../../hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md).
[X-038](../../../explorations/X-038-n100-lower-bound-survey.md) ranks the sides.
[Session 140](../../../agent-sessions/session-140-lb-survey.md) owns the clock.

The accept rule is the gate, not the float LP. A restricted optimum above `n` is a
site-set negative and is recorded on `covering-values.yaml`. T-028 is landed only on
`RETAINABLE`.

exp-161 is not this round. Do not `--search`. Do not mutate T-025 or T-026
`verify_claim.py`. Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or
`think-jwb1`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
