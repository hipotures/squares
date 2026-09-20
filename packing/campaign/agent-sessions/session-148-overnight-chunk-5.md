---
title: "Session 148 — chunk 5: the second stage inside the all-deep class, and the gap-g wedge"
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-148
  title: Chunk 5 — The Second Stage Inside the All-Deep Class, and the Gap-g Wedge
  date: '2026-09-20'
  started_at: '2026-09-20T15:22:00Z'
  deadline_at: '2026-09-20T17:22:00Z'
  branch: claude/kind-wright-whxxn6-chunk5
  primary_bead: think-b7pr
  status: in_progress
  goal: >-
    Take the two mathematical items the registration review left as the ones that
    could matter: make the 2-of-3 ring-centre relation inside the all-deep corner
    class at 96/25 precise enough to register and instrument, and derive the gap-g
    wedge conflict edge BC-364 asks for against the A6 64-family; beside them, thread
    the corner clip through the threshold routes so the first can run.
  workflow_phases:
  - workflow: insight-iteration
    focus: insight
    recording: contemporaneous
    clock_role: work
    commitment: BC-367
    objective: >-
      Two Fable derivation lanes (the ring-centre lemma and atom family with an exact
      check on the transported 88-family; the gap-g wedge lemma with an exact pair
      check on the 64-family) and one Opus lane (the corner clip on threshold.py and
      threshold_interval.py, unclipped byte-identical), then a Fable review of both
      derivations; no LP or column-generation target runs.
    status: in_progress
    entered_by: session_start
    switch_reason: null
    budget_minutes: 100
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T17:02:00Z'
    expected_output: >-
      A registered H-232 (or a recorded reason not to), a BC-364 disposition with the
      exact pair check, the threshold clip admitted or a design, and a review record.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      A derivation lane finds the relation false on the family; then the finding is
      recorded and the instrument is not built.
    fallback: Record what was derived, keep the clocks honest, and hand the rest to BC-367.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: Read the three lane reports, launch the review, and close the chunk.
  budget:
    wall_minutes: 120
    finalization_minutes: 20
  stop_conditions:
  - No hypothesis is registered without an exact check of its family charge on a retained artifact.
  - No LP or column-generation target runs in this chunk.
  - The chunk closes by 17:22Z with its records validated, committed, and pushed as a stacked draft pull request.
  progress:
    metric: BC-367 second-stage items derived and dispositioned
    before: The ring-centre 2-of-3 relation is a review sketch; the gap-g wedge is underived; the threshold routes take no clip.
    after: null
  delegations:
  - task: Derive the ring-centre 2-of-3 relation inside the all-deep class at 96/25 with an exact check on the transported 88-family, and write H-232
    operator: chunk5_ring; Claude Fable max
    status: in_progress
    recording: contemporaneous
    phase: 1
    outcome: null
    evidence: []
    files: []
    checks: []
    uncertainty: A derivation is evidence for a hypothesis, not a verdict; the family charge is a Lemma-D necessary condition.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Fable review, then registration of H-232 if the reading survives.
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T16:37:00Z'
    budget_minutes: 75
    write_scope: [session scratchpad chunk5-ring/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: report.md with the lemma, the atom family, the exact family charge, and the H-232 text.
    validation_command: Coordinator reads the report and re-runs its exact check.
    kill_condition: The relation is false on the transported family.
    fallback: Report the counterexample and stop.
  - task: Derive the gap-g wedge conflict edge and test it exactly against the A6 64-family (BC-364, H-230)
    operator: chunk5_wedge; Claude Fable max
    status: in_progress
    recording: contemporaneous
    phase: 1
    outcome: null
    evidence: []
    files: []
    checks: []
    uncertainty: The 7.11 degree orbit at gap 0.016 is the one X-040 names; a reach failure there is a finding, not a failure of the lane.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Fable review, then the BC-364 disposition.
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T16:37:00Z'
    budget_minutes: 75
    write_scope: [session scratchpad chunk5-wedge/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: report.md with the lemma, the pairwise condition, the exact pair check, and the verdict.
    validation_command: Coordinator reads the report and re-runs its exact check.
    kill_condition: The lemma's forced region is empty for every gap the family uses.
    fallback: Record why and stop.
  - task: Thread the corner clip through threshold.py and threshold_interval.py with the class claim policy and tests
    operator: chunk5_threshold_clip; Claude Opus high
    status: in_progress
    recording: contemporaneous
    phase: 1
    outcome: null
    evidence: []
    files: []
    checks: []
    uncertainty: If the change does not fit the budget the lane delivers a design, not a half-threaded change.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator runs the tests; a Fable review before any clipped threshold run.
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T16:22:00Z'
    budget_minutes: 60
    write_scope: [packing/src/sqpack/fractional/threshold.py, packing/src/sqpack/fractional/threshold_interval.py, packing/src/sqpack/fractional/corner_clip.py, packing/devtools/decide_threshold_certificate.py, packing/tests/test_threshold_corner_clip.py]
    excluded_commands: [git commit, git push, any edit to packing/cases/n11_threshold_certificate/verify_claim.py, any edit to a retained certificate]
    expected_output: The threaded clip with tests, or a design.
    validation_command: cd packing && uv run --frozen --all-extras --group dev pytest tests/test_threshold_corner_clip.py -q
    kill_condition: T-025's retained certificate decides differently unclipped.
    fallback: Revert and report.
  outputs:
  - packing/campaign/agent-sessions/session-148-overnight-chunk-5.md
  checks: []
  stop_reason: null
  next_action: Close the record with the hosted gate on this tree; BC-367's runs stay on think-b7pr.
---
# Session 148: Chunk 5

The loop continued at the owner’s request after the four overnight chunks, stacked on
Session 147’s branch.
The registration review of exp-219 named the instrument that could matter, a 2-of-3
threshold atom on ring-centre overlaps inside the all-deep corner class, and BC-364’s
gap-g wedge derivation was scheduled for a later chunk; both are mathematics first, so
this chunk runs them as Fable derivation lanes with an exact check on a retained family
each, and threads the corner clip through the threshold routes beside them so that the
first can be instrumented.
No target runs.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
