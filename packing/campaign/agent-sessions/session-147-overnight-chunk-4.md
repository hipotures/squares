---
title: "Session 147 — overnight chunk 4: the BC-367 registration entry"
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-147
  title: Overnight Chunk 4 — The BC-367 Registration Entry
  date: '2026-09-20'
  started_at: '2026-09-20T13:36:00Z'
  deadline_at: '2026-09-20T15:06:00Z'
  branch: claude/kind-wright-whxxn6-chunk4
  primary_bead: think-b7pr
  status: in_progress
  goal: >-
    Write the results-register entry for the exp-220 exclusion of the octagon class
    at 96/25 at the scope Session 146's review accepted, in the T-023 pattern at
    V4/C3, with its evidence entries and controls, so that the first decided item of
    the corner-conditioned point language is on the register with its limits stated.
  workflow_phases:
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    commitment: BC-367
    objective: >-
      One W2 review-and-register step: the register entry, its evidence rows, the
      rendered register and synopsis headline, and the rung-figure check against the
      retained exp-220 bytes; no target runs.
    status: in_progress
    entered_by: session_start
    switch_reason: null
    budget_minutes: 70
    started_at: '2026-09-20T13:36:00Z'
    deadline_at: '2026-09-20T14:46:00Z'
    expected_output: >-
      A results.yaml entry with the reviewed scope wording, evidence entries pointing
      at exp-220's bytes and gate outputs, the rendered RESULTS.md and synopsis
      headline, and the records tier passing.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      The rung checks refuse a figure the retained bytes do not carry; then the entry
      is not written and the refusal is recorded on H-222.
    fallback: Record what was written, keep the clocks honest, and leave the entry to BC-367.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: Write the entry, render, check, and close the chunk.
  budget:
    wall_minutes: 90
    finalization_minutes: 20
  stop_conditions:
  - The entry claims exactly the reviewed scope and names the exclusion as conditional and not a bound.
  - Every figure the entry quotes is carried by exp-220's retained bytes or gate outputs.
  - The chunk closes by 15:06Z with its records validated, committed, and pushed as a stacked draft pull request.
  progress:
    metric: BC-367 registration entry written
    before: The exp-220 exclusion is reviewed (REGISTER WITH CORRECTIONS, corrections applied) but not on the register.
    after: null
  delegations: []
  outputs:
  - packing/campaign/agent-sessions/session-147-overnight-chunk-4.md
  checks: []
  stop_reason: null
  next_action: Close the record with the hosted gate on this tree; the mixed classes and n=26 stay on think-b7pr.
---
# Session 147: Overnight Chunk 4

The fourth chunk of the overnight loop that
[agenda-040](../agendas/agenda-040-overnight-lower-bound-loop.md) schedules, stacked on
Session 146’s branch, taking BC-367’s registration item: the results-register entry for
the exp-220 exclusion at the scope the
[registration review](../series/series-000-smoke-and-calibration/results/agenda-040/h222-registration-review.md)
accepted. No target runs; the coordinator writes the record work itself.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
