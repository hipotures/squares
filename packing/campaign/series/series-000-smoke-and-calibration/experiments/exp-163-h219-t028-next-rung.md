---
title: exp-163 — T-028-seeded colgen at n=18 1871/400
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-163
  series: series-000
  title: T-028-seeded colgen at n=18 1871/400
  date: '2026-09-19'
  hypotheses: [H-219]
  tier: exploratory
  subject:
    label: >-
      Restricted covering optima at n=18 on the 181-direction net at B = 9977/10000,
      at sides in (187/40, 117/25), on named site sets seeded from T-028
    engine: >-
      sqpack.fractional.colgen through devtools.run_fractional_colgen; retain by
      declare_least_cell_mass then both routes of decide_certificate
    assurance: verified
    method: exact-algebraic
    host_system: Cursor cloud agent; project Python 3.14; no packing-campaign runner
  instance: {axis: n, point: 18, role: target}
  method:
    control: >-
      Standing verified floor T-028 187/40 and the covering-values rows already
      recorded at n=18, including the 117/25 plateau at 18.000000
    candidate: >-
      T-028 certificate seed plus auto grids and windows 5 at 1871/400, then
      freeze-then-decide if the row loop converges below 18
    runs_per_condition: 1
    interleaved: false
    operator: Cursor session-141
    entry_point: packing/devtools/run_fractional_colgen.py
    command: >-
      cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run
      --frozen --all-extras --group dev python -m devtools.run_fractional_colgen
      --n 18 --side 1871/400 --shrink 9977/10000 --direction-steps 181
      --grid-counts auto --seed-windows 5
      --seed-certificate cases/n18_fractional_certificate/certificate.json
      --seed-map scale --support-cap 32 --column-rounds 1 --max-rounds 60
      --deadline-seconds 1200 --scale 4000000
      --freeze results/agenda-039/n18-1871-400-t028-auto-windows5-certificate.json
      --json results/agenda-039/n18-1871-400-t028-auto-windows5-run.json
    budget: >-
      Session-141 research wall to 2026-09-19T15:26:00Z. First probe family only.
      No second attempt at a (n, side, site_set) already on covering-values.yaml.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/
  lease:
    expires: '2026-09-19T16:06:00Z'
    host: cursor-cloud-session-141
  results:
  - shape: determination
    role: outcome
    question: >-
      Does a T-028-seeded freeze at a side in (187/40, 117/25) have mass strictly
      below 18 and print RETAINABLE?
    outcome: invalid
    checked_by: Not yet measured; the round is claimed.
  verdict:
    decision: in-progress
    primary_criterion: >-
      Confirm H-219 only when decide_certificate prints RETAINABLE on a freeze with
      mass < 18 at a side in (187/40, 117/25)
    reason: Claimed; leftover n=18 1871/400 is the first Session-141 probe.
---
# Exp-163: Next Rung Above T-028

This is the first scientific round of
[H-219](../../../hypotheses/H-219-t028-seeded-colgen-raises-s18.md).
[X-039](../../../explorations/X-039-n100-re-rank-after-session-140.md) ranks the side.
[Session 141](../../../agent-sessions/session-141-n100-research.md) owns the clock.

The accept rule is the gate, not the float LP. A restricted optimum above 18 is a
site-set negative and is recorded on `covering-values.yaml`. The next T-id is landed
only on `RETAINABLE`. That retain does not confirm H-218.

exp-161 is not this round. Do not `--search`. Do not mutate T-025 or T-026
`verify_claim.py`. Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or
`think-jwb1`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
