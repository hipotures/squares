---
title: session-139 — n11 overnight research
softschema:
  contract: packing.squares:AgentSession/v2
  schema: ../schemas/agent-session.schema.yaml
  envelope: session
  status: enforced
session:
  id: session-139
  title: N11 Overnight Research
  date: '2026-09-18'
  started_at: '2026-09-18T05:33:00Z'
  deadline_at: '2026-09-18T13:33:00Z'
  branch: cursor/n11-overnight-8h-f02a
  primary_bead: think-mcb6
  status: in_progress
  goal: >-
    Make significant progress on unresolved small-n questions, especially n=11: register
    and then test Route S (H-163 / exp-161), close or tightly bound the H-216 n=6
    calibration, and land the think-g3j7 relational reader that unblocks Route F1.
  workflow_phases:
  - workflow: research-loop
    focus: insight
    recording: contemporaneous
    clock_role: work
    commitment: BC-357
    bead: think-mcb6
    objective: >-
      Freeze this session, register exp-161 for H-163, and dispatch three disjoint
      lanes: H-216 freeze/polish at n=6 299/100, the think-g3j7 new reader, and Route S
      preregistration. H-216 must exit this phase.
    status: in_progress
    entered_by: session_start
    switch_reason: null
    budget_minutes: 180
    started_at: '2026-09-18T05:33:00Z'
    deadline_at: '2026-09-18T08:33:00Z'
    expected_output: >-
      session-139, exp-161 in-progress with a live lease, an H-216 freeze or ceiling
      family receipt under agenda-037, and a think-g3j7 reader sketch or tests that do
      not touch T-025/T-026 verify_claim.py.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check &&
      uv run --frozen --all-extras --group dev packing-validate --records
    kill_condition: >-
      Stop H-216 at this phase deadline even if the bracket is open. Do not start a
      covering LP, packing-campaign numeric run, or Route S optimizer before exp-161
      exists. Do not mutate T-025/T-026 verify_claim.py.
    fallback: >-
      Retain whatever freeze, reader tests, and exp-161 contract exist, then spend
      Block 4 on think-g4n9 and Blocks 5–7 on Route S if exp-161 exists else the reader.
    outcome: null
    evidence: []
    stop_reason: null
    next_action: >-
      Block 4 is W5 think-g4n9. Blocks 5–7 run the exp-161 target if the artifact
      exists; otherwise continue the F1 reader. Block 8 is closeout.
  budget:
    wall_minutes: 480
    max_cycles: 8
    orientation_minutes: 15
    checkpoint_minutes: 60
    slice_minutes: 180
    finalization_minutes: 40
  stop_conditions:
  - Close by 2026-09-18T13:33:00Z with records, regenerated views, and a morning report.
  - Do not close think-qqzs, think-g3j7, think-gyzw, or think-jwb1.
  - Do not allocate exp-161 to F1 or M7; it is H-163 Route S only.
  - Do not mutate T-025 or T-026 verify_claim.py.
  - Do not change accept rules, thresholds, or metrics.
  - packing-campaign numeric unattended remains NO-GO.
  - H-216 calibration is not a significant n=11 result; cap it at this first phase.
  - Attic scratch is V0/C0 and does not decide a claim.
  progress:
    metric: >-
      Unresolved small-n questions with a retained artifact: exp-161 registered and
      either tested or still leased; H-216 confirmed, refuted, or tightly bracketed
      under both ceiling readers or both decide_certificate routes; think-g3j7 reader
      present without mutating T-025/T-026.
    before: >-
      exp-161 unallocated; H-163 open and untested; H-216 open with only attic scratch
      at n=6 299/100; F1 blocked on a missing reader, sites-1 checkpoint, and guarded
      colgen; PR walls advisory under think-g4n9.
    after: null
  delegations:
  - task: Register exp-161 for H-163 with source, target, budget, accept, stop, review
      boundary, and evidence paths. Build no optimizer and run no coverage until that
      artifact exists.
    operator: Cursor coordinator Lane C
    status: in_progress
    recording: contemporaneous
    outcome: null
    evidence: null
    files: null
    checks: null
    uncertainty: >-
      BC-343 remains agenda-blocked on BC-355's advisory walls. The owner authorized
      Route S registration tonight; think-97we is closed and the instrument is admitted.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Producer is in-tree and emits no candidate. Do not run coverage.
      A coverage-encoding search still waits. Admission-control manifests are excluded.
    phase: 1
    budget_minutes: 90
    started_at: '2026-09-18T05:33:00Z'
    deadline_at: '2026-09-18T07:03:00Z'
    expected_output: >-
      packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-161-h163-route-s-threshold-compression.md
      with a live lease and verdict in-progress.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev packing-ledger check
    kill_condition: >-
      Stop before writing a candidate, running coverage, or allocating this id to H-216
      or H-217.
    fallback: Keep H-163 open and untested rather than invent a target.
    write_scope:
    - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-161-h163-route-s-threshold-compression.md
    - packing/campaign/hypotheses/H-163-route-s-threshold-compression.md
    - packing/campaign/agendas/agenda-036-n11-strategy-reset-roadmap.md
    - packing/campaign/ideas.md
    - packing/campaign/explorations/X-032-route-s-threshold-compression.md
    excluded_commands:
    - packing-campaign run
    - optimizer
    - coverage target
    - candidate generation
  - task: Freeze and polish a helper-free point family at n=6, side 299/100, B=9977/10000,
      181-net, and hand it to both ceiling readers or both decide_certificate routes.
    operator: Cursor Lane A H-216
    status: in_progress
    recording: contemporaneous
    outcome: null
    evidence: null
    files: null
    checks: null
    uncertainty: >-
      X-037 attic numbers [83/14, 6.006571] are V0/C0. A float LP or incomplete row set
      decides neither direction.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Freeze covering 6.08216 does not confirm; polished family 76/13
      depth-one fails K3 and does not kill. H-216 stays open. Exit at 08:33Z.
    phase: 1
    budget_minutes: 180
    started_at: '2026-09-18T05:33:00Z'
    deadline_at: '2026-09-18T08:33:00Z'
    expected_output: >-
      A named freeze or polished ceiling-family JSON under
      packing/campaign/series/series-000-smoke-and-calibration/results/agenda-037/
      plus a two-reader or two-route decision, or a recorded stall.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.independent_ceiling_reader --help && uv run --frozen --all-extras
      --group dev python -m devtools.decide_certificate --help
    kill_condition: >-
      Exit at 08:33Z even if undecided. Do not treat a decided H-216 as an n=11 result.
      Do not allocate exp-161.
    fallback: Keep the freeze receipt and the exact bracket; leave H-216 open.
    write_scope:
    - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-037/
    excluded_commands:
    - packing-campaign run
    - optimizer
    - python3
  - task: Land a new relational-certificate reader for weighted-majority, k-of-S, and
      floor atoms without mutating T-025/T-026 verify_claim.py.
    operator: Cursor Lane B F1 reader
    status: in_progress
    recording: contemporaneous
    outcome: null
    evidence: null
    files: null
    checks: null
    uncertainty: >-
      think-h1ju and think-k1pe passed a private review whose candidate lived under
      /private/tmp/n11-floor-atom-prep, which is not in this checkout. Production
      adoption still has to happen in-tree.
    elapsed_seconds: null
    elapsed_quality: unavailable
    next_action: Implement the new reader and controls; do not start covering LP.
    phase: 1
    budget_minutes: 180
    started_at: '2026-09-18T05:33:00Z'
    deadline_at: '2026-09-18T08:33:00Z'
    expected_output: >-
      A new reader module and tests covering threshold (S,k,w) compatibility, a 2-of-5
      atom with a four-site core, and floor atoms, without editing
      packing/cases/n11_threshold_certificate/verify_claim.py.
    validation_command: >-
      cd packing && uv run --frozen --all-extras --group dev pytest -q
      tests/test_decide_relational_certificate.py
    kill_condition: >-
      Stop rather than mutate T-025/T-026 verify_claim.py or decide_threshold_certificate.py.
      Do not run a covering LP or sites-1 regeneration until the reader exists.
    fallback: Keep a failing test that states the missing format; leave think-g3j7 open.
    write_scope:
    - packing/src/sqpack/fractional/relational.py
    - packing/devtools/decide_relational_certificate.py
    - packing/tests/test_decide_relational_certificate.py
    excluded_commands:
    - packing-campaign run
    - optimizer
    - coverage target
    - python3
  outputs:
  - packing/campaign/agent-sessions/session-139-n11-overnight-research.md
  - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-161-h163-route-s-threshold-compression.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-037/h216-n6-299-100-covering.json
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-037/h216-n6-299-100-family-polished.json
  - packing/devtools/compress_threshold_certificate.py
  - packing/src/sqpack/fractional/relational.py
  checks: []
  stop_reason: null
  next_action: >-
    Continue Blocks 1–3 until 08:33Z: H-216 freeze/polish retained and open;
    keep the F1 reader tests green; producer exists but emits no candidate.
    Then Block 4 think-g4n9, Blocks 5–7 Route S only with --authorize-target
    exp-161 after a live --check, Block 8 closeout.
