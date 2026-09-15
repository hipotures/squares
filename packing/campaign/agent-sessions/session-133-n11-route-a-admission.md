---
title: session-133 — n11 Route A admission
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-133
  title: N11 Route A Admission
  date: '2026-09-14'
  started_at: '2026-09-15T02:37:36Z'
  deadline_at: '2026-09-15T03:52:36Z'
  branch: codex/n11-route-a-admission
  primary_bead: think-0t5y
  status: in_progress
  goal: >-
    Decide whether one complete same-corner availability-blocker root at side 96/25 can
    be represented with shared physical geometry and checked exactly before any
    scientific target runs.
  budget:
    wall_minutes: 75
    max_cycles: 3
    orientation_minutes: 10
    checkpoint_minutes: 30
    slice_minutes: 60
    finalization_minutes: 15
  stop_conditions:
  - >-
    Preserve the denominator of 16 ordered physical blocker roots; leaf, chart, and
    incidence subdivisions never increase the numerator.
  - >-
    Admit all label, pose, ownership, co-ownership, missing-mark, and seam cases with
    shared parent variables, or stop Route A at the representation boundary.
  - >-
    Freeze the matched baseline, candidate rows, controls, certificate format,
    independent checker, acceptance rule, and kill rule without running a scientific
    target.
  workflow_phases:
  - workflow: pipeline-improvement
    focus: process
    recording: contemporaneous
    clock_role: work
    commitment: BC-354
    bead: think-0t5y
    objective: >-
      Admit or reject the complete representation and exact-checking path for one
      same-corner Route A root at q = 96/25.
    status: in_progress
    entered_by: session_start
    switch_reason: null
    budget_minutes: 60
    started_at: '2026-09-15T02:37:36Z'
    deadline_at: '2026-09-15T03:37:36Z'
    expected_output: >-
      A denominator-preserving root specification, complete domain partition, matched
      controls, checker contract, and an admit-or-park decision in a separate pull request.
    validation_command: >-
      cd packing && env PYTHON_CPU_COUNT=4
      DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/opt/cairo/lib uv run --frozen
      --all-extras --group dev packing-validate --fast --jobs 3 --inner-jobs 1
    kill_condition: >-
      Park Route A if the 80 incidence strata, universal negative-label condition,
      shared parent/core variables, or method-distinct exact checker cannot be frozen
      inside the block; do not substitute a positive raw owner tuple.
    fallback: >-
      Make Route S's at-most-23-orbit certificate-compression admission the sole next
      entry without running either route's target.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: >-
      Reconcile the domain, checker, and control inventories into one executable
      admission contract before selecting an implementation slice.
  progress:
    metric: >-
      Required physical strata and invariants represented, exact checker obligations
      discharged, controls bound, and admission verdict reached.
    before: >-
      BC-353 selected the same-corner root, but existing tooling covers fixed positive
      owner classes rather than universal absence of labels 0 and 15 across all 80
      physical incidence strata.
    after: null
  delegations:
  - task: Inventory the complete physical domain for the selected same-corner root.
    operator: Codex domain-audit sub-agent, read-only
    status: completed
    recording: contemporaneous
    outcome: >-
      The selected root is the universal negative condition A_BL(P) intersect {0,15}
      empty across all 80 incidence strata, not one positive owner tuple. A full-domain
      proof transports to four same-corner roots but closes none of the eight adjacent
      or four opposite roots.
    evidence:
    - docs/project/research/research-2026-09-12-n11-selection-routing-first-principles.md
    - docs/project/reviews/review-2026-09-12-n11-selection-routing-first-principles.md
    files: []
    checks:
    - Read-only source audit; no target or verifier ran.
    uncertainty: The repository has no seam-safe shared-owner stratifier for this negative root.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Freeze the 80-stratum manifest and shared physical variables.
    phase: 1
  - task: Inventory the conditional-domain checker and adapter gap.
    operator: Codex checker-architecture sub-agent, read-only
    status: completed
    recording: contemporaneous
    outcome: >-
      Existing geometry code can decompose polygon residual domains, but the production
      threshold gate has no conditional-domain field and assumes D4-invariant atoms on
      the folded net. Admission requires a physical-root producer, a full-net generic
      polygon-domain sweep, and a method-distinct conditional interval replay.
    evidence:
    - packing/devtools/multi_owner_domains.py
    - packing/devtools/decide_threshold_certificate.py
    - packing/src/sqpack/fractional/threshold.py
    - packing/src/sqpack/fractional/threshold_interval.py
    files: []
    checks:
    - Read-only source audit; no target or verifier ran.
    uncertainty: A residual-domain adapter alone cannot represent shared parent compatibility.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Define the strict conditional-domain record and minimal reusable reducer.
    phase: 1
  - task: Inventory the matched baseline, controls, and admission verdict rules.
    operator: Codex controls-audit sub-agent, read-only
    status: completed
    recording: contemporaneous
    outcome: >-
      T-023 and T-025 supply geometry and checker controls, but neither is a rows-complete
      exact point baseline on the selected root. Acceptance requires identical physical
      domains, strict budget below 7 minus sigma on every stratum, two exact routes, and
      transfer to continuous angles; a complete survivor parks the representation.
    evidence:
    - packing/campaign/hypotheses/H-155-conditional-threshold-cover-on-an-owner-class.md
    - packing/cases/n11_threshold_certificate/t-025-threshold-certificate-proof.md
    - packing/devtools/check_n11_selection_routing.py
    files: []
    checks:
    - Read-only source audit; no target or verifier ran.
    uncertainty: The matched exact point-resource lower-bound receipt does not yet exist.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Bind the baseline claim and mutation controls before implementation.
    phase: 1
  outputs:
  - packing/campaign/agent-sessions/session-133-n11-route-a-admission.md
  - packing/campaign/agendas/agenda-036-n11-strategy-reset-roadmap.md
  checks:
  - The branch base is merged planning revision a9de8a705d785e5b7b6ac46f28c11b6f5a45d7c6.
  - No scientific target, solver, search, or verifier has run in BC-354.
  stop_reason: null
  next_action: Freeze the complete Route A domain and checker contract, or park it for Route S.
---
# N11 Route A Admission

This is the first active-hour block after the post-W5 planning merge.
It admits the representation and exact checker before any target run; an incomplete
positive owner-class proxy does not count as the selected physical root.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
