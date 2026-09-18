---
title: X-037 — n11 overnight review and route slate
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-037
  title: N11 Overnight Review and Route Slate
  date: '2026-09-17'
  author: >-
    Claude coordinator (session-138) with Fable and Opus sub-agents: four review lanes,
    one ideation pass, one independent adversarial review, and two execution lanes
  campaign: packing.squares
  brief: >-
    Review the n=11 record and look for a mechanism that could give a significant n=11
    result beyond the one-body ceiling L* = 38200/9977. Rank candidate mechanisms,
    subject them to an independent adversarial review, run the cheapest decisive
    measurements overnight, and leave dispositions and owner decisions. No hypothesis
    registration and no bound claim.
  sources:
  - packing/frontier/n-011.md
  - SYNOPSIS.md
  - packing/campaign/explorations/X-026-what-conditioning-does-and-does-not-buy.md
  - packing/campaign/explorations/X-027-stromquist-fractional-and-structural-strategy.md
  - packing/campaign/explorations/X-032-route-s-threshold-compression.md
  - packing/campaign/agendas/agenda-036-n11-strategy-reset-roadmap.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-034/lane-a5-the-fixed-support-maximum-under-the-atom-classes.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-034/lane-a6-structural-sites-and-the-depth-one-certificate.md
  - packing/cases/n11_threshold_certificate/t-025-threshold-certificate-proof.md
  - packing/cases/n11_threshold_certificate/verify_claim.py
  - packing/devtools/plateau_reader.py
  - packing/devtools/run_fractional_colgen.py
  - packing/devtools/polish_ceiling_family.py
  - packing/devtools/independent_ceiling_reader.py
  - packing/src/sqpack/fractional/colgen.py
  - epistemics.md
  proposes: [H-216, H-217]
---
# X-037: N11 Overnight Review and Route Slate

**Status: measurements and dispositions only.** The overnight program of 2026-09-17
([session-138](../agent-sessions/session-138-n11-overnight-review.md), bead
`think-4woh`) reviewed the n=11 record, ranked eight new mechanisms, reviewed them
adversarially, and ran two of them.
No bound moved, no hypothesis was registered that night, and nothing was measured above
side 191/50 in core units.
[agenda-037](../agendas/agenda-037-n11-relational-certificate-program.md) holds the
resulting queue.

**Resolutions, 2026-09-18.** The five owner decisions are resolved under
[`epistemics.md`](../../../epistemics.md).
[H-216](../hypotheses/H-216-no-point-certificate-at-n6-299-100.md) and
[H-217](../hypotheses/H-217-route-f1-majority-floor-at-153-40.md) are registered.
The overnight numbers remain scratch until a guarded tool reproduces them.
No bound moved.

## Evidence Boundary

Every number below comes from scratch work under the worktree’s gitignored
`attic/overnight/`. Those files are local scratch, not repository evidence.
Under OR-1 the scripts are not retained tools, and a number here becomes evidence only
once a guarded tool reproduces it.
The attic reports are:

| Report | Lane | Model |
| --- | --- | --- |
| `attic/overnight/block1/laneA-state-audit.txt` | A, state audit | Fable |
| `attic/overnight/block1/laneB-mechanism-scan.txt` | B, literature and other-n mechanisms | Fable |
| `attic/overnight/block1/laneC-machinery.txt` | C, machinery and gap list | Opus |
| `attic/overnight/block1/laneD-registry.tsv`, `laneD-notes.txt` | D, registry table | Opus |
| `attic/overnight/block1/ideation-fable-max.txt` | Ideation, M1–M8 | Fable (max) |
| `attic/overnight/block1/adversarial-fable-max.txt` | Independent adversarial review | Fable (max) |
| `attic/overnight/block3/M1-report.txt` | M1 execution | Fable (xhigh) |
| `attic/overnight/block3/M7-report.txt` | M7 execution | Opus (xhigh) |

Evidence tags follow the lane reports.
**Exact** means rational arithmetic with no tolerance, and **float** means a HiGHS LP
value used only as a screen.
**Gate** means the two-route `decide_certificate` verdict; **inference** means a
reading, not a measurement.

## The Question

