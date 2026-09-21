---
title: Session 150 — correctness on the agenda-040 stack, the n = 17 ladder, and the record it left
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-150
  title: Correctness on the Agenda-040 Stack, the n = 17 Ladder, and the Record It Left
  date: '2026-09-21'
  started_at: '2026-09-21T08:26:00Z'
  deadline_at: '2026-09-21T22:30:00Z'
  branch: claude/session-150-record
  resource_rollups:
  - packing/campaign/resource-usage/agent-a03d9f91834d31398.yaml
  - packing/campaign/resource-usage/agent-a0766254e1d7068d0.yaml
  - packing/campaign/resource-usage/agent-a1a5bdfe66ee80e7e.yaml
  - packing/campaign/resource-usage/agent-a5ada27ae702ebba4.yaml
  - packing/campaign/resource-usage/agent-a670ff040f974d000.yaml
  - packing/campaign/resource-usage/agent-a6bdd78cb6dd38a25.yaml
  - packing/campaign/resource-usage/agent-aa5aad61a5058f512.yaml
  - packing/campaign/resource-usage/agent-aadc3241b7be53c05.yaml
  - packing/campaign/resource-usage/agent-aae9b5ce445a8c884.yaml
  - packing/campaign/resource-usage/agent-ac18860fbbd613485.yaml
  - packing/campaign/resource-usage/agent-ac407d8706d60cddc.yaml
  - packing/campaign/resource-usage/agent-ac9c2597825d2ffd1.yaml
  - packing/campaign/resource-usage/agent-acc596ced5294ca9c.yaml
  - packing/campaign/resource-usage/agent-ae65c7226abcb1a98.yaml
  - packing/campaign/resource-usage/d71b369b-163a-561c-a698-2900d1d8109e.yaml
  primary_bead: think-b7pr
  status: in_progress
  goal: >-
    Land the agenda-040 overnight stack and the n = 17 intake on main with every
    confirmed review finding repaired at the integration point, decide what the record
    may say about a fifth external n = 17 value that appeared during the session, and
    leave the session's own analysis as retained records rather than as scratchpad prose.
  workflow_phases:
  - workflow: remediation
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Repair the confirmed findings from the PR 204-209 dispositions at the stack's
      integration point, land the stack, and clear PR 211's blockers.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 490
    started_at: '2026-09-21T08:26:00Z'
    deadline_at: '2026-09-21T16:30:00Z'
    expected_output: >-
      The stacked pull requests merged into main with each confirmed finding repaired on
      the integration point rather than deferred to a follow-up.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: A repair would change a registered scientific claim rather than a factual error.
    fallback: Land the stack without that one repair and file the finding as a defect with an owning bead.
    outcome: >-
      PRs 204, 205, 206, 207, 208 and 209 all merged. Four review findings were fixed at
      the integration point rather than after it: X-040's lane-2 and lane-3 tables gained
      the `Lane verdict` column lane 1 already had (PR 204's F1, High); agenda-040's two
      "n=45 one-spare" mislabels; H-226's `regime`, where a 25-point red set was corrected
      to Bentz's 22 red / 23 blue split; and D-506's `recorded_in`. `check_class_record_claims`
      moved from an `rglob` walk to the tracked tree through a new `repo_scope.tracked_files`.
    evidence:
    - packing/campaign/explorations/X-040-lower-bound-mechanisms-beyond-the-one-body-ceiling.md
    - packing/campaign/agendas/agenda-040-overnight-lower-bound-loop.md
    - packing/campaign/hypotheses/H-226-n21-one-spare-wall-charge-lemma.md
    - packing/devtools/check_class_record_claims.py
    - packing/devtools/repo_scope.py
    stop_reason: >-
      The stack is on main and every confirmed finding is either repaired or carried by a
      named bead.
    next_action: Survey the new external n = 17 artifact that appeared during the block.
  - workflow: research-survey
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Establish what Kleddamag's v1.0.0 artifact claims, how it relates to the four n = 17
      values beneath it, and whether its own checkers reproduce its stated result.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: >-
      The correctness line was clear, and a fifth external n = 17 value had appeared above
      the one the open intake was about to register.
    budget_minutes: 50
    started_at: '2026-09-21T16:30:00Z'
    deadline_at: '2026-09-21T17:20:00Z'
    expected_output: >-
      The five-value ladder read off the artifacts as exact rationals rather than off the
      announcements, and a replay verdict from the source's own two checkers.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: The artifact's own checkers do not reproduce its `RESULT.json`.
    fallback: Record the source as reported-only with the discrepancy stated.
    outcome: >-
      The full two-checker replay reproduced `RESULT.json` byte-identically and reported
      `PASS_TWO_COMPLETE_EXACT_REPLAYS`. The claim is `s(17) > 461300/99853 = 4.619791`,
      the fifth value in seventeen days and the fourth sharing the numerator 461300 over
      a falling denominator. The announcement chain and the artifact's own `bounds.json`
      disagree about which value is the immediate predecessor, and that disagreement is
      recorded rather than resolved.
    evidence:
    - packing/campaign/explorations/X-041-after-the-n17-certified-bound.md
    stop_reason: >-
      What the source claims and whether its computation reproduces are settled; whether
      the argument behind it holds is a separate obligation.
    next_action: Review the argument adversarially and decide what the record may say about it.
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Decide adversarially whether the Kleddamag argument is sound enough to retain and at
      what evidential rung, and finish the correctness line's remaining merges.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: >-
      A byte-identical replay says the computation reproduces; it says nothing about the
      reduction from a packing to the finite obligations the computation decides.
    budget_minutes: 80
    started_at: '2026-09-21T17:20:00Z'
    deadline_at: '2026-09-21T18:40:00Z'
    expected_output: >-
      An adversarial proof review with a stated rung, the artifact retained with a
      byte-level manifest, and the n = 17 intake landed on main.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: The review finds a Blocker, or a retention would imply a bound the replays do not support.
    fallback: Retain the artifact as reported-only and register nothing from it.
    outcome: >-
      The adversarial proof review found no Blocker and no High. The artifact is retained
      under `packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/` with an
      84-entry manifest, stated at V4/C3 with C4 blocked; no bound moved and
      `461300/99853` is registered by nothing. Pull request 213 carried it and merged
      after this phase closed. On the correctness line,
      PR 211 merged as `T-032` for `s(17) >= 461300/99999` after a `T-031` collision
      renumber that physically moved the 82-line row to the end of the register, because
      contiguity is read positionally, a session renumber from 148 to 149, and a
      correction to a stale claim that R012 was the strongest public n = 17 value.
    evidence:
    - docs/project/reviews/review-2026-09-21-n17-kleddamag-461300-99853.md
    - packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/retained-files.sha256
    - packing/campaign/agent-sessions/session-149-n17-external-intake.md
    - packing/frontier/results.yaml
    stop_reason: >-
      The external result is replayed, reviewed and retained at a stated rung, and the
      registered n = 17 bound on main is `461300/99999`.
    next_action: Rank what the ladder opens and land the session's own analysis as records.
  - workflow: review-planning-oversight
    focus: process
    recording: contemporaneous
    clock_role: work
    objective: >-
      Turn the session's three scratchpad analyses into retained records - a ranked slate,
      a dated currency review and this session record - and reconcile the generated views
      and censuses they move.
    status: in_progress
    entered_by: evidence_checkpoint
    switch_reason: >-
      The correctness and survey obligations are discharged; what remains is what the
      record says and which entry is selected next.
    budget_minutes: 230
    started_at: '2026-09-21T18:40:00Z'
    deadline_at: '2026-09-21T22:30:00Z'
    expected_output: >-
      X-041, a dated currency review under `docs/project/reviews/`, and this record, with
      every generated view regenerated rather than hand-edited and the synopsis censuses
      reconciled.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records --jobs 1
    kill_condition: A record would state a validation that was not run or name a run id that does not exist.
    fallback: Land the records the evidence supports and name what is missing in the pull request.
    outcome: null
    evidence:
    - packing/campaign/explorations/X-041-after-the-n17-certified-bound.md
    - docs/project/reviews/review-2026-09-21-derived-artifact-currency.md
    stop_reason: null
    next_action: Certify this record on the hosted fast gate, then close it in a record-only commit.
  budget:
    wall_minutes: 850
  stop_conditions:
  - Every record states only what a retained artifact or a named run supports.
  - Do not register 461300/99853; the artifact is replayed, reviewed and retained, not adopted.
  - Never declare a gate that has not run, and never write a passing line for a run that failed.
  - The exploration's triple-geometry claim stays V0/C0 until a guarded tool reproduces it.
  progress:
    metric: The agenda-040 stack, the n = 17 intake, and the session's own analyses on main
    before: >-
      PRs 204-209 and 211 open with four confirmed review findings unrepaired; main at
      9fe9999d carries none of them; nothing on record about Kleddamag's 461300/99853.
    after: null
  delegations:
  - task: Replay Kleddamag's v1.0.0 certificate through both of its own checkers
    operator: replay lane; Opus xhigh
    status: completed
    recording: retrospective
    phase: 2
    outcome: >-
      Two complete exact replays passed and reproduced `RESULT.json` byte-identically,
      reporting `PASS_TWO_COMPLETE_EXACT_REPLAYS` at 16 m 41 s of wall.
    evidence: [packing/campaign/explorations/X-041-after-the-n17-certified-bound.md]
    files: []
    checks: ['Both of the source''s checkers run to completion on the project interpreter; the emitted RESULT.json is byte-identical to the published one.']
    uncertainty: >-
      The replay decides the finite computation and nothing about the reduction that
      produces it; that is what the proof review was for.
    elapsed_seconds: 1001
    elapsed_quality: operator_reported_approximate
    next_action: Hand the verdict to the proof review and to the retention lane.
  - task: Adversarial proof review of the Kleddamag n = 17 argument
    operator: proof_review; Fable max
    status: completed
    recording: retrospective
    phase: 3
    outcome: No Blocker and no High. The argument is retained at V4/C3, with C4 withheld.
    evidence: [packing/campaign/explorations/X-041-after-the-n17-certified-bound.md]
    files: []
    checks: ['The written argument was read line by line against the replayed computation; no blocking or high-severity finding was raised.']
    uncertainty: >-
      V4/C3 rather than C4 because both of the source's checkers share one method; two
      implementations of one method are C3 under `epistemics.md`.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator states the rung in the retention pull request and withholds C4.
  - task: Retain the Kleddamag artifact with a byte-level manifest and a review document
    operator: retention lane; Opus high
    status: completed
    recording: contemporaneous
    phase: 3
    budget_minutes: 120
    started_at: '2026-09-21T17:20:00Z'
    deadline_at: '2026-09-21T18:40:00Z'
    expected_output: >-
      The artifact under `packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/`
      with an 84-entry manifest and a review document, on its own pull request.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: A retained file does not match its source bytes.
    fallback: Retain nothing and record the source as reported-only.
    write_scope: [packing/resources/web/n17-kleddamag-certified-bound-2026-09-21, docs/project/reviews]
    excluded_commands: [git push --force, packing-validate --records --jobs 1]
    outcome: >-
      Pull request 213 retained the artifact with an 84-entry manifest and a review
      document, V4/C3 stated and C4 blocked; no bound moved. It merged into main while
      this record was being written.
    evidence: [docs/project/reviews/review-2026-09-21-n17-kleddamag-461300-99853.md]
    files: [packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/retained-files.sha256]
    checks: ['The manifest has 84 entries; the review states V4/C3 with C4 blocked and moves no bound.']
    uncertainty: >-
      The lane's files reached this branch through the merge of main rather than through
      its own work, so this record declares them and does not author them.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Land pull request 213 under its own review.
  - task: Rank what to pursue after the n = 17 ladder, in X-040's shape
    operator: strategy lane; Opus high
    status: completed
    recording: retrospective
    phase: 4
    outcome: >-
      A ranked slate of eleven candidates in three tiers, each with mechanism, instrument,
      first discriminator and kill rule, plus five retirement proposals with reopening
      conditions. Its sharpest claim - that the artifact's 2-of-3 triples are
      near-coincident where T-025's are wide - is scratch and is flagged V0/C0.
    evidence: [packing/campaign/explorations/X-041-after-the-n17-certified-bound.md]
    files: [packing/campaign/explorations/X-041-after-the-n17-certified-bound.md]
    checks: ['Every cited number resolves to a retained artifact by path and line, or is marked scratch; the scratch measurements are reproduced by no tool and are declared V0/C0 at the head of the report.']
    uncertainty: >-
      The triple-geometry and tight-row measurements were taken in one-off code on the
      artifact's bytes. Under OR-1 the tool is missing, and the claim is not a result
      until it exists.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Build the triple-geometry census before any row that depends on the claim is taken.
  - task: Read-only currency audit of every derived artifact on main
    operator: audit lane; Opus high
    status: completed
    recording: retrospective
    phase: 4
    outcome: >-
      Main is current with one exception. Every generated view, register, figure, census
      and the whole document map re-derive byte for byte. The exception is the annotated-passage
      banner in the Bentz 2016 transcription, which says 7 where the file carries 9 and the
      archive census says 9, and which nothing in the repository checks.
    evidence: [docs/project/reviews/review-2026-09-21-derived-artifact-currency.md]
    files: [docs/project/reviews/review-2026-09-21-derived-artifact-currency.md]
    checks: ['packing-validate --records --jobs 1 passed at 34 of 34 selected steps against a detached clone at 9fe9999d; every generator with a --check mode agreed with its source; the four failing --fast steps were each run down to the shallow clone rather than to drift on main.']
    uncertainty: >-
      Browser-dependent gates could not run in that environment and the clone was shallow,
      so four --fast failures are environmental and are decided by CI rather than here.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Build the archive-annotation census checker that would have caught the banner.
  outputs:
  - packing/campaign/agent-sessions/session-150-n17-consolidation-and-correctness.md
  - packing/campaign/explorations/X-041-after-the-n17-certified-bound.md
  - docs/project/reviews/review-2026-09-21-derived-artifact-currency.md
  checks:
  - 'packing-validate --records --jobs 1 on this branch: pending at the time this record was authored.'
  stop_reason: null
  next_action: >-
    Certify this record on the hosted fast gate, then close it in a record-only commit
    that declares that gate with its real run ids.
---
# Session 150: Correctness First, Then the `n = 17` Ladder

The entry point was **W9 remediation**, because the input was a confirmed finding
inventory from the PR 204–209 dispositions and the exit was merged pull requests.
It moved to **W1 research survey** when a fifth external `n = 17` value appeared above
the one the open intake was about to register, to **W2 factual review** once the replay
said the computation reproduced and the question became whether the argument behind it
holds, and to **W10 review/planning/oversight** to land what the session had learned.

## What the stack cost to land

Six pull requests merged, and four confirmed review findings were repaired at the
integration point rather than deferred.
The one worth naming is PR 204’s F1, a High: `X-040`’s lane-2 and lane-3 tables had no
`Lane verdict` column, which lane 1 already carried, so two thirds of a reviewed report
presented lane claims without the reviewer’s disposition beside them.
The other three were factual: two “n=45 one-spare” mislabels in agenda-040, `H-226`’s
`regime` — a 25-point red set where Bentz’s construction splits 22 red and 23 blue — and
`D-506`’s `recorded_in`, pointed at a document that never mentions it.
`check_class_record_claims` also stopped walking the filesystem with `rglob` and started
reading the tracked tree, through a new `repo_scope.tracked_files`.

Three process defects were found and tracked rather than worked around, and all three
are about the machinery rather than the mathematics.

**`think-fqut`.** GitHub’s stacked-PR merge rebases child branches, which orphaned the
gate commits that two open children declared in `checks:` and turned
`check_session_gate` red on both.
The recovery proved the trees byte-identical and restored the pre-rebase SHAs.
The declaration format is doing its job here: a gate run whose commit has left the
history certifies nothing, and the checker said so.

**`think-qsn2`.** `check_session_gate`’s verdict depends on how much history the clone
happens to have fetched.
In a shallow or partial clone the step
`terminal sessions name the gate that certified them` fails for sessions 087–090 and
112–113 — their declared commits are simply not present — while a complete clone passes.
The checker already draws the right line for a *missing* object, and this is the case
where the line is drawn in the wrong place.

**`think-3umt`.** A record authored terminal can never earn its first receipt.
The checker demands a `full gate:` line at every commit where the record is terminal,
and `in_progress` cannot be re-entered afterwards: `ledger.py` requires a future
`deadline_at`, a matching non-terminal final phase, and an unexpired phase deadline.
The only way through is the one this record took — author it non-terminal with honest,
unexpired clocks, push, let the hosted gate pass, and close it in a record-only commit
that declares that gate by its real commit and run ids.

## The `n = 17` ladder

Five values in seventeen days, four of them sharing the numerator `461300` over a
falling denominator.
This session replayed the newest, `461300/99853 = 4.619791`, through both of the
source’s own checkers; both completed and reproduced `RESULT.json` byte-identically.
An adversarial proof review of the written argument found no Blocker and no High.

**None of that registered a bound.** The artifact is retained with an 84-entry manifest
and stated at `V4/C3`, with `C4` blocked, by pull request 213. `C4` is withheld for a
stated reason rather than an abundance of caution: both of the source’s checkers share
one method, and two implementations of one method are `C3` under `epistemics.md`. The
first-party, domain-parameterised verifier that would earn `C4` is the `B1` row of
`X-041`, and it does not exist yet.

What did register is `T-032`, `s(17) >= 461300/99999`, which merged as PR 211 after a
`T-031` collision renumber.
The renumber is worth recording because it is physical: `devtools/check_results.py`
reads contiguity positionally rather than by label, so the 82-line row had to move to
the end of the register rather than simply change its id.
A session renumber from 148 to 149 travelled with it, and a stale claim that R012 was
the strongest public `n = 17` value was corrected in the same change — it was true when
it was written and false by the time it landed.

## Where the plan and the session disagree

The session plan was drafted mid-session and is now partly historical.
Two of its statements did not survive contact.

It called this session **149**. It is 150: `session-149` on `main` is the `n = 17`
external intake, renumbered from 148 during the PR 211 landing.

It left `461300/99999`’s registration as an open owner question — whether to spend an id
on a value that would be superseded on arrival.
That was decided in the affirmative: PR 211 merged and `T-032` carries it, consistent
with the register’s standing practice of retaining a displaced rung, and the newer value
is registered by nothing.

The plan also forecast that Block 3 would close agenda-040 through disposition.
It did not. What Block 3 produced is the ranked slate in `X-041`, the currency review,
and this record; the agenda-040 closeout remains outstanding and is named as such rather
than implied to be done.

## The efficiency debt, published

`OR-12` asks for one efficiency block in every four to eight.
Counted from the records rather than recalled, the last block declaring a
`workflow: efficiency-loop` phase is Session 131, and seventeen blocks have closed
since. `think-zmos` opened this session with its measurements already taken: the deep
gate’s `exhaustive-tier` step ran 2674 s against its own declared 1943.05 s, a factor of
1.38; `deferred-steps` ran 2469 s; and one 45-minute run was spent over a tree
byte-identical to a tree already measured.
`OR-17` — a wall ceiling on every routine gate, with anything above it selected on
purpose — is the rule those numbers produced, and it merged as PR 212 with a `suite_b`
gate-budget re-measurement beside it, bringing `operating-rules.md` to seventeen rules.

Publishing the count is not discharging it.
The W5 is the selected next entry.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
