# BC303 Parent-Union Lemma: Independent Mathematical Review

Date: 2026-09-13. Bead: `think-utyw`. Workflow: bounded source-distinct mathematical
review of the parent’s W3 strategy analysis.

**Disposition: ACCEPT inequality (P), the one-parent and four-parent integer thresholds,
and the four-corner transport, with the literal nonextension scope stated below.** No
Blocker or High mathematical finding was found in this bounded review.
This accepts an analytic implication and a prospective discriminator.
At this review’s T1 cutoff, the target parent mass had not been computed.

The reviewed proposal is [X-030][proposal], specifically “Core surplus alone still
admits four bad corner owners” and “Charge the parent union and its unavailable atoms.”
Source files were inspected in the isolated T1 branch at clean HEAD
`375c7bc1d49c506636a5abf71d37a8455888ff42`. No source or PR file was edited.

## Source Premises and Independent Checks

The [raw BC303 measure][measure] is a finite nonnegative **point measure** on
$K=[0,96/25]^2$. Its working bytes equal its committed bytes at the inspected HEAD; the
source blob is `db8abed8f716a4173b47bcfb19f8e045b44513d1`. An independent
standard-library rational reconstruction, without importing the production reader,
confirmed all 377 sites are distinct, lie in $K$, and have positive weight.
Applying all eight affine container symmetries to every site and its weight confirmed
weighted D4 invariance.
Direct summation and denominator arithmetic gave

$$
W=4{,}000{,}000,\qquad
M=\frac{22524199}{2000000},\qquad
WM=45{,}048{,}398,\qquad
\varepsilon=M-11=\frac{524199}{2000000}.
$$

The universal floor is an **imported retained coverage result**, rather than a
consequence of the raw JSON’s `least_cell_mass` declaration or of the one T1 core.
The [BC303 retained replay, lines 1116–1125][bc303] reports a complete 181-direction
exact sweep with minimum $800003/800000$, together with the symmetry, arc, and
strict-containment conditions.
Thus every admitted selected core satisfies

$$
\mu(C_i)\ge 1+g,\qquad
g=\frac3{800000},\qquad W(1+g)=4{,}000{,}015.
$$

This review did not rerun that full sweep.
It independently checked its rational containment constants from the source:

$$
B=\frac{9977}{10000},\quad
D=\frac{207107}{90000000},\quad
B(1+D)=\frac{899996306539}{900000000000}<1,
$$

with strict slack $3693461/900000000000$. The nearer-net selection argument therefore
places a closed concentric core strictly inside every physical unit parent, including
parents whose physical angles are between net directions.
The reflected direction choices are admitted through weighted symmetry.
This is the strict selection used by the [structural definitions][helpers] at lines
26–88 and the [routing domain][routing] at lines 30–61.

[T-026, lines 34–92][t026] supplies the general strict-core counting proof: choose a
core separately for each parent and pull reflected choices back.
Since the selected cores lie in disjoint parent interiors, they are disjoint as closed
sets. T-026’s own 584-point and 320-threshold-atom certificate has different constants
and a different budget.
Its numerical certificate must not be substituted for BC303 here.
In particular, a threshold charge is not an additive measure on parent unions; (P) uses
BC303’s point measure.

The [T1 retained receipt][receipt] records source revision
`39714308ce2081abbd76624387d134fee4be6deb` and implementation revision
`81898608213774dcab99a16f776000421b9083ac`. Those are historical identities, not the
current documentation HEAD. The [final T1 review][t1review] explains the source and
executing-reader authentication and the subsequent port.
This audit reconstructed all 377 retained core-membership rows directly from the raw
source atoms using the literal coordinate bounds, checking each source index, point,
weight, integer weight, membership Boolean, and coordinate slack.
All rows agreed. The known core

$$
C_0=[23/20000,19977/20000]^2\subset\operatorname{int}[0,1]^2
$$

captures 19 atoms of total mass $800003/800000$. Every captured atom is strict, with
smallest coordinate slack $28671/24460000$. This check concerns the retained T1 core
only; no atom membership in the full parent was evaluated.

