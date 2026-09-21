# H-222 Registration Review of exp-219 (Session 146, chunk 3)

Status: **REGISTER WITH CORRECTIONS**. An adversarial, read-only Fable review of what
exp-219 establishes, its inherited conditions, the second stage the deep-branch
neutrality forces, the registration wording, and six bookkeeping defects.
The review text follows as delivered; exp-220 re-freezes the certificate under the
corrected claim strings (defect D1).

Reviewer worktree: /home/user/squares-chunk3 at b51a0a82 (branch
claude/kind-wright-whxxn6-chunk3), 2026-09-20. Nothing under the repository tree was
edited. Interpreter: packing/.venv/bin/python3 (3.14). Scratch beside this file:
checks.py / checks.out (independent predicate, geometry and covering checks),
replay-decide.stdout and replay-stalls.json (my replay of the gate),
replay-noflag.stdout (the record without the flag).

## 0. What was read

H-222; exp-219 experiment record; exp-219 receipt, decide.stdout, stdout, log, run.json,
rows.jsonl, covering.json (head and tail), family.json (keys), stalls.json;
corner_clip.py in full; the instrument commit 167a4b05 diffs for certificate.py,
sweep.py (current file in full), generate.py, interval.py, ceiling.py, colgen.py;
decide_certificate.py in full; the test names; chunk2-review.md; X-040 (lane 1, R1,
slate, overnight-loop end); lane-a Theorem B, Lemmas 2-4 and the 2026-09-08 domain
correction; agenda-040 BC-363/BC-366/BC-367; session-145 record; conventions.md section
4; epistemics rungs; the T-023 register entry as the precedent for a conditional
exclusion; X-023’s threshold-atom theorem.

## 1. What exp-219 establishes, stated as a theorem

Notation. L = 96/25, B = 9977/10000. N is the net of 181 half-tangents t_k = k *
207107/(500000*180), k = 0..180, i.e. angles theta_k = 2 arctan t_k in [0, ~pi/4] (t_180
= 0.414214 > tan(pi/8), so the arc reaches pi/4: Condition 3). D = max half-gap tangent
= 207107/90000000, and B(1 + D) = 0.99999590 < 1 (Condition 4, my recomputation), so for
a unit square Q at any angle the concentric closed B-square at the nearest net direction
(after D4 folding) lies strictly inside int Q. Call that square the **core** P(Q). mu is
the atom measure in exp-219-n11-96-25-clip-covering.json (SHA-256 5813d822 … 7040d): 680
point atoms, D4-symmetric about the container centre (Condition 1), total mass
10868617/1000000 < 11 (Condition 2). For a closed square S and a container corner j,
write delta_j(S) = min over S of (x + y) in corner j’s frame (the D4 image putting
corner j at the origin), and T_d = {x, y >= 0, x + y <= d}.

**Theorem (exp-219, conditional on the soundness of the instrument at 167a4b05).** There
is no family Q_1..Q_11 of closed unit squares with pairwise disjoint interiors in
[0, 96/25]^2 such that delta_j(P(Q_i)) >= 1/2 for every i in 1..11 and every corner j in
1..4. Equivalently, **every packing of eleven unit squares in [0, 96/25]^2 contains a
square Q_i and a corner j with delta_j(Q_i) <= delta_j(P(Q_i)) < 1/2**, i.e. some unit
square meets the *open* corner triangle {x, y >= 0, x + y < 1/2} in some corner frame.

Proof shape (what the certificate decides).
At every net direction theta_k the gate proves, exactly, that every core whose centre
lies in the kept domain K_k = {c : min_j delta_j(core at c, theta_k) >= 1/2} covers
mu-mass >= 2000013/2000000 >= 1. If all eleven cores had delta_j >= 1/2 at all corners,
their centres would lie in the kept domains (after D4 folding, which the clip is
invariant under: checked, section 2), the eleven cores are pairwise disjoint closed sets
(Condition 4), so the eleven traces on the atom set are disjoint and sum(mu(P_i)) <=
mu(total) = 10.868617 < 11, contradiction.

