---
title: "Session 148 — chunk 5: the second stage inside the all-deep class, and the gap-g wedge"
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-148
  title: Chunk 5 — The Second Stage Inside the All-Deep Class, and the Gap-g Wedge
  date: '2026-09-20'
  started_at: '2026-09-20T15:22:00Z'
  deadline_at: '2026-09-20T18:22:00Z'
  ended_at: '2026-09-20T17:04:00Z'
  branch: claude/kind-wright-whxxn6-chunk5
  primary_bead: think-b7pr
  status: stopped
  goal: >-
    Take the two mathematical items the registration review left as the ones that
    could matter: make the 2-of-3 ring-centre relation inside the all-deep corner
    class at 96/25 precise enough to register and instrument, and derive the gap-g
    wedge conflict edge BC-364 asks for against the A6 64-family; beside them, thread
    the corner clip through the threshold routes so the first can run.
  workflow_phases:
  - workflow: insight-iteration
    focus: insight
    recording: contemporaneous
    clock_role: work
    commitment: BC-367
    objective: >-
      Two Fable derivation lanes (the ring-centre lemma and atom family with an exact
      check on the transported 88-family; the gap-g wedge lemma with an exact pair
      check on the 64-family) and one Opus lane (the corner clip on threshold.py and
      threshold_interval.py, unclipped byte-identical), then a Fable review of both
      derivations; no LP or column-generation target runs.
    status: stopped
    entered_by: session_start
    switch_reason: null
    budget_minutes: 160
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T18:02:00Z'
    expected_output: >-
      A registered H-232 (or a recorded reason not to), a BC-364 disposition with the
      exact pair check, the threshold clip admitted or a design, and a review record.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      A derivation lane finds the relation false on the family; then the finding is
      recorded and the instrument is not built.
    fallback: Record what was derived, keep the clocks honest, and hand the rest to BC-367.
    outcome: >-
      H-232 registered after an adversarial review (ADMIT WITH CORRECTIONS): the
      all-deep class's structure is proved, the ring-centre 2-of-3 atom collects
      exactly 5/4 against budget 1 from the transported 88-family and that is the
      maximum, and the fixed-support screen is the full kill at value 7. The gap-g
      wedge lemma is derived and reaches the 7.11 degree orbit, but no weighted
      pair of the 64-family violates it (CANNOT REACH); its review and its port were
      stopped before reporting, so H-230 is not yet dispositioned. The threshold-clip
      build was stopped mid-edit; both partial code lanes are retained as patches.
    evidence:
    - packing/campaign/hypotheses/H-232-n11-all-deep-class-ring-centre-atom.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md
    stop_reason: >-
      The owner stopped the loop at 17:02Z to conserve tokens, with two lanes
      unreported; everything they left is captured under results/agenda-040.
    next_action: Resume under the follow-up bead from the retained patches and the wedge derivation.
  budget:
    wall_minutes: 180
    finalization_minutes: 20
  stop_conditions:
  - No hypothesis is registered without an exact check of its family charge on a retained artifact.
  - No LP or column-generation target runs in this chunk.
  - The chunk closes by 18:22Z with its records validated, committed, and pushed as a stacked draft pull request.
  progress:
    metric: BC-367 second-stage items derived and dispositioned
    before: The ring-centre 2-of-3 relation is a review sketch; the gap-g wedge is underived; the threshold routes take no clip.
    after: >-
      H-232 registered and blocked on its instrument; the gap-g wedge derivation
      retained with a CANNOT REACH verdict awaiting review; two partial ports
      retained as patches; BC-364 not yet dispositioned.
  delegations:
  - task: Derive the ring-centre 2-of-3 relation inside the all-deep class at 96/25 with an exact check on the transported 88-family, and write H-232
    operator: chunk5_ring; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      INSTRUMENT. The all-deep class's forced structure proved from lane-a Lemmas
      2 to 4 with the sharpened occupant box X' (beta = B/(1+D)); a wall census by
      chords giving at least three non-occupant squares at depth at least sqrt(2) - 1
      from every wall, and at most one square in the central 1.84-box; the family
      transported to 96/25 (verified, total 11) has corner mass exactly 4 and residual
      7 as 32 mid-wall plus 24 central cores; the ring-centre 2-of-3 atom on three
      named gap-strip sites collects exactly 5/4 against budget 1 on each of its eight
      D4 images, the exact maximum over all site triples (the reviewer's 3/2 is not
      attained; 3-of-4 atoms cut nothing); a counting proof with conditions (C) and
      (B) and the X' refund; H-232 drafted. The instrument needs a non-convex box cut
      on both threshold routes with per-cell exclusion, not the convex clip.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h232-ring-centre-derivation.md, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h232-transported-family-96-25.json]
    files: []
    checks: [transport_ceiling_family --verify proved at 96/25; the 5/4 charge found as the exact maximum over the 125 inclusion-maximal vertex traces of the 56-core arrangement.]
    uncertainty: A derivation is evidence for a hypothesis, not a verdict; the family charge is a Lemma-D necessary condition.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Fable review, then registration of H-232 if the reading survives.
    started_at: '2026-09-20T15:22:00Z'
    deadline_at: '2026-09-20T16:37:00Z'
    budget_minutes: 75
    write_scope: [session scratchpad chunk5-ring/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: report.md with the lemma, the atom family, the exact family charge, and the H-232 text.
    validation_command: Coordinator reads the report and re-runs its exact check.
    kill_condition: The relation is false on the transported family.
    fallback: Report the counterexample and stop.
  - task: Derive the gap-g wedge conflict edge and test it exactly against the A6 64-family (BC-364, H-230)
    operator: chunk5_wedge; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      CANNOT REACH. The gap-g extension of the wall-wedge lemma is derived and
      proved (Lemmas A to C), reproduces 0.3203 at g = 0 and 40.18 degrees, and
      does reach the 7.11 degree orbit (forced area at least 0.076 at the nearest
      wall and 0.150 at the adjacent wall); but on all 2016 pairs of the 64-family
      no core-disjoint pair enters a forced region and no forced regions overlap,
      because for unit squares the wedge conflict is implied by disjointness and
      every square entering a 7.11 degree pocket already overlaps that core; the
      nearest core-disjoint neighbour is 0.1227 outside the provable region and
      0.0029 outside the whole pocket, inside a realisable intrusion zone. H-230's
      first kill clause holds; a conflict-edge atom class would price a relation the
      family already respects.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md]
    files: []
    checks: [All 2016 pairs tested exactly with rigorous rational intrusion bounds; the extended closed depth maximum over 1724 arrangement points is exactly 1.]
    uncertainty: The 7.11 degree orbit at gap 0.016 is the one X-040 names; a reach failure there is a finding, not a failure of the lane. The first attempt was stopped by the owner at 15:46Z after a census only; this is the relaunch.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Fable review, then the BC-364 disposition.
    started_at: '2026-09-20T16:36:00Z'
    deadline_at: '2026-09-20T17:46:00Z'
    budget_minutes: 70
    write_scope: [session scratchpad chunk5-wedge/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: report.md with the lemma, the pairwise condition, the exact pair check, and the verdict.
    validation_command: Coordinator reads the report and re-runs its exact check.
    kill_condition: The lemma's forced region is empty for every gap the family uses.
    fallback: Record why and stop.
  - task: Thread the corner clip through threshold.py and threshold_interval.py with the class claim policy and tests
    operator: chunk5_threshold_clip; Claude Opus high
    status: canceled
    recording: contemporaneous
    phase: 1
    outcome: Stopped by the owner at 17:02Z on the relaunch with the clip threaded through the sweep and interval routes but the CLI and tests unfinished; the diff is retained as h232-threshold-clip-partial.patch and the code tree restored to HEAD.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md]
    files: []
    checks: []
    uncertainty: If the change does not fit the budget the lane delivers a design, not a half-threaded change. The first attempt was stopped by the owner at 15:46Z with partial edits in the worktree; the relaunch continues from them.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator runs the tests; a Fable review before any clipped threshold run.
    started_at: '2026-09-20T16:36:00Z'
    deadline_at: '2026-09-20T17:36:00Z'
    budget_minutes: 60
    write_scope: [packing/src/sqpack/fractional/threshold.py, packing/src/sqpack/fractional/threshold_interval.py, packing/src/sqpack/fractional/corner_clip.py, packing/devtools/decide_threshold_certificate.py, packing/tests/test_threshold_corner_clip.py]
    excluded_commands: [git commit, git push, any edit to packing/cases/n11_threshold_certificate/verify_claim.py, any edit to a retained certificate]
    expected_output: The threaded clip with tests, or a design.
    validation_command: cd packing && uv run --frozen --all-extras --group dev pytest tests/test_threshold_corner_clip.py -q
    kill_condition: T-025's retained certificate decides differently unclipped.
    fallback: Revert and report.
  - task: Adversarial review of the ring-centre derivation and the H-232 text
    operator: chunk5_ring_reviewer; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      ADMIT WITH CORRECTIONS. Theorems 1 to 3 and Corollary 4 sound (one unused
      chord-formula sentence corrected); every family number reproduced from
      independent code; the 5/4 maximality proved by a domination lemma over
      arrangement vertex traces; the counting proof verified line by line with the
      refund exact and idle on the kill side. Three required corrections, applied
      to H-232: the kill rule must name an exact 2-of-3 reader, since the ceiling
      readers alone pass the transported family; the fixed-support screen with
      all-triple 2-of-3 constraints is the full kill at value 7 for every site set;
      and the instrument gap must describe HEAD, where neither threshold route
      takes a cut.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h232-ring-centre-review.md]
    files: []
    checks: [Independent classification by a separating-axis test; transport replay byte-identical; own arrangement (1552 vertices, 881 traces, 125 maximal); max 3-of-4 charge 1.]
    uncertainty: The first attempt was stopped by the owner at 15:46Z before reading; this is the relaunch.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Register H-232 on ADMIT, or record the refusal on the session and X-040.
    started_at: '2026-09-20T16:36:00Z'
    deadline_at: '2026-09-20T17:26:00Z'
    budget_minutes: 50
    write_scope: [session scratchpad chunk5-ring-review/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: review.md with a verdict block and numbered findings with fixes.
    validation_command: Coordinator reads the review file.
    kill_condition: The lane's report is unreadable.
    fallback: Report that and stop.
  - task: Adversarial review of the gap-g wedge derivation and the H-230 kill
    operator: chunk5_wedge_reviewer; Claude Fable max
    status: canceled
    recording: contemporaneous
    phase: 1
    outcome: Stopped by the owner at 17:02Z before writing a finding; the H-230 kill is unreviewed.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md]
    files: []
    checks: []
    uncertainty: A kill under the first clause needs the lemma's proof and the pair test reproduced independently.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: exp-221 verdict and the BC-364 disposition.
    started_at: '2026-09-20T16:55:00Z'
    deadline_at: '2026-09-20T17:40:00Z'
    budget_minutes: 45
    write_scope: [session scratchpad chunk5-wedge-review/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: review.md with a verdict block and numbered findings with fixes.
    validation_command: Coordinator reads the review file.
    kill_condition: The lane's report is unreadable.
    fallback: Report that and stop.
  - task: Port the gap-g wedge lemma and the family pair test into devtools/gap_wedge with tests and the census JSON
    operator: chunk5_wedge_port; Claude Opus high
    status: canceled
    recording: contemporaneous
    phase: 1
    outcome: Stopped by the owner at 17:02Z with the geometry module begun; the diff is retained as h230-gap-wedge-port-partial.patch and the lane's exact-check scripts as .py.txt under h230-gap-wedge-scratch.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md]
    files: []
    checks: []
    uncertainty: The port must reproduce the scratch figures exactly; a difference is a finding.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: exp-221 registered on the ported command and run.
    started_at: '2026-09-20T16:57:00Z'
    deadline_at: '2026-09-20T17:42:00Z'
    budget_minutes: 45
    write_scope: [packing/devtools/gap_wedge/, packing/tests/test_gap_wedge_tools.py, packing/tests/test_module_boundaries.py, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-census.json]
    excluded_commands: [git commit, git push, any edit to the threshold routes or their tests, any edit to a retained family file]
    expected_output: The package, its tests, and the census JSON.
    validation_command: cd packing && uv run --frozen --all-extras --group dev pytest tests/test_gap_wedge_tools.py -q
    kill_condition: A ported figure differs from the scratch report's.
    fallback: Report the difference and leave the scratch report as the record.
  resource_rollups:
  - packing/campaign/resource-usage/5e071e1a-5ab8-5bae-a5c0-c3687815bf4a.yaml
  - packing/campaign/resource-usage/a559dad08e3059322.yaml
  - packing/campaign/resource-usage/ab767eaa07325eb5f.yaml
  - packing/campaign/resource-usage/af80e22bd291ac081.yaml
  - packing/campaign/resource-usage/aa765fa0c2414bc33.yaml
  - packing/campaign/resource-usage/a65f1dd01126278cb.yaml
  - packing/campaign/resource-usage/a2dbeb566572f2219.yaml
  - packing/campaign/resource-usage/a7d6f9f0f839a3ab3.yaml
  - packing/campaign/resource-usage/ac77b62ac52bfd061.yaml
  - packing/campaign/resource-usage/a7cda6271ca02151e.yaml
  outputs:
  - packing/campaign/agent-sessions/session-148-overnight-chunk-5.md
  - packing/campaign/hypotheses/H-232-n11-all-deep-class-ring-centre-atom.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h232-ring-centre-derivation.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h232-ring-centre-review.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h230-gap-wedge-derivation.md
  checks:
  - 'full gate: fast at e2530693: passed (hosted run 35524116652; pages run 35524116649)'
  - packing-validate --records passed locally on the stop tree; the stop commit adds records and retained text only, with the code tree restored to HEAD.
  - No LP or column-generation target ran; every family number in H-232 was reproduced independently by the review.
  stop_reason: >-
    Owner stop at 17:02Z to conserve tokens. Captured: H-232 registered with its
    derivation and review; the gap-g wedge derivation (CANNOT REACH, unreviewed);
    the ring and wedge exact-check scripts as retained text; the two partial ports as
    patches. Not done: the wedge review, exp-221 and BC-364's disposition, the
    threshold clip, the gap_wedge port, and H-232's fixed-support screen (think-qq32).
  next_action: Session 149 under think-n1v2 resumes from the retained patches and the wedge derivation, then the H-232 fixed-support screen.
---
# Session 148: Chunk 5

The loop continued at the owner’s request after the four overnight chunks, stacked on
Session 147’s branch.
The registration review of exp-219 named the instrument that could matter, a 2-of-3
threshold atom on ring-centre overlaps inside the all-deep corner class, and BC-364’s
gap-g wedge derivation was scheduled for a later chunk; both are mathematics first, so
this chunk runs them as Fable derivation lanes with an exact check on a retained family
each, and threads the corner clip through the threshold routes beside them so that the
first can be instrumented.
No target runs.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->

## How the chunk ended

The owner stopped the loop at 17:02Z with two lanes unreported.
What the chunk established is on the record: H-232 with its reviewed derivation, and the
gap-g wedge lemma with the exact all-pairs check that shows it cannot cut the 64-family.
What it did not finish is captured so that a successor starts where the lanes stopped:
the threshold-clip and gap_wedge diffs as patches beside this session’s receipts, and
the lanes’ exact-check scripts as retained text.
The follow-up bead is `think-n1v2`.
