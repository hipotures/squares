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
  - packing/resources/papers/bentz-2010-optimal-packings-13-and-46.md
  - packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md
  - packing/resources/papers/nagamochi-2005-packing-unit-squares-in-a-rectangle.md
  - packing/resources/papers/friedman-ds7-packing-unit-squares-in-squares.md
  - packing/witnesses/known-best/n-017.yaml
  - packing/src/sqpack/fractional/relational.py
  - packing/devtools/decide_certificate.py
  - packing/devtools/run_fractional_colgen.py
  proposes: [H-222, H-223, H-224, H-225, H-226, H-227, H-228, H-229, H-230, H-231]
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
lane report and checked by its reviewer; **proved** means a statement already carried by
a retained artifact.

## The Question

The bracket is `3.826447410572939 <= s(11) <= 3.877083590022814` (T-026 and Trump).
Every unconditional one-body certificate, point or density, is obstructed above
`L* = 38200/9977 ≈ 3.82881` by the retained 88-core family scaled to full unit squares
(X-027 §2). The threshold language (T-025) escapes the ceiling in principle but has a
measured plateau at `153/40` (the A6 64-family), and the conditional owner route (T-023,
BC303) stopped at an unproved routing theorem.
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
(lane-a Lemma 4), mass 9 in net cells 0–24 (H-131). Its ring sub-family has independence
number 8 at mass 8, its central sub-family 4 at mass 3, the whole family 10 (X-037’s
figure, reproduced), and **every one of the 24 central cores overlaps at least one ring
core.** The relation the family never pays for is ring–centre disjointness; the concrete
local conflict is a flush corner square against a 1.32°-tilted mid-wall neighbour whose
core reaches `x = 0.997`. The largest clique weighs 11/8 and consists of eleven cores
near one corner.

**Why the owner route failed.** X-026’s neutrality theorem is exact on the family: the
corner is where the family is *least* fractional (mass 1 per corner, in four variants of
1/4), so a patch condition there removes one unit of mass and one unit of count.
The T1 surplus inequality was refuted by a literal parent with surplus `3/800000`
(X-030), and X-031 shows subdividing the same local domain repeats the obstruction.
The diagnosis is that the program conditioned where the adversary is integral and priced
statistics the adversary already respects.
The remedy is to condition where the adversary is fractional, at the mid-wall and the
tilted central slots, and to price the ring–centre relation.

## Mechanisms for n=11 (lane 1)

Gains below are measured on the fixed retained families (the 88-family at `191/50` and
the A6 64-family at `153/40`), exact, by restricting each family to a case domain.
By Lemma D a positive gain is a necessary condition for a conditioned certificate in
that case, never a sufficient one; the decisive numbers are the restricted fractional
values `ν*_σ(q)` per case, which no lane ran.

| Id | Mechanism | Completeness | Measured gain on the 88-family | Lane verdict |
| --- | --- | --- | --- | --- |
| C1 | Corner-penetration case tree: bin each corner’s penetration `δ_j` at `d = 1/2`; banked corners contribute the box `[d, 1]^2` and the residual domain avoids it; free corners clip the triangle `x + y <= d` (lane-a Theorem B, proved, never run) | Exhaustive by construction; 16 bin vectors, 6 D4 classes | Free branch removes mass 1 for no count; deep branch removes 7/4 for one count; all four deep at `d = 1/2` leaves residual 4 against a requirement of 7 | Accept, rank 1; R1: neutral at the target side except the all-free class |
| C2 | Tilted-anchor tree: H-131 forces at least two squares with folded tilt above 6.585° at `96/25` and at `U`; condition on one such square’s centre box and angle bin | About 60 D4 cases from 81 centre boxes and four angle bins | Anchoring at the family’s 29° slot removes 33/8 for one count (A6: 55/16); mid-wall 3; corner at most 17/8; flush corner exactly 1 | Accept, rank 2; R1: at most 1.5 per cell, bin edge 6.4537° |
| C3 | Wall-census cap: at most three squares within `τ` of any wall for `τ <= 0.115` at 3.84, `0.105` at 3.85, `0.076` at `U` (derived here from Lemma B) | Dichotomy on the wall class size, at most 7 versus at least 8 | Both families have wall-class mass exactly 8, so the cap cuts the at-most-7 case only | Keep as a screen |
| C4 | Ring–centre clique and majority atoms seeded from the measured conflicts (Route F1 / H-217 with a structural seed) | Language admitted in X-037 | Fixed-support clique value 32/3 against 11 (X-037) | Keep, blocked on tooling |
| C5 | Two-parent geometric budgets (an atom of budget two whose two triggers cannot coexist) | Per atom | Not measured | Secondary |
| C6 | Transfer-closure localisation (X-021 lane C) | Per case | Not measured | Secondary |
| — | Killed: wall-contact normal-form trees, H-131 caps alone, contact-component width arguments, boundary-waste densities, integral 11-mark ownership at 3.84 (agrees with X-037 on M3) |  | The families satisfy each of these with equality or are wall-free where the lemma bites | Kill |