**Logical direction, checked against the code.** The clip *removes* rows:
`CornerClip.excludes` is `penetration <= d` (closed triangle, corner_clip.py) and
`half_planes`/`clip_polygon` keep the closed complement `penetration >= d`;
`reduce_to_cells`/`reduce_to_spans` (sweep.py) take the per-u-slab v-range of the
clipped convex polygon, which is a *superset* of the cells that meet it (the slab
intersection is convex, not a rectangle), so the exact route quantifies over at least
every kept centre. The interval route drops a box only when an outward-rounded upper
bound on max_box(sigma . q) is <= a lower bound on d + reach - mL for one corner
(`clip_excluded`), i.e. only boxes every point of which has penetration <= d; a box that
may straddle the cut is kept and searched.
So RETAINABLE on the clipped domain means “mass >= 1 on every core with penetration >=
1/2 at all four corners”, and the class it excludes is “all eleven cores have
penetration >= 1/2 everywhere”, which *contains* lane-a’s all-free (octagon) class “no
unit square meets the closed T_{1/2} at any corner” (because P(Q) subset of Q gives
delta_j(Q) <= delta_j(P(Q)), so delta_j(Q) > 1/2 implies delta_j(P(Q)) > 1/2). The
reading in the task prompt is confirmed, with one sharpening: the excluded class is
defined on the *cores* and is slightly larger than the unit-square class.

**Cores versus unit squares, and the loss.** The transfer is lossless in the direction
that matters. Hypothesis side: the excluded core-class contains the unit-square all-free
class (no loss; the theorem excludes strictly more).
Conclusion side: the contradiction yields a core with delta_j(P_i) < 1/2 (strict,
because the kept domain is closed), and P_i subset of Q_i gives delta_j(Q_i) <=
delta_j(P_i) < 1/2, so the conclusion about unit squares is at least as strong as the
one about cores. The only “loss” is the one that makes the class *larger*: a unit square
with delta_j(Q) in [1/2 - eps, 1/2], eps <= (1 - B) max(cos, sin) plus the net-angle
offset (corner_clip.py “as a constraint set”), may have a core with delta_j(P) >= 1/2
and so also lies in the excluded class.
That is a gain, not a loss: the theorem’s complement (what a second stage must exclude)
is “some core has penetration < 1/2”, which is *contained in* “some unit square has
delta_j < 1/2” (strict, open triangle).
A second stage may therefore assume a strict occupant, delta_j(O_j) < 1/2, at some
corner; it never has to handle the boundary case delta_j = 1/2.

**On the session’s sentence.** “Every packing of 11 unit squares at side 96/25 has a
square meeting a corner triangle x + y <= 1/2” is true and even slightly weak (open
triangle, strict inequality).
“At side 96/25” should read “in a square of side 96/25”. “Conditional, not a bound” is
right about s(11) but mislabels the sentence itself: the displayed statement is an
*unconditional structural theorem about every packing at 96/25* (assuming the instrument
is sound); what is conditional is the *exclusion* ("no packing exists") -- it holds only
in the all-free class.
The record should say “a structural theorem at 96/25 that excludes one class; s(11) is
untouched”, not “a conditional theorem”.
Note also that the statement is vacuous if s(11) > 96/25; its content is the case split
toward proving exactly that.

## 2. Is it a theorem given the certificate? Inherited conditions

Given the certificate bytes and the gate’s acceptance, the statement in section 1 is a
theorem modulo the following, all of which I list even where the exposure is nil:

1. **Conditions 1-4 of the certificate**, decided exactly by `closed_form_conditions`
   before either route runs: D4-closed atom multiset (680 atoms, no duplicate sites),
   total mass 10868617/1000000 < 11, final half-tangent with t^2 + 2t - 1 >= 0, B(1 + D)
   < 1. Recomputed here (checks.out).