s(11) lies in [3.826447410572939, 3.877083590022814]. The lower bound is T-026 and the
upper is Trump’s 1979 packing ([n-011.md](../../frontier/n-011.md), lines 137–140). L* =
38200/9977 ≈ 3.82881 caps every unconditional one-body resource at n=11: point measures,
continuous densities, and unconditional core selections.
The frontier sits 0.00236 below it ([SYNOPSIS.md](../../../SYNOPSIS.md), lines 184–186).
The owner asked for a significant n=11 result beyond that ceiling rather than another
microscopic gain inside the 0.00236 window.

## Lane A: State Audit

- **The ceiling is a theorem about one-body methods.** Pricing a relation between
  squares escapes it: trace indivisibility, shared parents, joint compatibility.
  T-025’s 2-of-3 threshold atoms are the existing proof that this works (X-027, lines
  173–175).
- **The threshold plateau is a catalogue-and-site measurement, not a wall.** A6’s
  64-placement depth-one family at 153/40 satisfies all 2,566 retained atom orbits.
  Lane A5 found that the same language has headroom: the fixed-support maximum falls
  from 32/3 to 10 with floor atoms.
- **New measurement (inference, scratch).** The ceiling family at 191/50 carries mass
  exactly 9 in folded net cells 0–24, which equals H-131’s near-axis cap.
  All three retained obstruction families satisfy every H-131 cap.
  By X-027’s optimal-face criterion, Route E’s caps as specified are predicted to park.
- **Procedural diagnosis.** No scientific target has run since 2026-09-14.
  Admission-before-target became admission-instead-of-target, and five process blocks
  ran in one day. The only live entry, `think-ufmk`, waits behind CI work (`think-97we`).
- **Open questions.**
  - Q1: a threshold or floor certificate at 3.83–3.85 on structure-generated sites.
    Its blockers are the `think-g3j7` format decision and the `think-q0f4` site
    generator.
  - Q2: a routing theorem for owner selection.
  - Q3: a physical integrality gap, with n=6 below side 3 as its clean control.
  - Q4: joint-parent budgets.
  - Q5: Route S’s 23-orbit LP.

## Lane B: Mechanisms from the Literature and Other n

Lane B ranked the top eight by expected value for n=11. Its numbering is its own and
unrelated to M1–M8 below.

1. The helper architecture with a new stage-one cover (Route A in kind).
   It is the only class with no ceiling below s(11) that has settled a hard case.
2. Calibration at n=6 and n=10: are helpers necessary where the literature used them?
3. Bentz’s moving covers in weighted form.
4. Pairwise compatibility tested by theta or cliques on the exact A6 and 88-core
   supports.
5. A restricted-family exact theorem: six axis-parallel squares plus five at one angle.
6. Boundary-occupancy and segment helpers as branch generators.
7. Threshold and floor algebra (Route F1).
8. Nagamochi closed-form capacities as leaf certificates, for a simpler proof.

Every one-body resource in the archive is capped at L*. Lane B also listed transcription
and register notes for the owner to file: the Roth–Vaughan constant, El Moumni’s Theorem
2, Friedman DS7 Theorem 10, Bentz 2010 Lemma 4, and Erdős–Graham’s Θ versus O.

## Lane C: Machinery and Gaps

- **Reusable.** An exact two-route certificate gate (event-cell sweep and interval
  branch and bound) with standalone verifiers, the dilation corollary, and D4 orbit
  codecs. `sqpack.exact_lp` with the `admit_fixed_support_dual` reader pattern.
  Continuous-angle point covers in `cases/green17/interval_audit.py`. `uniform_cell` box
  leaves, `angle_tile_certificate`, Trump’s local theorem, and `weighted_clique` proof
  trees.
- **Missing.** An SDP solver and exact PSD checker (15–27 h with a sound conflict
  geometry). An n-square pose-space branch-and-bound driver (15–25 h). A contact-type
  completeness theory.
  An elimination engine.
  A continuous-angle weighted charge (9–14 h). A seam-safe shared-parent residual-domain
  decomposer (8–15 h).
- **Cost rule.** A verifier slower than about 30–60 s belongs on the deferred surface.
- **Defects noticed, not filed.** A stale `FieldElement` docstring in `sqpack/cover.py`.
  `check_atlas.py` and `check_n11_selection_routing.py` run their checks on `--help`.

