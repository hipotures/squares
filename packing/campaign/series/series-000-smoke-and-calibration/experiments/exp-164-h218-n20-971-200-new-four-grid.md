---
title: exp-164 — T-021 four-grid plus windows 7 at n=20 971/200
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-164
  series: series-000
  title: T-021 four-grid plus windows 7 at n=20 971/200
  date: '2026-09-19'
  hypotheses: [H-218]
  tier: exploratory
  subject:
    label: >-
      Restricted covering optima at n=20 on the 181-direction net at B = 9977/10000,
      at side 971/200, on the T-021 four-grid (34, 46, 56, 64) plus windows 7
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate
    assurance: verified
    method: exact-algebraic
    host_system: Cursor cloud agent; project Python 3.14; no packing-campaign runner
  instance: {axis: n, point: 20, role: target}
  method:
    control: >-
      Standing verified floor T-021 97/20 and the covering-values rows already
      recorded at n=20, including leftover auto plus windows 6 at 971/200
      (19.910044 unconverged) and four-grid plus windows 7 at 973/200 (19.939212)
    candidate: >-
      T-021 certificate seed plus four-grid 34,46,56,64 and windows 7 at 971/200,
      then freeze-then-decide if the row loop converges below 20
    runs_per_condition: 1
    interleaved: false
    operator: Cursor session-141
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 20 --side 971/200 --shrink 9977/10000 --direction-steps 181
      --grid-counts 34,46,56,64 --seed-windows 7
      --seed-certificate cases/n20_fractional_certificate/certificate.json
      --seed-map scale --support-cap 32 --column-rounds 1 --max-rounds 60
      --deadline-seconds 2400 --scale 4000000
      --freeze results/agenda-039/n20-971-200-t021-grid4-windows7-certificate.json
      --json results/agenda-039/n20-971-200-t021-grid4-windows7-run.json
    budget: >-
      Session-141 research wall to 2026-09-19T15:26:00Z. This named site set only.
      Do not replay leftover auto plus windows 6 at 971/200 or four-grid plus
      windows 7 at 973/200.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/
  lease:
    expires: '2026-09-19T16:06:00Z'
    host: cursor-cloud-session-141
  results:
  - shape: determination
    role: outcome
    question: >-
      Does a T-021 four-grid plus windows-7 freeze at 971/200 have mass strictly
      below 20 and print RETAINABLE?
    outcome: invalid
    checked_by: Not yet measured; the round is claimed.
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-218 only when decide_certificate prints RETAINABLE on a freeze with
      mass < 20 at a side above T-021
    reason: Claimed; n=20 971/200 new four-grid is the first Session-141 H-218 probe.
---
# Exp-164: H-218 Reopen on a New n=20 Site Set

This is the Session-141 reopen of
[H-218](../../../hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md).
exp-162 is abandoned. The leftover auto plus windows 6 construction at `971/200`
finished at `19.910044` unconverged; remaining rows raise. This round uses a
different named set: T-021 four-grid `(34, 46, 56, 64)` plus windows 7.

Confirm only on `RETAINABLE`. n=18 T-029 does not confirm H-218.

exp-161 is not this round. Do not `--search`. Do not mutate T-025 or T-026
`verify_claim.py`. Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or
`think-jwb1`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