2. **Condition 5 on the clipped domain, by both routes.** Exact route: int64 event-cell
   sweep on the atoms’ common denominator (least 2000013/2000000, witness recomputed
   serially by me at the same value); interval route: directed-rounding branch and bound
   on the *doubled* net (theta_k and pi/2 - theta_k), enclosure of width zero at the
   same value, 1,743,736 boxes, 0 stalled, in 30 s on my replay.
   The routes decide the same set only because the clip is D4-invariant and folded
   (`reach = B max(|cos|, |sin|)`); I checked invariance under the five non-trivial D4
   generators at random rational centres (checks.out, zero mismatches) and the module’s
   `penetration` against my own vertex-based minimum of x + y (zero mismatches), and the
   clipped polygon’s membership against the predicate.
3. **Net discretisation is not an inherited condition of the statement.** The net enters
   only through which core P(Q) is used; Condition 4 makes the core a subset of Q for
   *every* angle, and the conclusion is stated on unit squares.
   Nothing about the theorem depends on the 181-direction net beyond its being the net
   the certificate was decided on.
   Likewise the **site set** (BC-191 auto grids 25/34/42 plus 5-per-window seeds) is a
   property of the certificate found, not of the statement; a different site set could
   fail to find one, but cannot invalidate this one.
4. **The exact-route versus interval-route semantics are the same statement.** The
   interval route quantifies over a *superset* of the kept domain (straddling boxes
   kept), the exact route over a superset of the cells meeting it (slab v-ranges); both
   are conservative, so agreement at the same rational is a genuine cross-check and not
   a coincidence of implementations.
   The routes share `Certificate` and Conditions 1-4 (one parser); that shared parser is
   the one non-independent component.
5. **Lane-a is not a hypothesis.** The theorem uses only Lemma 2 (min over a square of x
   \+ y, re-derived in corner_clip.py and in chunk-2 review section 1) and Condition 4.
   It does not use Lemma 3 (the box), Lemma 4 (uniqueness of the occupant) or Theorem
   B’s bin structure. The phrase “lane-a Theorem B’s free class” is a name, not a
   premise.
6. **The class hypothesis is not the closed-triangle class as printed.** The gate’s
   headline “no square meets x + y <= 1/2 in any corner frame” names a *sub*-class of
   what is excluded; correct but under-stated (section 1).
7. **Software trust.** corner_clip.py plus eleven threaded modules at 167a4b05, 19 new
   tests, and the chunk-2 review’s 13,357-point randomised check; my own checks in item
   2 are independent of the module for the predicate and the polygon, but the sweep and
   interval routes themselves were replayed, not re-implemented.
   The interval route’s `_clip_planes` folding
   (`Interval(max(cos.lo, sin.lo), max(cos.hi, sin.hi))`) is a valid enclosure of
   max(cos, sin) only because the doubled net keeps cos, sin >= 0; it does.
8. **Vacuity.** Non-vacuous only if eleven unit squares fit in [0, 96/25]^2, which is
   open (s(11) in [3.8264, 3.8771]). This is not a defect; it is what a case split is.

Verdict on 2: a genuine theorem at V4 strength for its scope, with no condition beyond
the certificate’s own five (clipped) and none inherited from the net, the site set, or
lane-a.

## 3. The second stage: the complementary class

**What must be excluded.** The complement of section 1’s hypothesis is “some core has
penetration < 1/2”, which is contained in “some corner j has delta_j < 1/2” (strict).
By lane-a Lemma 4 (threshold 1) that corner then has a *unique* occupant O_j meeting the
open T_{1/2}; by Lemma 3 it contains the closed box [1/2, 1]^2 in corner j’s frame; by
Lemma 2 its folded angle satisfies sin(phi) <= 1/2 - g_x - g_y, so |phi| <= 30 degrees,
and its centre lies in [h, 1]^2 with h = (cos phi + sin phi)/2 in [1/2, 0.683]. So a
corner contact pins one square to a pose region of about 1/2 in each centre coordinate
and 30 degrees in angle.
In the binary corner tree at d = 1/2 the complement is 15 bin vectors in 5 D4 classes: f
= 3 free corners (4 vectors), f = 2 adjacent (4), f = 2 opposite (2), f = 1 (4), f = 0
(1).

