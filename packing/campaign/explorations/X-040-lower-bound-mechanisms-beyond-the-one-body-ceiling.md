---
title: X-040 — lower-bound mechanisms beyond the one-body ceiling
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-040
  title: Lower-Bound Mechanisms Beyond the One-Body Ceiling
  date: '2026-09-20'
  author: Claude session-143 coordinator, with four Fable and Opus lanes and three Fable adversarial reviews
  campaign: packing.squares
  brief: >-
    Owner-directed deeper mathematical review from the top of PR 202: where the
    lower-bound results have been, and which mechanisms, especially general geometric
    arguments combined with point and threshold certificates on a conditioned family,
    could give materially better lower bounds at n=11, n=17, or other n, or another
    notable result. Rank them, price each first discriminator against the instruments
    that exist, and hand an adapted hypothesis list to an overnight research loop.
  sources:
  - SYNOPSIS.md
  - packing/frontier/RESULTS.md
  - packing/frontier/CERTIFICATE-REACH.md
  - packing/frontier/covering-values.yaml
  - packing/campaign/explorations/X-026-what-conditioning-does-and-does-not-buy.md
  - packing/campaign/explorations/X-027-stromquist-fractional-and-structural-strategy.md
  - packing/campaign/explorations/X-037-n11-overnight-review-and-route-slate.md
  - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
  - packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md
  - docs/project/reviews/review-2026-09-14-small-n-significant-progress-mathematical-audit.md
  - docs/project/reviews/review-2026-09-07-n17-comprehensive-review.md
  - docs/project/research/research-2026-09-12-n11-selection-routing-first-principles.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/lane-a-corner-structure.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-034/ceiling-family-191-50.json
  - packing/campaign/hypotheses/H-131-near-axis-counts-at-q.md
  - packing/resources/bentz-2010-optimal-packings-13-and-46.md
  - packing/resources/bentz-2016-optimal-packings-22-and-33.md
  - packing/resources/nagamochi-2005-packing-unit-squares-in-a-rectangle.md
  - packing/resources/friedman-ds7-packing-unit-squares-in-squares.md
  - packing/witnesses/known-best/n-017.yaml
  - packing/src/sqpack/fractional/relational.py
  - packing/devtools/decide_certificate.py
  - packing/devtools/run_fractional_colgen.py
  proposes: []
---
# X-040: Lower-Bound Mechanisms Beyond the One-Body Ceiling

**Status: analysis, measurements on fixed retained families, and a ranked slate.** No
bound moved, no hypothesis was decided, and no LP or column-generation target ran.
Every number below that is not cited to a retained artifact is scratch from the session
scratchpad and is `V0/C0` until a guarded tool reproduces it (OR-1).
[Session 143](../agent-sessions/session-143-lower-bound-math-review.md), bead
`think-srln`, opened from the top of PR 202 at `8cab8309`.

## Evidence Boundary

Four read-only lanes ran in parallel with disjoint deliverables, then three independent
adversarial reviews that did not read each other:

| Lane | Question | Model |
| --- | --- | --- |
| 1 | n=11: what stalled the program, and which conditioned-certificate mechanisms escape the ceiling | Fable, max |
| 2 | Mechanisms different in kind from the shrunken-core fixed-net certificate | Fable, max |
| 3 | Material targets at n=17 and other n, including exact-value cases | Fable, extra |
| 4 | Instrument, evidence, and ceiling map that prices each first discriminator | Opus, high |
| R1–R3 | Adversarial review of lanes 1, 2, and 3 | Fable, max |

Lane reports and scratch scripts lived in the session scratchpad, not the repository.
**Exact** below means rational arithmetic with no tolerance; **scratch** means a lane’s
own script on a retained JSON record; **derived here** means an argument written in a
lane report and checked by its reviewer; **proved** means a statement already carried
by a retained artifact.

## The Question

The bracket is `3.826447410572939 <= s(11) <= 3.877083590022814` (T-026 and Trump).
Every unconditional one-body certificate, point or density, is obstructed above
`L* = 38200/9977 ≈ 3.82881` by the retained 88-core family scaled to full unit squares
(X-027 §2). The threshold language (T-025) escapes the ceiling in principle but has a
measured plateau at `153/40` (the A6 64-family), and the conditional owner route
(T-023, BC303) stopped at an unproved routing theorem.
The owner asked, more aggressively than the earlier slates, whether general geometric
arguments in the classical style, combined with point and threshold certificates on the
family of packings those arguments leave, can reach `3.84`–`3.85` at n=11, whether n=17
or another n offers a more material result, and what an overnight loop should run.

