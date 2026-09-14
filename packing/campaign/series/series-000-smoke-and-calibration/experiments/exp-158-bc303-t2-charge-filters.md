---
title: exp-158 — BC303 T2 C and S first-owner charge filters
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-158
  series: series-000
  title: BC303 T2 C and S first-owner charge filters
  date: '2026-09-13'
  hypotheses: [H-160]
  tier: exploratory
  subject:
    label: Frozen BC293 377-atom measure on all eligible BC303 forced-0 source charts
    engine: Source-bound exact rational C and S first-owner event sweep
    assurance: verified
    method: exact-algebraic
    host_system: Darwin arm64; project Python 3.14
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      Before target evaluation, compare the optimized open-cell sweep to an
      independent all-strata direct reference on synthetic conditioned domains;
      cover closed atom edges and vertices, the forbidden axis edge, coincident
      events, rational wall equality, a lower-dimensional refusal, missing axis
      aliases, a changed atom row, and a wrong executing checkout revision.
      Authenticate all 377 source rows and integer weights against the reviewed
      source Git revision and identify the executing reader from its own path.
    candidate: >-
      Query C and S first-owner intervals from one exact event arrangement per
      eligible chart. Process coincident start/end events atomically before each
      open x strip. C uses its exact feasible y prefix; S uses X<x<h and the full
      y range. Retain both axis aliases and an attaining cell per minimum.
    runs_per_condition: 1
    interleaved: false
    operator: Codex BC303 T2 charge-sweep agent
    entry_point: packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      cases.n11_five_dot_cover.bc303_t2_charge_sweep run
      --expect-implementation-revision "$(git rev-parse HEAD)"
      --output campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-158-bc303-t2-charge-filters.json
    budget: >-
      One invocation, all 182 eligible source charts, with a 30-minute wall
      allowance. No partial positive verdict, early chart stop, changed source,
      threshold adjustment, or rerun under this registration.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-158-bc303-t2-charge-filters.json
  lease:
    expires: '2026-09-15T00:00:00Z'
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      C minimum >=4524200 and S first-owner minimum >=4524185 after all charts
      and source/control/revision admission.
    reason: The target charge has not run; source and adversarial controls must pass first.
---
# Exp158: Frozen Outcomes Before Target Charge

This record contains no target atom charge.
The source is the literal BC293 measure at reviewed revision
`39714308ce2081abbd76624387d134fee4be6deb`; its 377 rows, nonnegative integer weights at
scale `W=4000000`, 182 eligible source charts, and both axis aliases must be checked
before the target invocation.
The reader must identify its own checkout and full committed implementation revision.

The C determination is positive only if every feasible open cell has integer mass at
least `4524200`. A value at most `4524199` rejects C and the opposite and combined T2
helper only after exact closed membership, complete labels, and a rational physical
parent replay from the attaining cell.
An incomplete sweep is unresolved.

The S first-owner sufficient determination is positive only if every strict strip cell
has integer mass at least `4524185`; BC303’s imported coverage floor then proves the
actual S pair exceeds its threshold.
A lower strip cell rejects only this sufficient filter.
It does not reject S or T2 and becomes input to a separately registered pairing test.

Both positive determinations prove the combined local T2 surplus helper under the
accepted reduction. A C refuter rejects its opposite branch.
Neither result proves local availability in an eleven-parent packing, owner selection
into the admitted tuple family, adjacent-only T2 after an opposite rejection, or a
stronger global `s(11)` bound.
The disclosed C and S geometry fixtures are control poses, not target-blind discoveries.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
