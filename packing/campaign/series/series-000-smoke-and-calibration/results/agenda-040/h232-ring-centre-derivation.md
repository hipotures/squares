# H-232 Ring-Centre Derivation (Session 148, chunk 5)

Status: **INSTRUMENT** (lane verdict), reviewed ADMIT WITH CORRECTIONS in
[h232-ring-centre-review.md](h232-ring-centre-review.md); the corrections are applied in
[H-232](../../../../hypotheses/H-232-n11-all-deep-class-ring-centre-atom.md).
The lane’s report follows as delivered; the review notes one unused chord-formula
sentence in Theorem 2 whose breakpoint should read r = sin t (linear piece) with the
flat piece on [sin t, cos t], and that the instrument-gap paragraph describes a
concurrent lane’s uncommitted worktree edits, not HEAD.

Read-only Fable pass in /home/user/squares-chunk5 (branch
claude/kind-wright-whxxn6-chunk5, HEAD bfeba117). Nothing under the repository tree was
edited. Interpreter: packing/.venv/bin/python3 (3.14); every number below is exact
Fraction arithmetic unless it carries a tilde.
Scratch beside this file: family-96-25.json (the transported family), analyse.py /
analyse.out (classification), threshold_max.py / threshold_max.out (exact maximum
threshold charge on the family), triple.py / triple.out (the maximising atom),
simple_sites.json, H-232 draft at h-232.md.

Notation: L = 96/25, B = 9977/10000, net = 181 half-tangents t_k = k * 207107/90000000,
D = 207107/90000000 the largest half-gap tangent, corner j’s frame the D4 image putting
corner j at the origin, T_d = {x, y >= 0, x + y <= d}, delta_j(S) = min over S of x + y
in frame j. P(Q) is the core of a unit square Q: the concentric closed B-square at the
net direction nearest Q’s angle; Condition 4, B(1 + D) < 1, puts P(Q) in int Q.

## 1. The all-deep class at L = 96/25, stated exactly

**Definition.** A packing Q_1..Q_11 of closed unit squares with pairwise disjoint
interiors in [0, L]^2 is *all-deep* (bin vector f = 0 of the corner tree at d = 1/2)
when for every corner j some core P(Q_i) has delta_j(P(Q_i)) < 1/2. This is exactly the
complement, corner by corner, of the class exp-219/exp-220 excluded (all cores with
delta_j >= 1/2 at corner j); the sixteen bin vectors are these four binary choices, and
f = 0 is the one where every corner is deep.

**Theorem 1 (occupants; lane-a Lemmas 2, 3, 4).** In an all-deep packing, for each
corner j:

(a) There is a unique square O_j meeting the open triangle {x, y >= 0, x + y < 1/2} in
frame j, and O_j != O_k for j != k. Proof: the core with delta_j < 1/2 lies in its unit
square, so that square meets the open triangle; Lemma 4 at epsilon = 1/2 < 1 gives
uniqueness, and distinctness across corners because a square meeting T_{1/2} at two
corners has extent > L - 1 > sqrt 2.

(b) O_j contains the closed box [1/2, 1]^2 in frame j (Lemma 3 at d = 1/2, since the
open triangle is inside T_{1/2}).

(c) Writing O_j’s pose as (g_x, g_y, phi) in frame j with folded angle phi, Lemma 2
gives g_x + g_y + sin phi < 1/2, hence sin phi < 1/2, |phi| < pi/6 exactly, and g_x +
g_y < 1/2. Its centre (a, b) satisfies a, b in [h, 1) with h = (cos phi + sin phi)/2 in
[1/2, (1 + sqrt 3)/4) = [0.5, 0.6830): a = g_x + h >= h and a <= 1/2 + delta_j < 1 (the
2026-09-08 correction in lane-a).

