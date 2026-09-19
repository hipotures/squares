---
title: session-141 — n<100 research loop
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-141
  title: N<100 Research Loop
  date: '2026-09-19'
  started_at: '2026-09-19T07:26:00Z'
  deadline_at: '2026-09-19T16:06:00Z'
  branch: cursor/session-141-n100-research-f02a
  primary_bead: think-ul7y
  status: in_progress
  goal: >-
    Re-rank every open s(n) floor at n<100 from Session-140 evidence, iterate the
    stock covering loop on the highest-likelihood unused constructions, and test
    the other runnable hypotheses beside that core, for eight hours on a stacked PR.
    Land the next T-id only if decide_certificate prints RETAINABLE.
  workflow_phases:
  - workflow: review-planning-oversight
    focus: process
    recording: contemporaneous
    clock_role: work
    bead: think-evlf
    objective: >-
      Write X-039, register H-219 and H-220, claim exp-163, file the ranked queue,
      and open the stacked PR off the Session-140 branch.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 60
    started_at: '2026-09-19T07:26:00Z'
    deadline_at: '2026-09-19T08:26:00Z'
    expected_output: >-
      X-039, H-219, H-220, exp-163 with a live lease, session-141, agenda-039
      ranked queue, beads under think-ul7y, and a draft stacked PR.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check &&
      uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      Stop planning at 08:26Z even if the PR is still drafting. Do not start a
      covering LP before X-039 names the ranked queue.
    fallback: Keep the re-rank and beads and start the research phase on leftover n=18.
    outcome: >-
      X-039 re-ranks leftover n=18 first, then n=20 971/200 on a new four-grid,
      then seedless n=32. H-219, H-220, and exp-163 are registered. Parent bead
      think-ul7y. think-evlf closed.
    evidence:
      - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
      - packing/campaign/hypotheses/H-219-t028-seeded-colgen-raises-s18.md
      - packing/campaign/hypotheses/H-220-seedless-colgen-raises-nagamochi-floor.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-163-h219-t028-next-rung.md
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/ranked-queue.md
    stop_reason: Planning artifacts written; research phase opened.
    next_action: Run leftover n=18 1871/400 under think-u11x.
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    bead: think-u11x
    objective: >-
      Walk the X-039 ranked covering queue. Record every restricted optimum.
      Freeze and decide only when mass is below n. Land the next T-id only on
      RETAINABLE. Pause new probes for Block 4 W5.
    status: in_progress
    entered_by: planned_checkpoint
    switch_reason: Planning artifacts and beads are in the tree.
    budget_minutes: 472
    started_at: '2026-09-19T07:34:00Z'
    deadline_at: '2026-09-19T15:26:00Z'
    expected_output: >-
      Covering receipts under agenda-039, covering-values rows for every finished
      probe, and a T-id landing only if the gate accepts.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check &&
      uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      Stop new probes at 10:26Z for W5, resume at 11:26Z, and stop new probes at
      15:26Z. Do not --search. Do not close think-qqzs, think-g3j7, think-gyzw,
      or think-jwb1. Do not land a non-retainable freeze.
    fallback: Keep the re-rank, the finished covering rows, and a terminal exp-163.
    outcome: null
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n18-1871-400-t028-auto-windows5-receipt.md
      - packing/frontier/n-018.md
    stop_reason: null
    next_action: Walk n=44 675/100 seedless auto under think-coet / exp-173.
  budget:
    wall_minutes: 520
    max_cycles: 8
    orientation_minutes: 20
    checkpoint_minutes: 60
    slice_minutes: 60
    finalization_minutes: 40
  stop_conditions:
  - Close by 2026-09-19T16:06:00Z with records and a reviewable stacked PR.
  - Stop new covering probes at 2026-09-19T15:26:00Z.
  - Block 4 (10:26Z–11:26Z) is the W5 efficiency block under think-36n1 / think-g4n9.
  - Do not close think-qqzs, think-g3j7, think-gyzw, or think-jwb1.
  - Do not allocate exp-161 to this session; do not --search.
  - Do not mutate T-025 or T-026 verify_claim.py.
  - Do not change accept rules, thresholds, or metrics.
  - packing-campaign numeric unattended remains NO-GO.
  - Do not edit gate-budgets.yaml; do not flip wall enforcement.
  - Next T-id only if decide_certificate prints RETAINABLE.
  - n=11 stays T-026; H-216 is not an n=11 result.
  - n=18 does not confirm H-218.
  progress:
    metric: >-
      Open n<100 floors re-ranked, and covering rows recorded on untried
      constructions; a verified floor moves only on RETAINABLE
    before: >-
      Session-140 closed with T-028 at n=18. H-218 unconfirmed. Leftover n=18
      1871/400 and the Nagamochi second wave did not start. Unique covering sides 33.
    after: null
  delegations:
  - task: Re-rank n<100 covering from Session-140 masses
    operator: session-141 covering-rank lane
    status: completed
    recording: contemporaneous
    outcome: >-
      First spend is leftover n=18 1871/400 (H-219), then n=20 971/200 on a new
      four-grid plus windows 7 (H-218), then seedless n=32 29/5 (H-220).
    evidence:
      - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
    files:
      - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/ranked-queue.md
    checks:
      - Session-140 leftover ranking and covering-values rows quoted in X-039
    uncertainty: >-
      n=18 historically retained in 320 s; 117/25 still plateaus at 18, so 1871/400
      can lock.
    elapsed_seconds: 900
    elapsed_quality: operator_reported_approximate
    next_action: Register H-219 and write rank-queue.yaml.
    phase: 1
    budget_minutes: 20
    started_at: '2026-09-19T07:26:00Z'
    deadline_at: '2026-09-19T07:46:00Z'
  - task: Survey other open hypotheses besides H-218
    operator: session-141 hypothesis-survey lane
    status: completed
    recording: contemporaneous
    outcome: >-
      H-219 and H-220 are the new covering claims. H-210 and H-211 can run off-CPU.
      H-163 is --check only. H-216 stays parked as n=11. Block 4 is think-g4n9.
    evidence:
      - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
    files:
      - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
    checks:
      - think-qqzs, think-g3j7, think-gyzw, think-jwb1 left open
    uncertainty: >-
      Workbench H-210/H-211 need Node >= 24.18; this VM has been on Node 22.
    elapsed_seconds: 900
    elapsed_quality: operator_reported_approximate
    next_action: Keep covering on one core; park exp-161 encode.
    phase: 1
    budget_minutes: 20
    started_at: '2026-09-19T07:26:00Z'
    deadline_at: '2026-09-19T07:46:00Z'
  - task: Extract session and experiment registration fields
    operator: session-141 schema lane
    status: completed
    recording: contemporaneous
    outcome: >-
      Next ids are session-141, X-039, exp-163, H-219. Agenda drop is agenda-039.
      In-progress experiment needs a live lease and no effort block.
    evidence:
      - packing/campaign/agent-sessions/session-141-n100-research.md
    files:
      - packing/campaign/agent-sessions/session-141-n100-research.md
    checks:
      - packing.squares AgentSession/v2 and Experiment/v2 required fields
    uncertainty: Hypothesis status is ledger-derived, not a YAML field.
    elapsed_seconds: 600
    elapsed_quality: operator_reported_approximate
    next_action: Write the live records and open the stacked PR.
    phase: 1
    budget_minutes: 15
    started_at: '2026-09-19T07:26:00Z'
    deadline_at: '2026-09-19T07:41:00Z'
  - task: Land T-029 n=18 1871/400
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      T-029 retained s(18) >= 1871/400 = 4.6775 at V4/C4/S3. T-028 bytes sit at
      certificate-187-40.json. Confirms H-219 / exp-163. Does not confirm H-218.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n18-1871-400-t028-auto-windows5-receipt.md
    files:
      - packing/cases/n18_fractional_certificate/certificate.json
      - packing/frontier/results.yaml
      - packing/frontier/n-018.md
    checks:
      - decide_certificate printed RETAINABLE; sha256 dd06c0e39639f06af475459a2a63f9fc8d5836b0b83ea3b6c3a4de8f212892d4
    uncertainty: C5 still requires a mapped review.
    elapsed_seconds: 800
    elapsed_quality: operator_reported_approximate
    next_action: think-so2k
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T07:46:00Z'
    deadline_at: '2026-09-19T08:06:00Z'
  - task: Record n=20 971/200 four-grid and claim exp-165
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-164 stopped at 19.857588 unconverged below 20 after 48 rounds / 2516 s.
      No freeze. T-030 not offered. H-218 unconfirmed. Nagamochi n=32 start
      killed so 243/50 could run first as exp-165.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n20-971-200-t021-grid4-windows7-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-164-h218-n20-971-200-new-four-grid.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-165-h218-n20-243-50-four-grid.md
    checks:
      - decide_certificate not run; no freeze below 20
    uncertainty: Remaining rows on 971/200 four-grid raise; 243/50 is a thinner unused side.
    elapsed_seconds: 2600
    elapsed_quality: operator_reported_approximate
    next_action: think-so2k
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T08:38:00Z'
    deadline_at: '2026-09-19T08:58:00Z'
  - task: Record n=20 243/50 four-grid and claim exp-166
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-165 stopped at 19.887914 unconverged below 20 after 36 rounds / 1269 s.
      No freeze. T-030 not offered. H-218 unconfirmed. Walker started n=32 29/5
      as exp-166 / H-220.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n20-243-50-t021-grid4-windows7-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-165-h218-n20-243-50-four-grid.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-166-h220-n32-29-5-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 20
    uncertainty: Remaining rows on 243/50 four-grid raise; H-220 is a new n and class.
    elapsed_seconds: 1300
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T09:02:00Z'
    deadline_at: '2026-09-19T09:22:00Z'
  - task: Record n=32 29/5 seedless and claim exp-167
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-166 stopped at 29.803318 unconverged below 32 after 35 rounds / 1206 s.
      No freeze. T-030 not offered. H-220 unconfirmed. Walker started n=31 57/10
      as exp-167.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n32-29-5-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-166-h220-n32-29-5-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-167-h220-n31-57-10-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 32
    uncertainty: Remaining rows on n=32 29/5 raise; first first-party covering row at n=32.
    elapsed_seconds: 1250
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T09:22:00Z'
    deadline_at: '2026-09-19T09:42:00Z'
  - task: Record n=31 57/10 seedless and claim exp-168
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-167 stopped at 28.331329 unconverged below 31 after 38 rounds / 1285 s.
      No freeze. T-030 not offered. H-220 unconfirmed. Walker started n=30 559/100
      as exp-168.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n31-57-10-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-167-h220-n31-57-10-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-168-h220-n30-559-100-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 31
    uncertainty: Remaining rows on n=31 57/10 raise; first first-party covering row at n=31.
    elapsed_seconds: 1250
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T09:43:00Z'
    deadline_at: '2026-09-19T10:03:00Z'
  - task: Record n=30 559/100 seedless and claim exp-169
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-168 stopped at 27.178193 unconverged below 30 after 50 rounds / 1213 s.
      No freeze. T-030 not offered. H-220 unconfirmed. Walker started n=26 513/100
      as exp-169.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n30-559-100-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-168-h220-n30-559-100-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-169-h220-n26-513-100-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 30
    uncertainty: Remaining rows on n=30 559/100 raise; first first-party covering row at n=30.
    elapsed_seconds: 1250
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T10:04:00Z'
    deadline_at: '2026-09-19T10:24:00Z'
  - task: Record n=26 513/100 seedless and claim exp-170
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-169 stopped at 25.000000 unconverged below 26 after 42 rounds / 1209 s.
      Plateau from round 11. No freeze. T-030 not offered. H-220 unconfirmed.
      Walker started n=27 525/100 as exp-170.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n26-513-100-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-169-h220-n26-513-100-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-170-h220-n27-525-100-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 26
    uncertainty: Remaining rows on n=26 513/100 raise; first first-party covering row at n=26.
    elapsed_seconds: 1250
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T10:24:00Z'
    deadline_at: '2026-09-19T10:44:00Z'
  - task: Record n=27 525/100 seedless and claim exp-171
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-170 stopped at 25.000000 unconverged below 27 after 38 rounds / 1201 s.
      No freeze. T-030 not offered. H-220 unconfirmed. Walker stopped before n=29
      (remain=-1094s). Resume after 11:26Z as exp-171.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n27-525-100-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-170-h220-n27-525-100-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-171-h220-n29-548-100-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 27
    uncertainty: Remaining rows on n=27 525/100 raise; first first-party covering row at n=27.
    elapsed_seconds: 1250
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T10:44:00Z'
    deadline_at: '2026-09-19T11:04:00Z'
  - task: Record n=29 548/100 seedless and claim exp-172
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-171 converged at 26.040745 with freeze mass 52081879/2000000.
      declare accepted; decide interval refused (272 stalled, Condition 5).
      T-030 not offered. H-220 unconfirmed. Walker started n=45 684/100 as
      exp-172.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n29-548-100-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-171-h220-n29-548-100-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-172-h220-n45-684-100-seedless-auto-windows5.md
    checks:
      - decide_certificate printed REFUSED, not RETAINABLE
    uncertainty: First Nagamochi freeze below n; interval route stalled.
    elapsed_seconds: 1180
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 20
    started_at: '2026-09-19T11:44:00Z'
    deadline_at: '2026-09-19T12:04:00Z'
  - task: Record n=45 684/100 seedless and claim exp-173
    operator: session-141 coordinator
    status: completed
    recording: contemporaneous
    outcome: >-
      exp-172 stopped at 42.137360 unconverged below 45 after 26 rounds / 1254 s.
      No freeze. T-030 not offered. H-220 unconfirmed. Walker started n=44
      675/100 as exp-173.
    evidence:
      - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n45-684-100-auto-windows5-receipt.md
    files:
      - packing/frontier/covering-values.yaml
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-172-h220-n45-684-100-seedless-auto-windows5.md
      - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-173-h220-n44-675-100-seedless-auto-windows5.md
    checks:
      - decide_certificate not run; no freeze below 45
    uncertainty: Remaining rows on n=45 684/100 raise; first first-party covering row at n=45.
    elapsed_seconds: 1254
    elapsed_quality: operator_reported_approximate
    next_action: think-coet
    phase: 2
    budget_minutes: 42
    started_at: '2026-09-19T11:58:00Z'
    deadline_at: '2026-09-19T12:40:00Z'
  outputs:
    - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
    - packing/campaign/hypotheses/H-219-t028-seeded-colgen-raises-s18.md
    - packing/campaign/hypotheses/H-220-seedless-colgen-raises-nagamochi-floor.md
    - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-163-h219-t028-next-rung.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/ranked-queue.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n18-1871-400-t028-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n20-971-200-t021-grid4-windows7-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n20-243-50-t021-grid4-windows7-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n32-29-5-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n31-57-10-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n30-559-100-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n26-513-100-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/w5-think-g4n9-hosted-walls.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n27-525-100-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n29-548-100-auto-windows5-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-039/n45-684-100-auto-windows5-receipt.md
    - packing/campaign/agent-sessions/session-141-n100-research.md
  checks: []
  stop_reason: null
  next_action: think-coet