The shrink caps bound all of this at `B = 9977/10000`: `3.868983` plain and `3.876681`
with capture. The targets `3.84`–`3.85` sit inside; Trump’s side needs `B = 1` or an
exact-side tree.

## Mechanisms Different in Kind (lane 2)

Lane 2’s litmus test is the same as lane 1’s: a mechanism escapes the ceiling only if
the 88-family violates a constraint it adds.
Its readings of the family agree with lane 1’s (mass 9 within 1.32° of axis on a fuzzy 3
x 3 grid, mass 2 at 25.7° and 29.2° in four corner pockets, no tilted member touching a
wall).

| Id | Mechanism | Lane 2 reading | Cheapest discriminator |
| --- | --- | --- | --- |
| D1 | Schrijver `θ′` of the pose-conflict graph, verified by rational `LDL^T` or Cholesky-with-error-bound plus a rank-one Schur step, with the SDP solver only as an unretained producer | The 88-support has independence number 10 against LP 11, so `θ′` lies in `[10, 32/3]` there; plausible band 3.84–3.86, conjectured | `θ′` on the 88- and 64-supports against the clique-LP values 32/3 and 9; hours |
| D2 | Stressed-optimum reduction: an optimal packing carries an LP-dual stress whose stressed contact graph has one component touching all four walls; parametric in `L` | Derived here; reshapes Route A’s root without shrinking its leaves | The exact Trump stress over `Q(u)`; hours |
| D3 | A uniform `s(m^2 - 3) = m` theorem by a parametric unshrunk measure | Open; the shrunk ceilings `3.9908`, `4.9885`, `5.9862` clear `m - 0.01` | Column generation at `n = 13, 22, 33` at side `m - 0.01`; an hour |
| D4 | Unshrunk exact-orientation verifier (anabologyco’s architecture) | Worth at most `0.0024` at n=11; infrastructure for D1, D6, and the n=17 and integer-endpoint questions | Decide T-025’s atoms unshrunk; one to two days of tooling |
| D5 | Bentz’s n=13 idiom with computer leaves at n=12 | 16 points, slack 4, at least three tilted squares localised to wall strips; the record’s conditional certificates as leaves | Replay the Theorem 9 skeleton at 12 boxes; a day |
| D6 | Extended capture: wall-wedge waste lemmas as conflict edges | A wall-vertex tilted square at tilt `θ` guarantees empty sub-triangles of area `½ sin θ cos θ (1 - d(θ)/cos θ)^2` and its mirror, about 0.32 per square at 40.18°; the family’s tilted members are wall-free, so a gap extension is needed before it cuts | Wedge atoms on the 64-family LP |
| D7 | Complete joint-space interval CSP (Montanher–Neumaier–Markót) | The literature’s reach with rotation is n=3 in a circle | Reproduce n=3, then n=5 |
| — | Killed: integral piercing above `L*` (`τ_int >= τ* >= 11`), angular budgets as one-body resources, lifting from `s(10)`, Dewar 2024 and Alpert et al. as bound tools |  |  |

D1 is the mechanism X-037 retired as M2 with the reopening condition “only with an exact
PSD route that can reach C3”; lane 2 argues that condition can be met without an SDP
dependency in the repository.
Whether to admit it is an owner decision recorded below.

## Other n (lane 3, reviewed by R3)

**The retained family can close no case.** An integer case is capped at `m/(1 + D) < m`
and an oblique case strictly below its packing (`packing/frontier/CERTIFICATE-REACH.md`;
n=17 at `4.6710` against Bidwell’s `4.6755`). Closing anything needs an unshrunk
certificate whose obstruction lemma gives `s(n) >= S` from a certificate at `S`.