**What a corner contact forces on neighbours at 3.84.** (i) Every other square is
disjoint from int O_j, hence from the open box (1/2, 1)^2; (ii) no second square meets
T_1 at that corner (Lemma 4), and occupants of different corners are distinct; (iii) the
inner edges of two adjacent corner boxes are 3.84 - 2 = 1.84 < 2 apart, so at most one
further square lies within depth 1/2 of a wall between them: at most 8 wall squares and
at least 3 interior squares (this is X-040’s C3 census cap); (iv) the mid-wall neighbour
must clear x = 1 at every height, and x = 1.366 at the height of the lowest-right vertex
of a 30-degree occupant.
None of this is integral in a way the fractional adversary violates: the retained
88-family transported to 96/25 has four flush axis-parallel corner slots of mass exactly
1, its 1.32-degree mid-wall core’s left edge is 1.005 > 1 (R1), and its wall class has
mass exactly 8. The family *is* an all-deep configuration.
That is why R1 found the deep branches exactly neutral, and it is now a Lemma-D theorem
on record (BC-366): on the f = 0 domain the family’s residual is 11 - 4 = 7 =
requirement, so no point covering exists for the all-deep class on any site set and any
threshold vector at 96/25. exp-219 excluded the class the adversary never occupied; the
complementary class is the hard one *because the extremal fractional object lives in
it*.

**What the exp-219 covering itself says (checks.out).** It puts mass 0.70496 in each
corner box [1/2, 1]^2 (0.692 strictly inside it, 0.013 on its inner edges x = 1/2, y =
1/2) and nothing in T_{1/2} or strictly below depth 1/2 along any wall; its unclipped
least covered mass is 2819857/4000000 = 0.70496 at the flush corner core (0.508, 0.508).
So the free clip lets the covering leave 0.295 unpaid at each corner, and that is the
entire mechanism. Take the same covering into the banked classes: cores meeting the open
box (1/2, 1)^2 are no longer rows and the mass strictly inside it (0.69217 per corner;
the remaining 0.01279 sits on the line x = 1/2 or y = 1/2 and may still serve rows
avoiding the interior) is useless, so deleting it gives a *feasible* covering of the f =
3 program (requirement 10) of value 10.869 - 0.692 = 10.176; f = 2: 9.484 against 9; f =
1: 8.792 against 8; f = 0: 8.100 against 7 (openbox.out).
Each banked corner costs 0.308 relative to its requirement on this covering (the
counterpart of “neutral” in family terms, since the count credit is 1 and the interior
corner mass is only 0.692). The LP will re-optimise, and only a run says by how much; f
= 0 is already provably out of reach.

**Can threshold atoms (T-025 / X-023) price a corner contact?** A threshold atom (S, k,
w) charges cores containing at least k of S and has budget w floor(|S|/k); it escapes
Lemma D only when k does not divide |S| (clique and odd-cycle cuts).
The natural corner atom, “a core containing the inset box X' pays 1”, is a k = |S| atom:
by Lemma 3 every core that meets T_{1/2} contains X' (up to the inset), the family’s
four corner variants of weight 1/4 all contain it, charge 1 = budget, neutral.
A 2-of-3 atom needs three pairwise-overlapping cores with no common point; the corner’s
family cores all share X', so a clique atom there is implied by the point constraints.
Corner contact therefore creates no local integrality the threshold language can bill.
It creates a *global* one: with all four corners banked and at most four mid-wall
squares, at least three unit squares (area 3) lie in C minus the four unit corner boxes
minus the wall squares; the axis-parallel central box [1, 2.84]^2 has side 1.84 < 2 =
s(2), so it holds at most one unit square, and at least two interior squares must
protrude into the 0.84-wide wall-strip gaps between an occupant and a mid-wall square.
Fractional mass 3 spread over the 88-family’s 24 central poses ignores this; it is
exactly X-040’s “ring-centre disjointness the family never pays for”, and the instrument
for it is a 2-of-3 or clique atom on the ring-centre overlaps (C4, “blocked on tooling”;
X-037’s fixed-support clique LP stops at 32/3 < 11). The threshold instrument exists
(sqpack.fractional.threshold*, plateau 153/40 on the A6 64-family) but takes no domain
cut: 167a4b05 did not touch it.