## Lane D: Registry Findings

Lane D tabulated 307 registry rows at `035d84c6`: 123 hypotheses, 27 explorations, 30
agenda items, 88 beads, and 39 ledger rounds.
Of the 118 core n=11 hypotheses, 33 are blocked, 25 refuted, 22 confirmed, 21 open
questions, 9 unresolved, 5 open, 2 with a registered result, and 1 abandoned.

It also found these record inconsistencies.
They are listed for later filing; this program fixed none of them.

1. Eleven beads in the paused BC329 and BC303 T2 lanes are still `in_progress`.
   Agenda-035 marks BC-327 and BC-329 `blocked`, not paused.
2. BC-343 is `in_progress` with `think-ufmk`, but that bead is open and parented under
   `think-gvlg`. The `think-gtax` notes still name the closed `think-a1e8`.
3. Agenda state and bead status disagree:
   - BC-338 is complete while `think-ms9l` is in progress.
   - BC-331 is stopped while `think-lkvd` is open.
   - BC-333 is stopped, yet its next evidence says “ready to run”.
   - Four priorities differ between cell and bead.
4. Open beads sit on settled hypotheses:
   - `think-bj0s` on H-063, which is refuted.
   - `think-c4xs` on H-018, which is refuted.
   - `think-1qjs` on the abandoned H-064.
   - `think-j007` on a PR stack that has already landed.
5. Exploration ids are reused.
   `think-08tp` names an X-032 that is not main’s X-032. X-033 and X-020 are absent from
   main.
6. Result linkage is incomplete.
   T-026 has `produced_by: null` although exp-155 confirms H-156. H-061’s claim (s(12) ≥
   19/5) differs from the results the register credits to it.
7. `derived_from` and `proposes` are asymmetric for H-160/X-029, H-162/X-031,
   H-104–H-110 and H-122–H-124 (X-016), and H-061 (X-010, X-011).
8. H-160 has `instrument_ready: false` although its instrument exists and `think-j3w3`
   is closed.
9. exp-158 and exp-160 record an owner pause as `criterion_missed` and `blocked`, which
   reads like a missing instrument.
10. Older n=11 agendas remain `active` after agenda-036 became the controller.
    Agenda-025 through agenda-027 still hold in-progress or ready items, and agenda-022
    and agenda-024 hold blocked items.
11. H-163 reads `open`, but it cannot run before exp-161 is registered.
12. H-212 shows `open question` over three unresolved rounds.
    This is by design, but it hides those rounds’ state.

## Ideated Mechanisms M1–M8

The Fable max ideation ranked eight mechanisms.
P1 is the judged chance that tonight’s first step succeeds, and P2 the judged chance of
an eventual significant result.
Both are judgements, not measurements.

| Id | Mechanism | P1 | P2 |
| --- | --- | --- | --- |
| M1 | Clique atoms beyond 2-of-3: rank-one cuts of the pose-intersection graph | 0.6 | 0.3 |
| M7 | Helper-free certificates at n=10 (37/10) and n=6 (299/100) as calibration | 0.5 | 0.6 |
| M2 | Trace-conflict graph: Lovász theta or exact independence number | 0.5 | 0.25 |
| M4 | Slot-cover hand proof from a few named clique slots | 0.7 | 0.15 |
| M6 | LP-relaxation rounding as an upper-bound proposer | 0.7 | 0.02 |
| M3 | Exact-ownership 11-point set in Stromquist’s Memo II idiom | 0.4 | 0.15 |
| M8 | Odd-cycle (rank-two) atoms | 0.6 | 0.1 |
| M5 | Weighted Bentz moving covers for Route A’s roots | 0.3 | 0.2 |

## Independent Adversarial Verdicts

A separate Fable max review, which did not read the ideation’s reasoning, gave these
verdicts:

- **M7: keep.** Ranked first as the cheapest decisive measurement; run n=6 first.
- **M1: keep with changes, as Route F1.** Add weighted-majority and floor atoms, cite
  lane A5, use the closed intersection graph.
  A positive result needs the owner’s format decision (`think-g3j7`).