**Which integer cases were free (derived here).** The classical hexagonal unavoidable
set (Bentz 2010 Figure 1) fits `m` rows inside `[0, m]^2` only for `m <= 7` and then has
`m^2 - ceil(m/2)` points: 14, 22, 33, 45 for `m = 4..7`. That is why `s(46) = 7` needed
no case analysis, why 22 and 33 needed Bentz 2016’s Theorem 8, why 13 needed eight
cases, and why 12 is four spare points past any classical argument.
The one-spare cases are `n = 21` (`m = 5`), `n = 32` (`m = 6`), and `n = 45` (`m = 7`),
all open on the register.

| Target | Route | First discriminator | Kill |
| --- | --- | --- | --- |
| `s(21) = 5` | Bentz 2016 Theorem 8 with one spare red and two spare blue points, plus a two-wall line-capacity count (the one-spare deformation lemma); in parallel an unshrunk covering LP at side exactly 5 needing mass below 21 against the free 22 | An exact replay of Theorem 11 at the printed constant `sqrt(2) - 1/2`, then an enumeration of the exceptional structures | A structure that leaves at most four charges on every wall line and no forced partial-box point |
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
exact, so it is an admission gate rather than a two-route retention gate; the relational
producer refuses without the A6 sites-1 matrix, which is not in the repository
(`think-3xbr`). Threshold production is 2-of-3 only.
The 87 restricted optima at 45 sides are not recomputable: no run log or solver
checkpoint was retained for any of them, and a converged restricted optimum at or above
`n` kills point certificates on that site set only.

Named gaps, in build-cost order: a relational float route (one to two weeks), the
sites-1 rebuild, a relational column generator, an unshrunk exact-orientation verifier
generalised from `cases/green17/interval_audit.py`, a conditional-certificate gate whose
domain is a case predicate, a continuum-row oracle, a rational PSD checker (nothing
exists; `think-ol1z` is unstarted), a contact-hypothesis consumer, and owner-selection
routing. No open bead aims at moving the n=17 lower bound.
No scientific target has run since 2026-09-14.

Cost anchors from retained receipts: the two-route threshold gate about 90 s on three
workers for T-025; column-generation rows 82 s to 1620 s; the n=26 and n=27 runs hit a
1200 s deadline; the scratch relational chase about 45 minutes per variant.

## Adversarial Verdicts

Three Fable reviews at maximum effort, each reading one lane and its scratch scripts,
re-running every number, and reading the sources the lane cited.

**R1 on lane 1 (n=11).** Every number reproduces exactly at the families’ own sides.
Two corrections change the slate.
First, the lane measured its gains at `191/50` and `153/40` but proposed runs at `96/25`
and `77/20`; transported to those sides by centre homothety, with depth at most 1
verified exactly, the retained families make Theorem B’s deep branch **exactly neutral**
at every threshold, so the all-four-deep class has residual 7 against a requirement of 7
and is obstructed for every site set and threshold vector.
The `7/4` at `191/50` was a squeeze artefact: the 1.32° mid-wall core’s left edge is
`0.997` at `191/50` and `1.005` at `96/25`. The banked corner credit cancels exactly, so
the corner tree is a domain cut and its only non-neutral branch is the all-free
(octagon) class, gain 1 per corner at no count cost.
Second, the cell-24 upper boundary is `6.4537°`, not `6.585°` (that is cell 25’s centre
direction), so the tilted-anchor tree is incomplete until its lowest bin edge moves; and
the `33/8` removal is a single-pose number, at most `5/2` once priced over the lane’s
own cell, so the honest gain per anchor case is at most `1.5`. The strip lemma is
correctly derived and is a screen only.
R1’s first measurement: the octagon class at `96/25`, `d = 1/2`, on the convex clipped
domain with the existing loop, decisive either way.

