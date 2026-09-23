---
title: Session 153 — Native n11 adaptive parent-core verification
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-153
  title: Native n11 adaptive parent-core verification
  date: '2026-09-22'
  started_at: '2026-09-22T22:45:57.644Z'
  deadline_at: '2026-09-23T02:45:57.644Z'
  branch: codex/n11-parent-core-verifier
  primary_bead: think-d010
  status: in_progress
  goal: >-
    Preserve the exact adaptive parent-angle and centre-domain contract in a native
    verifier, then independently decide all 12028 retained n11 certificate intervals.
  workflow_phases:
  - workflow: pipeline-improvement
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Implement the exact native certificate premises and interval coverage adapter,
      verify adverse inputs, and measure source-row pilots and allocation budgets.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 30
    started_at: '2026-09-22T22:45:57.644Z'
    deadline_at: '2026-09-22T23:15:57.644Z'
    expected_output: Native library, retained verification tool, adverse tests and pilot receipts.
    validation_command: cd packing && .venv/bin/python3 -m pytest tests/test_fractional_parent_core.py
    kill_condition: A soundness counterexample survives correction, or requested pilot rows remain unresolved.
    fallback: Retain the counterexample or unresolved boxes and repair the native method without changing the theorem.
    outcome: >-
      The exact importer and parent-domain interval adapter certify the first, weakest
      and last source rows with zero stalled boxes. Three batch sizes preserve the
      existing temporary byte ceilings and give identical box counts; 2048 is selected
      for the complete run. The focused adverse suite passes, including seam refusal,
      exact rational input guards, multiplicities, parent-domain witnesses and parallel
      equivalence. Complete coverage remains pending.
    evidence:
    - docs/project/reviews/review-2026-09-22-native-n11-parent-core.md
    - packing/campaign/agent-sessions/session-153-native-pilot.json
    - packing/campaign/agent-sessions/session-153-native-pilot-batch256.json
    - packing/campaign/agent-sessions/session-153-native-pilot-batch512.json
    - packing/campaign/agent-sessions/session-153-native-pilot-two-workers.json
    stop_reason: The requested pilots certify and the mathematical and adverse reviews found no remaining blocker.
    next_action: Freeze the reviewed numerical code and run every source row with two workers.
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Run the complete native interval coverage decision, reconcile every source row,
      and review the resulting full theorem before any confirmation-level promotion.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: The bounded pilots and adverse tests establish readiness for the full catalogue.
    budget_minutes: 180
    started_at: '2026-09-22T23:09:00Z'
    deadline_at: '2026-09-23T02:09:00Z'
    expected_output: Complete source-bound native receipt or an explicit unresolved or refuted row.
    validation_command: cd packing && .venv/bin/python3 -m devtools.verify_kleddamag_n11_native --all --workers 2 --output campaign/agent-sessions/session-153-native-full.json
    kill_condition: A refuted or unresolved row prevents acceptance of the complete certificate.
    fallback: Retain the row journal, diagnose the exact obstruction and continue the native-verifier bead.
    outcome: >-
      The clean c183cc9ab run certifies all 12028 rows in 6197.381 seconds with
      136081500 boxes, zero stalls, no exhausted budgets and no refutations. Exact
      premises and the complete transfer theorem support strict s(11)>31/8. The
      coordinator independently reconciled the receipt and reviewed the mathematics.
      A permanent fast audit reconciles the row journal, exact premises and 19 frozen
      Git inputs; its 28 adverse and positive tests pass. The paired complete source
      and native methods support C4 only, with attribution and the numerical bound
      unchanged.
    evidence:
    - packing/campaign/agent-sessions/session-153-native-full.json
    - packing/campaign/agent-sessions/session-153-native-full.rows.jsonl
    - packing/campaign/agent-sessions/session-153-native-reconciliation.json
    - docs/project/reviews/review-2026-09-22-native-n11-parent-core.md
    stop_reason: Every preregistered row and exact premise passes, and independent mathematical review found no remaining blocker.
    next_action: Complete the reviewed evidence registration, integrate the green base, and close the publication record with separate final-head checks.
  - workflow: review-planning-oversight
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Preserve the complete proof provenance, finish C4 evidence registration and
      session accounting, and publish the reviewed closeout on the green stacked base.
    status: in_progress
    entered_by: evidence_checkpoint
    switch_reason: Complete coverage and proof review are accepted; only integration, records and final publication checks remain.
    budget_minutes: 10
    started_at: '2026-09-23T02:05:18Z'
    deadline_at: '2026-09-23T02:15:18Z'
    expected_output: Reviewed PR 223 closeout with immutable proof receipts, C4 evidence and scoped cost and validation records.
    validation_command: cd packing && .venv/bin/python3 -m devtools.audit_kleddamag_n11_native
    kill_condition: A changed numerical proof input or new mathematical blocker invalidates reuse of the complete receipt.
    fallback: Retain the original run, diagnose the affected premise, and withhold publication of the disputed claim until corrected.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: Merge only the final green PR 222 head, re-pin generated data, and finish final checks and root review before push.
  budget:
    wall_minutes: 240
    slice_minutes: 30
    finalization_minutes: 30
  stop_conditions:
  - Complete native coverage and its proof review, or retain an explicit external blocker without claiming C4.
  - Planning estimates are checkpoints and do not authorize truncating the user's task.
  progress:
    metric: Source intervals completely decided by native box branch and bound.
    before: No native adaptive parent-core certificate decision; source event sweeps already support the strict 31/8 bound.
    after: All 12028 intervals certify with exact premises and no unresolved boxes; the distinct native method supports C4 for the strict 31/8 bound.
  delegations:
  - task: Adverse tests and independent review of native domain and batching boundaries
    operator: GPT-5.6 Sol, high
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: Focused tests pass, including exact-seam refusal and serial-versus-two-worker equivalence.
    evidence: [packing/tests/test_fractional_parent_core.py]
    files: [packing/tests/test_fractional_parent_core.py]
    checks: [39 focused tests passed, Ruff check and format-check clean, BasedPyright clean]
    uncertainty: Tiny controls and source pilots do not establish complete source coverage.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Independent root review and complete native run.
  outputs:
  - packing/src/sqpack/fractional/parent_core.py
  - packing/src/sqpack/fractional/parent_core_interval.py
  - packing/devtools/verify_kleddamag_n11_native.py
  - packing/devtools/audit_kleddamag_n11_native.py
  - packing/tests/test_fractional_parent_core.py
  - packing/tests/test_native_parent_core_receipt.py
  - docs/project/reviews/review-2026-09-22-native-n11-parent-core.md
  - packing/campaign/agent-sessions/session-153-native-full.json
  - packing/campaign/agent-sessions/session-153-native-full.rows.jsonl
  - packing/campaign/agent-sessions/session-153-native-reconciliation.json
  - packing/campaign/agent-sessions/session-153-hosted-full.json
  checks:
  - Native pilot rows 0, 11962 and 12027 certify at batch sizes 256, 512 and 2048.
  - The two-worker source pilot matches the serial outcomes.
  - First records preflight took 176.85 seconds and failed on a missing venv PATH entry and the unregistered new review document; both causes were corrected before the push gate.
  - Combined interval regression selection passed 98 tests, with two existing Linux-only pool tests skipped on macOS and ten slow or exhaustive tests deselected.
  - Scoped push gate took 781.81 seconds within its 1800-second ceiling; 2115 selected tests passed, four failed, two skipped and twelve deselected. Failures were generated session views, test formatting, sandbox-blocked process inspection and a snapshot race caused by moving the new cost receipt during the gate. Freeze the tree and rerun those affected checks after correction.
  - After correction and staging, all four affected snapshot and process-lifecycle tests passed in 23.36 seconds. The four selected lint, synopsis and campaign steps passed in 9.75 seconds; close_session --check agreed with all 153 sessions. The final native file passed 39 tests, Ruff check and format-check, and BasedPyright.
  - The repaired base ab1b92bb3 merged without conflicts and changed none of the native verifier, shared interval modules, CLI or native tests. On the merged tree, all 39 native tests passed in 5.72 seconds and the three synopsis, session-cost and campaign checks passed in 12.95 seconds.
  - 'full gate: full at c183cc9abe93eedcb268a5390cdd1cdc6e7bbb39: passed'
  - 'The hosted five-job full checkpoint passed on frozen c183cc9ab: https://github.com/jlevy/squares/actions/runs/35799179943'
  - The complete native run used two workers and batch size 2048 on clean c183cc9ab. All 12028 rows certified in 6197.381 seconds, with 136081500 boxes, zero stalls and no exhausted budgets or refutations. The attempted nice priority 10 was refused; the actual nice value was 0, with the worker cap unchanged.
  - Receipt reconciliation recomputes exact premises and verifies all row identities, outcomes and journal agreement against 19 unchanged Git inputs and the exact external source SHA. Its 28 tests passed in 6.17 seconds, then 12.37 seconds including the retained-report comparison; Ruff and BasedPyright reported zero findings. This reconciliation is not a coverage replay or another confirmation method.
  - Closeout records preflight passed 35 selected steps in 220.04 seconds, dominated by 220.04 seconds reading the linked-worktree bead tree. After the evidence edit, all 8 applicable schema, inventory, rung, exact-figure, case-prose, generated-table and front-door checks passed in 11.79 seconds.
  resource_rollups:
  - packing/campaign/resource-usage/codex-task-tree-session-153-native-draft.yaml
  stop_reason: null
  next_action: Integrate the final green PR 222 base and publish the independently reviewed PR 223 closeout; keep the proof receipt pinned to c183cc9ab and distinguish final-head checks from its historical full gate.