- **M3: keep with changes, as a kill test.** 11 is not a sum of D4 orbit sizes {1, 4, 8}
  with at most one fixed point, so an 11-point set cannot be D4-symmetric and no
  existing D4 producer can search for one.
  The integral piercing number at 3.80 decides it.
- **M2: kill as a lane.** Theta needs an SDP dependency and an exact PSD certificate.
  Keep one record note: M1, M8, and M2 relax one integer set-packing object at
  increasing strength.
- **M4: kill at 3.82.** The fractional bound in a sub-language is already 10.967, and a
  hand-sized point cover is dead above 3.789.
- **M6: kill as a proof route.** Its ν*(U) diagnostic is ill-posed as stated.
  It survives only as a search hypothesis with Trump as the exact control.
- **M8: kill for this block.** A rank-two ring needs the same missing geometric-conflict
  certificate as M1’s kernel cliques.
- **M5: kill.** This is a category error: Bentz moves the cover for a fixed packing,
  while Route A’s anchor is a property of the packing.

The review also corrected the ideation.
The 32/3 clique-LP value on the 88-family is lane A5’s F1, not new, and A5’s floor atoms
take that support to exactly 10. Strict-majority triggers are the budget-one half of
T-025’s language. A fixed-support clique-LP value is not a covering value.

## Overnight Measurements

Everything here is at a fixed side, shrink B = 9977/10000, and a fixed direction net.
The results are measurements at that scope and are neither covering values nor bounds.

### Clique Numbers of the Retained Obstruction Families

Exact, reproduced independently by the ideation and adversarial lanes.

| Family | Maximal cliques | Max clique weight (size) | Clique-LP | Independence number |
| --- | --- | --- | --- | --- |
| 88-placement L* family at 191/50 | 205 | 11/8 (11) | 32/3 | 10 |
| A6 64-placement family at 153/40 | 69 | 3/2 (10) | 9 | 9 |

The 64-family’s clique-LP value of 9 is below the trivial floor of 10 that a physical
10-packing of cores forces at 153/40. It reads as “these families are not obstructions
to the clique language”, not as evidence that a certificate exists.
T-025’s 2-of-3 atom is a clique of the pose-intersection graph, but T-025 also carries
atoms of budget two or more, which are not cliques.

### Both Maximum Cliques Are Single Atoms

Exact, adversarial lane.
Each maximum clique is one weighted-site-majority atom on its own arrangement vertices:
five vertices for the 11/8 clique and six for the 3/2 clique.
For these two families the plateau is an artefact of the catalogue and site set.

### 44 of 44 Heavy Cliques Realised

Exact, M1 lane, at 153/40. All 44 maximal cliques of weight above 1 in the 64-family are
plain budget-one threshold atoms on their own arrangement vertices, in 26 distinct
orbits.

- The four 3/2 cliques need 4-of-7. Exhaustive check: they are not 2-of-2, 2-of-3, or
  3-of-5 on those vertices.
- The 11/8 cliques are 2-of-3 and the 21/16 cliques are 3-of-5.

The soundness lemma is the floor(|S|/k) = 1 case of T-025’s counting step, using closed
disjoint cores. An atom (S, k, w) with 2k > |S| has budget w. M1’s kill criterion (b),
“no threshold realisation of a 3/2 clique”, did not fire.

### Replacement-Support Chase

M1 lane, at 153/40. Exact values on fixed catalogues.

| Support | Atoms added | Value sequence |
| --- | --- | --- |
| 64-placement support | 2,566 retained orbits, then the 26 clique orbits | 11 → 9 |
| Union of ten retained families (424 placements) | 26 orbits, then the replacement family’s own cliques | 11; still 11 with the 26 orbits (a replacement mass-11 family); then 54/5 or 76/7, depending on the optimum vertex |
| Union with three 153/40 dual dumps (1,556 placements) | four clique rounds | 11, 11, 11, 11 → 296/27 |
| 424-placement union, majority and floor atoms from `devtools.plateau_reader` K4–K6 | one round | 11 → 54/5 |

Column generation over the pose net, with the T-025 sweep pricing the dual, ran for
about 45 minutes per variant.

