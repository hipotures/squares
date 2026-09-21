---
title: Session 149 — intake and verification of two external n = 17 weighted certificates
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-149
  title: Intake and Verification of Two External n = 17 Weighted Certificates
  date: '2026-09-20'
  started_at: '2026-09-20T08:05:00Z'
  deadline_at: '2026-09-20T18:00:00Z'
  branch: claude/n17-mira-guzhou-4613-intake
  primary_bead: think-pcd0
  resource_rollups:
  - packing/campaign/resource-usage/7163c7b2-b4ac-4c82-afcc-ab827886ebd9.yaml
  status: completed
  ended_at: '2026-09-20T18:00:00Z'
  goal: >-
    Decide whether Guzhou0806's R012 certificate for s(17) >= 461300/99999 is correct,
    what the record should say about it and about Mira's 4613/1000 certificate it
    descends from, and register both with their credits.
  workflow_phases:
  - workflow: research-survey
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Archive both sources at pinned commits and establish what each claims, how they
      relate to each other and to T-019, and what was already in the record.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 60
    started_at: '2026-09-20T08:05:00Z'
    deadline_at: '2026-09-20T09:05:00Z'
    expected_output: >-
      A retained archive packet with both repositories, a README in the precedent's
      shape, a hash list, and the chronology extended past the 2026-09-07 packet.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: Either source turns out to be already archived or to claim less than 459/100.
    fallback: Record the source as reported-only and stop.
    outcome: >-
      Both archived at their pinned commits, 92 retained files byte-identical to their
      sources. Mira's certificate of 7 September was published hours after the
      2026-09-07 GitHub check that produced the earlier packet, which is why the record
      had neither result.
    evidence:
    - packing/resources/web/n17-weighted-certificates-2026-09-20/README.md
    - packing/resources/web/n17-weighted-certificates-2026-09-20/retained-files.sha256
    stop_reason: The sources are retained and their claims are stated; verification is a separate obligation.
    next_action: Replay both and review the arguments.
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Decide both certificates with this repository's own verifiers where they apply,
      replay the source checker where they do not, and work through both written
      arguments adversarially.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: The archive is retained; what remains is whether the mathematics holds.
    budget_minutes: 415
    started_at: '2026-09-20T09:05:00Z'
    deadline_at: '2026-09-20T16:00:00Z'
    expected_output: >-
      Passing or failing verdicts with receipts from four replays, a proof review, and
      controls that fail on a forged measure.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev pytest tests/test_n17_external_weighted_certificates.py
    kill_condition: A verifier refuses either certificate, or the review finds a blocking defect.
    fallback: Record both as reported-only with the refusal or the defect, and file it.
    outcome: >-
      All four replays passed. Mira's certificate is accepted by both stock verifiers;
      R012's catalogue is accepted by its own exact checker and by this repository's
      interval branch and bound over all 2925 entries. The proof review found no error
      and nothing blocking.
    evidence:
    - docs/project/reviews/review-2026-09-20-n17-r012-and-mira-4613-proof-review.md
    - packing/resources/web/n17-weighted-certificates-2026-09-20/receipts/mira-4613-first-party-exact.json
    - packing/resources/web/n17-weighted-certificates-2026-09-20/receipts/mira-4613-first-party-interval.json
    - packing/resources/web/n17-weighted-certificates-2026-09-20/receipts/guzhou-r012-first-party-001.json
    - packing/tests/test_n17_external_weighted_certificates.py
    stop_reason: Both certificates are decided at V4/C4; what remains is what the register says.
    next_action: Register T-032 and reconcile the reader-facing documents.
  - workflow: documentation-pass
    focus: process
    recording: contemporaneous
    clock_role: work
    objective: >-
      Register the result and its evidence, move the n = 17 fields, and correct every
      document that still says nothing public exceeds 459/100.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: The verdicts are in and the record contradicts them.
    budget_minutes: 120
    started_at: '2026-09-20T16:00:00Z'
    deadline_at: '2026-09-20T18:00:00Z'
    expected_output: >-
      T-032 and four evidence entries, the n = 17 case record, the regenerated views,
      and the credits in the five places this repository credits external authors.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: A record change would overstate what the replays decided.
    fallback: Record the weaker statement the replays support and say what is missing.
    outcome: >-
      T-032 registered at V4/C4 with four evidence entries; the verified lower bound at
      n = 17 moves from 459/100 to 461300/99999.
    evidence:
    - packing/frontier/results.yaml
    - packing/frontier/evidence.yaml
    - packing/frontier/n-017.md
    stop_reason: The record states what was decided and credits both authors.
    next_action: Open the pull request.
  budget:
    wall_minutes: 600
  stop_conditions:
  - Both certificates have an explicit verdict with a receipt, or a recorded refusal.
  - Do not promote a bound past what the replays decide; Mira's dilation endpoint is out of scope.
  - Do not start a search for a stronger bound in this session.
  progress:
    metric: Verified lower bound at n = 17
    before: 459/100 = 4.59 (T-019, first-party, 2026-09-04).
    after: 461300/99999 = 4.61304613... (T-032, external, replayed and decided here).
  delegations:
  - task: Archive both sources and register them in the resource index
    operator: archive_packet; Opus high
    status: completed
    recording: retrospective
    phase: 1
    outcome: >-
      A 92-file packet with a README in the precedent's shape, all bytes verified
      against their source commits. Corrected four of the coordinator's briefing facts,
      including that source-availability.yaml is for unobtained sources and takes
      neither entry.
    evidence: [packing/resources/web/n17-weighted-certificates-2026-09-20/README.md]
    files: [packing/resources/web/n17-weighted-certificates-2026-09-20/README.md, packing/resources/web/n17-weighted-certificates-2026-09-20/retained-files.sha256, packing/resources/README.md]
    checks: ['shasum -a 256 -c over all 92 retained files; packing-validate --records passed; embedded-JavaScript gate passed over the packet''s 12 retained Python files.']
    uncertainty: The lane verified no mathematics; it recorded what each source claims.
    elapsed_seconds: 560
    elapsed_quality: platform_measured
    next_action: Coordinator decides the record fields.
  - task: Adversarial proof review of R012 and Mira's certificate
    operator: proof_review; Fable max
    status: completed
    recording: retrospective
    phase: 2
    outcome: >-
      No error found in either argument; eleven findings, none blocking. Two steps the
      R012 note omits are supplied: endpoint-only containment covers the whole angle
      interval, and the inset from the endpoint minimum of f gives exactly the union of
      legal parent centres.
    evidence: [docs/project/reviews/review-2026-09-20-n17-r012-and-mira-4613-proof-review.md]
    files: [docs/project/reviews/review-2026-09-20-n17-r012-and-mira-4613-proof-review.md]
    checks: ['All 2925 obligations re-derived from the source data and decided with this repository''s sweep kernel, agreeing with the source on every entry; a separating-axis pass sharing nothing with either kernel; brute force against an arrangement-vertex oracle on small instances.']
    uncertainty: Mira's Condition 5 was sampled at 16 directions in the review; the coordinator's replays decided it in full.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator records the findings as the review artifact for T-032.
  - task: First-party replay instruments for both certificates
    operator: replay_tools; Opus xhigh
    status: completed
    recording: retrospective
    phase: 2
    outcome: >-
      Two retained tools: Mira's certificate through the stock exact and interval
      verifiers, and R012's catalogue through the interval branch and bound over a
      restricted centre domain, with ten negative controls and a byte-level provenance
      check against Mira's atoms.
    evidence: [packing/resources/web/n17-weighted-certificates-2026-09-20/replay_mira_4613_first_party.py, packing/resources/web/n17-weighted-certificates-2026-09-20/replay_guzhou_r012_first_party.py]
    files: [packing/resources/web/n17-weighted-certificates-2026-09-20/replay_mira_4613_first_party.py, packing/resources/web/n17-weighted-certificates-2026-09-20/replay_guzhou_r012_first_party.py]
    checks: [All four replays passed; ten negative controls passed; every one of the 2925 interval brackets contains the source's exact minimum.]
    uncertainty: The coordinator reran both tools after repairing absolute paths in the receipts and the compressed-input reader.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator retains the receipts and writes the controls.
  outputs:
  - packing/resources/web/n17-weighted-certificates-2026-09-20/README.md
  - docs/project/reviews/review-2026-09-20-n17-r012-and-mira-4613-proof-review.md
  - packing/tests/test_n17_external_weighted_certificates.py
  - packing/campaign/agent-sessions/session-149-n17-external-intake.md
  checks:
  - R012's own exact checker recomputed all 2925 parent-angle intervals under Python 3.14.7 and printed its complete marker; catalogue minimum exactly 250023/250000.
  - This repository's interval branch and bound certified all 2925 R012 entries over 34,465,227 boxes, none stalled, every bracket containing the source's exact minimum.
  - Mira's certificate passed the stock exact verifier, least cell mass 1000002103/1000000000 at direction 2194, equal to the declared value.
  - Mira's certificate passed the stock interval verifier on the doubled 5761-direction net, 70,019,687 boxes, enclosure width zero at the same value.
  - Five controls pass, including a forged measure three parts in a million lighter that both routes refuse.
  stop_reason: >-
    Both certificates are decided, the register states what they support, and both
    authors are credited. No search for a stronger bound was started.
  next_action: >-
    Land the adoption under think-pcd0. The T-031 identifier contest with pull request
    208 is settled: the overnight stack merged into main first and kept T-031 for the
    n = 11 octagon corner class, and this result took T-032 when main was merged into
    this branch.
---
# Session 149: Two External Certificates at `n = 17`

The entry point was **W1 research survey**, because the owner supplied a link and the
record had neither the result behind it nor the certificate that result descends from.
It moved to **W2 factual review** once both sources were retained, and to **W8
documentation pass** once the verdicts contradicted the reader-facing documents.

Two results arrived together.
Guzhou0806’s R012, published on 20 September 2026, claims `s(17) >= 461300/99999`. Its
attribution names Mira’s `17squares` at a September commit, and following that pointer
found a second unrecorded result, Mira’s weighted certificate of 7 September at
`s(17) > 4.613028635886`. Both descend from this repository’s own `T-019` certificate
and credit it. Mira’s was published a few hours after the 2026-09-07 GitHub check that
produced the earlier packet, which is why the record missed it; R012 postdates that
check by two weeks.

The verification split cleanly.
Mira’s certificate is in this repository’s own schema, so both stock verifiers decide it
with no translation layer, and both accept it.
R012’s argument is the same method with three changes — parents slightly smaller than a
unit square, a per-angle choice of core, and coverage required only over legal parent
centres — so the stock verifiers do not take it as it stands.
It was decided instead by its own exact checker and, independently in method, by this
repository’s interval branch and bound over a restricted centre domain, which is a
subclass of the stock search changing only the domain.

What the replays do not decide is the reduction from a packing to R012’s 2925 finite
obligations. That is a short argument, read closely in the review artifact and closed
there, and it is a careful reading rather than a machine check.
The written note omits two steps, and the review supplies both.

One scope limit is worth stating plainly.
Mira’s headline is the dilation endpoint `4.61302863588611...`, `2.9e-5` above the
container side. That step needs a `T-022`-style proof note which this certificate does
not have, so the record carries the side and not the endpoint.
It costs nothing, because R012’s value is larger and is the one registered.

The identifier was contended, and the contest is settled.
Pull request 208, from the open overnight stack, also claimed `T-031`, and the
register’s contiguity rule leaves no free number below it, so whichever landed second
had to renumber.
The stack merged into `main` first and kept `T-031` for the `n = 11` octagon corner
class; this result took `T-032` when `main` was merged into this branch, and its row
moved to the end of the register, because `devtools/check_results.py` reads contiguity
positionally rather than by label.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
