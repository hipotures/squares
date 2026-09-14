---
title: agenda-036 — n11 strategy-reset roadmap
softschema:
  contract: packing.squares:ExperimentAgenda/v1
  schema: ../schemas/agenda.schema.yaml
  envelope: agenda
  status: enforced
agenda:
  id: agenda-036
  title: N11 Strategy-Reset Roadmap
  updated: '2026-09-14'
  status: active
  objective: >-
    Reconcile the merged research record, then choose among routes that can either
    improve the n=11 bound materially or replace the current certificate with a much
    simpler proof. Keep paused incremental lanes out of the execution queue unless new
    evidence changes their expected value.
  items:
  - id: BC-339
    purpose: tool_validation
    owner_focus: process
    instances: [11]
    state: in_progress
    priority: 0
    question: >-
      Can the post-merge agendas, sessions, explorations, hypotheses, experiments,
      frontier results, strategic boundary, and selected handoff be reconciled into one
      checked reader-facing account?
    budget: >-
      One W7 pipeline-improvement block with three independent read-only audits,
      source-first reconciliation, a durable W8 roll-up procedure, generated-view
      refresh, a focused drift check, and no scientific target.
    entry: >-
      PRs 156, 157, 161–168 have landed; the old selected handoff points at paused work;
      H-160 and H-162 are registered without target receipts; and the owner has selected
      a significant-improvement-or-simplification strategy.
    exit: >-
      SYNOPSIS.md carries a checked current-state block and one current handoff, README.md
      routes readers to it without copying volatile totals, the active plans state the
      strategy reset, and W8 defines how to repeat the roll-up.
    bead: think-uqa4
    depends_on: []
    next_evidence: >-
      Commit the reconciled records and documents, pass the records, push, and complete
      validation tiers, and retain a terminal session pointing at BC-347.
    workflows: [pipeline-improvement, documentation-pass]
    program: n11-strategy-reset
    artifacts:
    - SYNOPSIS.md
    - README.md
    - packing/campaign/documentation-pass.md
    - docs/project/specs/active/plan-2026-09-10-n11-daytime-strategy-and-explainer.md
    parallel_group: research-state-rollup
  - id: BC-347
    purpose: research
    owner_focus: insight
    instances: [6, 7, 10, 11, 13]
    state: blocked
    priority: 0
    question: >-
      Which mathematically distinct approaches have a credible path to significant
      progress on n=11 or transferable small-n techniques, given the retained theorems,
      scoped negatives, and tooling?
    budget: >-
      One read-only deep mathematical audit delegated to Astra Max. Evaluate Routes A,
      B, S, C, and D, generate additional hypotheses and approaches, rank them by
      information value and material upside, and run no scientific target.
    entry: >-
      BC-339 closes with one checked source inventory, scientific boundary, tool
      inventory, and current handoff.
    exit: >-
      A durable mathematical audit separates proved facts, evidence-backed inference,
      and speculation; ranks the enlarged route set; and gives each serious candidate a
      prerequisite, cheapest discriminator, transfer value, and kill or continue rule.
    bead: think-oj12
    depends_on: [BC-339]
    next_evidence: >-
      Read the retained n11 proof and negative-result stack, then test whether each
      proposed mechanism escapes the known point-certificate ceiling or merely
      repackages an incremental lane.
    workflows: [factual-review, insight-iteration]
    program: n11-strategy-reset
    artifacts:
    - docs/project/reviews/review-2026-09-14-small-n-significant-progress-mathematical-audit.md
    parallel_group: mathematical-strategy-audit
  - id: BC-346
    purpose: tool_validation
    owner_focus: process
    instances: [11]
    state: blocked
    priority: 0
    question: >-
      Given the reconciled state, is the validation-efficiency checkpoint due, and which
      one of it or Routes A, B, S, C, and D has the highest information value as the
      next bounded block?
    budget: >-
      One W10 planning block over dependency readiness, expected information value,
      stop rules, and resource cost; no implementation or scientific target.
    entry: >-
      BC-347 closes with a source-bound audit, enlarged approach set, relative priorities,
      and explicit discriminator and stop rules.
    exit: >-
      Exactly one selected next entry, with the remaining candidates explicitly
      continued, paused, or stopped and the active plan and handoff updated together.
    bead: think-9y7p
    depends_on: [BC-347]
    next_evidence: >-
      Reconstruct the W5 cadence, then compare any due checkpoint with the five shaped
      routes using their declared first discriminators; select one block rather than a
      multi-lane research promise.
    workflows: [review-planning-oversight]
    program: n11-strategy-reset
    parallel_group: route-selection
  - id: BC-340
    purpose: measurement_validation
    owner_focus: efficiency
    instances: [11]
    state: tentative
    priority: 0
    question: >-
      Does the four-to-eight-block cadence make an efficiency checkpoint due, and if so
      what one demonstrated bottleneck should it address before another large research
      block starts?
    budget: >-
      One W5 checkpoint from actual session and validation receipts; change at most one
      bottleneck behind an equivalence guard, or record a measured no-change decision.
    entry: BC-346 selects this checkpoint from the reconciled sequence and retained costs.
    exit: >-
      One measured bottleneck disposition or an evidence-backed no-change result, then a
      terminal handoff to a fresh W10 route selection. If the checkpoint is not due,
      BC-346 selects the scientific route directly and BC-340 remains tentative.
    bead: think-1ydi
    depends_on: [BC-346]
    next_evidence: >-
      Reconstruct the cadence from active daytime blocks and retained gate receipts;
      administrative work does not reset the cadence.
    workflows: [efficiency-loop, review-planning-oversight]
    program: n11-strategy-reset
    parallel_group: efficiency-checkpoint
  - id: BC-341
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 1
    question: >-
      At side 3.85, how much of the admissible occupancy or wall-contact case space can
      proved capacity caps and conditional threshold certificates close?
    budget: >-
      One day-or-less Route A discriminator: enumerate the proved case split, certify
      each closed case, and report both the closed share and the worst surviving class.
    entry: BC-346 selects Route A and the case partition, capacity caps, and unchanged certificate checker are frozen.
    exit: >-
      A measured fraction of cases closed with exact receipts and a named worst residual;
      continue only if the split removes a substantial part of the 3.85 problem.
    bead: think-9y6q
    depends_on: [BC-346]
    next_evidence: >-
      Freeze the smallest occupancy/contact partition that strictly extends T-023's
      single four-owner branch without claiming an owner-selection theorem.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: significant-lower-bound
  - id: BC-342
    purpose: research
    owner_focus: insight
    instances: [6, 11]
    state: tentative
    priority: 1
    question: >-
      Does a sound theta-prime or level-two pairwise relaxation close the known n=6
      control near side 3, and if so does it improve materially on the n=11 LP at 3.84?
    budget: >-
      One control-first Route B block; no n=11 target until the n=6 formulation,
      discretization soundness, and symmetry handling are independently checked.
    entry: BC-346 selects Route B and a sound placement-graph discretization has an explicit conflict-edge guarantee.
    exit: >-
      A passed n=6 control and measured n=11 separation, or a precise formulation,
      scaling, or soundness obstruction that parks the route.
    bead: think-ol1z
    depends_on: [BC-346]
    next_evidence: Specify the n=6 control and the conflict-edge soundness obligation before selecting a solver.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: pairwise-relaxation
  - id: BC-343
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 2
    question: >-
      Can the T-025/T-026 witness at side 3.82 be compressed into a small exact
      certificate described by a few D4-orbit, weight, and tight-cell templates?
    budget: >-
      One bounded Route S compression pass over the retained witness; test sparse or
      quantized templates with the existing exact coverage and budget replay.
    entry: BC-346 selects Route S and the unmodified T-025/T-026 receipt is the control.
    exit: >-
      A substantially smaller exact certificate with a human-statable template, or a
      recorded compression obstruction that parks this simplification route.
    bead: think-a1e8
    depends_on: [BC-346]
    next_evidence: Group the exact witness by D4 orbit, weight, and tight-cell incidence before changing any atom.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: proof-simplification
  - id: BC-344
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 2
    question: >-
      Can a robust orientation-class theorem rule out every two-orientation packing
      below Trump's recorded side, beginning with the 6+5 class at Trump's angle?
    budget: >-
      One Route C feasibility block with seeded layouts, exact disjunctive checks at the
      control angle, and one-degree interval bins near side 3.87.
    entry: BC-346 selects Route C and the fixed-angle control reproduces a known feasible arrangement before any exclusion claim.
    exit: >-
      A sound excluded orientation window with exact evidence, or a named feasibility or
      interval obstruction that prevents a structural theorem.
    bead: think-29ch
    depends_on: [BC-346]
    next_evidence: Reproduce the 6+5 control at Trump's angle before interpreting any solver infeasibility.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: orientation-structure
  - id: BC-345
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 3
    question: >-
      What competing local optima appear under a serious orientation-profile-organized
      n=11 search, and can any improve the 1979 upper bound after exact polishing?
    budget: >-
      One background Route D campaign at roughly one hundred times the earlier
      calibration budget, with exact polishing and rigidity checks for every endpoint at
      or below 3.90.
    entry: BC-346 selects Route D and the runner reproduces Trump's packing and its exact side as a positive control.
    exit: >-
      A new verified upper bound, or a retained catalogue of exact-polished competing
      optima useful to an optimality proof; unverified or unreplayed sub-Trump artifacts
      are presumed bugs until exact verification.
    bead: think-7n2w
    depends_on: [BC-346]
    next_evidence: Design the positive-control and endpoint-polishing contract before allocating the background search.
    workflows: [research-survey, research-loop]
    program: n11-strategy-reset
    parallel_group: upper-bound-search
---
# N11 Strategy-Reset Roadmap

This agenda is the current execution map after the September 14 strategy reset.
It preserves the older portfolio’s completed evidence while removing its paused
incremental lanes from the live queue.

The order is deliberate: finish the checked research-state roll-up, run one deep
mathematical audit that may enlarge the route set, then run one planning block that
first determines whether the efficiency checkpoint is due and selects exactly one
execution entry. Route A is the standing scientific favorite before the audit, not an
authorization to skip that analysis or the later selection.
Every unselected route remains tentative until the planning disposition says otherwise.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
