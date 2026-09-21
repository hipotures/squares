---
title: Session 143 — deeper mathematical review of lower-bound routes
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-143
  title: Deeper Mathematical Review of Lower-Bound Routes
  date: '2026-09-20'
  started_at: '2026-09-20T06:05:00Z'
  deadline_at: '2026-09-20T10:05:00Z'
  branch: claude/kind-wright-whxxn6
  primary_bead: think-srln
  ended_at: '2026-09-20T07:24:00Z'
  status: completed
  goal: >-
    Establish where the lower-bound results have been, and which deeper mechanisms,
    especially general geometric arguments combined with point and threshold
    certificates on a conditioned family of packings, could give materially better
    lower bounds at n=11, n=17, or other n, or another notable result; rank them
    with first discriminators, and select one next entry.
  workflow_phases:
  - workflow: insight-iteration
    focus: insight
    recording: contemporaneous
    clock_role: work
    objective: >-
      Run four parallel read-only research lanes from the top of PR 202 (8cab8309):
      n=11 relational mathematics beyond the one-body ceiling; mechanisms beyond the
      current route slate; material targets at n=17 and other n; and the machinery
      and evidence map that prices each first discriminator.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 150
    started_at: '2026-09-20T06:05:00Z'
    deadline_at: '2026-09-20T08:35:00Z'
    expected_output: >-
      Four lane reports in the session scratchpad, integrated into exploration X-040
      with a ranked mechanism slate, first discriminators, and honest failure modes.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      A lane proposes only mechanisms already on the X-037 or BC-347 slate with no
      new premise, or the lanes cannot name a decisive first discriminator for any
      candidate.
    fallback: >-
      Record the negative as an exploration outcome, keep think-qqzs / H-216 as the
      selected entry, and close the block with dispositions only.
    outcome: >-
      Four lane reports (n=11 relational, mechanisms beyond the slate, other n,
      machinery map) and three Fable adversarial reviews; R1 killed the corner
      deep branches at the target side, R2 killed the theta screen and the stress
      theorem as stated, R3 found the Bentz 2016 transcription defect (D-505) and
      corrected the one-spare case tree. X-040 integrates all seven.
    evidence:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    - packing/defects.yaml
    stop_reason: Lanes and reviews complete; integration and replanning move to W10.
    next_action: Register the adapted hypotheses and the overnight agenda.
  - workflow: review-planning-oversight
    focus: insight
    recording: contemporaneous
    clock_role: work
    objective: >-
      Register the adapted hypotheses H-222 to H-231, open agenda-040 with the
      overnight queue and the five retirements, correct the Bentz 2016 transcription
      under D-505 and D-506, close the session record, and select the next entry.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: All four lanes and three reviews reported.
    budget_minutes: 60
    started_at: '2026-09-20T07:05:00Z'
    deadline_at: '2026-09-20T08:05:00Z'
    expected_output: >-
      Ten hypothesis records, agenda-040, D-505 and D-506 with the corrected
      transcription, a closed session record, and PR 204 ready for review.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --fast
    kill_condition: A registration cannot state a kill rule, or a record check refuses the tree.
    fallback: Register what can be stated, leave the rest as open questions, and close.
    outcome: >-
      H-222 to H-231 registered with kill rules, agenda-040 opened with BC-361 to
      BC-366 and five retirements, D-505 and D-506 corrected the transcription, the
      synopsis rows reconciled, and the closeout commit declares the hosted fast gate
      on 3dc129e0. Session 144 opened on the stacked branch with exp-213 to exp-215.
    evidence:
    - packing/campaign/agendas/agenda-040-overnight-lower-bound-loop.md
    - packing/campaign/hypotheses/H-222-n11-octagon-class-at-96-25.md
    - packing/defects.yaml
    stop_reason: Registrations, corrections, and the gate declaration are complete.
    next_action: Session 144 runs BC-361 and BC-362 under think-pogj and think-89i1.
  resource_rollups:
  - packing/campaign/resource-usage/5e071e1a-5ab8-5bae-a5c0-c3687815bf4a.yaml
  - packing/campaign/resource-usage/ae3edbd2676fddaf2.yaml
  - packing/campaign/resource-usage/afc8f6dcbe7aef07d.yaml
  - packing/campaign/resource-usage/af860c4b4d0468ad0.yaml
  - packing/campaign/resource-usage/a5a0fa0629343ea04.yaml
  - packing/campaign/resource-usage/a593739458b58626a.yaml
  - packing/campaign/resource-usage/a8b8b405efc053f16.yaml
  - packing/campaign/resource-usage/a68c79e799a3fc678.yaml
  - packing/campaign/resource-usage/a1730fd7bec467b88.yaml
  budget:
    wall_minutes: 240
    finalization_minutes: 40
  stop_conditions:
  - Every candidate mechanism has a disposition, a first discriminator, and a kill reading.
  - No bound, hypothesis verdict, or frontier record changes in this block.
  - No LP, column-generation, or search target runs; small exact checks only.
  - Exactly one next entry is selected and recorded on agenda-037 and the bead.
  progress:
    metric: Candidate mechanisms with a disposition and a costed first discriminator
    before: Eight mechanisms M1–M8 and Routes A–D and S, all dispositioned in X-037 and BC-347; no candidate beyond the one-body ceiling has a running instrument.
    after: >-
      Nine mechanisms with a disposition and a costed first discriminator (H-222 to
      H-230), one open question (H-231), five retirements with reopening conditions,
      and three experiments registered for the first overnight chunk.
  delegations:
  - task: n=11 relational mathematics beyond the one-body ceiling, conditioned certificate program
    operator: lane1_n11_relational; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Eleven-orbit reading of the 88-family, saturation of every one-body cap, ring–centre relation named, corner tree and tilted-anchor tree proposed with exact gains on the fixed families.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: []
    uncertainty: A lane report is evidence, not a verdict; every derived lemma needs independent review before registration.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Adversarial review and integration into X-040.
  - task: Mechanisms different in kind from the shrunken-core fixed-net certificate
    operator: lane2_new_mechanisms; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Eleven mechanisms evaluated; theta, stress, uniform m^2-3, unshrunk verifier, Bentz idiom at 12, and wedge conflicts ranked; wall-wedge lemma derived.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: []
    uncertainty: Literature-derived lemmas need source checks against the archived copies before use.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Adversarial review and integration into X-040.
  - task: Material lower-bound or exact-value targets at n=17 and other n
    operator: lane3_other_n; Claude Fable extra
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Hex-set count m^2 - ceil(m/2) derived; one-spare cases 21, 32, 45 identified; n=17 cap and Bidwell geometry analysed; n=26 and n=12 priced.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: []
    uncertainty: Reach estimates are judgments, not measured covering values.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Adversarial review and integration into X-040.
  - task: Instrument, evidence, and ceiling map to price every first discriminator
    operator: lane4_machinery; Claude Opus high
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Instrument, evidence, ceiling, and gap map; only the unconditional point language is fully instrumented; no run log retained for any restricted optimum.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: []
    uncertainty: Build-cost estimates are not measured receipts.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Integration into X-040's machinery section.
  - task: Adversarial review of lane 1
    operator: review1_of_lane1; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Every lane number reproduced; transported to 96/25 and 77/20 the corner deep
      branches are exactly neutral; cell-24 edge corrected to 6.4537°; anchor gain at
      most 1.5 per cell; first measurement is the octagon class.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: [Strict-interior overlap recount; exact homothety transport with depth verified; strip constants re-derived.]
    uncertainty: H-131 used without replay; the record's transport was not compared with the reviewer's homothety.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Integrated into X-040 and H-222, H-229.
  - task: Adversarial review of lane 2
    operator: review2_of_lane2; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Theta chain correct but the screen cannot discriminate and the dual matrix is
      dense (44% edge density at 3.83); stress theorem false as stated; wedge lemma
      confirmed (0.3203) with the 64-family's 7.11° orbit at gap 0.016 leaving the
      kill unmet; s(12) reach estimate and the m = 5, 6 uniform test rejected.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md]
    files: []
    checks: [Wedge brute force; Trump wedge check on the exact build; Monte Carlo pose-pair density.]
    uncertainty: Several literature citations and the 19-per-unit-side slope unverified.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Integrated into X-040, H-223, H-230, H-231.
  - task: Adversarial review of lane 3
    operator: review3_of_lane3; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Cap and hex-set count verified; Bentz 2016 transcription prints (sqrt 2 - 1)/2
      where the PDF prints sqrt 2 - 1/2, and the proof closes only with the printed
      constant; n=45 is (0, 1) and blocked by the m = 7 height budget; n=21 has up to
      six stationary points; Green's numbers verified.
    evidence: [packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md, packing/defects.yaml]
    files: []
    checks: [Chord minima on the printed line replayed (1.0000 full, 0.8468 partial); rendered PDF pages 6 and 7 compared by the coordinator.]
    uncertainty: Whether an alternative m = 7 layout restores the 0.1 slide.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: D-505 and H-226, H-227.
  - task: Correct the Bentz 2016 transcription and file D-505 and D-506
    operator: fix_bentz_transcription; Claude Opus high
    status: completed
    recording: contemporaneous
    phase: 2
    outcome: >-
      Fifteen LaTeX spans corrected to the PDF's constants (D-505) and Lemma 7's
      0.505 sqrt 2 and Lemma 5 reference restored (D-506), each with inline notes;
      README annotation row 3 to 7; defects.md and the synopsis defect counts
      regenerated; glyph positions read from the PDF with pdfminer confirm both.
    evidence: [packing/defects.yaml, packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md, packing/resources/README.md]
    files: [packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md, packing/resources/README.md, packing/defects.yaml, defects.md, SYNOPSIS.md]
    checks: [check_synopsis, check_rung_figures, and check_math_spans (467 spans, 0 changed) passed; flowmark check clean.]
    uncertainty: The raw extraction is ambiguous at the same spots, so the corrections are read from the PDF's glyph positions and the rendered pages.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator verifies the diff against the rendered pages and commits.
  outputs:
  - packing/campaign/agent-sessions/session-143-lower-bound-math-review.md
  - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
  - packing/campaign/agendas/agenda-040-overnight-lower-bound-loop.md
  - packing/campaign/hypotheses/H-222-n11-octagon-class-at-96-25.md
  - packing/campaign/hypotheses/H-226-n21-one-spare-wall-charge-lemma.md
  checks:
  - 'full gate: fast at 3dc129e0: passed (hosted run 35496205905; pages run 35496205828)'
  - packing-validate --records passed locally at 3dc129e0 and on the closeout tree.
  - check_synopsis, check_rung_figures, and check_math_spans (467 spans, 0 changed) passed on the D-505 and D-506 corrections.
  - Every number in X-040 that is not cited to a retained artifact is marked scratch; no LP, column-generation, or search target ran.
  stop_reason: >-
    The review block is complete: X-040 retained, ten hypotheses and agenda-040
    registered, two transcription defects corrected, PR 204 green on its head.
    The overnight loop continues in Session 144 on a stacked branch.
  next_action: Session 144 under think-pogj decides exp-213 to exp-215 for BC-361, with the Bentz 2016 replay lane beside it.
---
# Session 143: Deeper Mathematical Review of Lower-Bound Routes

The entry point is **W3 insight-iteration**, requested by the owner from the top of PR
202\. The synopsis handoff names `think-qqzs` / H-216 as the next scientific entry; this
block is an owner-directed deviation from that order under OR-4, recorded here so the
deviation is visible rather than silent.

The block asks a strategic question rather than running a target: where have the
lower-bound results been, and what deeper mathematics could move them materially.
Four read-only research lanes run in parallel with disjoint deliverables, followed by an
adversarial review wave.
The coordinator owns the exploration record, the agenda cell, the bead, and validation.

No bound, hypothesis verdict, or frontier record changes in this block.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
