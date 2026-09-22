---
title: Session 151 — a deep low-n review, the efficiency block OR-12 was overdue, and what the research block decided
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-151
  title: A Deep Low-n Review, the Efficiency Block OR-12 Was Overdue, and What the Research Block Decided
  date: '2026-09-22'
  started_at: '2026-09-22T06:16:00Z'
  deadline_at: '2026-09-22T10:17:00Z'
  branch: claude/happy-johnson-i2ridl
  resource_rollups:
  - packing/campaign/resource-usage/216fe0a3-88ed-5da5-baf4-c4d6171928f3.yaml
  - packing/campaign/resource-usage/agent-a028ee98e0f75eb66.yaml
  - packing/campaign/resource-usage/agent-a41a6a4a1e33f736a.yaml
  - packing/campaign/resource-usage/agent-a64397e5f83d328e1.yaml
  - packing/campaign/resource-usage/agent-a8cd7f48de8eed7e1.yaml
  - packing/campaign/resource-usage/agent-a945578bf0da690f6.yaml
  - packing/campaign/resource-usage/agent-ab0c0b35e2bfe4085.yaml
  - packing/campaign/resource-usage/agent-acf9f81f0e2efd9e2.yaml
  - packing/campaign/resource-usage/agent-addd36018d6e6b82a.yaml
  - packing/campaign/resource-usage/agent-ae7cf10b917ea0717.yaml
  - packing/campaign/resource-usage/agent-afc70c9271ea1d01b.yaml
  - packing/campaign/resource-usage/agent-afcacea2c4bddfe4a.yaml
  primary_bead: think-gvlg
  status: stopped
  ended_at: '2026-09-22T09:20:00Z'
  certification_pending: think-gvlg
  goal: >-
    Ask again what significant improvement is available at n = 11, n = 17 or another low
    n now that the five-value n = 17 ladder, T-031 and T-032 have merged; run the
    efficiency block OR-12 has been overdue for since Session 131; and spend the rest of
    the run on what the review ranks, with the mathematics on Fable and the mechanical
    work on Opus.
  workflow_phases:
  - workflow: efficiency-loop
    focus: efficiency
    recording: contemporaneous
    clock_role: work
    objective: >-
      Establish that the research loop runs at all in this checkout, repair what does
      not, and discharge think-zmos, which Session 150 selected as the next entry and
      did not run.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 75
    started_at: '2026-09-22T06:16:00Z'
    deadline_at: '2026-09-22T07:31:00Z'
    expected_output: >-
      A passing edit tier from a fresh clone, a guarded check that names each missing
      precondition with its remedy, and the deep gate's four CI jobs clocked the way
      local tiers are.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --edit
    kill_condition: A repair would change a registered scientific claim rather than a factual error.
    fallback: Record what is missing as a defect with an owning bead and continue on the research lanes.
    outcome: >-
      The first command of the session was the edit tier and it failed three steps. Five
      preconditions no document named: the image's uv 0.8.17 cannot resolve the pinned
      3.14.7 because its index ends at 3.14.0rc2 and uv self update hits a rate limit;
      the interpreter was absent; the clone was shallow; vendor/kpress was unpopulated;
      npm ci had not run. A sixth, found later, is that the Rust engine was unbuilt, which
      blocks every upper-bound experiment. After repair the edit tier passes at 124.4 s
      against its 240 s ceiling. devtools/check_bootstrap.py reports all five with a
      remedy each and repairs nothing; it is stdlib-only because the failure it diagnoses
      is the one where the project interpreter does not exist, and it is deliberately in
      no tier. check_session_gate was also fixed: it called a true ancestor a non-ancestor
      in a shallow clone, which is what produced eleven false failures at session start.
      On think-zmos the headline is a correction rather than a confirmation. The
      exhaustive tier's 1.38x over its declared price is not drift: runs 35480905141 and
      35579234418 ran the same 58 tests, compared by name, at 1836.1 s against 2621.4 s,
      a uniform 1.428x, while two runs of the byte-identical commit 030d109a read 2608 s
      and 2771 s. 1943.05 s is the faster class of hosted runner. OR-17's text is
      corrected and the four jobs are now clocked in a new ci_gates register at reporting
      strength.
    evidence:
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-041/bootstrap-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-041/deep-gate-wall-clock-receipt.md
    - packing/devtools/check_bootstrap.py
    - operating-rules.md
    stop_reason: >-
      The loop runs, the five preconditions are documented and checked, and think-zmos's
      four questions are answered or explicitly left to think-haam.
    next_action: Open the review lanes, which were already running beside this phase.
  - workflow: insight-iteration
    focus: insight
    recording: contemporaneous
    clock_role: work
    objective: >-
      Ask what significant improvement is left at low n, as four Fable lanes with
      disjoint deliverables, each recomputing the arithmetic it relies on.
    status: completed
    entered_by: planned_checkpoint
    switch_reason: >-
      Opened beside the efficiency phase rather than after it, because OR-3 forbids
      waiting on a gate with nothing else in flight and the lanes are read-only.
    budget_minutes: 60
    started_at: '2026-09-22T06:20:00Z'
    deadline_at: '2026-09-22T07:20:00Z'
    expected_output: >-
      X-042 with a ranked slate, each item's mechanism, instrument, first discriminator
      and kill rule, and the falsifiable hypotheses the research block then runs.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --only "campaign record"
    kill_condition: A lane reports a bound movement rather than a reading.
    fallback: Land the slate the evidence supports and name what is unmeasured.
    outcome: >-
      X-042 landed, contradicting X-041 in nine places, each with the recomputation that
      settles it. Three redirect work. The n = 17 ladder is climbing away from 4.613
      rather than converging on it, A having moved away from 1 across all five values,
      and under scale invariance sigma = L/A is the language's only invariant, so a
      larger L is not a mechanism. The external measure has not been re-priced against
      its own final catalogue: two-thirds of its 7,853 rows sit on one plateau at
      1.00207034, 2,631 lie below it, and of the 0.0368 surplus it was priced to carry
      only 1.13e-4 survived. And at n = 19 and n = 26 the target itself is the least
      defended number in the low range, no search on record having reached Wainwright's
      1979 n = 19 packing.
    evidence:
    - packing/campaign/explorations/X-042-what-is-left-at-low-n.md
    stop_reason: The slate is written and its hypotheses are stated with kills.
    next_action: Put the new mathematics through an adversarial lane before spending Opus on it.
  - workflow: factual-review
    focus: correctness
    recording: contemporaneous
    clock_role: work
    objective: >-
      Try to break the review lanes' new derivations before a research block acts on
      them, and say which downstream actions are safe and which are unsound.
    status: completed
    entered_by: evidence_checkpoint
    switch_reason: >-
      Four lanes had produced theorems, propositions and a refutation, all unreviewed,
      and a three-hour research block was about to be dispatched on them.
    budget_minutes: 40
    started_at: '2026-09-22T06:51:00Z'
    deadline_at: '2026-09-22T07:31:00Z'
    expected_output: >-
      A verdict per claim with its reasoning, and a ranked list of what is safe to run.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --only "campaign record"
    kill_condition: The lane cannot decide a load-bearing claim and says so.
    fallback: Run only the cells that do not depend on a contested claim.
    outcome: >-
      It earned its place. X-042's claim that H-228 is refuted as stated was wrong and
      already pushed: the refutation uses the interior convention, while H-228 is stated
      for closed unit squares, where sixteen closed grid squares share edges and vertices
      and a total of 16 over them is compatible with mass below 12. The cross-n lane
      reached the same conclusion independently. The verdict is reverted and what remains
      is a specification constraint: the BC-365 verifier must decide closed cores.
      Confirmed: the restriction is a genuine relaxation, so a pass on the unrestricted
      test would have been decisive; the row-6512 witness reproduces exactly; the L*
      reconstruction holds and its structural correction is right. Corrected: an
      unrestricted certificate is a restricted one only above A_eff, not at it, and
      B3's kill at X-041:308 is mis-set by the same L/B-versus-S conflation.
    evidence:
    - packing/campaign/explorations/X-042-what-is-left-at-low-n.md
    stop_reason: Every load-bearing claim has a verdict and the unsound designs are named.
    next_action: Run the cells the lane cleared.
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    objective: >-
      Run what the review ranks and the validation cleared, on the instruments that
      exist, and report the numbers rather than the verdicts alone.
    status: stopped
    entered_by: evidence_checkpoint
    switch_reason: >-
      The slate is reviewed and the unsound rows are named, so the remaining time is
      measurement.
    budget_minutes: 150
    started_at: '2026-09-22T06:45:00Z'
    deadline_at: '2026-09-22T09:15:00Z'
    expected_output: >-
      Decided hypotheses with their exact numbers, receipts under results/agenda-041,
      and no registration that the two routes did not support.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --fast
    kill_condition: A run would register a bound that only one route accepts.
    fallback: Record the candidate and the refusal, and register nothing.
    outcome: >-
      Four cells decided and no bound moved. H-235: the 2-of-3 atoms are load-bearing at
      n = 17, the least point-only charge being 370792263/500000000 = 0.741585 against a
      point budget over n of 0.861183. The parent-centre restriction is load-bearing for
      the external measure, with an exact witness at row 6512 charging
      199827543/200000000 against M/17 = 0.999907492, derived independently by a Fable
      lane from the artifact's bytes and reproduced by the translation lane through its
      guarded translator. Read unrestricted through the gate's own exact route, the
      measure's least charge is 0.305414321 at direction 0, so it is refuted at every net.
      The grid escape at n = 12, 20 and 21 returned the null, which is the deliverable:
      it converts an absence of search into a measured negative at three sizes where the
      registers say so in as many words. And exp-225 established that the retained n = 29
      candidate at 548/100 certifies every n >= 27 by Condition 2, that a 103/100 re-bump
      clears its Condition 5 stall completely at the theorem's own threshold, and that the
      gate still refuses on its enclosure-agreement requirement, all 272 stalls sitting in
      direction 0 below the 1e-12 resolution floor.
    evidence:
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-221-n17-kleddamag-unrestricted-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-223-grid-escape/exp-223-grid-escape-receipt.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-n28-548-100-rebump-receipt.md
    stop_reason: >-
      Every dispatched cell is decided, the n = 11 rung is accepted by both routes with
      its limit record written, and what remains is a register entry this session
      deliberately did not write.
    next_action: Register the n = 11 rung, following the handoff's three steps.
  budget:
    wall_minutes: 241
  stop_conditions:
  - No bound moves without both routes accepting the frozen bytes.
  - Do not register 461300/99853, and do not register 548/100 at any n.
  - Every scratch number is V0/C0 until a guarded tool reproduces it.
  - Never declare a gate that has not run.
  progress:
    metric: What the record can say about where low-n improvement is available
    before: >-
      X-041's slate, written against main at 9fe9999d before T-031, T-032 and the
      Kleddamag retention landed, with its A2 cell unrun, the n = 17 restriction
      unmeasured, the n = 26 plateau called unexplained, and no session having declared
      an efficiency workflow since 2026-09-14.
    after: >-
      X-042 with nine corrections to it, four decided cells, the restriction and the
      triples both measured load-bearing at n = 17 with exact witnesses, the n = 26
      plateau explained as a real floor, fold_ceiling_family shown one-sided, the gate's
      4096-atom ceiling identified as a structural limit on external intake, and the
      research loop runnable in a fresh clone for the first time.
  delegations: []
  outputs:
  - packing/campaign/explorations/X-042-what-is-left-at-low-n.md
  - packing/campaign/agendas/agenda-041-low-n-review-and-first-party-n17.md
  - packing/devtools/check_bootstrap.py
  - packing/devtools/check_ci_gate_walls.py
  - packing/devtools/translate_kleddamag_certificate.py
  - packing/devtools/rebump_certificate.py
  - packing/devtools/measure_interval_stalls.py
  checks:
  - 'edit tier after the bootstrap repair: passed, 124.4 s of a 240 s ceiling, 50 of 82 steps'
  - 'campaign record: OK, 40 reports, 38 agendas'
  - 'synopsis agrees with the artifacts: passed after the census rows were reconciled'
  - 'fast tier: 637.3 s of a 600 s ceiling, reported not failed (4 cpus against a 4-cpu/--jobs-3 reference); four steps failed and each is classified below'
  - 'known-best atlas records and sample: failed as mine and is fixed - the n-011.md rigidity edit propagates into the generated composite-figure.json, regenerated with --update and the step now passes'
  - 'workbench browser behavior in Chromium: environment, not code. SQUARES_BROWSER_EXECUTABLE is unset in this container; with it pointed at /opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell the check passes in full'
  - 'test_timeout_kills_and_reaps_a_termination_resistant_process_group and test_nonzero_leader_exit_reaps_a_sigterm_ignoring_grandchild: container process semantics. Both fail in isolation as well as under load, so they are not the contention flakes the session-149 handoff expected; the error is "worker process group remained alive after SIGKILL" and pid 1 here is process_api rather than an init that reaps'
  - 'test_the_revision_is_the_length_this_repository_abbreviates_to: pre-existing and not caused by this branch. It asserts PUBLICATION_REVISION (8 characters) has the length git currently abbreviates to, and a complete clone of this repository abbreviates to 9 - origin/main is 97efd26f5. The shallow clone masked it'
  stop_reason: >-
    Stopped rather than completed, and the debt is named rather than papered over. Every
    dispatched cell is decided, one bound moved and is accepted by both retention routes
    with its dilation-limit record replayed, and the records are landed. What is missing
    is a qualifying gate pass: the fast tier failed four steps here, one of which was
    this branch's and is fixed, while three are the container and a pre-existing
    complete-clone fragility that no change on this branch caused and none can repair
    from inside it. Declaring a pass would be declaring a gate that did not pass, so the
    record carries certification debt instead.
  next_action: >-
    Under think-gvlg: obtain a qualifying fast-gate pass on a host where the three
    environment failures above do not apply, then register the n = 11 rung, which is
    accepted by both routes and has no T-id, following the handoff's three steps.
