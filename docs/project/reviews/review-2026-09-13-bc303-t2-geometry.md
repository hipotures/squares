# Independent Review of the BC303 T2 Geometry Reduction

Date: 2026-09-13. Bead: `think-8057`. Workflow: W2 independent mathematical review of
the bounded W3 analysis.
The original W2 review was read-only.
This durable copy accompanies the X-029 draft and the maintained geometry control.
No BC329 run, positive calibration, atom scan, or charge evaluation was made.

**ACCEPT the C geometry reduction, the S first-owner strip, and the rational S
feasibility control.
REFUSE the C paragraph asserting that an equality witness may require an irrational
parent ray.** The correction below strengthens witness representability without changing
the proposed feasibility test.
T2 and global owner routing remain undecided.

The review evaluated the original read-only analysis.
Its corrected text is retained in
[the X-029 draft](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md),
together with the
[maintained exact control](../../../packing/cases/n11_five_dot_cover/bc303_t2_geometry_control.py)
and [focused test](../../../packing/tests/test_bc303_t2_geometry_control.py).
The reviewed source tree was inspected at `7e4d2487f586e4200b1261cfa286f37ebda99c49`.
The original review’s Git comparison found no changes from frozen revision
`39714308ce2081abbd76624387d134fee4be6deb` in the sixteen imported paths listed in the
preregistration’s source table.
This includes the source measure, but the measure was not parsed or reverified here.

The source definitions checked directly were the
[sector proof](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-031/proofs/corner-owner-sector-footprints.md),
[snapping proof](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-032/proofs/fixed-cover-transfer-review.md),
[corner and proper-frame transport contract](../../../packing/cases/n11_five_dot_cover/wall-containment-contract.md),
[direction manifest generator](../../../packing/devtools/owner_footprints.py),
[source-cell construction](../../../packing/src/sqpack/fractional/adaptive.py), and
[global selection definition](../research/research-2026-09-12-n11-selection-routing-first-principles.md).
The reviewed preregistration and preceding mathematical review under `think-8v6c` supply
the exact closed equipment convention and imported BC303 coverage floor.
The underlying
[BC303 report](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md)
and
[source measure](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json)
are retained in the campaign.
The T1 reader review under `think-3jsz` accepted its disclosed nineteen-atom arithmetic
but refused instrument admission because retained atom rows were not authenticated
against source atoms and cross-checkout execution misidentified the reader revision.
The owner-requested V3 planning source remains unresolved under `think-i1fr`; this
review does not claim V3 alignment.

## Claim Dispositions

| Claim | Disposition | Reason and scope |
| --- | --- | --- |
| Complete proper signed frames and closed bins | ACCEPT | Four signed first rays exhaust the frames. A zero coordinate admits every matching frame; an angular endpoint belongs to both bins. |
| Source aliases and D4 transport | ACCEPT | There are 362 charts, 361 orientations, and 1444 signed rays. Reflection exchanges proper frame axes and transports the source reflection flag; both axis aliases remain. |
| The 182-chart bin-0 manifest | ACCEPT | Exactly both axis aliases, unreflected indices 1–179, and reflected index 180 qualify. The other 180 charts have no bin-0 ray. |
| Non-axis C rectangle | ACCEPT | The exact domain before parent containment is `0 <= x <= h-delta(c-s)`, `0 <= y <= h`. These rays cannot supply bin 7. |
| Axis C strict upper edge | ACCEPT | Label 15 occurs exactly when `y >= delta`; forced 0 requires `y < delta`, including exclusion of the two upper vertices. |
| C single-wall parent projection | ACCEPT | Bottom and far walls are inactive on this domain. The lower folded endpoint minimizes parent extent, so parent existence is exactly `a+cx-sy >= e_j`. |
| Rational event-stratum feasibility rule | ACCEPT | Positive maximum slack gives a feasible relative-interior point; negative slack excludes the stratum. At equality the unique maximizing corner must belong to the stratum. |
| Irrational parent witness required by a C equality case | REFUSE | A rational maximizing value equal to `e_j` makes the lower-endpoint parent ray rational. See the correction below. |
| S first-owner strip and its inactive walls | ACCEPT | Exclusion of the second mark is precisely `h-delta(c-s) < x <= h`. Every point in the strip has clearance greater than `1/sqrt(2)` from every container wall. |
| Rational S configuration | ACCEPT | Both cores have the asserted single-mark incidence and labels; their source-matching parents are contained and strictly separated. This proves feasibility only. |
| Two physical axis parents cannot realize S | ACCEPT | Their centre coordinates lie in an interval of length `2518679/2540000 < 1`, forcing interior overlap in both projections. Non-axis physical angles in axis source cells remain outside this exclusion. |
| Opposite rolewise product and combined T2 equivalence | ACCEPT | Opposite parent groups have strict separation `708/3175`; symmetry gives the same full-pair minimum for both forced types. The aggregate consists of eight products. |
| General complete S decision formulation | ACCEPT | Shared centres and parent angles with complete separating-axis alternatives give the stated semialgebraic formulation. No executable complete solver is admitted here. |
| C or S threshold determination, a charge minimum, adjacent-only T2, opposite T2 | REFUSE | No charge or complete threshold enumeration was evaluated. This refusal records absent evidence, not a scientific rejection. |
| Global availability, global owner routing, or a changed n11 bound | REFUSE | The required theorem over actual eleven-parent packings is still absent. Local geometry and local helper outcomes cannot replace it. |

