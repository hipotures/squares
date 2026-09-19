---
title: session-140 — n<=100 lower-bound survey
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-140
  title: N<=100 Lower-Bound Survey
  date: '2026-09-19'
  started_at: '2026-09-19T02:42:00Z'
  deadline_at: '2026-09-19T07:02:00Z'
  branch: cursor/lb-survey-stacked-f02a
  primary_bead: think-8x4t
  status: in_progress
  goal: >-
    Survey every n<=100 verified lower bound, rank which open floors the stock colgen
    can still raise, and run that queue for at least four hours on a stacked PR.
    Land T-028 only if decide_certificate prints RETAINABLE.
  workflow_phases:
  - workflow: review-planning-oversight
    focus: process
    recording: contemporaneous
    clock_role: work
    bead: think-u5tk
    objective: >-
      Write X-038, register H-218 and exp-162, file the probe beads, and open the
      stacked PR off the session-139 branch.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 20
    started_at: '2026-09-19T02:42:00Z'
    deadline_at: '2026-09-19T03:02:00Z'
    expected_output: >-
      X-038, H-218, exp-162 with a live lease, session-140, beads under think-8x4t,
      and a draft stacked PR.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check &&
      uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      Stop planning at 03:02Z even if the PR is still drafting. Do not start a
      covering LP before X-038 names the ranked queue.
    fallback: Keep the survey and beads and start the research phase on the first rank.
    outcome: >-
      X-038 ranks n=20 at 973/200, then n=12 at 397/100, n=17 at 23/5, n=19 at
      481/100. H-218 and exp-162 are registered. Parent bead think-8x4t.
    evidence:
      - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
      - packing/campaign/hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-162-h218-stock-colgen-small-n-floors.md
    stop_reason: Planning artifacts written; research phase opened.
    next_action: Run the X-038 ranked covering queue under phase 2.
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    bead: think-8x4t
    objective: >-
      Run the X-038 first-wave probes. Record every restricted optimum. Freeze and
      decide only when mass is below n. Land T-028 only on RETAINABLE.
    status: in_progress
    entered_by: planned_checkpoint
    switch_reason: Planning artifacts and beads are in the tree.
    budget_minutes: 238
    started_at: '2026-09-19T02:44:00Z'
    deadline_at: '2026-09-19T06:42:00Z'
    expected_output: >-
      Covering receipts under agenda-038, covering-values rows for every finished
      probe, and a T-028 landing only if the gate accepts.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check &&
      uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      Stop new probes at 06:42Z. Do not --search. Do not close think-qqzs,
      think-g3j7, think-gyzw, or think-jwb1. Do not land a non-retainable freeze.
    fallback: Keep the survey, the finished covering rows, and an unresolved exp-162.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: >-
      Rank 1 n=20 at 973/200, then n=12 at 397/100. T-028 only if RETAINABLE.
  budget:
    wall_minutes: 260
    max_cycles: 2
    orientation_minutes: 20
    checkpoint_minutes: 60
    slice_minutes: 40
    finalization_minutes: 20
  stop_conditions:
  - Close by 2026-09-19T07:02:00Z with records and a reviewable stacked PR.
  - Do not close think-qqzs, think-g3j7, think-gyzw, or think-jwb1.
  - Do not allocate exp-161 to this session; do not --search.
  - Do not mutate T-025 or T-026 verify_claim.py.
  - Do not change accept rules, thresholds, or metrics.
  - packing-campaign numeric unattended remains NO-GO.
  - T-028 only if decide_certificate prints RETAINABLE.
  - n=11 stays T-026; H-216 is not an n=11 result.
  progress:
    metric: >-
      Open n<=100 floors ranked, and first-wave covering rows recorded; a verified
      floor moves only on RETAINABLE
    before: >-
      Session-139 closed with T-027 at n=18. Covering register has rows at n=6, 11,
      12, 17, 18, 19, 20, 21. No n<=100 survey. T-028 not landed.
    after: null
  delegations:
  - task: Extract n<=100 verified gaps and covering surplus
    operator: session-140 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      32 proved, 68 open. First-wave ranks n=20 at 973/200, n=12 at 397/100, n=17 at
      23/5, n=19 at 481/100.
    evidence:
      - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
    files:
      - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
    checks:
      - >-
        uv run --frozen python extract of frontier n-001..n-100 verified bounds
        against covering-values.yaml
    uncertainty: >-
      Reported uppers (n=17 at 4.675) are not verified ceilings and do not decide
      the remaining window.
    elapsed_seconds: 480
    elapsed_quality: operator_reported_approximate
    next_action: Run rank 1.
    phase: 1
    budget_minutes: 15
    started_at: '2026-09-19T02:42:00Z'
    deadline_at: '2026-09-19T02:57:00Z'
  - task: n=20 973/200 four-grid plus windows 7
    operator: session-140 covering lane
    status: completed
    recording: contemporaneous
    outcome: >-
      Unconverged 19.930198 after 34 LP rounds, 492 still violated, no crossing.
      Not a freeze. T-021 unchanged.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n20-973-200-t021-grid4-windows7-receipt.md
    files:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n20-973-200-t021-grid4-windows7-run.json
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n20-973-200-t021-grid4-windows7-receipt.md
    checks:
      - run JSON objective 19.930197728018545; no freeze file
    uncertainty: >-
      Remaining rows can only raise the restricted optimum, so this is not a
      covering below 20.
    elapsed_seconds: 1212
    elapsed_quality: platform_measured
    next_action: Leave think-d2ad open for a longer wall or denser set.
    phase: 2
    budget_minutes: 40
    started_at: '2026-09-19T02:45:23Z'
    deadline_at: '2026-09-19T03:05:23Z'
    expected_output: >-
      agenda-038 n=20 973/200 four-grid plus windows 7 run JSON, log, and a receipt
      if the loop stops.
    validation_command: >-
      test -f packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n20-973-200-t021-grid4-windows7-run.json
    kill_condition: Stop at 1200 s or when the row loop converges.
    fallback: Record the restricted optimum and take rank 2.
    write_scope:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
    excluded_commands:
      - packing-campaign
  - task: n=12 397/100 four-grid plus windows 7
    operator: session-140 covering lane
    status: completed
    recording: contemporaneous
    outcome: >-
      Converged 12.133391; freeze mass 48534459/4000000. Site set refuted. No
      retain.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n12-397-100-t017-grid4-windows7-receipt.md
    files:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n12-397-100-t017-grid4-windows7-run.json
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n12-397-100-t017-grid4-windows7-receipt.md
    checks:
      - run JSON converged true; total_mass 48534459/4000000; decide_certificate not run
    uncertainty: Adding sites can still lower the covering value at 397/100.
    elapsed_seconds: 1079
    elapsed_quality: platform_measured
    next_action: Leave think-h02v open for a different site set; n=17 is next.
    phase: 2
    budget_minutes: 40
    started_at: '2026-09-19T03:06:01Z'
    deadline_at: '2026-09-19T03:26:01Z'
    expected_output: >-
      agenda-038 n=12 397/100 four-grid plus windows 7 run JSON and a receipt
      if the loop stops.
    validation_command: >-
      test -f packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n12-397-100-t017-grid4-windows7-run.json
    kill_condition: Stop at 1200 s or when the row loop converges.
    fallback: Record the restricted optimum and take rank 3.
    write_scope:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
    excluded_commands:
      - packing-campaign
  - task: n=17 23/5 four-grid plus windows 8
    operator: session-140 covering lane
    status: completed
    recording: contemporaneous
    outcome: >-
      Unconverged 17.120106 after 46 LP rounds, 237 still violated, crossed 17 at
      round 19. Worse than session-139 windows 5 at 17.042346. No freeze. T-019
      unchanged.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n17-23-5-t019-grid4-windows8-receipt.md
    files:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n17-23-5-t019-grid4-windows8-run.json
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n17-23-5-t019-grid4-windows8-receipt.md
    checks:
      - run JSON objective 17.12010567113054; no freeze file
    uncertainty: >-
      Remaining rows can only raise the restricted optimum, so this is not a
      covering below 17.
    elapsed_seconds: 1216
    elapsed_quality: platform_measured
    next_action: Leave think-5q81 open for a different site set; n=19 is next.
    phase: 2
    budget_minutes: 40
    started_at: '2026-09-19T03:24:40Z'
    deadline_at: '2026-09-19T03:44:40Z'
    expected_output: >-
      agenda-038 n=17 23/5 four-grid plus windows 8 run JSON and a receipt if
      the loop stops.
    validation_command: >-
      test -f packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n17-23-5-t019-grid4-windows8-run.json
    kill_condition: Stop at 1200 s or when the row loop converges.
    fallback: Record the restricted optimum and take rank 4.
    write_scope:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
    excluded_commands:
      - packing-campaign
  - task: n=19 481/100 T-020 auto plus windows 6
    operator: session-140 covering lane
    status: completed
    recording: contemporaneous
    outcome: >-
      Unconverged 19.132115 after 37 LP rounds, 333 still violated, crossed 19 at
      round 16. Closer than 97/20 at 19.808958. No freeze. T-020 unchanged.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n19-481-100-t020-auto-windows6-receipt.md
    files:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n19-481-100-t020-auto-windows6-run.json
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n19-481-100-t020-auto-windows6-receipt.md
    checks:
      - run JSON objective 19.132114728968762; no freeze file
    uncertainty: >-
      Remaining rows can only raise the restricted optimum, so this is not a
      covering below 19.
    elapsed_seconds: 1227
    elapsed_quality: platform_measured
    next_action: Leave think-zoq4 open for more wall or 97/20; n=18 is next.
    phase: 2
    budget_minutes: 40
    started_at: '2026-09-19T03:44:56Z'
    deadline_at: '2026-09-19T04:04:56Z'
    expected_output: >-
      agenda-038 n=19 481/100 T-020 auto plus windows 6 run JSON and a receipt if
      the loop stops.
    validation_command: >-
      test -f packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n19-481-100-t020-auto-windows6-run.json
    kill_condition: Stop at 1200 s or when the row loop converges.
    fallback: Record the restricted optimum and take rank 5.
    write_scope:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
    excluded_commands:
      - packing-campaign
  - task: n=18 4675/1000 T-027 auto plus windows 5
    operator: session-140 covering lane
    status: in_progress
    recording: contemporaneous
    outcome: null
    evidence: null
    files: null
    checks: null
    uncertainty: null
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Finish the named site set under think-15qo.
    phase: 2
    budget_minutes: 40
    started_at: '2026-09-19T04:05:23Z'
    deadline_at: '2026-09-19T04:25:23Z'
    expected_output: >-
      agenda-038 n=18 4675/1000 T-027 auto plus windows 5 run JSON and a receipt
      if the loop stops.
    validation_command: >-
      test -f packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n18-4675-1000-t027-auto-windows5-run.json
    kill_condition: Stop at 1200 s or when the row loop converges.
    fallback: Record the restricted optimum and take the n=20 longer wall.
    write_scope:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/
    excluded_commands:
      - packing-campaign
  outputs:
  - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
  - packing/campaign/hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md
  - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-162-h218-stock-colgen-small-n-floors.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n20-973-200-t021-grid4-windows7-receipt.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n12-397-100-t017-grid4-windows7-receipt.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n17-23-5-t019-grid4-windows8-receipt.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/n19-481-100-t020-auto-windows6-receipt.md
  checks:
  - Planning artifacts written; research phase open.
  - >-
    n=20 973/200 four-grid plus windows 7 stopped at 19.930198 unconverged, no
    freeze. n=12 397/100 converged at 12.133391, freeze above 12, no retain.
    n=17 23/5 four-grid plus windows 8 stopped at 17.120106 unconverged, no
    freeze. n=19 481/100 T-020 auto plus windows 6 stopped at 19.132115
    unconverged, no freeze; new covering side 4.81. n=18 4675/1000 started
    04:05Z.
  stop_reason: null
  next_action: >-
    Run the X-038 ranked queue under think-8x4t. Do not close think-qqzs.