---
# Session 151: What Is Left at Low `n`, and a Loop That Could Not Run

The entry point was **W5 efficiency-loop**, not by plan but by measurement: the first
command of the session was the edit tier, and it failed three steps.
`OR-12` was seventeen terminal blocks overdue, and `think-zmos` had been selected by
Session 150 as the next entry and not run.

## The block opened by finding that nothing could run

A fresh remote-session clone of this repository could not run `packing-validate --edit`
at all, and none of the five reasons was a bug in the gate.
Each was a fact about the checkout that no tool asked about, so each surfaced as a
confusing failure somewhere downstream.
The bootstrap receipt has them in the order they were hit.

The measurement that matters for `OR-14` is the one after the repair: **124.4 s of wall
against a 240 s ceiling**, 52%, exit 0. No figure from this session is the one to write
into `gate-budgets.yaml`, because this box has four CPUs and the edit tier’s reference
shape is two.

## `think-zmos` answered, and its own hypothesis refuted

The bead attributed the exhaustive tier’s 731 s of unexplained wall to setup,
serialisation, or a step that grew.
Setup is 22 s of 2,674; the tier’s own step is 2,648, or 99.0%. And no step grew: the
same 58 tests, compared by name across two runs, cost 1,836.1 s and 2,621.4 s, a uniform
1.428x, while two runs of the byte-identical commit `030d109a` read 2,608 s and 2,771 s.
**The 1.38x is the hosted runner pool, not drift.** `OR-17`’s text is corrected
accordingly; the clocking obligation it states is unchanged and the correction
strengthens it, since a number nothing clocks cannot tell a regression from a slow draw.