**R2 on lane 2 (mechanisms).** The `θ′` chain is in the right direction and a certified
`θ < 11` on a sound graph would give a bound without dilation, but the proposed screen
cannot discriminate: floor atoms already take the 88-support to 10 (X-037) and the
64-support’s clique LP is already 9. The sparse verifier certifies `θ`, not `θ′`; a
Monte Carlo at `3.83` gives 44% of legal pose pairs overlapping, so the dual matrix is
dense, verification is cubic, and the lane’s own resolution arithmetic gives about
`1.4 x 10^7` cells per D4 class, above its own kill line.
The stress theorem is false as stated: the two-square side-by-side minimiser has a
horizontal chain only, and X-021 already records the “or” form.
The wall-wedge lemma is correct with a `min(tan β, b/a)` cap; `0.3203` reproduces by an
independent brute force; Trump’s squares 7 and 10 are its wall-vertex tilted squares;
and the kill condition is **not** met because the A6 64-family has a 7.11° orbit of mass
`3/4` at gap `0.016` from the top wall.
The `s(12)` reach estimate `12.3`–`12.6` is wrong: certificate masses are upper bounds
on covering values and no depth-one family of total 12 is retained below 4. The uniform
`m^2 - 3` test fails at `m = 5, 6` because `4.99` and `5.99` lie above the shrunk grid
ceilings; only `m = 4` at `3.99` is testable.
All six kills stand.
R2’s cheapest decisive measurement: the n=13 covering at `3.99` with window sites.

**R3 on lane 3 (other n).** The cap `4.67104` reproduces and the hex-set count
`m^2 - ceil(m/2)`, fitting only for `m <= 7`, is exact.
Two corrections and one finding.
The repository’s transcription of Bentz 2016 printed the finishing line of Theorems 9
and 11 at `x = (sqrt(2) - 1)/2 ≈ 0.2071` and the midpoint standoff at `1/(2 sqrt 2)`;
the PDF prints `x = sqrt(2) - 1/2 ≈ 0.9142` and `sqrt(2)/2 - 1/2`. With the transcribed
constant the last step is false (an axis-parallel box of side `1.0001` centred at
`(0.708, y_i)` defeats it); with the printed constant Lemma 5 gives `2 sqrt 2 - 2d = 1`
exactly and the chord minimum over boxes containing `[0.4, 1] x {y}` is `1.0000`. The
coordinator confirmed this against rendered pages 6 and 7 of the archived PDF; it is
filed as D-505 and corrected in the transcription.
Lane 3’s spare conventions were mixed: with `k = |P| - boxes`, 22 was `(0, 1)`, 21 is
`(1, 2)`, 32 is `(1, 1)`, 45 is `(0, 1)`, so 45 is not one-spare, and the `m = 7` height
budget `6.8925 < 7` blocks Bentz’s `0.1` slide there.
Doubly-covered boxes fix two points, so n=21 has up to six stationary points and about
38 red by 1,200 blue exceptional structures modulo D2, not the lane’s “at most three
assignments”; the lemma is plausibly provable for 21 and 32 but is new casework, and its
kill is a structure with four charges on both walls, not a 21-box packing.
At n=17 the “at most four per line” refutation is stronger than stated (Bidwell has six
squares on one vertical line and seven on one horizontal), the “at most four per wall”
argument is invalid, and “no rational-grid certificate at exactly `U`” is overstated
because six of the 24 contacts lie on `x = 1` or `y = 1`. Green’s numbers verify;
“unproved” should read unpublished and unrecovered.

## Ranked Slate After Review

| Rank | Item | Hypothesis | Instrument | Significance if it lands | First measurement |
| --- | --- | --- | --- | --- | --- |
| 1 | Seeded point certificate at n=26, `53/10` | H-225 | Exists | A first-party floor `+0.30` above Nagamochi, recipe for five more `n^2 + 1` cases | One seeded run, 3600 s deadline, then the gate |
| 2 | Bentz 2016 replay at the printed constants, then the n=21 and n=32 one-spare structures | H-226, H-227 | Enumeration tool to build | Two new exact values and a reusable lemma | The Theorem 11 chord replay |
| 3 | Depth-one ceiling family of total 17 at n=17, `23/5` | H-224 | Exists | Closes the fixed-shrink point route at n=17 for every site set; says an unshrunk or relational language is required | Freeze-family, polish, both readers |
| 4 | The n=11 octagon class at `96/25` | H-222 | Convex clip predicate to admit | A structural negative about corner conditioning, or a conditional exclusion at 3.84 | The restricted loop on the clipped domain |
| 5 | Point certificate at n=13, `399/100` | H-223 | Exists | Calibration of the integer-endpoint mechanism | One run with window sites |
| 6 | Gap-g wedge conflict edges against the 64-family | H-230 | Derivation, then exact checks | A first two-body conflict atom with a proved geometric budget | The gap extension at 7.11° and gap 0.016 |
| 7 | Tilted-anchor case containing the 29° slot | H-229 | Non-convex domain predicate | A second conditioned exclusion at 3.84 | After the BC-204 instrument |
| 8 | Unshrunk covering below 12 at side 4 | H-228 | Unshrunk verifier | `s(12) = 4` | After the verifier |
| — | Theta on pose cells | H-231 | None | Open question | None |