---
# Session 153: Native n11 Adaptive Parent-Core Verification

The
[proof contract and run plan](../../../docs/project/reviews/review-2026-09-22-native-n11-parent-core.md)
declare the original acceptance rule and explain the domain and threshold semantics.
The external certificate remains the credited source of the bound.
This session adds a complete native method of coverage verification.

The complete run certifies every interval, preserves strict containment at the final
parent side, and finishes with no unresolved boxes.
Its exact budget margin is `13483/125000000`. Together with the source event-cell
replay, the complete native interval method and reviewed transfer theorem support C4 for
the strict bound `s(11)>31/8`; no C5 promotion or new result identifier is claimed.

The immutable proof receipt belongs to clean `c183cc9ab`, which includes the repaired
base `ab1b92bb3`. Later base integration and record changes preserve that provenance.
The permanent reconciliation compares transitive numerical inputs with their frozen Git
blobs, and binds the external certificate to its reviewed SHA-256. It checks the
recorded outcomes and exact premises without rerunning interval coverage; it cannot
authenticate coordinated invented receipt and journal data.
Final publication checks are recorded separately from the full checkpoint on
`c183cc9ab`.

The
[initial task-tree cost receipt](../resource-usage/codex-task-tree-session-153-native-draft.yaml)
covers this primary Astra implementation lane from its start through 23:18 UTC:
1,922.174 elapsed seconds and 1,984.469 agent-active seconds, including automatic
approval review. It is a live lower bound and excludes the separate Sol test lane and
shared coordinator. Subsequent receipts must start at this cutoff to avoid counting the
same interval twice.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