(d) The *core* P(O_j) contains the inset box X' = [1 - beta/2, (1 + beta)/2]^2 in frame
j with beta = B/(1 + D) = 89793000/90207107 ~ 0.99540938, i.e. X' =
[45310607/90207107, 180000107/180414214]^2 ~ [0.502295, 0.997705]^2. Proof: the core is
a B-square concentric with O_j at angle offset at most the half-gap delta with tan delta
<= D, and a square of side beta at the parent’s angle fits in it iff beta (cos delta +
sin delta) <= B, which holds for beta = B/(1 + D) since cos delta + sin delta <= 1 + tan
delta.
So P(O_j) contains the homothetic image of [1/2, 1]^2 about the centre (a, b) with
ratio beta, which is [(1 - beta) a + beta/2, (1 - beta) a + beta] x (same in b); over a,
b in [1/2, 1] the intersection of those images is [1 - beta/2, (1 + beta)/2]^2. This is
sharper than lane-a Theorem B’s conservative inset [d + 0.005, 1 - 0.005]^2 and is what
the refund in section 2 uses.

(e) Every other square is disjoint from int O_j, hence from the open box (1/2, 1)^2_j,
hence every non-occupant core avoids the four open boxes (1/2, 1)^2_j. The seven
non-occupant cores therefore lie in the *box-cut domain* D_box = {admissible cores
avoiding all four open boxes}.

All of (a)-(e) are theorems (lane-a Lemmas 2-4 are proved with numerical replays on
record; (d) is elementary and checked on the family below).

**Theorem 2 (wall lines; elementary, new here).** Fix a wall, say y = 0, and a height c
in (1/2, sqrt 2 - 1/2] (sqrt 2 - 1/2 ~ 0.9142). On the line y = c, int O_1 covers (1/2,
1\) x {c} and int O_2 covers (L - 1, L - 1/2) x {c} = (2.84, 3.34) x {c}. The open chord
of a non-occupant square on that line is disjoint from both and lies in (0, L), so a
chord of length >= 1 lies in [1, L - 1], of length L - 2 = 46/25 = 1.84 < 2. Hence **at
most one non-occupant square per wall has a chord of length >= 1 on the line at depth
c**, and at most four in all.

For a unit square with folded tilt theta in [0, pi/4] and lowest point at height y_min,
the chord at relative height r = c - y_min is r/(sin theta cos theta) for r <= sin theta
cos theta, 1/cos theta on
[sin theta cos theta, cos theta + sin theta - sin theta cos theta], and symmetric above;
so the chord is >= 1 iff r lies in [s c_theta, f(theta)] with f(theta) = cos theta + sin
theta - sin theta cos theta, which decreases from 1 to sqrt 2 - 1/2 on [0, pi/4]. Since
0 <= y_min and c <= sqrt 2 - 1/2 <= f(theta), a non-occupant square whose chord at depth
c is < 1 must have r < sin theta cos theta, i.e. **y_min > c - sin theta cos theta >= c
\- 1/2 > 0**. (The case “entirely below the line” is impossible because y_max >= 1 > c;
“entirely above” is the same inequality.)

**Theorem 3 (at least three deep squares).** In an all-deep packing at L = 96/25 at
least three non-occupant squares Q have, for every wall, distance >= sqrt 2 - 1/2 - sin
theta_Q cos theta_Q >= sqrt 2 - 1 ~ 0.4142 from that wall; for folded tilt theta_Q <=
27.9 degrees (sin 2 theta <= 2 sqrt 2 - 2) the distance is >= 1/2. Proof: for each c in
(1/2, sqrt 2 - 1/2) Theorem 2 leaves at least 7 - 4 = 3 non-occupant squares with no
unit chord on any of the four lines at depth c, each at depth > c - sin theta cos theta
from every wall; there are finitely many triples, so one triple works for a sequence c_n
-> sqrt 2 - 1/2, and the bound passes to the limit.

**Corollary 4 (central box).** [1, L - 1]^2 has side 46/25 = 1.84 < 2 = s(2), so it
contains at most one unit square.
At least two of Theorem 3’s deep squares therefore meet the open frame Omega = [0, L]^2
\ [1, L - 1]^2; since they avoid the open corner boxes and lie at depth
> = sqrt 2 - 1 from every wall, each meets a *gap strip* G_j = {p : depth_j(p) in [sqrt
> 2 - 1, 1)} minus the two open corner boxes on that wall, the region of width 1 - (sqrt
> 2 - 1) ~ 0.586 (width 1/2 for tilt <= 27.9 degrees) between a wall’s depth-1 line and
> the deep zone. This is the reviewer’s “0.84 wall-strip gaps” statement made exact; note
> the count is one-body: it says two squares meet the frame, and the family below puts
> mass exactly 2 (its sixteen tilted central cores) in the frame, so the count itself
> bills the family nothing (section 2.4).