## What Stalled at n=11 (lane 1, reviewed by R1)

**The ceiling, precisely.** Lemma D of lane-d (agenda-030) bounds every program whose
constraint is a linear functional of pointwise depth: points, densities, segment
lengths, region masses, and class counts a physical packing also respects are all
satisfied by the 88-family automatically.
Only integrality escapes it: indivisible site consumption (thresholds), pairwise
conflict (cliques), or a case hypothesis that removes poses from the domain without
removing a unit from the count.

**The extremal family is a fractional 8 + 3 packing (scratch, exact).** Decomposed under
D4 by exact centre-and-angle matching, the 88 cores are eleven D4 orbits of one pose
each, every orbit of mass exactly 1: four corner slots, four mid-wall slots (two tilted
by 1.32°), one inner-corner slot at 0.79°, and two tilted slots at 25.7° and 29.2°
smeared over a ring of eight spots around the centre.
Trump’s packing has the same census: eight squares within 0.1 of a wall, three interior.
The family saturates every proved one-body cap with equality: mass 3 within 0.10 of each
wall (X-027 §4 Lemma B), mass 1 meeting each corner triangle `x + y <= d` for `d <= 0.9`
(lane-a Lemma 4), mass 9 in net cells 0–24 (H-131).
Its ring sub-family has independence number 8 at mass 8, its central sub-family 4 at
mass 3, the whole family 10 (X-037’s figure, reproduced), and **every one of the 24
central cores overlaps at least one ring core.** The relation the family never pays for
is ring–centre disjointness; the concrete local conflict is a flush corner square
against a 1.32°-tilted mid-wall neighbour whose core reaches `x = 0.997`.
The largest clique weighs 11/8 and consists of eleven cores near one corner.

**Why the owner route failed.** X-026’s neutrality theorem is exact on the family:
the corner is where the family is *least* fractional (mass 1 per corner, in four
variants of 1/4), so a patch condition there removes one unit of mass and one unit of
count. The T1 surplus inequality was refuted by a literal parent with surplus
`3/800000` (X-030), and X-031 shows subdividing the same local domain repeats the
obstruction. The diagnosis is that the program conditioned where the adversary is
integral and priced statistics the adversary already respects.
The remedy is to condition where the adversary is fractional, at the mid-wall and the
tilted central slots, and to price the ring–centre relation.

## Mechanisms for n=11 (lane 1)

Gains below are measured on the fixed retained families (the 88-family at `191/50`
and the A6 64-family at `153/40`), exact, by restricting each family to a case domain.
By Lemma D a positive gain is a necessary condition for a conditioned certificate in
that case, never a sufficient one; the decisive numbers are the restricted fractional
values `ν*_σ(q)` per case, which no lane ran.

| Id | Mechanism | Completeness | Measured gain on the 88-family | Lane verdict |
| --- | --- | --- | --- | --- |
| C1 | Corner-penetration case tree: bin each corner’s penetration `δ_j` at `d = 1/2`; banked corners contribute the box `[d, 1]^2` and the residual domain avoids it; free corners clip the triangle `x + y <= d` (lane-a Theorem B, proved, never run) | Exhaustive by construction; 16 bin vectors, 6 D4 classes | Free branch removes mass 1 for no count; deep branch removes 7/4 for one count; all four deep at `d = 1/2` leaves residual 4 against a requirement of 7 | Accept, rank 1 |
| C2 | Tilted-anchor tree: H-131 forces at least two squares with folded tilt above 6.585° at `96/25` and at `U`; condition on one such square’s centre box and angle bin | About 60 D4 cases from 81 centre boxes and four angle bins | Anchoring at the family’s 29° slot removes 33/8 for one count (A6: 55/16); mid-wall 3; corner at most 17/8; flush corner exactly 1 | Accept, rank 2 |
| C3 | Wall-census cap: at most three squares within `τ` of any wall for `τ <= 0.115` at 3.84, `0.105` at 3.85, `0.076` at `U` (derived here from Lemma B) | Dichotomy on the wall class size, at most 7 versus at least 8 | Both families have wall-class mass exactly 8, so the cap cuts the at-most-7 case only | Keep as a screen |
| C4 | Ring–centre clique and majority atoms seeded from the measured conflicts (Route F1 / H-217 with a structural seed) | Language admitted in X-037 | Fixed-support clique value 32/3 against 11 (X-037) | Keep, blocked on tooling |
| C5 | Two-parent geometric budgets (an atom of budget two whose two triggers cannot coexist) | Per atom | Not measured | Secondary |
| C6 | Transfer-closure localisation (X-021 lane C) | Per case | Not measured | Secondary |
| — | Killed: wall-contact normal-form trees, H-131 caps alone, contact-component width arguments, boundary-waste densities, integral 11-mark ownership at 3.84 (agrees with X-037 on M3) | | The families satisfy each of these with equality or are wall-free where the lemma bites | Kill |