**Bentz’s wall-line charge idiom.** A line y = c meets at most floor(3.84) = 3 square
interiors with chord >= 1, spare 0.84; four wall lines give capacity 12 for 11 squares
with two spares (n = 11 = 3^2 + 2, not m^2 + 1), and in the all-deep class each depth
line already carries its two occupants and at most one mid-wall square, which is Trump’s
census.
The idiom can charge the 8 wall squares and leaves the 3 interior ones uncharged;
it closes nothing at n = 11 on its own, and the one-spare enumeration (exp-216/217)
shows how much casework it costs even where the spare is single.

**A concrete, costed first discriminator.** Two candidates; be clear which question each
answers.

(A) *Does banking ever pay in the LP?* Run the f = 3 class (one corner banked at d =
1/2, three free) on the exp-219 site set with requirement 10. Instrument: a box cut --
remove cores meeting the open box (1/2, 1)^2_j -- as the complement of a convex octagon
(the Minkowski sum of the box and the rotated core) inside `centre_domain`; the sweep’s
per-slab v-range is already a superset so soundness is unchanged, the interval route
drops a box iff it is provably inside the octagon (the conjunction mirror of
`clip_excluded`), the readers get K4-box, and the record declares a `corner_bins` vector
under `variant: class`. Cost: the mirror of chunk 2, four to six hours of build plus an
adversarial review, then about five minutes per run (exp-219 took 266 s), so all four
mixed D4 classes in an hour.
Kill readings: a converged value >= 10 refutes this site set for f = 3; a polished
depth-one family on the f = 3 domain with K4-box and exact total >= 10, accepted by both
readers, kills f = 3 for every site set and, with f = 0 dead, ends the corner tree at
96/25 in the point language.
A value < 10 accepted by both routes is a second conditional exclusion.
**Either way the tree cannot make 96/25 unconditional**, because BC-366’s f = 0
obstruction is for every site set; (A) answers a question about the mixed classes only,
and its prior from the exp-219 covering is unfavourable (0.176 to recover at f = 3,
0.484 at f = 2, 0.792 at f = 1).

(B) *The one that could matter.* Inside the f = 0 class, where the pinning is exact
(four occupants with |phi| <= 30 degrees containing the four boxes, seven remaining
cores in C minus the boxes, at most four of them within depth 1/2 of a wall), price the
ring-centre relation with a threshold atom: a 2-of-3 atom on three points chosen in the
pairwise intersections of one ring core and two central cores of the transported
88-family, budget 1 where the family pays 3/2 (X-023). Instrument: the threshold sweep
plus the box cut of (A) plus the count credit 7. Cost: (A)'s build plus wiring the clip
into threshold.py/threshold_interval.py, one to two days, then runs.
Kill reading: a depth-one family on the f = 0 domain feasible for every point and
threshold atom in the language with exact total >= 7 kills the corner tree at 96/25 in
the point-plus-threshold language for every site set; that is the reading BC-366 asks
for before the deep branches reopen.
If instead a covering of value < 7 is accepted, the corner tree is alive and the four
mixed classes become worth running.

Honest summary: the complementary class is the hard one, and not marginally so.
The all-deep member of it is provably unreachable by the language exp-219 used, for
every site set, and it is where the one-body extremal family sits; the corner contact
pins one square but forces nothing on its neighbours at 3.84 that the family does not
already meet with equality.
What remains is the global integrality of three interior squares in a 1.84-box plus 0.84
gaps, which is the same problem the unconditional route faces, now with the corners
pinned.

## 4. Registration recommendation