Retired with reasons and reopening conditions in agenda-040’s BC-366: the corner deep
branches, the theta screen, the stressed contact-graph theorem in its four-wall form,
the uniform `m^2 - 3` test at `m = 5, 6`, and the n=45 and n=44 cases.

## The Overnight Loop

The owner asked for about eight hours of research in one- to two-hour chunks, each a
fresh session record and a stacked pull request on the previous head, with mathematics
delegated to Fable and mechanical work to Opus under a Fable review.
[agenda-040](../agendas/agenda-040-overnight-lower-bound-loop.md) carries the queue:

1. **Chunk 1 (BC-361, Session 144).** H-223, H-224, H-225 on the stock instruments, each
   under its own experiment id, beside the BC-362 mathematical lane’s Theorem 11 replay.
2. **Chunk 2 (BC-363).** Admit the convex corner-clip predicate with an independent
   reader and a T-023 replay control; run H-222.
3. **Chunk 3.** H-222 classes and the n=21 structure inventory; a second n=26 site set
   if the first parks.
4. **Chunk 4 (BC-364).** The gap-g wedge derivation; the anchor case if the predicate
   generalises.
5. **Closeout.** Dispositions, handoff, and the next selected entry.

`think-qqzs` / H-216 stays the registered n=6 calibration entry and can fill an idle CPU
slot.

## How the Overnight Loop Ended

Two chunks ran before the account’s spend limit and the clock closed the loop
([Session 144](../agent-sessions/session-144-overnight-chunk-1.md),
[Session 145](../agent-sessions/session-145-overnight-chunk-2.md)); the dispositions are
on [agenda-040](../agendas/agenda-040-overnight-lower-bound-loop.md).

- **BC-361.** None of the three stock-instrument determinations reached its target.
  H-223’s site set converged at 15.566 (exp-214) and H-224’s at 17.042 (exp-218), with
  depth-one family totals 85/8 and about 14, so both site sets are refuted and the
  claims untouched; H-225 stopped on the clock at the 25.000000 plateau (exp-215).
- **BC-362.** Theorem 11 replays exactly at the printed constants.
  The one-spare inventory has 42,124 D2-orbits at n=21, of which 22,603 need geometry
  beyond the paper’s toolkit after Theorem 8 co-location propagation, and the n=32 lemma
  fails on the 0.0265 vertical budget; H-226 and H-227 are rejected as stated (exp-216,
  exp-217) and the inventories are retained under `devtools/bentz2016`. D-507 records a
  third transcription defect (Theorem 9’s budget factor 2).
- **BC-363.** The convex corner-clip instrument was admitted, and exp-219 excludes the
  octagon class at 96/25: every packing of 11 unit squares in a square of side 3.84 has
  a square meeting the open corner triangle x + y < 1/2 at some corner, RETAINABLE under
  the corner class hypothesis from both routes with mass 10.868617. This is the first
  decided item of the corner-conditioned point language; the exclusion is conditional
  and not a bound, and since the all-deep class is already outside the language
  (BC-366), the tree cannot close at 96/25 by clipping alone.

No bound on `s(n)` moved.
The next entry is BC-367: register the conditional exclusion after review, clip the
remaining corner-bin classes, and give n=26 a second site set.

## Owner Decisions

None are requested. The theta route stays retired under X-037’s condition; the Bentz
transcription correction is a factual repair with a defect record; every other item is a
registered hypothesis with a kill rule.

## What This Block Did Not Establish

- No bound on `s(n)` moved for any `n`, and no hypothesis was decided.
- Every gain figure is a Lemma-D necessary condition measured on a fixed retained
  family; none is a covering value.
- The wall-wedge lemma, the strip lemma, and the hex-set count are derived and reviewed
  here, not registered results.
- The n=21 and n=32 lemma is a conjecture with a corrected case-tree size; nothing about
  it is proved beyond Bentz 2016’s own theorems at the printed constants.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
