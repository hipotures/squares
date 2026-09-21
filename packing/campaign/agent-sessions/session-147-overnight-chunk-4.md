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
  ended_at: '2026-09-20T13:46:00Z'
  branch: claude/kind-wright-whxxn6-chunk4
  primary_bead: think-b7pr
  status: completed
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
    status: completed
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
    outcome: >-
      T-031 registered at the reviewed scope, V4/C3 on the two gate routes,
      significance 2, apparently novel, with two evidence entries carrying a novelty
      basis, a case package whose certificate.json is the retained exp-220 bytes, a
      control test pinning the digest, and the register views, README and n=11 record
      naming it; check_results and check_rung_figures pass.
    evidence:
    - packing/frontier/results.yaml
    - packing/cases/n11_corner_class_certificate/certificate.json
    - packing/tests/test_n11_corner_class_certificate.py
    stop_reason: The entry is written and every register check passes; the loop's clock ends the chunk.
    next_action: Close the record and update the stacked pull request.
  resource_rollups:
  - packing/campaign/resource-usage/5e071e1a-5ab8-5bae-a5c0-c3687815bf4a.yaml
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
    after: T-031 on the register with its case package and control test; the mixed classes and n=26 remain on BC-367.
  delegations: []
  outputs:
  - packing/campaign/agent-sessions/session-147-overnight-chunk-4.md
  checks:
  - 'full gate: fast at e2721b68: passed (hosted run 35514319906; pages run 35514319902)'
  - packing-validate --records passed locally at e2721b68 and on the closeout tree.
  - 'check_results derives V4 and C4 from the two machine decisions and accepts the declared C3 as an explained understatement (the two gate routes are one invocation, PR 208 review finding 1); check_rung_figures recomputes the mass from the case certificate''s atoms.'
  - The case certificate is byte-identical to the retained exp-220 covering and carries its digest.
  stop_reason: >-
    The BC-367 registration entry is on the register with every check passing; the
    four mixed corner classes and the n=26 second site set stay on BC-367 under
    think-b7pr, and the overnight loop closes on its clock.
  next_action: Session 148 under think-b7pr takes BC-367's mixed classes and the n=26 second site set on the next stacked branch.
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

## How the chunk ended

The entry went on the register in one pass with the review’s scope wording, at C4 rather
than the review’s suggested C3 because the checker derives C4 from two machine decisions
of different method, exactly as T-026 records its two routes; C5 waits on the review
being mapped under `docs/project/reviews`. The overnight loop ends here on its clock:
four chunks ran, one bound-bearing instrument was admitted, one conditional exclusion is
registered, and no bound on `s(n)` moved.