- **V1 (clique atoms).** The value climbed 76/7 → 664/61 → 338/31 → 11 in ten pricing
  rounds. That rebuilt a depth-one mass-11 family from poses the record never held, and
  new atoms cut it to 358/33 and 479/44 before the deadline.
- **V2 (majority and floor atoms).** Eight separations in 20 rounds.
  Pricing brought the value back to exactly 11 after the cuts, floor atoms (budgets
  9–52, violation 1/2) and cliques up to weight 3/2 cut every rebuilt mass-11 family,
  and the run stopped at 185/17 at its deadline.

Neither run reached a terminal state.
None produced a mass-11 family with no violated atom (the kill) or a pricing round with
no violated cell below 11 (a certificate candidate).
Nothing went to the gate.

**M1 verdict: blocked by tooling on the decisive test.** The rows-complete covering LP
at 153/40 could not run: its `sites-1` checkpoint (15,021 rows, 17,389 sites) is
unretained scratch on another host.
That neither kill criterion fired is not evidence that the LP is below 11. Tonight’s
atoms also cannot be retained:
[`verify_claim.py`](../../cases/n11_threshold_certificate/verify_claim.py) refuses
weighted atoms at line 183 and anything other than 2-of-3 at lines 191–193.

### M7: Helper-Free Point Certificates at n=6 and n=10

Opus xhigh lane, 03:35 to 05:05 PT, on the 181-direction net unless stated; follow-up
bead `think-qqzs`.

**Verdict: stall measured at both targets.** Both stalls are float site-level stalls,
except the exact integer ceiling at n=10. Certificates were verified only below the
targets. No tooling surgery was needed: the producers already take n and side.

- **n=6 at 299/100 is bracketed, not decided.** The covering value lies in
  [83/14 = 5.928571 (exact), 6.006571 (float)]. The upper value is the best
  rows-complete LP, at 18,025 sites, and was still falling.
  The lower value is the exact optimum of a polished 360-placement support.
  A polish of a 1,128-placement union reached 5.962963 in float, but its exact check was
  stopped after more than 20 minutes, twice.
  The candidate statement, “no point certificate at n=6, 299/100 for any site set,” is
  neither established nor killed.
- **n=6 crossing at 297/100: accepted by the two-route gate.** A 176-atom weighted-point
  certificate of mass 5791893/1000000; both routes agree at least cell mass
  1000003/1000000.
- **n=6 between the two.**
  - 298/100: one exact route accepts, but the interval route stalls on 3,996 boxes, so
    the gate refuses.
  - 2985/1000: a rescaled candidate of mass 23672072/3999787 passes a one-worker exact
    sweep at least cell mass 1, but the gate refuses it on 780 stalled interval boxes.
- **n=10 at 37/10 is foreclosed exactly before any LP.** B·s(10) ≈ 3.6986 < 3.70, so a
  B-scaled copy of the known-best 10-packing is a depth-one mass-10 ceiling family.
  `verify_ceiling` and `independent_ceiling_reader` both accept it.
  Any certificate at 37/10 needs B > 0.998083 and at least 216 net steps (derived).
- **n=10 crossings: accepted by the two-route gate.** s(10) ≥ 73/20, 92/25, and 737/200.
  At 369/100 the site LP stays at exactly 10 after 80 column rounds.
- **Clique scans.** Only the trivial integer family reaches total ≥ n. On the polished
  sub-n families the clique-LP and independence numbers sit below the totals.

Every M7 certificate is weaker than the proved values s(6) = 3 and s(10) = 3 + 1/√2.
None is a new result, and nothing shows that helpers are necessary at n=6 or n=10. The
lane found five tooling gaps, G1–G5:

- G1: `run_fractional_colgen` truncates the dual at 32 rows and does not write the dual
  family.
- G2: a record-convention mismatch in `polish_ceiling_family`.
- G3: `independent_ceiling_reader` decides K2 and K3 by equality.
- G4: no threshold-atom producer takes n, so threshold certificates at n=6 were not run;
  T-025’s producer exists only as agenda-034 scratch (about 2–3 h to lift).
- G5: the gate’s interval route stalls on some candidates, plausibly where sites nearly
  coincide (inferred, not diagnosed).