---
# Session-141: Eight-Hour n<100 Research Loop

Stacked on Session-140 / PR 200. Branch `cursor/session-141-n100-research-f02a`.
Workflow entry is planning, then the research loop. Primary bead is `think-ul7y`, not
`think-qqzs`.

[X-039](../explorations/X-039-n100-re-rank-after-session-140.md) is the re-rank.
[H-219](../hypotheses/H-219-t028-seeded-colgen-raises-s18.md) is leftover n=18.
[H-220](../hypotheses/H-220-seedless-colgen-raises-nagamochi-floor.md) is the Nagamochi
wave. H-218 stays the n=12/17/19/20 claim; exp-162 is abandoned, and a new n=20 site
set is the reopen path after exp-163 terminals.

## Eight-hour schedule

| Block | Window (UTC) | Workflow | Focus |
| ---: | --- | --- | --- |
| 1 | 07:26–08:26 | W10 | Plan, register, stacked PR |
| 2 | 08:26–09:26 | W6 | H-219 leftover n=18 `1871/400` |
| 3 | 09:26–10:26 | W6 | H-218 n=20 `971/200` new four-grid, or continue n=18 |
| 4 | 10:26–11:26 | W5 | `think-g4n9` hosted walls; covering paused |
| 5 | 11:26–12:26 | W6 | Resume covering; H-210/H-211 off-CPU if Node permits |
| 6 | 12:26–13:26 | W6 | H-220 second wave or optional follow-ups |
| 7 | 13:26–14:26 | W6 | Remaining ranked probes |
| 8 | 14:26–15:26 | W6 | Last research hour |
| closeout | 15:26–16:06 | W10 | Terminalize; 40-minute reserve |