The shrink caps bound all of this at `B = 9977/10000`: `3.868983` plain and `3.876681`
with capture. The targets `3.84`–`3.85` sit inside; Trump’s side needs `B = 1` or an
exact-side tree.

## Mechanisms Different in Kind (lane 2)

Lane 2’s litmus test is the same as lane 1’s: a mechanism escapes the ceiling only if the
88-family violates a constraint it adds. Its readings of the family agree with lane 1’s
(mass 9 within 1.32° of axis on a fuzzy 3 x 3 grid, mass 2 at 25.7° and 29.2° in four
corner pockets, no tilted member touching a wall).

| Id | Mechanism | Lane 2 reading | Cheapest discriminator |
| --- | --- | --- | --- |
| D1 | Schrijver `θ′` of the pose-conflict graph, verified by rational `LDL^T` or Cholesky-with-error-bound plus a rank-one Schur step, with the SDP solver only as an unretained producer | The 88-support has independence number 10 against LP 11, so `θ′` lies in `[10, 32/3]` there; plausible band 3.84–3.86, conjectured | `θ′` on the 88- and 64-supports against the clique-LP values 32/3 and 9; hours |
| D2 | Stressed-optimum reduction: an optimal packing carries an LP-dual stress whose stressed contact graph has one component touching all four walls; parametric in `L` | Derived here; reshapes Route A’s root without shrinking its leaves | The exact Trump stress over `Q(u)`; hours |
| D3 | A uniform `s(m^2 - 3) = m` theorem by a parametric unshrunk measure | Open; the shrunk ceilings `3.9908`, `4.9885`, `5.9862` clear `m - 0.01` | Column generation at `n = 13, 22, 33` at side `m - 0.01`; an hour |
| D4 | Unshrunk exact-orientation verifier (anabologyco’s architecture) | Worth at most `0.0024` at n=11; infrastructure for D1, D6, and the n=17 and integer-endpoint questions | Decide T-025’s atoms unshrunk; one to two days of tooling |
| D5 | Bentz’s n=13 idiom with computer leaves at n=12 | 16 points, slack 4, at least three tilted squares localised to wall strips; the record’s conditional certificates as leaves | Replay the Theorem 9 skeleton at 12 boxes; a day |
| D6 | Extended capture: wall-wedge waste lemmas as conflict edges | A wall-vertex tilted square at tilt `θ` guarantees empty sub-triangles of area `½ sin θ cos θ (1 - d(θ)/cos θ)^2` and its mirror, about 0.32 per square at 40.18°; the family’s tilted members are wall-free, so a gap extension is needed before it cuts | Wedge atoms on the 64-family LP |
| D7 | Complete joint-space interval CSP (Montanher–Neumaier–Markót) | The literature’s reach with rotation is n=3 in a circle | Reproduce n=3, then n=5 |
| — | Killed: integral piercing above `L*` (`τ_int >= τ* >= 11`), angular budgets as one-body resources, lifting from `s(10)`, Dewar 2024 and Alpert et al. as bound tools | | |

D1 is the mechanism X-037 retired as M2 with the reopening condition “only with an
exact PSD route that can reach C3”; lane 2 argues that condition can be met without an
SDP dependency in the repository.
Whether to admit it is an owner decision recorded below.

## Other n (lane 3, reviewed by R3)