## Proof of the Parent-Union Inequality

Assume eleven closed unit-square parents $Q_1,\ldots,Q_{11}$ lie in $K$ with pairwise
disjoint interiors. Choose one coherent admitted collection of strict cores
$C_j\subset\operatorname{int}Q_j$ satisfying the BC303 floor.
For any set $I$ of $k$ distinct parent indices, put $Q_I=\bigcup_{i\in I}Q_i$.

The geometric step in the proposal is valid even when parents share edges or vertices.
Suppose $x\in Q_i\cap\operatorname{int}Q_j$ with $i\ne j$. An open ball about $x$ lies
in $\operatorname{int}Q_j$. Every point of a closed full-dimensional square is a limit
of its interior points, so this ball meets $\operatorname{int}Q_i$. That contradicts
disjoint parent interiors.
Hence

$$
Q_i\cap\operatorname{int}Q_j=\varnothing\qquad(i\ne j).
$$

Consequently $Q_I$ is disjoint from every $C_j$ with $j\notin I$, and those outside
cores are pairwise disjoint.
All these sets lie in $K$. Nonnegative finite additivity gives

$$
\mu(Q_I)+\sum_{j\notin I}\mu(C_j)\le M.
$$

Substituting $M=11+\varepsilon$ and the $11-k$ lower bounds $1+g$ yields

$$
\boxed{\mu(Q_I)-k+(11-k)g\le\varepsilon.}\tag{P}
$$

The proof works for $0\le k\le11$ and needs no contact normalization, owner labels, or
jointly selected witness poses beyond the actual parents in the hypothetical packing.
In fact, the cores of the $k$ charged parents need not be fixed: the necessary condition
depends on their full geometric union and the existence of admitted cores for the other
parents.

For the proposal’s unused-mass interpretation, set
$U_I=Q_I\setminus\bigcup_{i\in I}C_i$. The disjointness just proved implies that $U_I$
meets no selected core, inside or outside $I$. Also
$\mu(Q_I)=\sum_{i\in I}\mu(C_i)+\mu(U_I)$. Thus that interpretation counts the same
resource exactly. Legal parent contacts can carry positive atom weight, so replacing
$\mu(Q_I)$ by $\sum_{i\in I}\mu(Q_i)$ would in general be invalid.

If a set of marks $Z$ is proved unowned by **every selected core of the same packing**,
$Q_I\cup Z$ can replace $Q_I$. A mark merely unowned by the disclosed local owners does
not satisfy this premise.
The union is necessary when an unowned mark already lies in $Q_I$.

## Four-Corner Transport and Exact Thresholds

The admitted local charts use corner order BL, BR, TL, TR and maps

$$
(F_c)_c=(I,H,V,HV),\quad H(x,y)=(q-x,y),\quad V(x,y)=(x,q-y),
\quad q=96/25.
$$

These are the maps in the [wall-containment contract, lines 57–74][wall]. The four
images of $Q_0=[0,1]^2$ use the intervals $[0,1]$ or $[q-1,q]$ in each coordinate.
Any distinct pair differs in at least one coordinate interval, whose gap is
$q-2=46/25>0$. They are therefore disjoint even as closed sets.
Weighted D4 invariance gives

$$
\mu\!\left(\bigcup_cF_c(Q_0)\right)=4\mu(Q_0).
$$

Each transported core remains concentric, strict, and admitted.
In the corresponding reflected local chart it co-owns both marks and has the original
labels $\{3,4,11,12\}$. Directly at BL, the mark-to-centre coordinate differences are
$(-3129/6350,-1497/6350)$ and the swapped pair.
Both are strictly southwest, so the west-first proper frame yields closed bins 3 and 4
for each mark. Transporting the whole corner chart preserves this calculation.
Reflections must transport the ordered frame as specified by the
[contract, lines 101–113][wall]; carrying a global frame’s numerical label unchanged
would not be justified.

The four cores therefore have total surplus $4g$, and the seven omitted core floors
would give only $11g=33/800000$. Independently,