## Numbers That Need a Guarded Tool Before Retention

Scratch scripts produced every value above.
The coordinator filed follow-up beads for the tooling:

- **`think-gyzw`.** Turn M1’s column-generation loop (`colgen4.py`) into a checkpointed
  tool with an independent reader of the final family and a gate hand-off.
  The replacement-support chase values and any future terminal state of that loop need
  it.
- **`think-3xbr`.** Retain or regenerate the `sites-1` checkpoint so the rows-complete
  LP at 153/40 can run.
- **Clique measurements.** The clique numbers, the single-atom realisations, and the
  44-of-44 result need a maintained clique and atom-realisation tool with a refusal
  guard. They should use the closed intersection graph and exact geometry.
- **`think-qqzs`.** Close M7’s n=6 bracket and build an n-parameterised threshold
  producer. The gate-accepted n=6 and n=10 certificate bytes exist only in the attic, and
  retaining them is a coordinator decision.
  The n=6 bracket needs G1, G2, and G5 as guarded changes to the stock drivers before
  its values can be retained.

## Dispositions and Next Evidence

| Route | Disposition | Next evidence |
| --- | --- | --- |
| M7 calibration | Continue | Close the n=6 bracket at 299/100 (`think-qqzs`): an exact family of total ≥ 6, or a rows-complete value below 6 on some site set; fix G5 first. Then n=10 with B in (0.99808, 0.99885]. |
| M1 as Route F1 | Continue, blocked | Format decision (`think-g3j7`); the `sites-1` checkpoint (`think-3xbr`); the convergence tool (`think-gyzw`); then the rows-complete LP at 153/40 with majority and floor atoms. |
| M3 kill test | Continue as a kill test | The integral piercing number of the T-018 site set at 3.80 on a 37-direction net (`think-k4vb`). 12 or more kills it; 11 opens a Memo II hand-proof project. |
| M2 | Retired as a lane | A record note unifying M1, M8, and M2 as relaxations of one set-packing object. Reopen only with an owner-approved SDP dependency. |
| M4 | Retired at 3.82 | None. It could return only as exposition at 3.80, behind a catalogue LP. |
| M5 | Retired | None. The weighted moving-cover lemma could go into X-027’s helper section as a note. |
| M6 | Retired as a proof route | None as proof. A Route D search campaign is an owner decision. |
| M8 | Retired for this block | Revisit only after a geometric-conflict certificate exists for M1. |

## Owner Decisions Needed

