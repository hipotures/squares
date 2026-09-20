---
title: exp-171 — seedless auto plus windows 5 at n=29 548/100
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-171
  series: series-000
  title: Seedless auto plus windows 5 at n=29 548/100
  date: '2026-09-19'
  hypotheses: [H-220]
  tier: exploratory
  subject:
    label: >-
      Restricted covering optima at n=29 on the 182-direction net from 181 steps at B = 9977/10000,
      at side 548/100, on auto grids plus windows 5 with no certificate seed
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate
    assurance: numerically-checked
    method: numerical-f64
    precision:
      binary_bits: 64
      rounding: IEEE 754 binary64 in NumPy and SciPy HiGHS
    tolerance: >-
      Row addition used 1e-9; convergence also accepts an already-held row within
      LP_FEASIBILITY = 1e-7. The floating restricted optimum is not an exact optimum.
    migration_annotation: >-
      2026-09-19 correctness review: the subject is the numerical restricted optimum.
      The separate frozen rational candidate passes exact verification, but its
      interval route remains unresolved and it has not been retained.
    host_system: Cursor cloud agent; project Python 3.14; no packing-campaign runner
  instance: {axis: n, point: 29, role: target}
  method:
    control: >-
      Nagamochi-only floor at n=29 (1 + sqrt(20) ≈ 5.47213595499) and no
      first-party covering rows recorded at this n. H-218 n=20 four-grid probes
      do not apply.
    candidate: >-
      Stock colgen with auto grids and windows 5 at 548/100, no --seed-certificate,
      then freeze-then-decide if the row loop converges below 29
    runs_per_condition: 1
    interleaved: false
    operator: Cursor session-141
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 29 --side 548/100 --shrink 9977/10000 --direction-steps 181
      --grid-counts auto --seed-windows 5
      --support-cap 32 --column-rounds 1 --max-rounds 60
      --deadline-seconds 1200 --scale 4000000
      --freeze results/agenda-039/n29-548-100-auto-windows5-certificate.json
      --json results/agenda-039/n29-548-100-auto-windows5-run.json
    budget: >-
      Session-141 research wall to 2026-09-19T15:26:00Z. Sixth H-220 probe only.
      Starts after the 11:26Z W5 resume. Do not replay n=32 29/5, n=31 57/10,
      n=30 559/100, n=26 513/100, or n=27 525/100 auto plus windows 5.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/
  results:
  - shape: determination
    role: outcome
    question: >-
      Does a seedless auto plus windows-5 freeze at 548/100 have mass strictly below 29
      and print RETAINABLE?
    outcome: no_progress
    checked_by: >-
      Covering converged at 26.040745 with freeze mass 52081879/2000000 = 26.0409395
      and 1329 atoms. declare_least_cell_mass accepted least 4000013/4000000.
      decide_certificate refused the interval route: Condition 5, 272 stalled boxes,
      enclosure (398409/400000, 4000013/4000000). Not RETAINABLE.
  verdict:
    decision: unresolved
    primary_criterion: >-
      Confirm H-220 only when decide_certificate prints RETAINABLE on a freeze with
      mass < 29 at a side strictly above the Nagamochi floor
    reason: >-
      Seedless auto plus windows 5 at 548/100 converged below 29 and froze, but
      the interval route stalled on 272 boxes. That leaves verification unresolved;
      it does not refute the candidate or its site set. T-030 was not offered.
      H-220 stays unconfirmed.
    budget_spent: Covering 1068.7 s, declare 45 s, decide 66 s on one core.
    best_reached: freeze mass 26.0409395; interval refused
    resume_from: >-
      Keep the existing rational freeze for a future verification budget; no new
      LP is needed to retry its interval route. Session-141 deferred it and moved
      to exp-172 at n=45 684/100.
  effort:
    timebox: Session-141 n=29 548/100 seedless auto plus windows 5
    wall_seconds: 1180
    stopped_by: guard
---
# Exp-171: H-220 Sixth Nagamochi Probe

This is the sixth scientific round of
[H-220](../../../hypotheses/H-220-seedless-colgen-raises-nagamochi-floor.md), after
[exp-170](exp-170-h220-n27-525-100-seedless-auto-windows5.md) stopped at `25.000000`
unconverged below 27.

Auto resolved to `(39, 53, 65)`. The row loop converged at `26.040745` with freeze mass
`52081879/2000000`. `decide_certificate` refused the interval route.
T-030 was not offered.
The follow-up is exp-172 at n=45 `684/100`.

Confirm only on `RETAINABLE`. There is no n=29 case package.

Correctness review (2026-09-19): the fresh exact route accepts the frozen candidate with
least covered mass `4000013/4000000`. The historical interval run still leaves 272 boxes
unresolved. This is not a site-set refutation and does not satisfy the two-route
retention rule. The numerical restricted optimum and exact frozen mass have different
assurance levels; the subject label above describes the former.

exp-161 is not this round.
Do not `--search`. Do not mutate T-025 or T-026 `verify_claim.py`. Do not close
`think-qqzs`, `think-g3j7`, `think-gyzw`, or `think-jwb1`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
