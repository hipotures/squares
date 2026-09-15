# BC303 Floor-Normalized T2: Independent Mathematical Review

Date: 2026-09-13. Reviewer: independent Astra mathematical lane.
Workflow: source-only derivation from the accepted geometry, charge bridge,
registrations, and retained results.
Inspected source: the repository was clean at
`93c5e217aa951522546a7c33b3fc916d33770fe6`.

**PROVE:** subtracting the universal surplus floor from all eleven selected cores gives
a complete two-corner resource criterion with lower thresholds than H-160. Its exact
one-corner conditions are C mass at least `4524132` units and actual S-pair mass at
least `8524147` units.
A sufficient S first-owner filter uses `4524132` units.

**PROVE:** the retained H-161 boundary audit implies that the entire atomic membership
set of Q0 is constant under every sufficiently small admissible rigid-motion
perturbation. **REFUSE:** constancy under unrestricted admissible perturbations, a
universal label-preservation claim, a measured positive normalized-T2 verdict, or an
eleven-parent extension or exclusion.

No source file, registration, or bead was changed.
No charge sweep, atom-mass replay, radius measurement, or other scientific target was
run. The argument below was derived without reading another agent’s proposed
normalization or assuming its thresholds.

## Source Identity and Imported Premises

Every source link in this table resolves within the repository.
Blob IDs were read from the tree at the full inspected commit above.
The frozen atom source, BC303 replay, and wall contract have no Git differences from
source revision `39714308ce2081abbd76624387d134fee4be6deb`.

| Source | Repository-relative path | Git blob at the inspected commit |
| --- | --- | --- |
| Accepted C/S geometry | [X-029](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md) | `8a3200390a1a367c1e4c9449262a2973336688ea` |
| Accepted charge bridge | [charge bridge](../research/research-2026-09-13-bc303-t2-charge-bridge.md) | `84ff589ab204ce511f97cbf03ac9743c1edb9180` |
| Frozen H-160 registration | [H-160](../../../packing/campaign/hypotheses/H-160-bc303-t2-charge-filters.md) | `28359f560a1d5396248d5bd683f09b1f1441d761` |
| Unrun H-160 experiment | [exp-158](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md) | `40f271fa6f2068305f84bfe1d833c888d7022225` |
| H-161 registration and disposition | [H-161](../../../packing/campaign/hypotheses/H-161-bc303-literal-parent-union.md) | `7c33e90c7db62634eb8afad221adef1301647e0b` |
| H-161 experiment | [exp-159](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md) | `1ff0a72a70da41447ffdfe43872590fde967e778` |
| H-161 target receipt | [target receipt](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union.json) | `7543e070db0da199580e3b4cfdcd4fa16da1397a` |
| H-161 independent source audit | [source audit](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union-audit.json) | `445df4e51f7f954dd4a4bde8b51db779e0ae9ad5` |
| Point measure | [BC293 atoms](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json) | `db8abed8f716a4173b47bcfb19f8e045b44513d1` |
| Imported universal floor | [BC303 replay](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md) | `ef7f2f5d6342904082a291f860f5ba732dc52a41` |
| Corner/frame transport | [wall contract](../../../packing/cases/n11_five_dot_cover/wall-containment-contract.md) | `24e00f7cbbbb07c26347e22a4b2b3467cea701fa` |
| T1 core and complete labels | [exp-157 receipt](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-157-bc303-literal-t1-witness.json) | `3debc35bcc6c3d4ad620f02729745cc6a2c433b2` |

The H-161 target receipt and experiment record identify the historical execution commit
`f27c8ec7c8ebeb8a9b369c1c6f7efef4b531c359`, admitted reader commit
`641beab7020570e71680950a92535073c8f698bd`, and source SHA-256
`c30b600d3d35f3851f0595e2c42962bf353721f9e72b0539bd691aec522e876f`. These are retained
provenance, not an assertion that the current documentation head executed that target.

The retained source audit establishes 377 positive rational point atoms and weighted D4
invariance. The numerical premises are