Covering may start as soon as X-039 names the queue, before 08:26. First walker
`--stop-at 2026-09-19T10:26:00Z`. A probe already on the core at 10:26 finishes; no new
probe starts until 11:26.

OR-12: Block 4 is the efficiency block. The record says so here and on `think-36n1`.

## Research loop

1. Pick the top open cell on [ranked-queue.md](../series/series-000-smoke-and-calibration/results/agenda-039/ranked-queue.md).
2. Restate the claim (H-219, then H-218, then H-220). Register a new experiment before
   measuring a claim exp-163 does not own. Only one in-progress experiment at a time.
3. Run `run_covering_queue` on one core.
4. Record every restricted optimum on `covering-values.yaml`.
5. If freeze mass `< n`, stop the queue and run both decide routes.
6. Land a T-id only on `RETAINABLE`.
7. Re-screen: a retain eats later sides on that n; a crossing above n kills more wall
   on that site set.

H-210 and H-211 use the workbench harness, not HiGHS. H-163 is
`admit_threshold_compression --check` only. Do not `--search`. Do not encode beside
covering.

## T-id recipe

T-029 is landed: `s(18) >= 1871/400`. Next T-id is T-030. Copy the T-029 landing
pattern, not a new case class. Score S3. `produced_by.session` is `session-141`.

