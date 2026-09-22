---
title: Session 152 — External rectangle-density and n11 certificate review
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-152
  title: External rectangle-density and n11 certificate review
  date: '2026-09-22'
  started_at: '2026-09-22T17:55:23.253Z'
  deadline_at: '2026-09-22T21:55:23.253Z'
  branch: codex/pr-219-followup
  primary_bead: think-6xoc
  status: in_progress
  goal: >-
    Retain the complete Tokoharu and Kleddamag source repositories and supplied social
    claims, independently audit the mathematics and executable certificates, and
    integrate supported findings into the Frontier without conflating source claims,
    source-checker replays, independent verification, and result promotion.
  workflow_phases:
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Audit the frozen external proof packages, with W1 acquisition as a supporting
      lane and a final integration review against the existing proof contracts.
    status: in_progress
    entered_by: session_start
    switch_reason: null
    budget_minutes: 240
    started_at: '2026-09-22T17:57:35Z'
    deadline_at: '2026-09-22T21:40:23.253Z'
    expected_output: Retained sources, two mathematical audits, replay receipts, and reconciled Frontier records.
    validation_command: cd packing && .venv/bin/packing-validate
    kill_condition: A certificate fails a load-bearing soundness or completeness condition.
    fallback: Preserve the failure, retain the public claim as reported, and record the exact promotion blocker.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: Pin source trees and identify the complete replay and proof obligations.
  budget:
    wall_minutes: 240
    slice_minutes: 30
  stop_conditions:
  - Complete every source-claim disposition and integration obligation, or document a concrete external blocker.
  - Planning estimates are checkpoints, not authority to truncate the requested review.
  - No verified-bound promotion from a passing source checker alone.
  progress:
    metric: Reviewed external certificate claims with reproducible provenance and explicit assurance.
    before: The supplied n11, n26, and n29 releases are absent from the Frontier source set.
    after: Complete source packet and three proof/integration reviews retained; all new full replays pass, supporting 19 case improvements plus the prior n17 adoption correction.
  delegations:
  - task: Acquire complete external repositories and social provenance
    operator: GPT-5.6 Sol, high
    status: completed
    recording: retrospective
    phase: 1
    outcome: Complete pinned source packet, release and social provenance retained.
    evidence: [packing/resources/web/external-square-certificates-2026-09-22/acquisition/sources.json]
    files: [packing/resources/web/external-square-certificates-2026-09-22/README.md]
    checks: [Eight per-tree SHA-256 manifests passed.]
    uncertainty: The unspecified later wand125 density improvement has no recovered numerical certificate.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Complete; all assigned case updates and the eight-manifest archive integrity check passed.
  - task: Review density mathematics, executable proof and import controls
    operator: GPT-6 Astra, max
    status: completed
    recording: retrospective
    phase: 1
    outcome: All three density replays passed; no proof blocker found; two false driver admissions reproduced.
    evidence: [docs/project/reviews/review-2026-09-22-tokoharu-density-mathematics.md]
    files: [packing/devtools/audit_tokoharu_density.py, packing/devtools/tokoharu_density_probe.cpp, packing/tests/test_tokoharu_density_audit.py]
    checks: [Full source coverage for n11/n26/n29, exact premise audit, 1080 polygon comparisons, 1296 line-section samples, six passing tests, Ruff and BasedPyright clean.]
    uncertainty: Independent probes do not decide complete global coverage by a second method.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Complete; the point adapter and all ten replays support the verified transfers, including local n52/n68 deductions.
  - task: Review n11 threshold mathematics and exact adversarial controls
    operator: GPT-6 Astra, max
    status: completed
    recording: retrospective
    phase: 1
    outcome: Complete Python and JavaScript sweeps, exact premises, adverse controls and reconciliation passed; independent cross-review found no proof blocker.
    evidence: [docs/project/reviews/review-2026-09-22-kleddamag-n11-mathematics.md]
    files: [packing/devtools/audit_kleddamag_n11.py, packing/tests/test_kleddamag_n11_audit.py]
    checks: [48112 exact quadratics and 12028 centre envelopes, 16 adverse controls, 34909 independently clipped sample slabs, six passing tests, Ruff and BasedPyright clean.]
    uncertainty: Complete event sweeps share a method; the independent complete coverage route remains unimplemented.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Complete; n11 and the prior n17 correction are recorded with strict endpoints and actual replay provenance.
  outputs:
  - docs/project/reviews/review-2026-09-22-external-square-certificates-integration.md
  - packing/resources/web/external-square-certificates-2026-09-22/README.md
  - packing/frontier/evidence.yaml
  - packing/frontier/source-coverage.yaml
  checks:
  - Baseline records tier passed 35 of 82 steps in 86.55 seconds after environment bootstrap.
  - Source coverage reconciled 324 cases and 648 printed facts with zero divergences.
  resource_rollups:
  - packing/campaign/resource-usage/codex-task-tree-session-152.yaml
  stop_reason: null
  next_action: Finish generated artifacts and final validation, then continue native parent-core generalization under think-d010.