$$
W=4000000,\qquad M=\frac{22524199}{2000000},\qquad
\varepsilon=M-11=\frac{524199}{2000000},\qquad
g=\frac3{800000},\qquad w=\frac{106251}{800000}.
$$

Thus `WM=45048398`, `Wε=1048398`, `Wg=15`, and `Ww=531255`. Here **g is the surplus
above one**, so the mass floor is `1+g`, or `4000015` units.
The BC303 replay’s `corner-pair.out`, lines 1116–1125, reports the complete
181-direction coverage minimum `800003/800000`, with symmetry, arc coverage, and strict
containment admitted.
The JSON declaration alone would not prove this floor.

Strict containment uses

$$
B=\frac{9977}{10000},\qquad D=\frac{207107}{90000000},\qquad
B(1+D)=\frac{899996306539}{900000000000}<1.
$$

The complete floor is imported from that retained proof and replay.
This review does not reverify its full coverage.
It applies to every admitted selected core, including the unused parents’ selected
cores; finite target samples or the literal Q0 result would not support that universal
quantifier.

## The Eleven-Core Account

Fix a hypothetical eleven-parent packing and one coherent admitted selected core `C_i`
strictly inside each parent.
Disjoint parent interiors make those closed cores disjoint.
With `U` the measure outside their union,

$$
U+\sum_{i=1}^{11}(\mu(C_i)-1)=\varepsilon,
\qquad U\ge u_{\rm total}w.
$$

Define the nonnegative normalized surplus

$$
s_g(C_i)=\mu(C_i)-1-g\ge0,
\qquad E=\varepsilon-11g=\frac{1048233}{4000000}.
$$

Then

$$
\boxed{U+\sum_{i=1}^{11}s_g(C_i)=E.}
$$

For a displayed pair of corners with `k` distinct actual owners and `u` globally unowned
marks, the necessary inequality is

$$
\sum_{i=1}^{k}s_g(C_i)\le E-uw.
$$

Consequently the strict universal local inequality

$$
\sum_{i=1}^{k}s_g(C_i)>E-uw \tag{N}
$$

excludes that forced-type conflict from any such packing.
In the original surplus notation `S=Σ(μ(C_i)−1)`, (N) is exactly

$$
S>\varepsilon-uw-(11-k)g.
$$

This charges each of the eleven floors exactly once.
Subtracting `11g` from the right-hand side while leaving `S` unchanged would be unsound.
Nor may one replace the disjoint-core sum by a sum of closed-parent masses: touching
parents can share positive atomic mass.

The permitted roles and owner counts remain X-029’s. Full/full combinations are C,C
(`k=2`), C,S or S,C (`k=3`), and S,S (`k=4`). One-missing combinations are O1,C or C,O2
(`k=2`) and O1,S or S,O2 (`k=3`). The O1,O2 pair is absent under seven-of-eight
ownership. The meaning of an O role in the global contradiction must come from the
packing’s actual incidence: a mark missing from the displayed owners need not be
globally unowned after arbitrary other parents are added.

## Complete Reduction to C and Actual S

Let `D` be the union of the exact forced-0 BL C and S domains in X-029. Every local
configuration includes its actual contained physical parent or simultaneous physical
parents. Let `k(X)=1` for C and `k(X)=2` for S, and define

$$
A_g=\min_{X\in D}\left(\sum_{C_i\in X}\mu(C_i)-k(X)(1+g)\right).
$$

The minimum is attained: `D` is nonempty, and a finite point measure gives only finitely
many charge values even when the geometric domain is not closed.

If `A_g>E/2`, every full/full corner pair has normalized surplus at least `2A_g>E`. For
a one-missing pair, the full corner contributes at least `A_g` and the O owner
contributes at least zero.
Also

$$
2w-E=\frac{14277}{4000000}>0,
\qquad E/2>E-w.
$$

Thus every one-missing pair also satisfies (N). The proof covers every adjacent
realization, because it only uses its actual local components and nonnegative surpluses;
it does not assert that arbitrary adjacent local configurations coexist.