**What is a conjecture.** The reviewer’s census “at most 8 wall squares, at least 3
interior” with *wall square* meaning “meets the open strip of depth 1/2 along a wall” is
not proved here.
Theorem 2 counts unit chords on one line, which misses a strongly tilted
square hugging the wall (theta = pi/4, y_min < (1 - cos theta)(1 - sin theta) ~ 0.086
has no unit chord at c near 1) and a strongly tilted square dipping to depth just under
1/2; excluding both from the same 1.84 gap needs casework over tilt pairs (the
45/45-degree pair is excluded by x-extent, 2.333 > 1.84, but I have not done the general
case).
Theorem 3 is the version that is proved, with depth sqrt 2 - 1 in place of 1/2 for
the most tilted squares.
X-040’s C3 cap is proved only for strips of depth tau <= 0.115. Nothing in section 2
depends on the conjecture: the counting proof uses only Theorem 1(e) and the atom
budgets.

**The family is an all-deep configuration (exact, analyse.out).** The retained 88-family
transported by devtools.transport_ceiling_family (scale 1, --side 96/25, --verify:
proved, max depth 1, total 11, translation (1/100, 1/100)) has: 32 cores meeting an open
corner box, mass 4, exactly 1 per corner, and these are exactly the 32 cores with some
delta_j < 1/2 (the box cut and the deep predicate agree on the family); every one of
them contains all four vertices of X'; their folded tilts are 0 and 0.2637 degrees and
their minimum penetrations lie in [0.02001, 0.0799]. The residual 56 cores have mass 7
(each 1/8), split 32 mid-wall cores of mass 4 (tilts 0 and 1.318 degrees, nearest-wall
distance < 1/2) and 24 central cores of mass 3 (tilts 0.791, 25.668, 29.152 degrees,
eight each; nearest-wall distance >= 0.6561). Eight central cores (the 0.791-degree
inner-corner slot, mass 1) lie inside [1, L - 1]^2; the other sixteen (mass 2) meet the
frame. All 24 central cores overlap (positive area) at least one mid-wall core,
reproducing X-040’s ring-centre relation.
Residual 7 against requirement 7 is BC-366.

## 2. The ring-centre lemma: an explicit atom family with a counting proof

### 2.1 The atom

Three sites, exact rationals in the left gap strip (frame of the left wall x = 0; y is
the container coordinate):

```
s_1 = (101/100, 367/200) ~ (1.01, 1.835)
s_2 = (34/25,   19/10)   ~ (1.36, 1.90)
s_3 = (101/100, 401/200) ~ (1.01, 2.005)
```

The 2-of-3 threshold atom A = (S = {s_1, s_2, s_3}, k = 2, w) charges w to every core
containing at least two of the three sites; budget w floor(3/2) = w (threshold.py’s
theorem: disjoint cores consume disjoint sites).
Its D4 orbit has eight images (the mirror in the wall’s midline y = 48/25 sends s_1 <->
s_3 and s_2 to (34/25, 97/50)), so the orbit costs 8w and Condition 1' is met by
including all eight.
None of the sites lies in any X’_j (x = 101/100 > 0.9977), so the occupant refund on
this orbit is zero.

The sites were found as vertices of the arrangement of the 56 residual cores (1552
vertices, 881 distinct traces, 125 inclusion-maximal traces); the vertex traces dominate
every cell’s trace because cores are closed and the charge is monotone in the trace, so
the maximum over triples of maximal traces is the maximum over all triples of points.
The simple rationals above have the same traces as the maximising vertices (triple.out).

### 2.2 What the family pays: 5/4 against 1 (exact; the reviewer’s 3/2 is not attained)

On the residual family, cores containing at least two of the sites:

- s_1 and s_3 (both at x = 1.01, 0.17 apart vertically): the six left mid-wall cores
  (indices 2, 4 flush at tilt 0; 19, 22, 25, 31 at 1.318 degrees), mass 6/8 = 3/4;