---
# Session 139: N11 Overnight Research

Workflow entry: **W10 then a W6/W7/W5 mix**. This record is the live eight-hour
overnight. The latest terminal handoff remains
[session-138](session-138-n11-overnight-review.md); its selected next entry is still
`think-qqzs` / BC-357. This session executes that entry in parallel with Route S
registration and the F1 reader, because the owner authorized autonomous overnight work
whose top goal is unresolved questions, especially n=11.

## Block schedule

| Block | Window (UTC) | Kind | Work |
| --- | --- | --- | --- |
| 0 | 05:33–05:50 | W10 freeze | This record, branch `cursor/n11-overnight-8h-f02a`, hourly watchdog, 8h closeout |
| 1–3 | 05:33–08:33 | W6/W7 | Lane A H-216; Lane B `think-g3j7` reader; Lane C exp-161. H-216 exits at 08:33 |
| 4 | 08:33–09:33 | W5 | `think-g4n9` PR-wall ≤180s (OR-12) |
| 5–7 | 09:33–12:53 | W6 | Route S target if exp-161 exists; else continue the F1 reader. No covering LP until reader, sites-1, and guarded colgen exist |
| 8 | 12:53–13:33 | W10 closeout | Morning report, `packing-validate --records`, terminalize this session |

Hourly watchdog: `overnight-priority-check`. Closeout timer: `overnight-8h-closeout`.