**As what.** A results-register entry in packing/frontier/results.yaml modelled on
T-023, which is the precedent for “a conditional exclusion that changes no global bound
for s(11)” (T-023 sits at V3/C3 with significance 3). Not a frontier-bound entry, not a
note on H-222 only (the theorem is a first-party structural statement with a machine
certificate and deserves an id, a replay command and a control test), and not
“computationally verified, conditional” as a status: under conventions section 4 the
assurance is `verified`, method `exact-algebraic` plus `interval-certified`, and the
conditionality belongs in the claim’s scope wording, not in its assurance.
Rungs: V4 (exact-algebraic and interval-certified certificate with a replay command and
a passing repository replay, this review’s included); C3 (repository-origin machine
confirmation with passing replay).
The two gate routes were not counted as method-distinct for T-022 and should not be
here, so C4 needs a genuinely separate derivation; C5 needs this review filed as a
mapped review artifact under docs/project/reviews/. Significance: 2, not 3. T-023
excluded a four-owner branch by a new mechanism; exp-219 excludes one D4 class of a tree
that BC-366 already shows cannot close in this language, and the class excluded is the
one the fractional adversary never occupied.
Novelty: apparently-novel (a conditioned point certificate on a corner-clipped domain
has not been run before; lane-a records Theorem B as “sound, unrun”).

**Scope wording I would accept.**

> At L = 96/25 and B = 9977/10000 on the 181-direction net (half-tangents k *
> 207107/90000000, k = 0..180), the D4-symmetric point measure of total mass
> 10868617/1000000 in exp-219-n11-96-25-clip-covering.json (SHA-256
> 5813d822d3f83eef98326de0c16e245466afbcb8c4988b039e81a4bcf3d7040d) charges at least
> 2000013/2000000 to every closed B-square at a net direction whose minimum of x + y is
> at least 1/2 in each of the four corner frames (decided by the exact event-cell sweep
> and by the interval branch and bound, agreeing at that value).
> Consequently every packing of eleven unit squares in [0, 96/25]^2 contains a unit
> square whose minimum of x + y in some corner frame is strictly below 1/2, i.e. one
> that meets the open corner triangle x + y < 1/2 at that corner; equivalently, the
> all-free (octagon) class of lane-a Theorem B at threshold 1/2 contains no
> eleven-square packing at side 96/25. This is a conditional exclusion of one corner-bin
> class and changes no bound on s(11); the all-deep class is separately known to be
> outside this language’s reach (BC-366), so the corner tree cannot close at 96/25 by
> clipping alone.

**What an independent replay must check** (from packing/, prefix
`uv run --frozen --all-extras --group dev`; the project interpreter, never the system
one):

1. `sha256sum campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-219-n11-96-25-clip-covering.json`
   prints 5813d822 … 7040d (my replay: identical).
2. `python -m devtools.decide_certificate --corner-clip 1/2 <that file>` prints
   `interval accepted=True enclosure=(2000013/2000000, 2000013/2000000) ... stalled=0`,
   `exact accepted=True least=2000013/2000000`, and the RETAINABLE UNDER THE CORNER
   CLASS HYPOTHESIS line ending in the same sha256 (my replay: 30 s + 6 s, identical;
   stalls dump has 0 boxes in every direction).
3. The same command *without* `--corner-clip` prints REFUSED naming variant ‘class’ (my
   replay: it does; exit 1). This is the check that the record cannot be read as a
   bound.
4. `pytest tests/test_fractional_corner_clip.py -q` (19 tests, including the residual-7
   control on the transported 88-family and the empty-domain refusal).
5. Optional but cheap: recompute the unclipped least covered mass of the same file
   (`sweep.minimum_covered_mass` without a clip) and confirm it is 2819857/4000000 < 1
   at the flush corner, so the reader sees that the clip is what decides.

Before registration the record itself needs D1 below fixed (the bytes currently carry
the claim string “s(11) >= 96/25” and an unconditional-looking id), which changes the
SHA; the fix is a five-minute re-run plus the gate, and the register entry should pin
the corrected file. A case directory (the receipt’s own W2 plan) with the certificate,
the gate command as a control test (the T-022 pattern:
packing/tests/test_dilation_corollary.py), and this review mapped is what earns C5.

## 5. Defects, with fixes

