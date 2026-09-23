# New Lower Bounds for Packing Unit Squares in a Square

**Draft, 2026-09-14**

## Abstract

Let $s(n)$ denote the side of the smallest square into which $n$ unit squares can be packed
with disjoint interiors, allowing arbitrary rotations. We prove four new lower bounds:

$$s(26) \ge 5.45, \qquad s(29) \ge 5.57, \qquad s(39) \ge 6.5, \qquad s(40) \ge 6.5 .$$

Each improves the best previously recorded value, all of which are due to an unpublished
2000 communication of Green recorded in Friedman's dynamic survey. Our proofs are weighted
fractional unavoidable-set certificates in the sense of Burns and Massaccesi: finite sets of
rational points carrying rational weights, together with a finite verification that every
admissible unit square must cover mass at least one. Every certificate is supplied as a
machine-checkable file and has been independently verified in three computing environments.

As a corollary of the last two bounds, at most 38 unit squares fit in a square of side $6.5$.

## 1. Introduction

Write $s(n)$ for the side of the smallest square containing $n$ non-overlapping unit squares,
where the unit squares may be rotated freely. Exact values are known only for
$n \in \{1,\dots,10, 13,\dots,16, 22,\dots,25, 33,\dots,36, 46,\dots,49, \ldots\}$ —
essentially the cases where a grid packing is optimal, plus the sporadic
values $s(5) = 2+\tfrac{1}{\sqrt 2}$, $s(10) = 3+\tfrac{1}{\sqrt 2}$ (Stromquist),
$s(13) = 4$, $s(46) = 7$ (Bentz), $s(22)=5$, $s(33)=6$ (Bentz).

For every other $n$ the value is bracketed between a construction (an upper bound) and a
proof of impossibility (a lower bound). Upper bounds are plentiful: a packing can be
exhibited and checked. Lower bounds are scarce, because a lower bound must exclude every
packing at once.

The authoritative record of lower bounds is Table 2 of Friedman's dynamic survey DS7, last
revised on 14 August 2009. For the cases treated here it reads

| $n$ | lower bound | source |
|---|---|---|
| 26–27 | $2\sqrt2 + \frac{27 + 2\sqrt{10}}{13} \approx 5.3918$ | Green |
| 28–30 | $2\sqrt2 + \frac{6}{\sqrt5} \approx 5.5117$ | Green |
| 37–39 | $2\sqrt2 + \frac{113 + 10\sqrt3}{37} \approx 6.3506$ | Green |
| 40–41 | $\approx 6.4061$ | Green |

All four entries are attributed to a private communication of Trevor Green from 2000; the
geometric arguments behind them have never appeared. To our knowledge no stronger lower
bound for $n \in \{26, 29, 39, 40\}$ has been published since.

**Theorem.** $s(26) \ge \frac{109}{20}$, $s(29) \ge \frac{557}{100}$,
$s(39) \ge \frac{13}{2}$, and $s(40) \ge \frac{13}{2}$.

**Corollary.** At most $38$ unit squares fit in a square of side $\frac{13}{2}$; that is,
$36 \le N(6.5) \le 38$ where $N(x) = \max\{n : s(n) \le x\}$.

Since $s$ is non-decreasing, $s(39) \ge \frac{13}{2}$ alone yields the corollary. We prove
$s(40) \ge \frac{13}{2}$ independently nonetheless: it improves the recorded bound for
$n = 40$ in its own right, and the two certificates are logically independent, so each is a
check on the other.

## 2. Weighted fractional unavoidable sets

The method generalises Stromquist's unavoidable point sets. Let $K = [0,L]^2$ be the
candidate container.

**Definition.** An *atom* is a point $z \in K$ together with a nonnegative rational weight
$w(z)$. For a region $Q$ the *atomic measure* is
$\mu(Q) = \sum \{\, w(z) : z \in Q \,\}$.

Atoms have no width and block nothing; they are bookkeeping mass. Stromquist's construction
is the special case where all weights are $1$ and every admissible square is required to
contain a marked point. Allowing fractional weights lets a linear program search for them.

Fix $B < 1$ (we use $B = \frac{9977}{10000}$), a *direction net*
$\theta_r = 2\arctan t_r$ for $r = 0,\dots,R$ carried as rational half-angle tangents, and
let $D = \max_r \tan\!\big(\tfrac{\theta_{r+1}-\theta_r}{2}\big)$.

**Proposition.** Suppose a finite weighted atom set on $K$ satisfies

1. *(symmetry)* the weights are invariant under the dihedral group $D_4$ of $K$;
2. *(budget)* $\mu(K) < n$;
3. *(net reach)* $\theta_R \ge \pi/4$;
4. *(shrink)* $B(1 + D) < 1$;
5. *(covering)* every closed square of side $B$ centred anywhere in $K$ and oriented along
   any net direction covers mass at least $1$.