- n=20 `243/50` finished `19.887914` unconverged; do not replay that set.
  n=20 `971/200` four-grid finished `19.857588` unconverged; do not replay that
  set. H-218 stays unconfirmed.
- n=32 `29/5` finished `29.803318` unconverged; do not replay that set.
- n=31 `57/10` finished `28.331329` unconverged; do not replay that set.
- n=30 `559/100` finished `27.178193` unconverged; do not replay that set.
- n=26 `513/100` finished `25.000000` unconverged; do not replay that set.
- n=27 `525/100` finished `25.000000` unconverged; do not replay that set.
- n=29 `548/100` converged and froze at mass `26.0409395`; interval refused;
  do not replay that set.
- n=45 `684/100` finished `42.137360` unconverged; do not replay that set.
- A Nagamochi RETAINABLE at n=44 (H-220) is T-030. There is no n=26,
  n=27, n=29, n=30, n=31, or n=32 case package yet. Copy the T-029 landing
  pattern into a new `cases/nNN_fractional_certificate/` tree. T-030 artifacts
  list only the live pointer.
- n=18 `4679/1000` is H-221, not a replay of H-219. Claim a new experiment before
  that probe starts.
- Do not mint a T-id on an unconverged freeze, a freeze with mass `>= n`, or n=21
  `97/20`.

## Constraints

- Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or `think-jwb1`.
- Do not allocate exp-161. Do not `--search`.
- Do not mutate T-025 or T-026 `verify_claim.py`.
- packing-campaign numeric unattended remains NO-GO.
- Do not edit `gate-budgets.yaml`.
- n=11 stays T-026. H-216 is not an n=11 result.
- Attic scratch is V0/C0.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