- s_1 and s_2: central cores 44 (29.152 degrees) and 76 (25.668 degrees), centres ~
  (1.335, 1.397) and (1.354, 1.401), the lower-left pocket, mass 1/4;
- s_2 and s_3: their mirror images 42 and 74 at ~ (1.335, 2.443), (1.354, 2.439), the
  upper-left pocket, mass 1/4;
- all three: none.

Charge 3/4 + 1/4 + 1/4 = 5/4 against budget 1, on each of the eight images (D4 symmetry
of the family). For an arbitrary depth-one family the 2-of-3 charge is at most
(depth(s_1) + depth(s_2) + depth(s_3))/2 <= 3/2, with equality iff all three depths are
1 and no core contains one site only; here depth is 1 at each site (the traces have
eight cores each) but the mid-wall cores containing s_1 also contain s_3 and the pairs
are unbalanced (1/4, 3/4, 1/4), so the family pays 5/4, not 3/2. **5/4 is the exact
maximum over every 2-of-3 atom on the residual family** (threshold_max.out), so 3/2 is
not available on this family for any site choice; the reviewer’s figure is X-023’s
generic bound, not this family’s number.

The relation being billed is the one X-040 names: a ring (mid-wall) core against two
tilted central cores that each overlap it, pairwise overlapping through the three sites
with no common point.
The family holds all three roles at fractional weight; a packing can hold at most one
core containing two of the sites near each wall.

### 2.3 The counting proof on the all-deep class

Let mu be a D4-invariant point measure with sites outside the four open boxes (sites
inside the boxes charge no core of D_box and are useless here), and let w >= 0 be the
weight on the eight-image orbit of A (further orbits enter the same way).
Suppose the **covering condition**

```
(C)  every core P in D_box, at every net direction, satisfies
     mu(P) + w * #{images A' of A : P contains >= 2 sites of A'} >= 1,
```

and the **budget condition**

```
(B)  mu([0, L]^2) - sum_j mu(X'_j) + 8 w < 7.
```

Then no all-deep packing exists at L = 96/25. Proof: the seven non-occupant cores are in
D_box (Theorem 1(e)), so each is charged at least 1 by (C); each occupant core contains
X’_j (Theorem 1(d)), so it is charged at least mu(X’_j); the eleven cores are pairwise
disjoint, so the point sites are consumed at most once each and each image of A charges
at most floor(3/2) = 1 core; summing, 7 + sum_j mu(X’_j) <= mu([0, L]^2) + 8w,
contradicting (B). The budget is strictly below 11 in the sense of the task: 4 + (budget
after refund) < 11.