Then $n$ unit squares do not fit in $K$, and hence $s(n) \ge L$.

*Proof.* Suppose $n$ unit squares $U_1,\dots,U_n$ lie in $K$ with disjoint interiors. A
square is unchanged by a quarter turn, and a diagonal reflection reduces its angle into
$[0,\pi/4]$; by (1) this reduction changes no covered mass. Let $U_i$ have reduced angle
$\alpha_i$ and let $\theta_{r(i)}$ be the nearer endpoint of the net interval containing
$\alpha_i$, so the angular error $d_i$ satisfies $\tan d_i \le D$ by (3).

Place inside $U_i$ the closed square $P_i$ of side $B$, concentric with $U_i$ and oriented
along $\theta_{r(i)}$. Measured along $U_i$'s own axes, $P_i$ reaches from the shared centre
by at most
$$\tfrac{B}{2}(\cos d_i + \sin d_i) \;\le\; \tfrac{B}{2}(1 + D) \;<\; \tfrac12$$
using (4), so $P_i$ lies strictly inside the interior of $U_i$. The interiors are pairwise
disjoint, hence the closed squares $P_1,\dots,P_n$ are pairwise disjoint and no atom is
counted twice. By (5), $\mu(P_i) \ge 1$ for each $i$. Since all weights are nonnegative,
$$\mu(K) \;\ge\; \sum_{i=1}^n \mu(P_i) \;\ge\; n,$$
contradicting (2). Any packing in a smaller container also fits in $K$, so $s(n) \ge L$. $\square$

The shrink step (4) is what bridges the continuum of orientations to a finite net: it is not
a sampling argument. Nonnegativity does two jobs — it makes the counting chain valid, and it
ensures that gaining an atom on a cell boundary cannot lower a covered mass.

## 3. Certificates

Our four certificates use $B = \frac{9977}{10000}$ and the net
$t_r = \frac{83r}{40000}$, $r = 0,\dots,200$, so that
$D = \frac{83}{40000} = 0.002075$ and $B(1+D) = 0.9997702\ldots < 1$, while
$t_{200} = \frac{83}{200} = 0.415 > \tan(\pi/8) = 0.414213\ldots$, giving
$\theta_{200} = 45.0769\ldots^\circ > \pi/4$.

| $n$ | $L$ | atoms | $D_4$ orbits | total mass $\mu(K)$ | budget |
|---|---|---|---|---|---|
| 26 | $109/20$ | 1376 | 179 | $\frac{646393601}{25000000} = 25.855744$ | $< 26$ |
| 29 | $557/100$ | 748 | 100 | $\frac{453011}{15625} = 28.992704$ | $< 29$ |
| 39 | $13/2$ | 2724 | 362 | $\frac{481487971}{12500000} = 38.519038$ | $< 39$ |
| 40 | $13/2$ | 1892 | 250 | $\frac{975019903}{25000000} = 39.000796$ | $< 40$ |

Atoms lie on a dyadic grid of spacing $2^{-j}$ refined locally by column generation,
together with their reflections $L - x$; their coordinate denominators therefore divide
$2^{j}$ times the denominator of $L$ (at most $320$ for $n=26$, $400$ for $n=29$, $128$ for
$n=39$ and $256$ for $n=40$). Weights are rationals with denominator $10^6$ for $n = 29$ and
$10^8$ for the other three. Conditions 1–4 are short exact computations; all four have been
checked with rational arithmetic. Condition 5 is the large finite lemma and is discussed next.

## 4. Verifying the covering condition

At a fixed net direction the centre of the inner square ranges over a two-dimensional
continuum. We decide condition 5 by branch and bound on the set of admissible centres.

For a box $R$ of centres and a fixed direction, an atom is covered by *every* centre in $R$
exactly when its projections onto the two square axes lie within the corresponding shrunken
intervals; this is a conjunction of four linear inequalities. If the atoms passing this test
already weigh at least $1$, every centre in $R$ satisfies condition 5 and the box is
discarded. Otherwise the box is split along its longer side. A box that reaches side
$10^{-7}$ without being discharged is reported as a failure.

The arithmetic is float64 with an explicit margin. Every geometric comparison is shifted by
$\varepsilon = 10^{-9}$ and the mass threshold is $1 + 10^{-9}$. All coordinates have
magnitude below $100$ and each compared quantity is formed by at most six floating-point
operations, so its absolute rounding error is below $10^{-13} \ll \varepsilon$; the mass is a
sum of at most $10^4$ nonnegative terms below $1$, so its rounding error is below
$10^{-11} \ll 10^{-9}$. Hence every box the sweep accepts is genuinely covered. Weights are
rounded *up* to multiples of $10^{-8}$, so rounding can only add mass, which is the safe
direction for condition 5 and is accounted for in condition 2 by using the rounded total.