- **D1 (bookkeeping, flattering).** The certificate bytes declare
  `"claim": "s(11) >= 96/25"` and `"id": "C-n011-fractional-96-25"`, the strings of an
  unconditional retained certificate, because run_fractional_colgen.py:434 writes
  `claim = f"s({n}) >= {side}"` regardless of the clip and decide_certificate.py
  *requires* exactly that string (`declared_claim != expected_claim` refuses).
  The `variant: class` key is the only thing that stops the bytes reading as a bound,
  and the gate does enforce it (check 3), so no verdict is wrong; but a class record
  must not carry the unconditional claim text.
  Fix: the driver writes a class claim (e.g. “corner class d = 1/2 at 96/25: no packing
  of 11 unit squares has every core avoiding T_{1/2}”) and a class id, the gate expects
  that form under `--corner-clip`, the tests cover both, and exp-219’s covering is
  re-frozen and re-gated (five minutes) so the registered SHA is of a self-describing
  file.
- **D2 (bookkeeping).** BC-367’s question ("extend … to the other corner-bin classes at
  96/25, so that the corner-conditioned point language closes at 3.84") and the
  receipt’s “the other fifteen corner-bin classes … are untouched” contradict BC-366’s
  retire-negative: the all-deep bin vector is obstructed for every site set and
  threshold vector, on record, by R1’s exact transport.
  Fix: BC-367 scopes to the four mixed D4 classes (14 bin vectors) and states that the
  tree cannot close by clipping alone; the receipt and H-222’s notes say “fourteen bin
  vectors in four D4 classes remain open, and the all-deep class is already excluded
  from this language (BC-366)”.
- **D3 (wording).** The session record, agenda-040 BC-363 and H-222’s notes call the
  displayed theorem “conditional”.
  The structural statement ("every packing … has a square meeting a corner triangle") is
  unconditional; the *exclusion* is conditional.
  “At side 96/25” should be “in a square of side 96/25”. Fix per section 1’s last
  paragraph.
- **D4 (bookkeeping).** The experiment record’s `engine` lists polish_ceiling_family,
  independent_ceiling_reader --corner-clip and replay_ceiling_family --corner-clip, none
  of which ran for exp-219 (no outputs in the results directory; the frozen family’s
  total 8.94 is below the kill line so there was nothing to read).
  The frozen family carries the clip only in `provenance.settings`, not as a top-level
  declaration, so a reader replaying it without the flag prints the unconditional
  sentence (sound, since a clipped depth-one family is an unconditional one, but the
  record should say what it is).
  Fix: engine says “readers not run: family total 8.94 < 11”; freeze-family writes
  `variant`/`corner_clip` at the top level (the S1/N2 territory of the chunk-2 review).
- **D5 (wording, conservative).** The gate’s headline “(no square meets x + y <= 1/2 in
  any corner frame)” names a sub-class of the excluded class (the excluded class is on
  cores, and the conclusion is strict).
  Also `ceiling 3.990800, certifies every n >= 11` is printed for a class record, where
  “certifies” is the unconditional word.
  Fix: headline “(every core with min x + y >= 1/2 at all four corners is charged)” and
  suppress or reword the “certifies” line under a clip.
- **D6 (clarity).** The receipt says the run “converged at round 0 … after one column
  round added one orbit”; colgen’s last column round (`index + 1 == column_rounds`) adds
  the orbit without a further row solve, so the frozen covering is the round-0
  row-converged solution and the added orbit is not in it.
  Harmless (the gate decides the bytes), but the receipt should say so rather than leave
  a reader wondering whether an unsolved column entered the freeze.
- No soundness defect found.
  The reading in the task prompt is confirmed; the instrument, the replay, and the
  numbers reproduce exactly.

## Verdict

**REGISTER WITH CORRECTIONS.** Register as a results-register entry (T-023 pattern) at
V4/C3, significance 2, with the scope wording of section 4, after: D1 (re-freeze with a
class-specific claim and id, re-gate, pin the new SHA), D2 (BC-367 and the receipt
scoped to the four mixed classes with the all-deep obstruction cited), and D3 (wording).
D4-D6 are should-fixes that can ride with the registration commit.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