---
# Session 140: N<=100 Lower-Bound Survey

Workflow entry: **W10 planning, then a research loop**. This record is the live
four-hour stacked PR. The latest terminal handoff remains
[session-139](session-139-n11-overnight-research.md); its selected next entry is still
`think-qqzs`. This session does not close that bead.

Branch: `cursor/lb-survey-stacked-f02a`, stacked on `cursor/n11-overnight-8h-f02a`.

## Block schedule

| Block | Window (UTC) | Kind | Work |
| --- | --- | --- | --- |
| 0 | 02:42–03:02 | W10 | X-038, H-218, exp-162, beads, stacked PR |
| 1–6 | 02:50–06:42 | research loop | Ranked covering queue, 40-minute slices |
| 7 | 06:42–07:02 | W10 closeout | Freeze-then-decide any pending retain, render, reviewable PR |

Hourly watchdog: `lb-survey-hourly`. Closeout timer: `lb-survey-4h-closeout`.

## Hard constraints

- Project Python 3.14 via `uv run --frozen` from `packing/` only.
- Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or `think-jwb1`.
- `exp-161` is not this session. Do not `--search`.
- Do not mutate T-025/T-026 `verify_claim.py`.
- `packing-campaign` numeric unattended is NO-GO.
- T-028 only if `decide_certificate` prints `RETAINABLE`.
- n=11 stays T-026. H-216 is not an n=11 result.

## Ranked queue

See [X-038](../explorations/X-038-n100-lower-bound-survey.md). First probe: n=20 at
`973/200` with the T-021 seed, a four-grid, and windows 7.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