## Exact Geometry Checks

For the unique bin-0 ray `r=(c,s)`, write `z=m1+xr+yJr`. Then

$$
z-m_2=(x+\delta(c-s))r+(y-\delta(c+s))Jr.
$$

The inequalities `h^2>2 delta^2` and `h>delta` imply `0<delta(c+s)<h` and
`h-delta(c-s)>0`. Thus, throughout the label-0 square `[0,h]^2`, the second coordinate
already satisfies closed containment.
Its first coordinate gives exactly the C rectangle and its strict S complement.
For a non-axis eligible ray the four signed rays occupy bins 0, 2, 4, and 6 only.
For the axis, the east ray also belongs to bin 7; its second-mark sign changes at
`y=delta`. These facts account for every boundary and zero-sign alternative relevant to
the forced predicate.

On C, `z_y>=b>1/sqrt(2)`, and both centre coordinates are below `1+h sqrt(2)<2`. The far
walls have clearance above `q-2>1/sqrt(2)`. Only `z_x>=e_j` can constrain parent
existence. Reflection and quarter turns preserve the coordinate half-extent, so the
minimum extent formula applies to every eligible source alias, including reflected index
180\. It does not assert coexistence of two independently chosen parents.

For the first S owner, the strict strip yields

$$
z_x>a+(c-s)(h-\delta c)>a,
\qquad z_y\ge b>1/\sqrt2.
$$

The same far-wall bounds apply.
Every unit-parent angle therefore fits at this centre; the source-angle restriction and
coexistence with owner 2 still apply.

For C strata, the complete label set is constant after retaining the interior level
`y=delta(c+s)` and all rectangle endpoints.
If `M=a+c sup(I_x)-s inf(I_y)`, positivity of `c,s` makes this the unique maximizing
corner of the closure.
When `M>e_j`, points of the stratum approach that corner while retaining their atomic
membership. When `M=e_j`, every other point has smaller wall clearance.
Hence equality requires both maximizing coordinates to be included.
With singleton/open-interval products this permits only the vertex stratum.
An excluded lower source endpoint instead requires strict clearance.

## Required Correction: C Parent Witnesses Can Be Rational

The original scratch analysis stated that an equality case might require an irrational
parent ray. The
[retained X-029 text](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md)
includes this correction: every feasible C stratum admits a rational parent witness.

Every event coordinate is rational, so `M` is rational.
If an accepted equality case has `M=e_j` and lower whole-angle tangent `L=L_j`, then

$$
\cos\beta=\frac{1}{\sqrt{1+L^2}}
=\frac{2M}{1+L},
\qquad
\sin\beta=\frac{2ML}{1+L}.
$$

Both components are rational.
The maximizing vertex, and therefore the centre, are rational too.
Source reflection and quarter turns preserve that property.

If `M>e_j`, choose a rational centre inside the same stratum with positive parent-wall
clearance. Rational unit rays are dense in each nondegenerate source cell, so a source
angle sufficiently close to its lower endpoint gives a rational parent with that
clearance. This also works when a source policy excludes the lower endpoint.

Consequently every nonempty C stratum in this proposed method has a rational centre and
a rational parent witness.
This is an existence result; blind enumeration of rational poses still supplies no
complete absence proof.
The quadratic comparison remains necessary to decide the strata exactly.
No rational-witness assertion for general S follows from this argument.

