---
title: Session 142 — correctness review of PRs 199–201
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-142
  title: Correctness Review of PRs 199–201
  date: '2026-09-19'
  started_at: '2026-09-19T23:54:00Z'
  deadline_at: '2026-09-20T01:24:00Z'
  branch: codex/stack-review-corrections
  primary_bead: think-gz4k
  resource_rollups:
  - packing/campaign/resource-usage/session-142-stack-correctness.yaml
  status: completed
  ended_at: '2026-09-20T01:49:13Z'
  goal: >-
    Audit Sessions 139–141 one PR at a time, replay their mathematical claims,
    correct confirmed defects in a new layer above PR 201, and report merge readiness.
  workflow_phases:
  - workflow: pipeline-improvement
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Integrate solver-status and geometry guards, queue ownership, and research
      record corrections; validate and publish the correction layer.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 90
    started_at: '2026-09-19T23:54:00Z'
    deadline_at: '2026-09-20T01:24:00Z'
    expected_output: >-
      A correction PR above 201, regression tests for computational boundaries and
      queue exclusion, corrected provenance and assurance, and a final review record.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate
    kill_condition: A proposed repair changes the accepted mathematical claim or needs a new search.
    fallback: Preserve the finding as open and make a bounded repair without new research.
    outcome: >-
      Computational and scheduler repairs pass 50 combined tests. Sixteen numerical
      subjects and result provenance are corrected. Eight atlas exports were
      regenerated, and a fast stale-label negative control passes.
    evidence:
    - docs/project/reviews/review-2026-09-19-pr199-201-correctness.md
    - packing/tests/test_covering_queue.py
    - packing/tests/test_known_best_atlas.py
    stop_reason: Implementation complete; integrated validation and publication move to W2.
    next_action: Audit the integrated correction layer and its full checkpoints.
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: Validate the integrated repairs and publish the new stacked correction PR.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: >-
      All implementation lanes are complete, including the publication defect found
      by the original stack's deferred checkpoint.
    budget_minutes: 70
    started_at: '2026-09-20T00:17:06Z'
    deadline_at: '2026-09-20T01:24:00Z'
    expected_output: A reviewable correction PR, integrated validation, and explicit per-PR merge verdicts.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --fast
    kill_condition: A validation failure contradicts a claimed repair or retained mathematical result.
    fallback: Reopen the specific finding, repair it, and repeat the affected validation.
    outcome: >-
      PR 202 repairs all confirmed findings at the stack tip. Final code 8dbc1068
      passed the matching hosted fast and deferred checkpoints; the original lower
      heads remain unchanged and are not independently ready to merge.
    evidence:
    - docs/project/reviews/review-2026-09-19-pr199-201-correctness.md
    - https://github.com/jlevy/squares/pull/202
    - https://github.com/jlevy/squares/actions/runs/35480879196
    - https://github.com/jlevy/squares/actions/runs/35480905141
    stop_reason: Corrected code passed the full checkpoint; remaining publication changes record the observed results.
    next_action: Return to the selected H-216 research entry.
  budget:
    wall_minutes: 120
  stop_conditions:
  - All confirmed findings have an explicit disposition and the correction PR is reviewable.
  - Do not merge or rewrite PRs 199–201.
  - Do not promote n=29, change certificate mathematics, or start a new search.
  - Preserve think-qqzs as the selected research follow-up.
  progress:
    metric: Confirmed review findings corrected and validated
    before: Eight findings and three smaller corrections across the open stack.
    after: Nine findings and three smaller corrections repaired; four retained certificates replayed; final code passes all 80 checkpoint steps.
  delegations:
  - task: Independent review of PR 199 mathematics and new computational boundaries
    operator: review_199_math; GPT-6 Astra max
    status: completed
    recording: retrospective
    phase: 1
    outcome: T-027 replay passed; solver-status, geometry-domain and multiplicity defects were reproduced.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [62 focused mathematical and producer tests passed; exact and interval T-027 replay passed.]
    uncertainty: The review did not re-prove the unchanged verifier implementation.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Integrate the bounded repairs under think-gz4k.
  - task: Independent review of PR 200 survey and provenance
    operator: review_200_survey; GPT-6 Astra max
    status: completed
    recording: retrospective
    phase: 1
    outcome: T-028 replay passed; scientific-status, assurance, provenance and census corrections identified.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [Exact and interval T-028 replay; frontier census and record-schema inspection.]
    uncertainty: Floating LP outcomes do not certify site-set impossibility.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Correct the historical records with dated annotations.
  - task: Independent review of PR 201 mathematics and final research disposition
    operator: review_201_math; GPT-6 Astra max
    status: completed
    recording: retrospective
    phase: 1
    outcome: T-029 and T-030 passed both routes; n=29 passed exact verification but remains interval-unresolved.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [80 focused tests passed; separate exact and interval certificate replays.]
    uncertainty: The n=29 artifact has no accepted second-route verification and is not promoted.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Preserve the accepted n=18 results and correct unresolved dispositions.
  - task: Repair solver and geometry boundaries
    operator: fix_math_boundaries; GPT-5.6 Sol xhigh
    status: completed
    recording: retrospective
    phase: 1
    outcome: Solver outcomes retain diagnostics; unsupported angles and weighted columns fail closed.
    evidence: [packing/tests/test_produce_threshold_certificate.py, packing/tests/test_integral_piercing.py, packing/tests/test_threshold_separation.py]
    files: [packing/devtools/produce_threshold_certificate.py, packing/src/sqpack/fractional/integral_piercing.py, packing/src/sqpack/fractional/threshold_separation.py]
    checks: [36 focused tests passed; four subsequent vector-shape controls passed in the producer suite; Ruff and BasedPyright passed.]
    uncertainty: Weighted column generation remains unsupported.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Independent review of queue ownership and integrated validation.
  - task: Repair covering-queue ownership and independently review solver boundaries
    operator: fix_queue_ownership; GPT-5.6 Sol xhigh
    status: completed
    recording: retrospective
    phase: 1
    outcome: >-
      Output leases exclude concurrent writers and survive an orphaned generator;
      exceptions release ownership. Independent review added solver-vector shape checks.
    evidence: [packing/tests/test_covering_queue.py, packing/tests/test_produce_threshold_certificate.py]
    files: [packing/devtools/run_covering_queue.py, packing/tests/test_covering_queue.py, .gitignore, packing/devtools/produce_threshold_certificate.py, packing/tests/test_produce_threshold_certificate.py]
    checks: [10 queue tests and 20 producer tests passed; Ruff and BasedPyright passed.]
    uncertainty: Direct generator invocations do not participate in the queue-walker lease.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Integrated validation of the correction layer.
  - task: Reconcile research evidence and unresolved outcomes
    operator: fix_research_records; GPT-5.6 Sol high
    status: completed
    recording: retrospective
    phase: 1
    outcome: >-
      Fifteen subjects now have numerical assurance; unfinished runs remain unresolved;
      census, direction counts, T-027 provenance and T-029 artifact identity are corrected.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: [packing/frontier/results.yaml, packing/frontier/evidence.yaml, packing/campaign/explorations/X-038-n100-lower-bound-survey.md, packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md]
    checks: [Schema, campaign, inventory, result and certificate record checks passed; Flowmark and diff checks passed.]
    uncertainty: Numerical restricted optima do not establish exact lower bounds on their own.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Regenerate coordinator-owned views and validate the final tree.
  - task: Repair atlas publication and add fast claim-drift detection
    operator: fix_math_boundaries; GPT-5.6 Sol xhigh
    status: completed
    recording: retrospective
    phase: 1
    outcome: >-
      Eight composite SVG/PNG/PDF outputs regenerated. Fast retained checks compare
      visible labels to the figure record without rebuilding the geometry.
    evidence: [packing/tests/test_known_best_atlas.py, packing/atlas/known-best/known-best-1-100.svg, packing/atlas/known-best/known-best-1-324.svg]
    files: [packing/devtools/build_known_best_atlas.py, packing/tests/test_known_best_atlas.py, packing/atlas/known-best/known-best-1-100.svg, packing/atlas/known-best/known-best-1-324.svg]
    checks: [Canonical atlas update passed; four fast atlas tests passed; labels and all export receipts passed; Ruff and BasedPyright passed.]
    uncertainty: Full geometry validation belongs to the coordinator's full checkpoint.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Final integrated validation; no duplicate whole-corpus rebuild in this lane.
  - task: Independently review the integrated computational boundaries
    operator: fix_queue_ownership; GPT-5.6 Sol xhigh
    status: completed
    recording: retrospective
    phase: 2
    outcome: No further interaction defect found in solver diagnostics, queue lifetime, geometry guards, or atlas labels.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [Read-only review of 2aaa296d through 4c202aeb; no duplicate tests.]
    uncertainty: Static review is not a replacement for the final checkpoint.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Complete final mathematical review and validation.
  - task: Adversarial final review of proof arguments and corrected boundaries
    operator: final_math_adversarial; GPT-6 Astra max
    status: completed
    recording: retrospective
    phase: 2
    outcome: >-
      Found positive-infinite marginals being clipped before validation and an n=29
      receipt inconsistency. No additional flaw in the retained proof arguments.
    evidence: [packing/tests/test_produce_threshold_certificate.py, docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [Positive-infinity counterexample reproduced; proof bridge and n=29 assurance reviewed without duplicate certificate replays.]
    uncertainty: No external novelty search or new proof of the unchanged verifier.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Root integrates the two findings and repeats affected validation.
  - task: Prepare correction-layer dispositions and publication records
    operator: final_publication_records; GPT-5.6 Sol high
    status: completed
    recording: retrospective
    phase: 2
    outcome: Prepared publication records and independently audited hosted receipts against the final source tree and full step union.
    evidence: [docs/project/reviews/review-2026-09-19-pr199-201-correctness.md]
    files: []
    checks: [Documentation guidelines applied; fast, macOS and deferred receipts audited; no duplicate mathematical replays.]
    uncertainty: Root owns final integration and verification of CI outcomes.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Publish the measured final dispositions and preserve original-head limits.
  - task: Diagnose partial-selection scheduling and repair the timeout fixture
    operator: final_pipeline_analysis; GPT-5.6 Sol xhigh
    status: completed
    recording: retrospective
    phase: 2
    outcome: >-
      Tracked costly narrow-selection scheduling under think-1i1x. Replaced the
      200-millisecond child-startup assumption with deterministic timeout injection
      at the artifact-journaling boundary; real subprocess coverage remains separate.
    evidence: [packing/tests/test_validation_cli.py]
    files: [packing/tests/test_validation_cli.py]
    checks: [125 validation CLI tests passed; Ruff and BasedPyright passed; D-502 through D-504 reconciled with the defect register and SYNOPSIS.]
    uncertainty: Automatic worker allocation remains an open efficiency follow-up.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Final hosted checkpoint; preserve H-216 as the selected research entry.
  outputs:
  - docs/project/reviews/review-2026-09-19-pr199-201-correctness.md
  - packing/campaign/agent-sessions/session-142-stack-correctness.md
  checks:
  - T-027, T-028, T-029 and T-030 passed exact and interval replay with zero stalled boxes.
  - Targeted original-stack engineering tests passed; the lower PR direction-count assertion is wrong.
  - 'full gate: fast at 4c202aeb: passed (hosted run 35479932912; merge 564d5dbc has the same Git tree as the head)'
  - The final solver fix passes 52 boundary and queue tests; the deterministic timeout fixture passes all 125 validation CLI tests.
  - 'full gate: full at 8dbc1068: passed (hosted fast 35480879196 plus deferred 35480905141; clean merge 8ac5a340 has the identical source tree)'
  - Final local push passed 49 selected steps and 1619 affected tests in 392.33 seconds.
  - Seven defect-log and eleven synopsis negative controls passed after D-502 through D-504 were added.
  stop_reason: >-
    Review and bounded correctness repairs are complete and published as PR 202.
    Original lower-head failures remain explicit; costly partial-selection allocation
    is deferred under think-1i1x. No merge or new research was performed.
  next_action: Return to H-216 under think-qqzs.
---
# Session 142: Stack Correctness Pass

The overall entry point was **W2 factual review**, focused on mathematical and
engineering correctness.
That initial review is recorded retrospectively in the linked review: all four retained
n=18 certificates passed both routes, and eight findings plus three smaller corrections
were filed under `think-x2n7`. It preceded this clocked integration session and is not
presented as a preregistered phase.
The user then requested a new correction PR and explicit correctness-workflow tracking.
The final W2 pass audited the integrated repairs and their matching full checkpoint.

The bounded **W7 pipeline-improvement** phase addresses the reproduced solver,
input-domain and scheduler defects.
Three implementation lanes have disjoint write scopes: mathematical boundaries and their
tests, research records, and queue ownership and its tests.
The coordinator owns integration, the review, the defect register, generated views and
validation. The planning budget is a checkpoint, not a reason to leave the authorized
corrections unfinished.

No new mathematical result is claimed.
Lower PR history remains unchanged: a correction at the stack tip does not make an
earlier failing revision pass.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