Conversely, suppose `A_g≤E/2`. X-029’s whole-configuration diagonal reflection exchanges
forced 0 and forced 15, preserves charge and the number of owners, and transports
complete signed-frame labels.
Transport the reflected minimizer to the opposite corner.
Every BL-mark parent is separated from every TR-mark parent by the uniform `x+y` gap

$$
2q-2(a+b)-4=\frac{708}{3175}>0.
$$

This follows because every physical unit square has `x+y` width at most two, and the two
BL marks have the same `x+y` value.
Each local S pair must already coexist before transport.
The two corner configurations then coexist and have normalized surplus `2A_g≤E`,
violating the opposite full/full inequality.
Therefore

$$
\boxed{\text{All normalized adjacent and opposite inequalities (N)}
\quad\Longleftrightarrow\quad A_g>E/2.}
$$

This is completeness for the stated local helper, including all eight admitted opposite
role products.
It is not a theorem that a violating local configuration extends to eleven
parents, nor a reduction of adjacent-only failure to an arbitrary product of local
configurations.

## Exact Integer Thresholds

`WE/2=1048233/2=524116.5`. Hence a normalized local surplus passes precisely when it is
at least `524117` integer units.

| Complete local test | Strict inequality before rounding | First passing integer | Last failing integer | Original T2 first passing integer |
| --- | --- | ---: | ---: | ---: |
| C mass `N` | `N−4000015>524116.5` | 4,524,132 | 4,524,131 | 4,524,200 |
| Actual S-pair mass `N1+N2` | `N1+N2−8000030>524116.5` | 8,524,147 | 8,524,146 | 8,524,200 |

The source-bound complete C sweep has exactly the same geometric domain and open-cell
completeness proof at the lower cutoff.
Both axis aliases, closed membership, the forbidden axis edge, exact wall feasibility,
and physical-parent witness replay remain required.
A complete S determination still quantifies over both owners and one simultaneous
realization of their physical parents, with its complete label and boundary predicates.

The charge bridge supplies a cheaper sufficient S test.
Its first-owner strip is a superdomain of every actual forced-0 S first owner, and every
actual second owner has at least `4000015` units.
Therefore

$$
\min_{r,v\in E_r}N_1\ge4524132
\quad\Longrightarrow\quad
N_1+N_2\ge4524132+4000015=8524147.
$$

Equivalently, every violating actual S pair has both `N1,N2≤4524131`. A strip cell at or
below `4524131` only defeats this sufficient filter.
It is not an S refuter without a qualifying second owner and simultaneous-parent replay.
The complete half-budget equivalence uses actual S, not the relaxed first-owner strip
minimum.

H-160 requires C at least `4524200` and the S first owner at least `4524185`. The
normalized sufficient filters use `4524132` for both: reductions of **68** and **53**
integer units respectively.
The complete actual-S cutoff falls by **53** units.
These are strictly lower numerical acceptance requirements.
No charge has been evaluated here to prove that the fixed BC303 minima actually occupy
one of the newly accepted intervals.
A claim of measured benefit would therefore be premature.

As an independent check, direct two-corner total-mass cuts derived from (N) are

$$
\sum_{i=1}^{k}N_i\ge k(4000015)+1048234-u(531255).
$$

| Pair roles | `k` | `u` | First passing total mass |
| --- | ---: | ---: | ---: |
| C,C | 2 | 0 | 9,048,264 |
| C,S or S,C | 3 | 0 | 13,048,279 |
| S,S | 4 | 0 | 17,048,294 |
| O1,C or C,O2 | 2 | 1 | 8,517,009 |
| O1,S or S,O2 | 3 | 1 | 12,517,024 |

The first three cuts equal the sums of the appropriate one-corner minima above.
Compared with the original raw two-corner cuts, they save `(11−k)15` units: 135, 120,
and 105 for `k=2,3,4`. This checks the owner-count dependence and strictness.

H-160 and exp-158 retain their frozen criteria and current unrun status.
The normalized criterion is a separate analytic implication; accepting it does not prove
H-160, change its recorded thresholds, or supply a scientific outcome.