## What the review found, and what the validation lane caught

`X-042` contradicts `X-041` in nine places.
The three that redirect work are in its opening section and are not repeated here.

The validation lane earned its place by catching an error of this session’s own making.
`X-042` claimed `H-228` was refuted as stated, and that was wrong: the argument uses the
interior convention, `H-228` is stated for closed unit squares, and sixteen closed grid
squares share their edges and vertices.
The cross-n lane reached the same conclusion independently.
The verdict is reverted, and what the episode leaves is a specification constraint
rather than a finding — the `BC-365` verifier must decide closed cores, because an
open-core verifier is dead at every integer side, and the record nowhere fixes the
convention.

## What the research block decided

Four cells, no bound moved, and every number exact.
The two that matter most are negatives with witnesses rather than absences: the 2-of-3
atoms are load-bearing at `n = 17`, and so is the parent-centre restriction, the latter
with one exact witness at row 6512 that two lanes derived independently and agreed on to
the last digit.

The `n = 27` and `n = 28` cell is the most interesting refusal.
Its premise held exactly, its re-bump cleared the Condition 5 stall completely at the
theorem’s own threshold, and the gate refused anyway — on its requirement that the two
routes agree on the exact least mass, with all 272 stalls in the axis-parallel direction
below the resolution floor of the arithmetic.
That is a finding about the gate rather than a bound, and it is recorded as one.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
