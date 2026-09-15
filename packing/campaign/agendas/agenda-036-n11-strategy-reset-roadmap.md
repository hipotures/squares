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
    improve the n=11 bound materially, replace the current certificate with a much
    simpler proof, or resolve another small case through a transferable technique. Keep
    paused incremental lanes out of the execution queue unless new evidence changes
    their expected value.
  items:
  - id: BC-339
    purpose: tool_validation
    owner_focus: process
    instances: [11]
    state: complete
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
      BC-347 consumes the checked inventory and scientific boundary without reopening
      the source reconciliation.
    workflows: [pipeline-improvement, documentation-pass]
    program: n11-strategy-reset
    artifacts:
    - SYNOPSIS.md
    - README.md
    - packing/campaign/documentation-pass.md
    - docs/project/specs/active/plan-2026-09-10-n11-daytime-strategy-and-explainer.md
    parallel_group: research-state-rollup
    outcomes:
    - scope: >-
        The reader-facing research inventory, source precedence, generated views,
        current handoff, and repeatable roll-up procedure after the September 14 merge
        stack.
      classification: achieved
      result: >-
        The synopsis now carries a source-derived program snapshot and current handoff;
        README and the active plans route through it; W8 defines the repeatable roll-up;
        and focused checks reject stale counts, lifecycle ordering, and handoff drift.
        No scientific target or frontier claim changed.
      evidence:
      - SYNOPSIS.md
      - README.md
      - packing/campaign/documentation-pass.md
      - packing/campaign/agent-sessions/session-128-research-state-rollup.md
      disposition: retire-success
      follow_up: null
  - id: BC-347
    purpose: research
    owner_focus: insight
    instances: [6, 7, 10, 11, 13]
    state: complete
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
      BC-346 compares the audited prerequisites, first discriminators, payoff, and cost
      and selects exactly one execution entry.
    workflows: [factual-review, insight-iteration]
    program: n11-strategy-reset
    artifacts:
    - docs/project/reviews/review-2026-09-14-small-n-significant-progress-mathematical-audit.md
    parallel_group: mathematical-strategy-audit
    outcomes:
    - scope: >-
        The retained n11 proof, fractional ceiling, scoped negative results, five shaped
        routes, and additional mechanisms with potential at n=11 or another small n.
      classification: achieved
      result: >-
        Astra Max ranked the original A, S, B, C, and D routes; added E, F1, F2, N, and
        G; corrected premises and discriminators; and advised the order A, S, E, B, F1,
        F2, N, C, D, G. This is a recommendation, not a selected scientific target.
      evidence:
      - docs/project/reviews/review-2026-09-14-small-n-significant-progress-mathematical-audit.md
      disposition: retire-success
      follow_up: null
  - id: BC-346
    purpose: tool_validation
    owner_focus: process
    instances: [11]
    state: in_progress
    priority: 0
    question: >-
      Given the reconciled state, is the validation-efficiency checkpoint due, and which
      one entry from the enlarged audited route set has the highest information value
      as the next bounded block?
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
      Reconstruct the W5 cadence, then compare any due checkpoint with Routes A, S, E,
      B, F1, F2, N, C, D, and G using their declared first discriminators; select one
      block rather than a multi-lane research promise.
    workflows: [review-planning-oversight]
    program: n11-strategy-reset
    artifacts:
    - docs/project/reviews/review-2026-09-14-n11-w10-route-selection.md
    - packing/campaign/agent-sessions/session-130-n11-w10-route-selection.md
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
      terminal handoff to BC-353's fresh W10 route selection.
    bead: think-1ydi
    depends_on: [BC-346]
    next_evidence: >-
      Reconstruct the cadence from active daytime blocks and retained gate receipts;
      administrative work does not reset the cadence.
    workflows: [efficiency-loop, review-planning-oversight]
    program: n11-strategy-reset
    parallel_group: efficiency-checkpoint
  - id: BC-353
    purpose: tool_validation
    owner_focus: process
    instances: [11]
    state: blocked
    priority: 0
    question: >-
      After the due efficiency checkpoint, which one scientific route has the highest
      information value under the new gate evidence and retained mathematical audit?
    budget: >-
      One fresh W10 planning block after BC-340. Recheck repository stability and all
      scientific candidates; select exactly one execution entry and run no target.
    entry: >-
      BC-340 closes with a measured repair or measured no-change decision, its own merged
      pull request, and a terminal handoff to this block.
    exit: >-
      Exactly one scientific route is selected, every alternative has an explicit
      disposition and resume condition, and only the selected route becomes ready.
    bead: think-d3h5
    depends_on: [BC-340]
    next_evidence: >-
      Reconsider Route A at side 3.84 first, Route S as its admission fallback, and Route
      E in the first tier, while incorporating BC-340's measured result.
    workflows: [review-planning-oversight]
    program: n11-strategy-reset
    parallel_group: post-efficiency-route-selection
  - id: BC-341
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 1
    question: >-
      At side 3.84, can one complete difficult occupancy or wall-contact root family be
      closed by proved capacity caps and conditional certificates, with 3.85 retained
      only as a stretch target after its premises are re-established?
    budget: >-
      One day-or-less Route A discriminator: freeze an original root-family denominator,
      certify each closed domain, and report the unchanged denominator, closed roots,
      and exact worst surviving domain. Subdivided leaves do not change the denominator.
    entry: BC-353 selects Route A and the case partition, capacity caps, and unchanged certificate checker are frozen.
    exit: >-
      A complete difficult root family closes or a precise relaxation witness and worst
      surviving domain identify why it does not. Continue only on new matched strength.
    bead: think-9y6q
    depends_on: [BC-353]
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
      Does a sound theta-prime or level-two pairwise relaxation pass the n=6 formulation
      controls and improve materially on the strongest matched n=11 point-and-threshold
      baseline at 3.84?
    budget: >-
      One control-first Route B block; no n=11 target until the n=6 formulation,
      discretization soundness, and symmetry handling are independently checked.
    entry: BC-353 selects Route B and a sound placement-graph discretization has an explicit conflict-edge guarantee.
    exit: >-
      A passed n=6 control and measured n=11 separation, or a precise formulation,
      scaling, or soundness obstruction that parks the route.
    bead: think-ol1z
    depends_on: [BC-353]
    next_evidence: Specify the n=6 control and the conflict-edge soundness obligation before selecting a solver.
    workflows: [insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: pairwise-relaxation
  - id: BC-343
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 1
    question: >-
      Can the T-025/T-026 witness at side 3.82 be compressed into a small exact
      certificate described by a few D4-orbit, weight, and tight-cell templates?
    budget: >-
      One bounded Route S pass beginning with T-025; test sparse or quantized templates
      with the existing exact coverage and budget replay.
    entry: BC-353 selects Route S and the unmodified T-025/T-026 receipt is the control.
    exit: >-
      A fivefold reduction in orbit representatives or comparable independent geometric
      complexity, with a human-statable generating rule and exact replay, or a recorded
      obstruction that parks the selected template family.
    bead: think-a1e8
    depends_on: [BC-353]
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
      One Route C feasibility block with the exact Trump-angle control followed by one
      complete positive-width interval at a rational target near 3.87. Midpoint shrink
      does not make one-degree bins adequate.
    entry: BC-353 selects Route C and the fixed-angle control reproduces a known feasible arrangement before any exclusion claim.
    exit: >-
      A sound excluded orientation window with exact evidence, or a named feasibility or
      interval obstruction that prevents a structural theorem.
    bead: think-29ch
    depends_on: [BC-353]
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
      One background Route D proposer-control block comparing one changed proposal
      mechanism with the stock control at equal pair-test work. A larger campaign is
      admissible only after independent or perturbed starts recover an oblique control.
    entry: BC-353 selects Route D and the runner reproduces Trump's packing and its exact side as a positive control.
    exit: >-
      A new verified upper bound, or a retained catalogue of exact-polished competing
      optima useful to an optimality proof; unverified or unreplayed sub-Trump artifacts
      are presumed bugs until exact verification.
    bead: think-7n2w
    depends_on: [BC-353]
    next_evidence: Design the positive-control and endpoint-polishing contract before allocating the background search.
    workflows: [research-survey, research-loop]
    program: n11-strategy-reset
    parallel_group: upper-bound-search
  - id: BC-348
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 1
    question: >-
      Do H-131's proved aggregate angle-count caps, admitted as coherent global
      resources, remove the retained fractional optimal face beyond the strongest
      matched point-and-threshold baseline?
    budget: >-
      One Route E admission-and-discrimination block. Freeze a common angle partition,
      coherent selection semantics, every admissible integer profile, the matched
      baseline, and an exact checker before any synthesis target.
    entry: BC-353 selects Route E and the existing H-131 cap receipts are replayed without strengthening their scope.
    exit: >-
      A valid angular resource removes an optimum retained by the matched baseline, or
      an exact surviving optimum parks this cap family while leaving other angle bands
      and charge functions open.
    bead: think-u15l
    depends_on: [BC-353]
    next_evidence: Test the valid angle-count rows against the entire retained optimal face before building a larger certificate.
    workflows: [factual-review, insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: global-angular-resources
  - id: BC-349
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 2
    question: >-
      Can a weighted motif, genuinely multilevel floor atom, or higher-rank composition
      strictly dominate ordinary threshold atoms on one exact realizable trace universe?
    budget: >-
      One Route F1 discriminator. Freeze one candidate charge language, trace universe,
      ordinary-threshold baseline, and exact evaluator; declare whether think-g3j7's
      certificate-format work is a prerequisite.
    entry: BC-353 selects Route F1 and freezes the exact realizable trace universe and matched ordinary-threshold comparison.
    exit: >-
      An exact strict domination gap justifies a larger support-and-atom comparison; an
      ordinary domination proof parks the tested motif without judging other charge
      languages.
    bead: think-o4p9
    depends_on: [BC-353]
    next_evidence: Relate the selected candidate explicitly to adjacent think-yc80 support work and think-g3j7 format admission.
    workflows: [factual-review, insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: stronger-charge-language
  - id: BC-352
    purpose: research
    owner_focus: insight
    instances: [11]
    state: tentative
    priority: 2
    question: >-
      Can joint-parent geometry lower the ordinary budget of one atom by proving that two
      simultaneous physical parents cannot both trigger it in a declared domain?
    budget: >-
      One Route F2 discriminator. Freeze one atom with ordinary budget at least two, one
      joint-parent domain, exact containment and trigger semantics, and a complete pair
      evaluator.
    entry: BC-353 selects Route F2 and separates its physical capacity theorem from charge-language and serializer work.
    exit: >-
      A complete joint-parent exclusion lowers the selected atom's budget, or one feasible
      simultaneous triggering pair rejects that reduction without judging other atoms.
    bead: think-iy9h
    depends_on: [BC-353]
    next_evidence: Decide whether the selected atom needs think-g3j7's K5/K6 format before freezing the scientific target.
    workflows: [factual-review, insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: geometry-dependent-budget
  - id: BC-350
    purpose: research
    owner_focus: insight
    instances: [6, 12, 13]
    state: tentative
    priority: 2
    question: >-
      Can one uniform boundary-capacity or deformation lemma for L = 4 - epsilon turn
      the open n12 bracket into a stable finite reduction toward s(12) = 4?
    hypotheses: [H-039]
    budget: >-
      One Route N discriminator over a nontrivial epsilon interval, with n=6 and n=13
      as solved controls and the flexible side-four n12 family included. Do not resume a
      decimal ladder.
    entry: BC-353 selects Route N and freezes the uniform lemma, interval, control behavior, and exact replay contract.
    exit: >-
      A stable complete case reduction or exact parameterized inequality, or a legal
      flex or boundary degeneration that parks the mechanism without resolving H-039.
    bead: think-0z9b
    depends_on: [BC-353]
    next_evidence: Reuse H-039 and the existing n12 lane with its obsolete pre-T-017 target explicitly superseded.
    workflows: [factual-review, insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: n12-exact-value
  - id: BC-351
    purpose: research
    owner_focus: insight
    instances: [6, 11]
    state: tentative
    priority: 3
    question: >-
      Can an orientation-sensitive two- or three-parent gap lemma be summed without
      double counting to prove geometric waste beyond the one-body density ceiling?
    budget: >-
      One speculative Route G discriminator: one exact local lemma, the Trump and n=6
      angular-rattler controls, and one explicit global accounting map.
    entry: BC-353 selects Route G and freezes the local domain, deficit, degeneration controls, and non-overcounting obligation.
    exit: >-
      Both the uniform local deficit and complete accounting rule hold, or a legal
      degeneration or duplicate charge parks the candidate.
    bead: think-gzjq
    depends_on: [BC-353]
    next_evidence: Register no hypothesis until W10 selects one concrete local lemma and domain.
    workflows: [factual-review, insight-iteration, research-loop]
    program: n11-strategy-reset
    parallel_group: geometric-waste
---
# N11 Strategy-Reset Roadmap

This agenda is the current execution map after the September 14 strategy reset.
It preserves the older portfolio’s completed evidence while removing its paused
incremental lanes from the live queue.

The research-state roll-up and mathematical audit are certified and closed in declared
dependency order. BC-346’s W10 review has now selected BC-340, the due W5 efficiency
checkpoint, as the next execution entry; exact-revision certification is still pending.
A conservative source reconstruction counts eight substantive non-W5 blocks since the
latest qualifying W5 in Session 116/BC-322, which reaches OR-12’s mandatory ceiling.

No scientific target is authorized before W5 closes and BC-353’s fresh W10 selects one.
The advisory scientific order remains A at side `3.84`, S, angular resources, B,
stronger charge algebra, geometry-dependent budgets, n12, C, D, then geometric waste.
Route A is the expected first scientific choice and Route S is its admission fallback,
but both remain tentative until the post-W5 planning block.

The W10 review maps the next six active work hours into five sequential PR-bounded
blocks: BC-340 W5, BC-353 W10, selected-route admission, one exact discriminator, and a
review-and-replan closeout.
The last three blocks are conditional on the preceding exit; an unadmitted target does
not run, and no later branch starts before the prior PR merges.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