## H-161 Perturbations: What Is Stable

The retained target and independent audit give

$$
Q_0=[0,1]^2,\qquad W\mu(Q_0)=4000015,
$$

with 19 member atoms, no boundary member atoms, and no parent-only atoms beyond the
selected T1 core. Because Q0 is closed, any source atom on its boundary would be a
boundary member. The empty list therefore establishes `supp(μ)∩∂Q0=∅`, including
potential entrants as well as captured atoms.

There is an exact local constancy theorem.
For a parent with centre `z` and physical rotation `θ`, define for each source atom `p`

$$
F_p(z,\theta)=\left\|R_{-\theta}(p-z)\right\|_\infty-\frac12.
$$

Closed parent membership is `F_p≤0`. At the literal pose `z0=(1/2,1/2), θ=0`, every
`F_p` is nonzero. Finitely many atoms give a positive number

$$
\rho=\min_{p\in\operatorname{supp}\mu}|F_p(z_0,0)|>0.
$$

Continuity and finiteness supply one neighborhood in which every `F_p` keeps its sign.
Every rigid-motion parent in that neighborhood has the same 19 member atoms and mass
`4000015/W`. Intersecting the neighborhood with the contained, admissible physical poses
preserves this statement.
No numerical value for `ρ` or a finite claimed pose cell has been measured or certified
here.

Q0 touches the two container walls, so a full ambient neighborhood also contains
infeasible poses. For example, rotating around its fixed centre pushes it beyond a near
wall. Feasible nearby poses nevertheless exist: sufficiently small inward translations
do, and a small angle `θ` can be accompanied by centre
`((cos θ+|sin θ|)/2,(cos θ+|sin θ|)/2)` to keep the two near-wall contacts.
These geometric facts must be checked separately from membership constancy.

The four D4 corner copies have strict inter-parent gap `q−2=46/25`, so that gap also
persists under sufficiently small independent perturbations.
Their masses then remain `4000015/W` each, even without requiring the perturbed tuple
itself to be exactly D4-symmetric.
Both H-161 tests consequently retain their `1048233` units of unused budget throughout a
sufficiently small admissible neighborhood.
This proves local stability of the tests’ failure to exclude, not extension of the
tuple.

Arbitrary-size admissible perturbations can cross atom membership events.
The boundary-free argument proves local constancy only; it cannot support invariance
over all contained poses, an unspecified finite cell, or a full connected component.

## Labels and Physical Corner Roles

Parent mass alone does not determine selected-core ownership or complete labels.
H-161 charges the parent independently of the equipment used inside it.
The retained T1 core is

$$
C_0=[23/20000,19977/20000]^2,
$$

and its complete labels are `{3,4,11,12}`. Both marks are strictly inside, and their
centre-coordinate differences are the two orderings of `(−3129/6350,−1497/6350)`. In the
fixed axis selected-core chart, these strict signs and strict mark containment persist
for sufficiently small centre perturbations.
The least mark-to-core coordinate slack is

$$
\frac{19977}{20000}-\frac{3152}{3175}
=\frac{15479}{2540000}>0.
$$

Thus one can retain this same missing-choice C role and these complete labels locally by
retaining the axis selected core and staying within its admitted physical-angle cell.
This conclusion uses the label and snapping predicates in addition to the atom argument.
Angular-bin labels lie on deliberately closed seams, so changes of selected-core
direction or chart need their own label check; they do not inherit exact label equality
merely from mass constancy.
Replacing the frame representation of the same core, while retaining every admissible
signed frame in the complete label calculation, does not change its complete label set.

In particular, this literal local configuration offers neither 0 nor 15. It is not in
the forced-0 C/S domain defining `A_g`, and sufficiently small perturbations preserving
its stated axis chart keep it outside that domain.
The H-161 equality with the floor therefore supplies no normalized-T2 refuter.
Nor does its local physical feasibility construct seven more parents, preserve a global
normalized contact structure, or settle coherent owner selection.
No global bound follows from this review.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