## Hard constraints

- Project Python 3.14 via `uv run --frozen` from `packing/` only.
- Do not close `think-qqzs`, `think-g3j7`, `think-gyzw`, or `think-jwb1`.
- `exp-161` is H-163 only.
- Do not mutate T-025/T-026 `verify_claim.py`.
- `packing-campaign` numeric unattended is NO-GO (D-044/D-046; no `runner.command` on
  H-216/H-163).
- A decided H-216 does not move `s(6)=3` and is not an n=11 result.

## Lanes

**A / BC-357 / H-216.** Stock drivers on main:
`run_fractional_colgen --freeze-family --support-cap 0`, `polish_ceiling_family`,
`independent_ceiling_reader`, `verify_ceiling`, `decide_certificate`. Confirm only with
covering < 6 both gate routes; kill only with an exact depth-one family of total ≥ 6
both ceiling readers.

**B / BC-358 tooling.** New reader first (`think-g3j7`). `think-3xbr` and `think-gyzw`
wait on it. k-of-S is already T-025’s `(S,k,w)`; floor atoms are a new class.
A T-id in the new class needs two-route C4.

**C / BC-343 / H-163.** Register `exp-161`, then build the named producer, then a
target. Confirm only at `N+ <= 23`, budget < 11, least charge ≥ 1, both exact routes,
source-distinct replay.
Refute only by exact infeasibility of every `N+ <= 23` family member.
The three admission-control manifests cannot confirm.
Timeout is unresolved, never rejected.

## Hour 1 note (2026-09-18T05:55Z)

H-216 freeze covering total `76027/12500 = 6.08216` does not confirm. Polish then both
ceiling readers: exact total `76/13`, max depth 1, K3 fails. That does not kill.
H-216 stays open; not an n=11 result. exp-161 accept hole closed. Producer is in-tree
and emits no candidate. F1 reader modules are in-tree with the 2-of-5 versus floor
charge test. Hosted typecheck band is now 55.67 s / ceiling 111 s. Head `876dd80f`
is hosted-green (37 checks). A second H-216 site set on grids 18/24/29/34 froze
covering `151931/25000` = 6.07724 (does not confirm).

## Block 4 W5 plan (`think-g4n9`, 08:33Z)