The independent finite control gives a stronger fact for this particular net: `e_j^2`
has a rational square root only at index 0. It tests the reduced numerator and
denominator using exact integer square roots for all 181 indices.
Thus none of the actual non-axis C charts can have rational `M=e_j`. Keeping the generic
equality branch in a reusable oracle is sound, but it is not an active non-axis case for
these constants.

The corrected X-029 statement uses the exact quadratic comparison to decide feasibility.
Rational witness enumeration alone cannot prove absence.

## Independent Arithmetic and Reproduction

The
[maintained control](../../../packing/cases/n11_five_dot_cover/bc303_t2_geometry_control.py)
retains the independent polygon-edge containment and coordinate-bin predicates.
Its [test](../../../packing/tests/test_bc303_t2_geometry_control.py) fixes the exact
summary. The original scratch review also replayed the author’s geometry JSON exactly;
that large scratch JSON is not a campaign result.

They check all 2896 D4/source-chart combinations, including proper frames and alias
transport; 4550 critical centre cases across the 182 eligible charts; all eight corner
transports of both split owners; and rational-square status for every minimum parent
extent. The centre cases include the C/S dividing edge, the second-mark sign level, and
rectangle vertices. These controls supplement the analytic proofs; they are not an
enumeration of the atomic arrangement.

For the rational S control, independent vertex calculations verify the two mark
memberships, strict core-in-parent containment, container containment, and complete
labels `{0,7}` and `{9}`. The second parent’s whole-angle tangent lies strictly between
`L_180` and 1. The supporting functional `y-x` gives exact parent separation

$$
\frac{2022521}{878547000}>0.
$$

The first parent uses the admitted axis endpoint.
The control’s geometry is valid under the declared equipment convention, and the second
parent avoids seam and fold ties.
The first parent retains its own explicit endpoint obligation.
No mass is attached to this feasibility result.

Reproduce the maintained control from `packing/`:

```bash
uv run --frozen --all-extras --group dev pytest -q tests/test_bc303_t2_geometry_control.py
```

Scientific execution still requires a source-bound reader and authenticated
source/implementation receipts.
The geometry control does not constitute instrument admission or a distinct-method
charge confirmation.

## Remaining Determinations and the Next Bounded Experiment

The next implementation slice is the maintained C event-stratum reader with the accepted
one-wall predicate and corrected witness statement.
Bind all source atoms, their integer weights, the complete source manifest, and the
executing implementation.
Retain synthetic closed-edge, vertex, zero-sign, missing-alias, wrong-source, and
excluded-endpoint controls.
Complete independent instrument review before a registered C target run.

That target asks whether any forced-0 C stratum has `W mu(C)<=4524199` and a contained
source-matching parent.
A valid witness rejects opposite T2 and the combined helper.
An exact exclusion of every such stratum proves the C role above threshold; it leaves S
open. Evaluating a disclosed C or S control first can provide a bounded charge check
after reader admission, but a charge above threshold decides only that configuration.

For S, the first-owner strip removes only its individual wall constraints.
The second owner’s mark exclusion, complete absence of label 15, individual parent
containment, and joint parent coexistence remain.
Acceptance requires a complete necessary relaxation excluding all pairs with
`W(mu(C1)+mu(C2))<=8524199`, or a complete exact joint feasibility determination.
A relaxed low-charge pair requires simultaneous parent replay before it rejects T2.
Contacts, sign zeros, source seams, determinant-zero cases, and unresolved cover cells
must retain explicit dispositions.

Both role thresholds must pass to accept the combined helper.
Equality at integer surplus 524199 rejects the strict test; acceptance requires at least
524200 in each nonempty role.
A threshold certificate need not compute the exact role minimum.
Opposite rejection alone leaves adjacent-only T2 unresolved.

For global routing, the remaining statement is that every hypothetical eleven-parent
packing, or a valid normalized representative equipped after normalization, has a
selection of actual owner labels in the admitted excluded family.
T2 success would exclude conflicting forced types, but every corner must also offer
label 0 or 15. The known local T1 counterexample rejects its stated universal resource
helper without deciding availability on actual eleven-parent packings.
That global availability and selection obligation remains separate from both T2 geometry
and instrument readiness.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