---
# External Certificate Review

The owner requested this block on top of PR #219 at
`697cd74873140c9d594cb966e77ba082627aca9c`. The requested source set is Tokoharu’s
rectangle-density bounds for n = 26 and 29 and Kleddamag’s n = 11 certificate, including
the two supplied X posts and linked proof dependencies.
This overrides the standing handoff’s next research slice for this branch.

## Plan and ownership

Work proceeds in slices of at most 30 minutes, with an integration checkpoint targeted
within four hours.
A long checker may cross slice boundaries while its reviewer continues
independent proof analysis.
Each slice ends with a retained finding or a concrete revised next action; the estimate
does not cap the user’s request.

| Lane | Operator | Question and exit | Owned files |
| --- | --- | --- | --- |
| Acquisition | GPT-5.6 Sol, high | Are complete pinned trees, release assets, proof dependencies and social provenance retained? Exit with inventory and explicit omissions. | A new source packet and acquisition manifest under `packing/resources/web/` |
| Density mathematics | GPT-6 Astra, max | Do the measure theorem, continuous coverage, and arithmetic justify each claimed bound? Exit with a claim-by-claim proof or counterexample and replay evidence. | `docs/project/reviews/review-2026-09-22-tokoharu-density-mathematics.md` and its dedicated audit tool |
| n11 mathematics | GPT-6 Astra, max | Does the 3.875 certificate discharge continuous geometry, boundaries and exact arithmetic? Exit with proof obligations, adversarial controls and replay evidence. | `docs/project/reviews/review-2026-09-22-kleddamag-n11-mathematics.md` and its dedicated audit tool |
| Integration | Coordinator | Which reported, verified and research-planning records follow from the evidence? Exit with reconciled source records and passing relevant checks. | Shared Frontier records, session, synthesis, generated views and final commit |

The first acquisition dispatch requested `gpt-6-sol`, which the account rejected as
unsupported. No work ran in that dispatch; the replacement uses GPT-5.6 Sol at high.

1. Acquire and pin both repositories; inspect proof and replay entry points; run the
   existing record gate before registry edits.
2. Execute full supplied replays while independently deriving each mathematical
   implication. Record strict versus weak endpoints and all domain restrictions.
3. Exercise adversarial controls and compare decisive computations with independent
   reasoning or a separately implemented checker.
   Classify shared implementation ancestry.
4. Reconcile findings, preserve source claims and failures, and make only promotions
   justified by the existing assurance contract.
5. Review integration consequences for n11 and rectangle-density research; refresh
   affected reader and generated surfaces, run the documentation pass and validation,
   then retain the session cost and a concrete continuation.

## Acceptance rule

Source acquisition requires immutable Git identities and all files needed for offline
replay, with the user’s transcription distinguished from independently fetched text.
A source replay requires the entire declared job to finish successfully; partial or
sampled checks do not satisfy it.
Mathematical acceptance requires an argument covering every allowed translation and
rotation, correct measure/interior handling, and justified exact or outward-rounded
arithmetic. Local verification records name the actual checker and independence limits.
Result promotion obeys the existing strongest-certifiable-bound contract.
Complete rigorous coverage replay plus the discharged mathematical assumptions
qualifies; a favourable review cannot substitute for unperformed coverage.
An intermediate draft incorrectly required a second native method before updating
verified case fields.
The reviewers checked the actual schema, assurance implementation and epistemics rules,
and corrected that extra requirement: C4 is additional confirmation, not a prerequisite
for C3 evidence or a mapped C5 review.
The integration review retains that correction.

## Host-load checkpoint

At the owner’s CPU-load question around 19:20 UTC, the 10-core host reported 100% CPU
utilization, roughly 50 runnable processes and a one-minute load average above 116. The
three active verification workers attributable to this block used about 1.5 cores in the
process snapshot: the serial point replay, exhaustive exact tests, and one
negative-control worker.
Most host contention came from other concurrent project jobs.
These are instantaneous process measurements, not cumulative CPU billing.
The point batch had accumulated about 33 CPU-minutes over 75 wall-minutes; the exact
test process had about 21 CPU-minutes over 55 wall-minutes.

The coordinator lowered the known task process trees to nice level 10. The next
validation phase exposed an important limitation of the initial cap: `--jobs 2` limits
concurrent steps, while its slow-test step used nine internal xdist workers.
At the next snapshot those workers plus the point replay used about 2.7 cores, all at
nice 10. The coordinator corrected the owner-facing explanation and selected
`PYTHON_CPU_COUNT=2` for subsequent gate commands so the inner test allocation also sees
the intended CPU limit.
No additional independent heavy lane was started.
The broad gate’s concurrency with the certificate campaign was poorly timed for this
host load.
Final validation records distinguish wall timeouts from mathematical failures.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