$$
\varepsilon-11g=\frac{1048233}{4000000}>0.
$$

This establishes the proposed failure of the resource test that uses only those core
surpluses and the omitted floors.
It does not construct the omitted seven parents.
The [routing analysis, lines 382–442][routing] explicitly distinguishes this kind of
four-parent realization from an eleven-parent packing and from its normalized domain.

Let $N=W\mu(Q_0)$. It is an integer because $W$ is the least common multiple of the
source weight denominators.
The following computations use only source constants; they do not evaluate $N$.

| Frozen parents | Necessary inequality | Largest integer $N$ surviving this inequality | First rejecting integer $N$ |
| --- | --- | ---: | ---: |
| One literal $Q_0$ | $N\le45{,}048{,}398-10(4{,}000{,}015)=5{,}048{,}248$ | 5,048,248 | 5,048,249 |
| Four separated corner copies | $4N\le45{,}048{,}398-7(4{,}000{,}015)=17{,}048{,}293$ | 4,262,073 | 4,262,074 |

At the first one-parent rejection, the total exceeds the budget by one integer unit.
At the first four-parent rejection it exceeds the budget by three units:
$4(4{,}262{,}074)=17{,}048{,}296$. The preceding four-parent integer is one unit below
the budget. Thus neither ceiling nor strictness is off by one.

## Accepted Scope and Boundary Limits

A measured $N\ge5{,}048{,}249$ would exclude an eleven-parent packing containing the
exact physical square $Q_0$ at the specified container coordinates.
A measured $N\ge4{,}262{,}074$ would exclude an eleven-parent packing containing all
four specified corner copies simultaneously.
The second conclusion alone does not exclude one such parent.
These conclusions depend on the imported universal BC303 floor and strict selection, and
survive a different admissible equipment choice for those same literal parents: (P) does
not charge their chosen cores.

A value below a rejection threshold establishes only that the corresponding necessary
inequality survives.
It supplies neither an extension nor a counterexample to routing.
In particular, accepting (P) is not a new bound on $s(11)$.

Closed parent membership is correct for the literal test, including atom sites on a
parent boundary: no outside strict core can own such a site.
It is not automatically stable under parent perturbation.
To exclude a pose cell, prove a lower bound for the parent **union** throughout that
cell, or exhibit a fixed set of distinct source atoms contained throughout it.
A strictly interior captured subset has positive geometric margin and persists in some
sufficiently small neighborhood because the support is finite.
To turn that fact into a useful exclusion, its weight must still beat the appropriate
threshold and the neighborhood must cover the stated cell.
Pointwise boundary atoms alone give no such neighborhood certificate.

Global local availability still requires a complete domain for every missing-choice
owner pattern that can occur in a physical eleven-parent packing, including split
ownership, missing marks, continuous parent angles, seams, and every admitted signed
frame.
Core/owner choices must be coherent within each packing; a changed choice for each
separate constraint does not prove a shared selection.
If S1 is used, selection occurs after normalization and the named wall chart must be
retained. These are the quantifiers in the
[routing analysis, lines 30–107 and 335–377][routing]. None is discharged by one literal
parent-union scan.

T-026’s exact lower bound $s(11)\ge C$ remains unchanged.
Its strict rational dilation family excludes sides below $C$; [lines 177–186][t026] do
not provide a certificate at $C$ or establish $s(11)>C$. Nothing in (P) alters that
endpoint status.

[proposal]: ../../../packing/campaign/explorations/X-030-n11-post-t1-proof-obligations-draft.md
[measure]: ../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json
[bc303]: ../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md
[helpers]: ../research/research-2026-09-10-x027-structural-helpers.md
[routing]: ../research/research-2026-09-12-n11-selection-routing-first-principles.md
[t026]: ../../../packing/cases/n11_threshold_certificate/t-026-verifiable-claim-dilation-limit.md
[receipt]: ../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-157-bc303-literal-t1-witness.json
[t1review]: review-2026-09-13-n11-bc303-t1-reader-final-math.md
[wall]: ../../../packing/cases/n11_five_dot_cover/wall-containment-contract.md

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