Packing wall pole is **frontend** (6 of the last 8 exact-head successes). Pages
full-build is usually ≤180 s; the newest explainer-in-scope head was 190 s on
print-layout. Both walls stay **advisory**. Do not flip enforcement. Do not add
`suite-c` in this block: a third shard leaves the frontend job at 168–189 s.

Slice: start Chromium early with the existing `_submission_order` / `start_early`
tool, and stop serializing independent Chromium work.

- `packing/src/sqpack/cli/validate.py`: `start_early=True` on workbench Chromium
  behavior (hosted pair 59.09 s / 91.69 s).
- `.github/workflows/packing-validation.yml`: `playwright install --with-deps`
  in parallel with uv/Node after checkout; apt-archive cache like Pages.
- `.github/workflows/pages.yml`: print-layout self-check concurrent with
  `check_print_layout`; typography paper/startup/geometry as concurrent groups.
- Tests: `test_validation_cli.py`, `test_module_boundaries.py`,
  `test_pages_workflow.py`.
- Do not edit `gate-budgets.yaml` in the first commit.

Predicted packing wall ~150 s typical / ~169 s at 1.8× of fast Chromium, still
failing on suite-a slow runners and queue ≥30 s. `suite-c` is the follow-on.
Re-enforcement still needs five consecutive exact-head runs with **both** walls
≤180 s.

Live `admit_threshold_compression --check` passed at 2026-09-18T06:05Z (exit 0).
Coverage on frozen U025 is linear in orbit weights; the producer formulates `A w >= 1`
under `--authorize-target exp-161` and enumerates only with `--encode-coverage`.
Default still emits no candidate. sites-1 regeneration refuses: the 15,021-row matrix
and sepcore/lp383 APIs are unretained (`missing-inputs`).

## Hour 1 watchdog (2026-09-18T06:07Z)

H-216 chase is done for this phase: two named site sets, both covering ≥ 6. Not n=11.
Lane B: `devtools.regenerate_sites1_checkpoint` is in-tree and refuses. Lane C: live
`--check` passed; coverage encoding landed. Next: `think-gyzw` guarded colgen skeleton
(refuses without sites-1), G4 n-parameterised threshold producer, M3 `think-k4vb` kill
test if cheap. Block 4 at 08:33Z is Chromium-early.

## Hour 1 continuation (2026-09-18T06:15Z)

Coverage encoding is ruff-clean and type-clean; 24 tests passed.
Authorized producer default path is on the branch (`encoding_ready`, no candidate).
Three implementation lanes plus a low-n scout are in flight: guarded relational colgen,
G4 n-parameterised threshold producer (in-tree rewrite of the agenda-034 separator, not
a `.py.txt` promotion), and the M3 piercing tool. Do not start another H-216 freeze.
`--encode-coverage` waits for Blocks 5–7.

## Hour 1 scout follow-up (2026-09-18T06:18Z)

H-216 third freeze is not started (phase exit). n=7–9 are proved and have no covering
rows. n=12 grid covering at `3969/1000` converged at `12.363498` (crossed 12 at round 4;
site set refuted; side open). n=11 at `383/100` is next. Guarded
`devtools.run_relational_colgen` refuses covering without sites-1 (`think-gyzw` remains
open).

## Hour 1 n=11 383/100 (2026-09-18T06:32Z)

n=11 auto grids `(25, 34, 41)` at `383/100` converged in 82.2 s at restricted optimum
`11.192598` (rationalised `44770567/4000000`). Crossed eleven at LP round 6. Site set
refuted; side open. T-025 and T-026 unchanged. Next cheap probe: denser grids at the
same side. G4 and M3 sources are on disk, uncommitted until their tests pass.

## Hour 1 four-grid (2026-09-18T06:36Z)

n=11 `--grid-counts 25,34,41,48` at `383/100` converged in 81.7 s at `11.142857`
(rationalised `2228577/200000`). About 2,300 extra sites dropped 0.050 from the auto
grid. Still above eleven. Next: T-025-seeded grids at the same side. G4 and M3 landed.

## Hour 1 T-025 seed (2026-09-18T06:39Z)

Four-grid union T-025 (584 seed sites, 6249 total) converged at `11.140351` in 107.9 s.
Drop from four-grid: 0.0025. Point-atom covering at `383/100` is above eleven on three
named site sets. Next: scout #3, denser grids at `191/50`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