Box counts for the four certificates:

| $n$ | boxes examined | failures |
|---|---|---|
| 26 | 4 811 681 | 0 |
| 29 | 2 524 711 | 0 |
| 39 | 8 409 303 | 0 |
| 40 | 7 531 281 | 0 |

## 5. How the certificates were found

The search is a covering linear program with row and column generation. Choose a finite site
set $\mathcal X$ (initially a grid of spacing $1/16$, reduced to $D_4$ orbit representatives)
and a finite pose set $\mathcal P$. The program is
$$\min \sum_{x \in \mathcal X} w(x) \quad\text{s.t.}\quad
\sum \{\, w(x) : x \in Q \,\} \ge 1 \ \ \forall Q \in \mathcal P, \qquad w \ge 0 .$$

*Row generation.* The branch-and-bound sweep of §4 is used as a separation oracle: poses whose
covered mass falls below $1$ are added as new rows. Adding rows can only raise the objective.

*Column generation.* The dual assigns weights $y(Q)$ to poses. For a site $x$ not in
$\mathcal X$ the reduced cost of its $D_4$ orbit $O$ is $|O| - \sum_Q y(Q)\,|O \cap Q|$;
orbits with negative reduced cost are added. Adding columns can only lower the objective.

A run is abandoned as soon as the LP optimum reaches $n$, since further rows only raise it.
This test is cheap and decided most of our failed attempts within minutes. We record the
side lengths ruled out this way in an appendix, as they delimit what the method can reach
with a given atom grid.

Three implementation details mattered.

- **Row margin.** The LP rows demand mass $\ge 1 + 10^{-5}$ and use a shrink of
  $5 \times 10^{-4}$ relative to the verifier's test. Without this, solver tolerance and the
  gap between "covered at the centre" and "covered throughout a leaf box" produce spurious
  holes that the oracle re-reports forever.
- **Degeneracy is not the obstacle.** The covering polytope has many optimal vertices, and we
  expected that choosing an interior point of the optimal face would spread the mass and
  reduce residual holes. Measured on a stalled instance the opposite held: the simplex vertex
  left 32 holes, an interior point left 128, and maximising total covered mass subject to a
  slightly relaxed budget left 3840. The sharp vertex is the better choice.
- **Orbit growth.** Once the atom set exceeds roughly 4000 orbits, iterations slow by an order
  of magnitude and holes stop shrinking. We cap the orbit count and stop a run whose objective
  has not moved for 40 iterations.

## 6. The corollary and half-integer sides

Let $N(x) = \max\{\, n : s(n) \le x \,\}$. A $k \times k$ grid always fits in a square of side
$k + \tfrac12$, so $N(k + \tfrac12) \ge k^2$. Whether the inequality is ever strict, and for
which $k$ first, appears not to have been studied.

Our bound $s(39) \ge 6.5$ gives $N(6.5) \le 38$, since $s$ is non-decreasing. The $6 \times 6$
grid gives $N(6.5) \ge 36$. The remaining question for $k = 6$ is therefore whether 37 or 38
unit squares fit in side $6.5$; the best known packings need $6.5986$ and $6.7071$
respectively, so no current construction achieves either.

The independent certificate for $n = 40$ is consistent with this and sharpens the record for
that case, but adds nothing to the corollary.

Two remarks place this in context.

First, no known impossibility result forbids $N(k+\frac12) > k^2$ for moderate $k$. Packing
$k^2+1$ unit squares in side $k+\varepsilon$ wastes area $W = 2k\varepsilon + \varepsilon^2 - 1$.
The Roth–Vaughan bound $W(x) = \Omega\big((x\lVert x\rVert)^{1/2}\big)$, with
$\lVert x \rVert$ the distance to the nearest integer, requires
$2k\varepsilon - 1 \ge c\sqrt{k\varepsilon}$ for the implied constant $c$. Writing
$u = k\varepsilon$ this reads $2u - c\sqrt u - 1 \ge 0$, so
$u \ge \big(\tfrac{c + \sqrt{c^2+8}}{4}\big)^2$. Even for $c = 2$ this gives
$u \ge 1.87$, hence $\varepsilon \ge 1.87/k$, which is below $\tfrac12$ already for
$k \ge 4$. The obstruction to $N(k+\frac12) > k^2$ is therefore constructive rather than
information-theoretic: the known constructions, not the known impossibility results, are what
stop at excess $0.5355$.