**What a sweep must decide** is (C): the threshold sweep (Condition 5') on the box-cut
domain, i.e. with every core meeting an open box (1/2, 1)^2_j removed from the row set,
with mu and the orbit of A admitted, agreeing on both routes.
(B) is closed-form. Nothing else is open: the counting is Theorem 1 plus threshold.py’s
own budget theorem.

### 2.4 Why the count version bills nothing and the pairwise version bills 1/4 per image

Corollary 4 says two squares meet the frame; a region atom on the frame charges the
family’s frame mass, which is exactly 2 (sixteen tilted central cores at 1/8). A point
or region statistic that a packing respects is satisfied by the family with equality
(Lemma D), and the frame count is one more instance.
The 2-of-3 atom is different in kind: it charges the family 5/4 on a budget of 1, so any
dual family feasible for the language loses at least 1/4 per image of mass on the ten
charged cores, or moves it.
That is a necessary condition for the LP to fall below 7, never a sufficient one; the
fixed-support LP of section 3 is the sufficient-side test.

## 3. Confirm, kill, and the instrument gap

**Confirm reading.** A frozen certificate (point atoms plus the orbit of A and any
further threshold orbits) on the box-cut domain with both routes agreeing on (C) and (B)
holding with the exact refund sum_j mu(X’_j) and X' as in Theorem 1(d) excludes the
all-deep class at 96/25. With T-031’s all-free exclusion that leaves the fourteen mixed
bin vectors (four D4 classes); it is a class exclusion, not a bound on s(11).

**Kill reading.** A depth-one family on D_box, feasible for every point atom (depth <=
1\) and for every 2-of-3 atom in the language (charge <= 1 on every triple of sites,
refunded sites included) with exact total >= 7, accepted by independent_ceiling_reader
and verify_ceiling with a K4-box condition, kills the point-plus-2-of-3 language on the
all-deep class for every site set.
**The transported 88-family is not such a family**: its residual pays 5/4 > 1 on A, so
it does not kill; scaling it by 4/5 restores feasibility for A but drops the total to
28/5 < 7, which decides nothing about the LP.

**The cheapest exact discriminator before any LP**, in order:

1. Done here: the family’s exact maximum 2-of-3 charge, 5/4 (a value <= 1 would have
   been the kill). Also running at the time of writing: the family’s maximum 3-of-4,
   3-of-5 and 2-of-5 charges on the residual, and the 2-of-3 maximum on the full 88
   (appendix).
2. Next (an LP, so not run here; seconds of work): the fixed-support LP on the 56
   residual cores, maximise total weight subject to depth <= 1 on the 125 maximal traces
   and charge <= 1 on every 2-of-3 atom drawn from triples of those traces (317,750
   candidates, separated lazily).
   Value >= 7 kills the single-orbit instrument on this support and says the LP must
   generate new columns to matter; value < 7 says the support is cut and the real LP is
   worth running. X-037’s unconditional analogue on the whole 88-support stopped at 32/3
   < 11, so the prior is that this value is below 7.
3. Then the build below and the class LP.

**Instrument gap (threshold.py / threshold_interval.py, read at HEAD).**

- threshold.py already threads `clip: CornerClip` (the convex free-corner clip) through
  `reduce_to_spans`, `centre_domain`, the worker and the verdict; it takes **no box
  cut**. The all-deep class has no free corner, so the free clip is the wrong
  instrument: what is needed is the *banked* cut, “remove every core meeting the open
  box (1/2, 1)^2_j”. In centre coordinates at one direction the removed centres form the
  open Minkowski sum of the box with the reflected core, a convex octagon, so the kept
  domain is the centre domain minus four open octagons: **non-convex**.
  `reduce_to_spans` takes a per-u-slab v-range of a convex polygon; on this domain that
  range would re-include the octagons’ interiors and the cut would decide nothing.
  The exact route needs a per-cell predicate instead: drop an event cell iff its closure
  lies inside one of the four open octagons (the conjunction mirror of
  `CornerClip.excludes`), keep straddling cells; that is sound (quantifies over a
  superset of D_box) and tight enough, and `_cell_witness` already visits cells one by
  one.
- threshold_interval.py takes no clip of either kind (no reference to corner_clip). It
  needs the box-cut mirror of interval.py’s `clip_excluded`: drop a box iff an
  outward-rounded bound proves every centre in it meets an open box.
- The budget (Condition 2') must become (B): total minus the exact refund sum_j mu(X’_j)
  plus, for a threshold atom, w_a per corner j in which the atom has >= k_a tokens in
  X’_j, with X' = [1 - beta/2, (1 + beta)/2]^2, beta = 89793000/90207107. Certificate
  records need `variant: class` with a `corner_bins` vector (all four deep) and the
  class claim string (the D1 lesson), and decide_threshold_certificate must refuse the
  unconditional claim under the cut.
- Readers: verify_ceiling / independent_ceiling_reader need the K4-box condition (every
  family core avoids the four open boxes) and the count credit 7; the residual-7 control
  in tests/test_fractional_corner_clip.py `_residual` is the template.
  A box cut alone, without the free clip, is what the all-deep class needs; the mixed
  classes need both.
- The separation side (threshold_separation.py) already produces 2-of-3 atoms from a
  dual solution (T-025 used 320 of them); it needs to read the box-cut row set.

Cost: the mirror of the corner-clip build (four to six hours plus review) for the exact
route, the same again for the interval route, then minutes per run.

## 4. Verdict

**INSTRUMENT.** The counting proof is complete and elementary (section 2.3); what is
open is the covering condition (C), which only a sweep on the box-cut domain decides,
and the LP value that precedes it.
The family that obstructs every point covering on this class is cut by the named atom by
exactly 1/4 per image, so the kill reading is not already in hand.
Two corrections to the reviewer’s sketch: the family pays 5/4, not 3/2, and no 2-of-3
atom on this family can pay more; and the instrument needs a non-convex box cut, not a
clip, on both routes, plus the exact refund box X'.

## Numbered findings

1. The all-deep class is exactly stated in section 1; Theorem 1 (a)-(e) are theorems
   from lane-a Lemmas 2-4; the occupant core contains X' =
   [45310607/90207107, 180000107/180414214]^2 (beta = B/(1 + D) = 89793000/90207107),
   sharper than Theorem B’s inset; |phi| < 30 degrees; centre in [h, 1)^2, h in [1/2,
   0.683).
2. Theorems 2-3 (new, elementary): at most one non-occupant square per wall has a unit
   chord on the line at any depth c in (1/2, sqrt 2 - 1/2]; hence at least three
   non-occupant squares lie at depth >= sqrt 2 - 1/2 - sin theta cos theta >= sqrt 2 - 1
   from every wall (>= 1/2 for tilt <= 27.9 degrees).
   The “8 wall squares at depth 1/2” census is a conjecture; nothing in the counting
   proof needs it.
3. Corollary 4: at most one square in [1, 2.84]^2 (s(2) = 2), so at least two deep
   squares meet the frame; the family puts mass exactly 2 in the frame, so this count is
   Lemma-D neutral.
4. The transported family at 96/25 (verify_ceiling proved, total 11): corner mass 1 per
   corner, 32 corner cores each containing X', residual 56 cores of mass 7 = 32 mid-wall
   (mass 4) + 24 central (mass 3); all 24 central cores overlap a mid-wall core; 8
   central cores (mass 1) inside [1, 2.84]^2.
5. The ring-centre 2-of-3 atom: sites (101/100, 367/200), (34/25, 19/10), (101/100,
   401/200), k = 2, budget 1; the family pays 5/4 (six left mid-wall cores through s_1,
   s_3; two lower-left tilted central cores through s_1, s_2; two upper-left through
   s_2, s_3; no core holds all three).
   5/4 is the exact maximum over all 2-of-3 atoms on the residual family; the reviewer’s
   3/2 is the generic bound and is not attained.
6. Counting proof (section 2.3): (C) on D_box plus (B) budget - refund + 8w < 7 excludes
   the class; the sweep decides (C) only.
7. The family does not kill: it violates A. The next discriminator is the fixed-support
   LP on the 56 residual cores with lazily separated 2-of-3 atoms (value >= 7 kills the
   single-orbit instrument on that support).
8. Instrument gap: threshold.py has the convex free clip only; both routes need a
   non-convex box cut (per-cell exclusion in the exact route, provable-inside test in
   the interval route), the refund accounting with X', class claim strings and
   corner_bins, and K4-box in the readers.

## Appendix: exact checks run (all under packing/.venv/bin/python3, Fractions)

- transport_ceiling_family, scale 1, --side 96/25, --verify: proved, max_depth 1,
  vertices 21116, decided_exactly 3860, total 11; translation (1/100, 1/100). 2 s.
- analyse.py: classification above; 0.1 s.
- threshold_max.py on the residual 56: 1552 arrangement vertices, 881 traces, 125
  maximal; max 2-of-3 charge 5/4 (4 s); max 3-of-4 charge exactly 1 = budget (189 s), so
  3-of-4 atoms cut nothing on this family.
  The 3-of-5 and 2-of-5 scans (limited to 60 traces) and the full-88 2-of-3 scan were
  stopped at the 10-minute limit without finishing; they are not needed for the verdict
  (the full family contains the residual, so it pays at least 5/4 on A as well).
- triple.py: the charged cores by class (6 mid-wall, 4 central, 0 corner); simple
  rational sites with identical traces; orbit.py: 8 distinct D4 images, each charging
  5/4, orbit charge 10 against budget 8; no site in X' or in an open corner box; depth 1
  at each site.
- Readers: no reader refused; the class-record readers were not needed because the
  transported file is an ordinary unconditional family record (variant absent), and all
  class arithmetic was done from the JSON directly.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