Resolved 2026-09-18; see [Resolutions](#resolutions-2026-09-18). The questions as asked:

1. **Atom format (`think-g3j7`).** Should the retained threshold verifier accept
   weighted-majority, k-of-S, and floor atoms?
   Without that no M1 atom can enter a retained certificate.
2. **M7’s n=6 calibration statement.** Should the adversarial review’s statement be
   registered as a hypothesis?
   The statement: no point-atom certificate exists for n=6 at side 299/100 with B =
   9977/10000 on the 181-step net, for any site set.
3. **M1 as Route F1.** Should the rows-complete LP with weighted-majority and floor
   atoms on arrangement-vertex sites at 153/40 be registered, with the adversarial
   review’s kill rule?
4. **M6 as a Route D campaign.** Should LP-rounded seeds be registered as a search
   hypothesis with Trump’s packing as the exact control, or left retired?
5. **The M2 SDP dependency.** Should an SDP solver be admitted under the supply-chain
   rules so that theta can serve as a diagnostic?

## Resolutions (2026-09-18)

Classifications follow [`epistemics.md`](../../../epistemics.md).
A compound claim takes the minimum rung of its load-bearing parts.
Significance never gates.
Attic scratch under `attic/overnight/` is V0/C0 and is not repository evidence.
A draft is not a hypothesis, and a hypothesis is not a result.
`exp-161` stays reserved for Route S.

| # | Question | Resolution | Record |
| --- | --- | --- | --- |
| 1 | Atom format | Admit weighted-majority, k-of-S, and floor atoms as a certificate language. Do not reread T-025 or T-026. A new class needs two-route C4 before a T-id. Admission is not a bound. | `think-g3j7` implements; `verify_claim.py` still refuses until that lands |
| 2 | n=6 statement | Do not promote the attic negative to a result. Register it as a determination. | [H-216](../hypotheses/H-216-no-point-certificate-at-n6-299-100.md) |
| 3 | M1 as Route F1 | Register the rows-complete majority-and-floor LP at 153/40 with the adversarial kill rule. The instrument does not exist yet. | [H-217](../hypotheses/H-217-route-f1-majority-floor-at-153-40.md) |
| 4 | M6 as Route D | Leave retired. Do not register a search hypothesis. | BC-360 |
| 5 | M2 SDP | Do not admit an SDP solver. M2 stays retired. | BC-360 |

### 1. Atom format — admit the language

Weighted-majority, k-of-S, and floor atoms are a method, not a statement about `s(n)`.
Admitting them does not create a result and carries no V/C rung.

T-025 and T-026 are V4/C5 in the 2-of-3 (+ point) language.
Their frozen bytes stay in that language.
Rereading them as majority or floor certificates would be a new compound claim and would
take the minimum rung of a part that has no two-route evidence.

A certificate in the new classes can support a bound only at V4/C3, and C4 needs two
distinct methods. Until `think-g3j7` lands a retained verifier, no M1 atom can enter a
certificate. Format admission unblocks that implementation.
It does not unblock BC-358’s covering run, which still waits on the verifier,
`think-3xbr`, and `think-gyzw`.

### 2. n=6 statement — hypothesis, not a result

The attic claim “no point certificate at n=6, 299/100, for any site set” is V0/C0.
Registering it as already true would treat scratch as evidence.

[H-216](../hypotheses/H-216-no-point-certificate-at-n6-299-100.md) is the same sentence
stated so it can be wrong.
Confirm with an exact depth-one family of total at least 6 that both ceiling readers
accept. Refute with a frozen covering below 6 on a named site set that both routes of
`decide_certificate` accept.
The overnight bracket `[83/14, 6.006571]` does not decide either side.

G1, G2, G3, and G5 are on main, so the instrument exists.
G4 is a threshold producer and is not this measurement.
A decided H-216 is calibration at a solved case; `s(6) = 3` does not move.

### 3. M1 as Route F1 — register, blocked on tools

The rows-complete majority-and-floor LP at 153/40 is a claim that can be wrong.
[H-217](../hypotheses/H-217-route-f1-majority-floor-at-153-40.md) takes the adversarial
kill rule as its criterion: a depth-one mass-11 family with no violated majority or
floor atom kills the route at this scope; a dual with no cell below 1, accepted by both
gate routes, confirms.

The overnight chase did not terminate.
Surviving an informal kill, and every fixed-support value below 11, is not evidence that
the covering LP is below 11. `instrument_ready` is false until the three named tools
exist.

### 4. M6 — stay retired

The proof-route diagnostic ν*(U) is ill-posed as stated.
A Route D search hypothesis would need a criterion that can be wrong, Trump’s packing as
the exact control, and an instrument that proposes LP-rounded seeds.
None of those exists.
Significance never gates, so the low judged P2 is not why this stays retired.
A draft is not a hypothesis.
Reopen only with those three pieces named before a run.

### 5. M2 SDP — do not admit

Lovász theta without an exact PSD certificate is at most V1. A bound in this repository
needs V4/C3, so theta cannot support one.
An SDP solver would be a new dependency without a confirmation path, which is not a
package the supply-chain rules say to add.
M1, M8, and M2 remain one integer set-packing object at increasing relaxation strength,
as the record note already says.
M2 stays retired until an owner-approved exact PSD route exists.

## What This Program Did Not Establish

- No bound on s(11), s(10), or s(6) moved.
  The gate-accepted n=6 and n=10 certificates are weaker than the proved values.
- No covering value was measured above 191/50, and no certificate candidate at n=11
  reached the gate.
- Fixed-support values (9, 32/3, 54/5, 76/7, 296/27, and the chase’s 11s) are not
  covering values and bound nothing.
- The M1 loop did not converge.
  Surviving both kill criteria is not evidence that the covering LP is below 11 at
  153/40.
- The n=6 bracket does not show that helpers are necessary at n=6.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