**The retained family can close no case.** An integer case is capped at `m/(1 + D) < m`
and an oblique case strictly below its packing (`packing/frontier/CERTIFICATE-REACH.md`;
n=17 at `4.6710` against Bidwell’s `4.6755`). Closing anything needs an unshrunk
certificate whose obstruction lemma gives `s(n) >= S` from a certificate at `S`.

**Which integer cases were free (derived here).** The classical hexagonal unavoidable set
(Bentz 2010 Figure 1) fits `m` rows inside `[0, m]^2` only for `m <= 7` and then has
`m^2 - ceil(m/2)` points: 14, 22, 33, 45 for `m = 4..7`. That is why `s(46) = 7` needed
no case analysis, why 22 and 33 needed Bentz 2016’s Theorem 8, why 13 needed eight
cases, and why 12 is four spare points past any classical argument.
The one-spare cases are `n = 21` (`m = 5`), `n = 32` (`m = 6`), and `n = 45` (`m = 7`),
all open on the register.

| Target | Route | First discriminator | Kill |
| --- | --- | --- | --- |
| `s(21) = 5` | Bentz 2016 Theorem 8 with one spare red and two spare blue points, plus a two-wall line-capacity count (the one-spare deformation lemma); in parallel an unshrunk covering LP at side exactly 5 needing mass below 21 against the free 22 | An exact script enumerating the at most three stationary-point assignments against the five rows and four wall lines; half a day | An assignment that leaves at most four charges on every wall and a 21-box configuration realising it |
| `s(45) = 7` | The 45-point hexagonal set is already `m^2 - 4`; one sliding row and one line charge | Check the set stays unavoidable under a `0.1` horizontal slide of one row, exactly | The slide breaks unavoidability at the wall quadrilaterals |
| n=26 certificate at or above `5.35` | Seeded column generation with a long deadline; the recipe transfers to 37, 50, 65, 82, where Green’s DS7 Theorem 9 is unproved and worth `+0.20`–`0.28` | One seeded run at `5.35` with a 3600 s deadline | Two seeded site sets converge at or above 26 |
| n=17 above `4.671` | Unshrunk verifier, then a certified dual near `U`; Bidwell’s packing has three tilt classes, degree-18 coordinates, and is not rigid, so closing 17 is harder than 11 on every axis | A depth-one ceiling family at `4.62` of total at least 17 would kill every point certificate there | The certified dual reaches 17 below `4.67` |
| `s(12) = 4` | One unshrunk LP at side exactly 4 with wall-offset and grid-line atoms | The LP; a day | A certified dual of value at least 12 at `3.99` |

## Machinery and Evidence (lane 4)

Only the unconditional point language is fully instrumented: one producer
(`devtools.run_fractional_colgen`), one scheduler, and the two-route gate.
`decide_certificate` refuses `variant: class` and `variant: conditional` by name, so a
T-023-style conditional exclusion has no retention path.
The floor, majority, and k-of-S reader landed on this branch
(`packing/src/sqpack/fractional/relational.py`, 19 tests) but both of its routes are
exact, so it is an admission gate rather than a two-route retention gate; the
relational producer refuses without the A6 sites-1 matrix, which is not in the
repository (`think-3xbr`).
Threshold production is 2-of-3 only.
The 87 restricted optima at 45 sides are not recomputable: no run log or solver
checkpoint was retained for any of them, and a converged restricted optimum at or above
`n` kills point certificates on that site set only.

Named gaps, in build-cost order: a relational float route (one to two weeks), the
sites-1 rebuild, a relational column generator, an unshrunk exact-orientation verifier
generalised from `cases/green17/interval_audit.py`, a conditional-certificate gate whose
domain is a case predicate, a continuum-row oracle, a rational PSD checker (nothing
exists; `think-ol1z` is unstarted), a contact-hypothesis consumer, and owner-selection
routing.
No open bead aims at moving the n=17 lower bound.
No scientific target has run since 2026-09-14.

Cost anchors from retained receipts: the two-route threshold gate about 90 s on three
workers for T-025; column-generation rows 82 s to 1620 s; the n=26 and n=27 runs hit
a 1200 s deadline; the scratch relational chase about 45 minutes per variant.

## Adversarial Verdicts

Pending: R1, R2, and R3 are appended when they report.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