Second, the constructions that achieve the record excess
$s(k^2+1) - k = \frac{5}{\sqrt2} - 3 \approx 0.5355$ for $k \ge 8$ cannot do better. These are
Göbel's family: a $b \times b$ block of squares tilted $45^\circ$ centred in a container of
side $a + 1 + b/\sqrt2$, holding $2a^2 + 2a + b^2$ squares, valid when
$a - 1 < b/\sqrt2 < a+1$, possibly extended by whole rows and columns.

**Proposition.** No member of Göbel's family, extended by rows and columns, packs $k^2 + 1$
unit squares into a square of side less than $k + \frac12$.

*Proof.* Write $S = a+1+b/\sqrt2$, $N = 2a^2+2a+b^2$, $k = \lfloor S \rfloor$ and suppose
$S - k < \frac12$. If $k = 2a+1$ then $a \le b/\sqrt2 < a + \frac12$, so
$b^2 < 2a^2 + 2a + \frac12$ and $N < 4a^2+4a+\frac12$, giving $N \le k^2 - 1$. If $k = 2a$
then $a - 1 \le b/\sqrt2 < a - \frac12$, so $b^2 < 2a^2 - 2a + \frac12$ and
$N < 4a^2 + \frac12$, giving $N \le k^2$. Adding a row and a column increases $k$ by one and
$k^2+1$ by $2k+1$, which is exactly the number of squares added, so the deficit is preserved. $\square$

A numerical search over $b \le 400$ confirms this: the best case falls one square short, at
$(a,b) = (9,12)$ with 324 squares against 325, and again at $(a,b) = (50,70)$ with 10000
against 10001.

We also modelled a more general family — a block of $w \times \ell$ squares at an arbitrary
tilt, with the axis-parallel remainder filled optimally by integer programming — and scanned
tilts from $5^\circ$ to $45^\circ$ for $k \le 12$ at $S = k + \frac12$. The best counts were
$k^2$ for $k = 4,5,6$ and $k^2 - 3$ or worse for $k \ge 7$. The single-tilt band does not
break the wall either.

## 7. Reproducibility

Each certificate is a JSON file listing every atom as an exact rational triple
$(x, y, w)$ together with $n$, $L$, $B$ and the net. The verifier reads the file, checks the
$D_4$ symmetry of the atom set, sums the mass exactly with rational arithmetic, checks the net
and shrink conditions exactly, and runs the branch-and-bound sweep of §4. A single
verification takes 20–60 seconds.

Each certificate has been verified in three environments: on the machine that produced it
(both from the internal binary format and from the JSON), and on a second machine with a
different CPU architecture and different NumPy and SciPy versions, from the JSON alone.

## Appendix: side lengths ruled out by the LP optimum

For these $n$ and $L$ the covering LP optimum reached $n$ or more, so no certificate of this
form exists on the atom grid used. This delimits the method rather than the problem.

| $n$ | $L$ | LP optimum |
|---|---|---|
| 26 | 5.48, 5.465 | 26.08, 26.03 |
| 29 | 5.58 | 29.04 |
| 37 | 6.45, 6.40, 6.30 | 38.63, 38.03, 37.06 |
| 39 | 6.55 | 39.09 |
| 40 | 6.55 | 40.01 |
| 41 | 6.60 | 41.94 |
| 50 | 7.45, 7.38 | 50.88, 51.77 |
| 52 | 7.45, 7.40, 7.36 | 52.57, 52.20, 52.69 |
| 53 | 7.55, 7.50, 7.42 | 53.55, 53.16, 53.35 |
| 54 | 7.45 | 54.43 |
| 55 | 7.60, 7.52, 7.48 | 55.41, 55.54, 55.02 |

## References

- W. Bentz, *Optimal packings of 13 and 46 unit squares in a square*, Electron. J. Combin.
  17 (2010), #R126.
- W. Bentz, *Optimal packings of 22 and 33 unit squares in a square*, arXiv:1606.03746.
- S. Burns, *Proposing a better lower bound for n = 17 square packing*, 2026.
- E. Friedman, *Packing unit squares in squares: a survey and new results*, Electron. J.
  Combin., Dynamic Survey DS7, version of 14 August 2009.
- F. Göbel, *Geometrical packing and covering problems*, in Packing and Covering in
  Combinatorics (A. Schrijver, ed.), Math. Centre Tracts 106 (1979), 179–199.
- G. Massaccesi, *Another better lower bound for n = 17 square packing*, 2026.
- H. Nagamochi, *Packing unit squares in a rectangle*, Electron. J. Combin. 12 (2005), #R37.
- K. F. Roth and R. C. Vaughan, *Inefficiency in packing squares with unit squares*,
  J. Combin. Theory Ser. A 24 (1978), 170–186.
- W. Stromquist, *Packing 10 or 11 unit squares in a square*, Electron. J. Combin. 10 (2003),
  #R8.
