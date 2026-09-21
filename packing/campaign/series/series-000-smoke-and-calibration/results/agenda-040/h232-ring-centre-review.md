# H-232 Ring-Centre Review (Session 148, chunk 5)

Status: **ADMIT WITH CORRECTIONS**. An adversarial, read-only Fable review of the
chunk-5 ring-centre derivation with its own code beside it; the corrections are applied
in [H-232](../../../../hypotheses/H-232-n11-all-deep-class-ring-centre-atom.md).

Reviewer: Fable, read-only in /home/user/squares-chunk5 (HEAD 19cdd4f8; the lane’s
report says bfeba117, its parent; the retained family file is identical at both).
Interpreter packing/.venv/bin/python3, exact Fractions.
Own code beside this file: indep.py (family classification, X', atom charge, orbit),
arr.py (own arrangement, max 2-of-3, random sanity search), k34.py (max 3-of-4),
replay-96-25.json (transport replay).

## Verdict

**ADMIT WITH CORRECTIONS.** The mathematics the lane calls theorems is sound (Theorem 1
with the sharpened X', Theorems 2-3, Corollary 4, the counting proof), every family
number reproduces exactly from independent code, and the 5/4 maximality claim is a
proof, not a scan. Three things must change before H-232 is registered: the kill rule
names readers that do not decide the 2-of-3 condition it states (the transported family
itself would pass them); the instrument-gap paragraph describes uncommitted working-tree
code as HEAD; and the fixed-support screen is a full language kill when its value is >=
7, not the weaker reading the report gives it.
The rest is wording.

## What was recomputed (all exact, my own code)

- Condition 4: B(1+D) = 899996306539/900000000000 < 1. D = t_1 = 207107/90000000 is the
  largest half-gap tangent (gaps 2(atan t_{k+1} - atan t_k) decrease in k; the net’s top
  direction is 45.00004 deg, so with the mirror the net covers every square angle).
- beta = B/(1+D) = 89793000/90207107; X' = [45310607/90207107, 180000107/180414214]^2 ~
  [0.502295, 0.997705]^2, strictly inside the open box (1/2,1)^2 (so every D_box core
  misses X' entirely, which is what makes the refund exact on the dual side, see finding
  3).
- Transport replay of ceiling-family-191-50.json (sha256 95cf0647 …) at scale 1, side
  96/25, --verify: placements and net byte-identical to the lane’s family-96-25.json;
  verify_ceiling proved, max_depth 1, total 11, 21116 vertices.
- Classification by a separating-axis test (not the lane’s clipping): 32 cores meet an
  open corner box, mass 4, exactly 1 per corner, each in exactly one box; the same 32
  are exactly the cores with some corner penetration < 1/2; every one contains all four
  vertices of X' (tested in square-frame coordinates, not by cross products); folds 0
  and 0.2637 deg; min penetration 0.02001. Residual 56, mass 7 = 32 mid-wall (mass 4,
  folds 0 and 1.318 deg, nearest-wall distance 0.0175 < sqrt2 - 1) + 24 central (mass 3,
  folds 0.791 / 25.668 / 29.152 deg, min wall distance 0.65613); 8 central cores (0.791
  deg, mass 1) inside [1, L-1]^2; central mass meeting the frame 2.
- Atom A on (101/100, 367/200), (34/25, 19/10), (101/100, 401/200), k = 2: charge 5/4 on
  the residual and on the full 88; depth exactly 1 at each site; 8 distinct D4 images,
  each charging 5/4; no site in any X’_j.
- Own arrangement of the 56 residual cores: 1552 vertices, 881 traces, 125 maximal, max
  depth 1; max 2-of-3 over triples of maximal traces = 5/4 (pair masses 1/4, 3/4, 1/4,
  triple 0), attained by exactly 8 triples (the orbit); 4000 random rational points give
  280 distinct traces, every one dominated by a maximal vertex trace.
- Max 3-of-4 over maximal traces = 1 = budget (4 s with sum-bound pruning; the lane’s
  189 s is the same number).

## Findings

1. **Theorem 1 (a)-(e): sound.** (a) uses Lemma 4 at epsilon = 1/2 < 1 and Lemma 3 at d
   = 1/2 exactly as stated in lane-a (closed T_d, hypothesis g_x + g_y + sin phi <= d;
   meeting the open triangle implies it).
   (c): a = g_x + h with g_x <= delta_j - sin phi gives a <= delta_j + (cos phi - sin
   phi)/2 < 1 and a >= h >= 1/2, so a, b in
   [1/2, 1) as used. (d) re-derived: a beta-square at the parent’s angle, concentric, fits in the B-square at offset delta iff beta(cos delta + sin delta) <= B, and cos delta + sin delta <= 1 + tan delta on [0, pi/4]
   since (cos d - 1)(1 + tan d) <= 0; the homothety of [1/2,1]^2 about (a,b) with ratio
   beta, intersected over a, b in [1/2, 1], is exactly [1 - beta/2, (1 + beta)/2]^2. The
   offset bound tan delta <= D holds because the largest net gap is the one at zero.
   No fix needed. (Sharper boxes are available from the true centre range
   [h, delta_j + (cos phi - sin phi)/2] but nothing here needs them.)
2. **Theorems 2-3 and Corollary 4: sound; one formula in the text is wrong but unused.**
   The single-line chord count is sound for tilted squares: a non-occupant’s open chord
   on y = c is an open interval disjoint from int O_1 and int O_2, so from (1/2,1) and
   (L-1, L-1/2), hence inside one of (0,1/2], [1, L-1],
   [L-1/2, L); length >= 1 forces [1, L-1] of length 1.84 < 2, so at most one per line.
   The “chord >= 1 iff r in [sin t cos t, f(t)]” set is correct and f(t) = cos t + sin t
   \- sin t cos t is decreasing with f(pi/4) = sqrt2 - 1/2 (f' = (cos - sin)(1 - cos -
   sin) <= 0). Since y_min >= 0 and c <= f(t), r > f(t) cannot happen, so a square
   without a unit chord has y_min > c - sin t cos t >= c - 1/2; the bound sqrt2 - 1 and
   the 27.9-degree figure for 1/2 follow.
   **Text error:** the piecewise formula says the chord is 1/cos t on
   [sin t cos t, ...]; the linear piece r/(sin t cos t) runs to r = sin t (where it
   equals 1/cos t), and the flat piece is [sin t, cos t]. Fix the sentence; the “iff”
   that the proof uses is right.
   The limit c_n -> sqrt2 - 1/2 is unnecessary: c = sqrt2 - 1/2 is in the admitted range
   and can be used directly.
   Corollary 4 is correct (s(2) = 2 is classical), and the frame statement is one-body
   as the lane says. The lane’s downgrade of “at most 8 wall squares at depth 1/2” to a
   conjecture is right: the reviewer’s (iii) argued from axis-parallel extents; the
   strongly tilted cases need pairwise casework that nobody has done.
3. **Counting proof (section 2.3): sound, and its refund is exact on the dual side.**
   Line by line: seven non-occupant cores in D_box (Theorem 1(e)) are each charged >= 1
   by (C); each occupant core contains X’_j (1(d)), so is charged >= mu(X’_j); eleven
   pairwise disjoint closed cores (Condition 4 puts each in the interior of its square)
   consume each point site at most once, and an image of A charges a core only if the
   core holds >= 2 of its 3 sites, so at most floor(3/2) = 1 core per image; 7 + sum_j
   mu(X’_j) <= mu(total) + 8w contradicts (B). Answers to the posed questions: an
   occupant core charged by a point atom outside X’_j only raises its charge, and the
   lower bound mu(X’_j) is all the proof uses, so the direction is right; an image whose
   sites split across two cores charges at most one of them, so 8w is right; “at most
   floor(3/2) = 1 core per image” is the upper bound the budget side needs, so it is the
   right direction. The dual reading: the LP’s point atom at a site in X’_j costs 0 after
   the refund, so the dual family must have depth 0 there, which every D_box family has
   automatically because X’_j sits strictly inside the open box.
   So the refund adds no constraint to the kill family, and a threshold atom with >= k
   tokens in an X’_j never charges a D_box core at all (its other sites are too few), so
   the “plus w_a per corner” refund the report’s section 3 asks for is exact but never
   worth having; state it as a subtraction of w_a and note it is idle on D_box.
4. **(C) is what a sound sweep decides, one-sidedly.** With the box cut as “drop a cell
   iff its closure lies inside an open octagon”, every D_box centre, including one on a
   cell boundary, has an adjacent kept open cell whose charge is at most its own
   (monotone trace), so “min over kept cells >= 1” implies (C); a kept-cell minimum
   below 1 does not refute (C) unless the witness is itself in D_box. The H-232
   direction uses only the accepting side, which is correct.
   The lane’s argument that the convex per-slab v-range of reduce_to_spans cannot
   express the cut is right: the kept domain is the centre domain minus four open
   octagons, non-convex.
5. **The 5/4 charge and its maximality: verified and proved.** Domination lemma: for any
   point p the intersection of the closed cores containing p is a nonempty convex
   polygon whose vertices are core vertices or crossings of edges of two different
   cores, all in the arrangement vertex set; any such vertex contains every core of
   T(p). The 2-of-3 charge is monotone in each of the three traces, so the maximum over
   triples of inclusion-maximal vertex traces is the maximum over all triples of points;
   equal traces give charge <= depth <= 1 < 5/4, so distinctness is not a restriction.
   My arrangement reproduces 1552 / 881 / 125 and 5/4, with the 8 orbit triples the only
   maximisers, and the random search found no undominated trace.
   The generic bound (d_1 + d_2 + d_3)/2 <= 3/2 is right, and the reviewer’s 3/2 is
   indeed not attained.
   3-of-4 max = 1 confirmed.
6. **Kill rule in H-232 is not decidable by the instruments it names (must fix).** The
   direction kills with a family “feasible for every point atom and for every all-ones
   2-of-3 atom … that independent_ceiling_reader and verify_ceiling accept with a K4-box
   condition”. Those readers decide depth <= 1 and box avoidance only; neither decides
   the 2-of-3 condition, and the transported family itself (depth 1, residual 7, avoids
   the boxes) passes both while paying 5/4 on A. Fix: name the exact 2-of-3 reader, i.e.
   the arrangement-vertex scan of finding 5 (max 2-of-3 charge over triples of maximal
   traces <= 1), built as a devtool per OR-1 with the domination lemma written beside
   it, and require its verdict in the kill rule.
   The same scan is what makes the kill complete over all site sets.
7. **Fixed-support screen: the report understates it (correct the reading).** Section 3
   says a value >= 7 “kills the single-orbit instrument on this support and says the LP
   must generate new columns to matter”.
   By weak duality (finding 3) plus the domination lemma, a family on the 56-core
   support with depth <= 1 on the 125 maximal traces and 2-of-3 charge <= 1 on every
   triple of those traces is feasible for every point atom and every 2-of-3 atom in the
   plane; total >= 7 is therefore the full H-232 kill for every site set, not a
   statement about one orbit.
   Value < 7 decides nothing (another support may reach 7). Rewrite the reading
   accordingly; it makes the screen the decisive first experiment, which is good news
   for the schedule.
8. **Instrument gap describes uncommitted code as HEAD (must fix wording).** The report
   says threshold.py “already threads clip: CornerClip ... (read at HEAD)”. At HEAD (git
   show HEAD:packing/src/sqpack/fractional/threshold.py) there are zero references to
   CornerClip; the 13 in the worktree file and the 7 in threshold_interval.py are the
   unrelated lane’s uncommitted partial edits (118 and 49 changed lines).
   So the true gap is larger than stated: neither route takes any clip at HEAD, free or
   banked. The substantive analysis (a non-convex box cut with per-cell exclusion on the
   exact route and a provable-inside test on the interval route, the refund with X',
   class claim strings, corner_bins, K4-box in the readers) stands; H-232’s instrument
   field is right to list all of it and instrument_ready: false is honest.
   Add the 2-of-3 reader of finding 6 to that list.
9. **H-232 text.** Claim: “restricted fractional packing value … strictly below 7” names
   the dual (packing) value while the metric is the covering value; they agree on a
   fixed finite site set by LP duality, and across site sets only through the
   kill/confirm pair. Say “covering value” in the claim, or state the language value as
   the infimum over finite certificates, which is what “exists on some named site set”
   already means. The parenthetical class definition in the claim is exactly Theorem 1’s
   and is right; X' and beta are right; “3-of-4 atoms collect at most 1” is right.
   Confirm rule: sound and decidable once the cut is built (finding 4). Kill rule:
   finding 6. Notes say “Session 147 chunk 5”; the lane is Session 148. Cost estimate
   plausible. Evidential status: the report’s “theorem” labels on Theorems 1-3 and
   Corollary 4 are earned (proof-audited here); the family numbers are exact
   computations; (C) is open; the H-232 claim is a hypothesis and is registered as one.
10. **Minor.** Report says the family puts “mass exactly 2 in the frame”; the frame mass
    is 6 (mid-wall 4 plus central 2); the intended and correct statement is mass 2 at
    depth
> = sqrt2 - 1 in the frame, which is what Corollary 4 counts.
> The provenance hash in the lane’s JSON (bfeba117) differs from a replay at HEAD
> (19cdd4f8) by one campaign commit; the family file and output are identical, so no
> consequence.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
