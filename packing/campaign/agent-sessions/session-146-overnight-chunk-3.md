---
title: "Session 146 — overnight chunk 3: the exp-219 registration review and the fold tool"
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-146
  title: Overnight Chunk 3 — The exp-219 Registration Review and the Fold Tool
  date: '2026-09-20'
  started_at: '2026-09-20T12:52:00Z'
  deadline_at: '2026-09-20T14:52:00Z'
  ended_at: '2026-09-20T13:32:00Z'
  branch: claude/kind-wright-whxxn6-chunk3
  primary_bead: think-b7pr
  status: completed
  goal: >-
    Take BC-367's first two items in the loop's remaining wall: an adversarial
    Fable review of the exp-219 conditional exclusion for registration, with a
    costed second-stage discriminator for the complementary corner class, and the
    retained family-fold tool that discharges the OR-1 debt Sessions 144 recorded.
  workflow_phases:
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    commitment: BC-367
    objective: >-
      A Fable lane reviews what exp-219 establishes, its inherited conditions, the
      second stage the deep-branch neutrality forces, and the registration wording;
      an Opus lane retains devtools.fold_ceiling_family with a --check that re-folds
      the exp-214 and exp-218 families against the retained merged files. The n=26
      second site set and the remaining corner-bin classes stay on BC-367 for the
      next session; no LP or column-generation target runs here.
    status: completed
    entered_by: session_start
    switch_reason: null
    budget_minutes: 95
    started_at: '2026-09-20T12:52:00Z'
    deadline_at: '2026-09-20T14:27:00Z'
    expected_output: >-
      A review receipt under results/agenda-040 with a registration verdict, the
      H-222 notes updated to the reviewed scope, the fold tool with tests, and the
      two receipts pointing at it.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      The review returns DO NOT REGISTER on a soundness finding; then the finding is
      recorded on H-222 and the registration is refused with its reason.
    fallback: Record what was reviewed, keep the clocks honest, and hand the rest to BC-367.
    outcome: >-
      The registration review returned REGISTER WITH CORRECTIONS with no soundness
      defect: the gate replays byte-for-byte, the theorem is stated with every
      hypothesis explicit, and the all-deep class is already outside the point
      language (BC-366) so the corner tree cannot close at 96/25 by clipping alone.
      The bytes' unconditional claim string (D1) was fixed in the driver, the gate and
      the four readers, and exp-220 re-froze the same 680-atom covering under the
      class claim with both routes accepting (sha256 876820dd...7a461); D2 to D4 and
      D6 are applied to the records. devtools.fold_ceiling_family is retained with a
      --check that reproduces both retained merged families. The registration entry
      itself, the four mixed classes and the n=26 second site set stay on BC-367.
    evidence:
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h222-registration-review.md
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-receipt.md
    - packing/devtools/fold_ceiling_family.py
    stop_reason: >-
      Both lanes reported and exp-220 decided; the loop's clock ends the chunk before
      the registration entry is written.
    next_action: Close the record and update the stacked pull request.
  resource_rollups:
  - packing/campaign/resource-usage/5e071e1a-5ab8-5bae-a5c0-c3687815bf4a.yaml
  - packing/campaign/resource-usage/a57beb19e2ae7ed7b.yaml
  - packing/campaign/resource-usage/a556b81b10ff8b762.yaml
  - packing/campaign/resource-usage/aac63642e9cd0a16e.yaml
  budget:
    wall_minutes: 120
    finalization_minutes: 25
  stop_conditions:
  - No registration without a REGISTER or REGISTER WITH CORRECTIONS verdict, and every correction applied before the record says registered.
  - The fold tool is retained only if its --check matches both retained merged families exactly.
  - The chunk closes by 14:52Z with its records validated, committed, and pushed as a stacked draft pull request.
  progress:
    metric: BC-367 items decided
    before: exp-219 accepted but its conditional exclusion is unreviewed for registration; the family fold is a scratch script.
    after: >-
      The exp-219 statement reviewed for registration with corrected scope and the
      bytes re-frozen under the class claim (exp-220 accepted); the fold tool
      retained; the registration entry, the mixed classes and n=26 remain on BC-367.
  delegations:
  - task: Adversarial review of the exp-219 conditional exclusion for registration, with the second-stage discriminator
    operator: chunk3_reviewer; Claude Fable max
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      REGISTER WITH CORRECTIONS. The gate replays byte-for-byte (both routes at
      2000013/2000000, 0 stalled boxes); the predicate, D4 invariance and polygon
      membership checked independently on 8,400 centres; the theorem stated with every
      hypothesis explicit and its direction confirmed against the code, lossless from
      cores to unit squares. Six bookkeeping defects, none of soundness: the bytes
      carry an unconditional claim string (D1, re-frozen as exp-220), BC-367 and the
      receipt overstate what remains open (D2), wording (D3, D5, D6), and the engine
      field lists readers that never ran (D4). The all-deep class is already outside
      the point language (BC-366), so the corner tree cannot close at 96/25 by
      clipping alone; the second stage is a 2-of-3 threshold atom on ring-centre
      overlaps inside the all-deep class.
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h222-registration-review.md]
    files: []
    checks: [Gate replayed with and without the flag; 8,400-centre predicate check; conditions 1 to 4 recomputed; unclipped least mass 2819857/4000000 measured.]
    uncertainty: A review is evidence for the record's wording, not a replay; the replay command it names is what a successor runs.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator writes the receipt and the H-222 notes from the verdict.
    started_at: '2026-09-20T12:52:00Z'
    deadline_at: '2026-09-20T13:52:00Z'
    budget_minutes: 60
    write_scope: [session scratchpad chunk3-review/]
    excluded_commands: [git commit, git push, any edit under the repository tree, any LP or column-generation target run]
    expected_output: review.md with a verdict block and numbered findings.
    validation_command: Coordinator reads the review file.
    kill_condition: The receipt or the instrument is unreadable.
    fallback: Report that and stop.
  - task: Retain devtools.fold_ceiling_family with tests and a --check against the retained merged families
    operator: chunk3_fold_tool; Claude Opus high
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      devtools.fold_ceiling_family retained with a pure fold keyed on the polisher's
      own fold_half_tangent, a --check that refuses to overwrite its inputs, and seven
      tests; --check re-folds exp-214 (312 placements, 8 folded, total 298314/19165)
      and exp-218 (256 placements, 0 folded) to the retained merged files with 0
      differences, and the exp-214 refold is byte-identical outside the provenance
      block. Both receipts name the tool.
    evidence: [packing/devtools/fold_ceiling_family.py, packing/tests/test_fold_ceiling_family.py]
    files: [packing/devtools/fold_ceiling_family.py, packing/tests/test_fold_ceiling_family.py, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-receipt.md, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-218-n17-23-5-receipt.md]
    checks: [7 tests pass; ruff, ruff format and basedpyright clean; check_no_embedded_js and test_module_boundaries pass; --check exit 0 on both retained pairs.]
    uncertainty: The retained merged files were written by the scratch script; the check proves the tool reproduces them, not that the rule is the right one.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator runs the tests and the records tier.
    started_at: '2026-09-20T12:52:00Z'
    deadline_at: '2026-09-20T13:32:00Z'
    budget_minutes: 40
    write_scope: [packing/devtools/fold_ceiling_family.py, packing/tests/test_fold_ceiling_family.py, packing/tests/test_module_boundaries.py, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-214-n13-399-100-receipt.md, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-218-n17-23-5-receipt.md]
    excluded_commands: [git commit, git push, any edit to a retained family file]
    expected_output: The module, its tests, two --check outputs, and the two receipt sentences.
    validation_command: cd packing && uv run --frozen --all-extras --group dev pytest tests/test_fold_ceiling_family.py -q
    kill_condition: The fold of a retained raw family differs from the retained merged file.
    fallback: Report the difference and leave the scratch script named as the record.
  - task: Write the class claim and id under a corner clip, make the gate expect them, and re-freeze exp-219 as exp-220
    operator: chunk3_claim_strings; Claude Opus high
    status: completed
    recording: contemporaneous
    phase: 1
    outcome: >-
      Under a corner clip the driver writes the claim "corner class d = 1/2 excluded
      at s(11) >= 96/25" and the id C-n011-fractional-96-25-clip-1-2, the family
      record carries variant and corner_clip at top level, the gate expects the class
      strings under the flag and names a mismatch, and the four readers refuse a
      class record without the flag; eleven new tests. exp-220 re-froze the covering
      in 262.9 s with all 680 atoms equal to exp-219's; both routes accept at
      2000013/2000000 (sha256 876820dd...7a461) and the gate refuses without the flag.
      The checkpoint path still has no clip parameter (think-bxu1).
    evidence: [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-decide.stdout, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-decide-noflag.stdout]
    files: [packing/src/sqpack/fractional/corner_clip.py, packing/devtools/run_fractional_colgen.py, packing/devtools/decide_certificate.py, packing/devtools/declare_least_cell_mass.py, packing/devtools/replay_ceiling_family.py, packing/devtools/independent_ceiling_reader.py, packing/devtools/polish_ceiling_family.py, packing/tests/test_fractional_corner_clip.py]
    checks: [ruff, ruff format and basedpyright clean on the eight files; 115 tests across the six affected test files; 680 atoms compared as exact Fractions.]
    uncertainty: The re-freeze should reproduce exp-219's placements exactly; a difference is a finding, not a failure of the fix.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Coordinator decides exp-220 from the two gate outputs and pins the new SHA.
    started_at: '2026-09-20T13:10:00Z'
    deadline_at: '2026-09-20T13:55:00Z'
    budget_minutes: 45
    write_scope: [packing/devtools/run_fractional_colgen.py, packing/devtools/decide_certificate.py, packing/devtools/declare_least_cell_mass.py, packing/devtools/polish_ceiling_family.py, packing/devtools/independent_ceiling_reader.py, packing/devtools/replay_ceiling_family.py, packing/tests/, packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-*]
    excluded_commands: [git commit, git push, any edit to exp-219's retained files, any change to the registered exp-220 command]
    expected_output: The corrected driver and gate with tests, the exp-220 run files, and the two gate outputs.
    validation_command: cd packing && uv run --frozen --all-extras --group dev pytest tests/test_fractional_corner_clip.py -q
    kill_condition: The registered command refuses on a guard.
    fallback: Record the refusal on exp-220 and leave exp-219's bytes as the record.
  outputs:
  - packing/campaign/agent-sessions/session-146-overnight-chunk-3.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/h222-registration-review.md
  - packing/devtools/fold_ceiling_family.py
  - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-220-h222-n11-96-25-class-refreeze.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-220-n11-96-25-class-receipt.md
  checks:
  - 'full gate: fast at 8ffdf553: passed (hosted run 35513500902; pages run 35513500975)'
  - packing-validate --records passed locally at 8ffdf553 and on the closeout tree.
  - No target ran before its experiment record existed; exp-220's command is exp-219's with new output paths, copied verbatim from the record.
  - The corrected gate refuses exp-219's retained bytes and accepts exp-220's; exp-220's 680 atoms equal exp-219's as exact Fractions.
  stop_reason: >-
    BC-367's review and re-freeze items are done and the fold tool is retained; the
    registration entry, the four mixed corner classes and the n=26 second site set
    stay on BC-367 under think-b7pr, and the overnight loop closes on its clock.
  next_action: Session 147 under think-b7pr writes the BC-367 registration entry at the reviewed scope, then the mixed classes and n=26.
---
# Session 146: Overnight Chunk 3

The third chunk of the overnight loop that
[agenda-040](../agendas/agenda-040-overnight-lower-bound-loop.md) schedules, stacked on
Session 145’s branch, taking the two items of BC-367 that fit the loop’s remaining wall:
the registration review of the exp-219 conditional exclusion and the retained fold tool.
The n=26 second site set and the remaining corner-bin classes stay on BC-367.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->

## How the chunk ended

Both lanes reported inside their budgets.
The review found no soundness defect and six bookkeeping ones; the one in the bytes (an
unconditional claim string on a class record) was fixed in code and demonstrated by
re-freezing the same covering as exp-220, which the corrected gate accepts under the
flag and refuses without it, while the same gate now refuses exp-219’s bytes.
The registration entry at the reviewed scope is the next session’s first item; the
review’s second-stage analysis says the tree cannot close at 96/25 by clipping alone, so
the mixed classes are a bounded follow-up and the instrument that could matter is a
2-of-3 threshold atom inside the all-deep class.
