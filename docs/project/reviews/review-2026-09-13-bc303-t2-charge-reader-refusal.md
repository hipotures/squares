# BC303 T2 Charge Reader: Independent Admission Review

Date: 2026-09-13. Review bead: `think-ncn8`.

**REFUSE instrument admission at `cdf854e240aa0068b0a4554f6c20d09385aa02d8`.** The
reflected index-180 witness replay accepts physical parents outside their declared
source cell. The independent reference can silently omit a feasible open cell and return
an incorrect minimum.
Repair beads are `think-sv4b` and `think-3lcm`. Both require disposition and a fresh
independent admission before exp-158.

The C open-cell reduction, exact wall-prefix decision, S first-owner implication, atom
binding, chart enumeration, and frozen thresholds survive this review.
No BC293 atom charge, C target, S target, disclosed target witness, or exp-158
invocation was evaluated.
The refusal concerns reader admission and its control evidence; it does not decide T2.

## Scope and Exact Identity

The source-distinct review inspected the clean checkout at
`cdf854e240aa0068b0a4554f6c20d09385aa02d8` against merged T1/T2 base `b8a058b4`. The
diff has eight files.
The review read the complete reader and tests, accepted X-029 geometry and charge
bridge, their reviews, and the source manifest and angle-cell implementation.
No repository source or PR was changed.

Repository paths below are relative to that checkout.
These Git blobs identify the reviewed implementation and its accepted specifications:

| Path | Blob |
| --- | --- |
| [packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py](../../../packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py) | `f743721ec5b5bdf1a880b4ea4c221275b9b8d736` |
| [packing/tests/test_bc303_t2_charge_sweep.py](../../../packing/tests/test_bc303_t2_charge_sweep.py) | `903a4faf2a62abb1fa0251b4bc14f2cd12b55bbb` |
| [packing/cases/n11_five_dot_cover/bc303_t2_geometry_control.py](../../../packing/cases/n11_five_dot_cover/bc303_t2_geometry_control.py) | `035bebdbf63e2714cbf602fc71694d08867277c9` |
| [packing/tests/test_bc303_t2_geometry_control.py](../../../packing/tests/test_bc303_t2_geometry_control.py) | `0d191bc7c717f282b92bb321890fcf4c563fafe6` |
| [packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md) | `8a3200390a1a367c1e4c9449262a2973336688ea` |
| [docs/project/reviews/review-2026-09-13-bc303-t2-geometry.md](../../../docs/project/reviews/review-2026-09-13-bc303-t2-geometry.md) | `7ba1f52480f737797b99434fb35e6da0abfca876` |
| [docs/project/research/research-2026-09-13-bc303-t2-charge-bridge.md](../../../docs/project/research/research-2026-09-13-bc303-t2-charge-bridge.md) | `84ff589ab204ce511f97cbf03ac9743c1edb9180` |
| [docs/project/reviews/review-2026-09-13-bc303-t2-charge-bridge.md](../../../docs/project/reviews/review-2026-09-13-bc303-t2-charge-bridge.md) | `1078408b5b580938f2c99eb302e24fc32230929e` |
| [packing/campaign/hypotheses/H-160-bc303-t2-charge-filters.md](../../../packing/campaign/hypotheses/H-160-bc303-t2-charge-filters.md) | `28359f560a1d5396248d5bd683f09b1f1441d761` |
| [packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md) | `40f271fa6f2068305f84bfe1d833c888d7022225` |

The six frozen source paths are byte-identical to reviewed source revision
`39714308ce2081abbd76624387d134fee4be6deb`:

| Path | Blob at Both Revisions |
| --- | --- |
| [packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json) | `db8abed8f716a4173b47bcfb19f8e045b44513d1` |
| [packing/devtools/owner_footprints.py](../../../packing/devtools/owner_footprints.py) | `65501ad186a463eb5e7e16978daf03e603149fbd` |
| [packing/src/sqpack/fractional/adaptive.py](../../../packing/src/sqpack/fractional/adaptive.py) | `d80f6e060904bc5e01c21f5f23eba87ede456422` |
| [packing/src/sqpack/fractional/model.py](../../../packing/src/sqpack/fractional/model.py) | `a5df6094eadfe441dba66fee8fe37a4e5530b6f6` |
| [packing/src/sqpack/fractional/sweep.py](../../../packing/src/sqpack/fractional/sweep.py) | `6bd5c56564a8f1a0681213c9b083cf62e4621a95` |
| [packing/cases/n11_five_dot_cover/wall-containment-contract.md](../../../packing/cases/n11_five_dot_cover/wall-containment-contract.md) | `24e00f7cbbbb07c26347e22a4b2b3467cea701fa` |

## Findings

### R1 — Blocker: Reflected Parent Construction and Replay Lose the Source Reflection

At `packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py:409`, the constructor
returns the unreflected folded ray.
At line 431, S instead uses the selected core ray as its physical parent.
Lines 446–448 test the physical slope directly against folded source bounds.
They never undo the retained source reflection.

This fails on the existing synthetic fixture in
`packing/tests/test_bc303_t2_charge_sweep.py:111`. Its chart is `(180, True)`, with

$$
L_{180}=37175706500000/37322097608629,
\qquad U_{180}=1.
$$

The source construction reflects a folded parent `(v_x,v_y)` to `(v_y,v_x)`, modulo
quarter turns. Thus, for these positive physical rays, source membership must compare
`u_x/u_y` with `[L_180,1]`.

The accepted C receipt returns

$$
u=(13575/19193,13568/19193),
\qquad u_x/u_y=13575/13568>1.
$$

The accepted S first-owner receipt returns

$$
u=(207107000000/292893309449,207106690551/292893309449),
\qquad u_x/u_y=207107000000/207106690551>1.
$$

Both parents are outside the declared reflected source cell, although the current replay
accepts their scalar wall clearance, core containment, labels, and ownership.
The charges 10 and 15 printed by these reproductions use three synthetic atoms only.
They are unrelated to the frozen BC293 measure.

**Fix:** Transport the folded rational parent by the chart’s source reflection and
quarter turn.
In replay, independently pull the physical parent back to that source chart
before checking its angle and endpoint policy.
Construct a source-admitted rational parent for S as well: selecting the core ray itself
is invalid for index 180, whose folded selected ray overshoots the endpoint.
Retain wrong-reflection and source-endpoint negative controls for both roles.
Track under `think-sv4b`.

The scalar C wall minimum remains correct: coordinate half-extent is invariant under
reflection. This finding does not require changing the pose domains or thresholds.

### R2 — High: The All-Strata Reference Silently Drops Feasible Cells

At `packing/tests/test_bc303_t2_charge_sweep.py:52`, the reference tries only 64 dyadic
points near an open cell’s maximizing corner.
If all fail, it omits that cell without proving infeasibility or reporting an unresolved
construction. The later finite event/midpoint grid also misses feasible portions of some
wall-cut strata.

A retained target-free counterexample uses the rational synthetic chart

$$
r=(4/5,3/5),\quad L=3/4,\quad e=7/10,\quad
X=h-\delta(4/5-3/5).
$$

Set `x_high=1/1000`, `epsilon=2^-100`, and `y_low=(a+(4/5)x_high-7/10-epsilon)/(3/5)`.
Two unit-weight synthetic atoms have core-frame coordinates `(x_high+h,h/2)` and
`(h/2,y_low-h)` relative to the first mark.
Their rectangles leave the open cell `(0,x_high) × (y_low,h)` at charge zero.
Its wall-clearance supremum is `7/10+2^-100`, so it is feasible.
The explicit rational point

$$
x=x_{\rm high}-x_{\rm high}/2^{110},\qquad
y=y_{\rm low}+(h-y_{\rm low})/2^{110}
$$

has clearance strictly greater than `7/10` and closed charge zero.
The optimized sweep returns C minimum **0**; `direct_all_strata_minima` incorrectly
returns **1**. This is a defect in the claimed reference, not a failure of the optimized
sweep.

The maintained fixtures also do not exercise an interior negative x-event.
Their nondegenerate rectangles end at `x=h`, which the strip loop never processes.
The coincident events they test are starts only.
A retained independent fixture with a weight-7 rectangle ending and a weight-11
rectangle starting at `X/2`, over a weight-13 full-domain rectangle, passes: C minimum
20, S minimum 24, and closed event charge 31.

**Fix:** Give each point/open-interval product stratum an exact feasibility decision,
including the endpoint-attainment rule at equality.
After proving nonemptiness, construct its representative without silently treating a
search cap as absence.
An exhausted construction must refuse the reference result.
Promote the narrow-cell and interior end/start regressions into the maintained controls.
Track under `think-3lcm`. The accepted bridge requires this reference evidence before
target execution.

## Mathematical and Source Dispositions

**Atom binding passes.** `source_atoms` compares all six source paths with their
reviewed Git bytes before parsing the measure.
The parser checks all 377 rows, distinct rational sites, nonnegative weights, exact
integer scaling at `W=4000000`, header parameters, and total integer mass `45048398`.
Its explicit nonnegative-weight guard establishes the premise needed for boundary
monotonicity. The source-check operation identifies this module’s own checkout and the
pinned clean revision before any charge.

**The 182-chart enumeration passes independently.** A retained control constructs rows
from frozen `full_owner_direction_manifest` and `derive_cells`, using direct signed-ray
bin inequalities. Every reader row, selected ray, lower tangent, and upper tangent
matches. The identities are both axis aliases, unreflected 1–179, and reflected 180;
there are 181 distinct selected orientations.

**The event sweep and C wall prefix pass mathematical review.** Each source atom is
projected into its exact closed membership rectangle and clipped to `[0,h]^2`. Zero-area
intersections are discarded only from open-cell charging; `charge_at` retains the
complete atom tuple.
The cut `X` and axis bound `delta` are explicit event levels.
All starts and ends at one x-level are applied before querying the next strip, including
full-domain rectangles.
The range tree preserves exact integer sums and returns a stable leftmost minimum.

For a non-axis cell, positive clearance maximum `M=a+c*x_high-s*y_low` satisfies parent
existence exactly when `4*M^2*(1+L^2)>(1+L)^2`. It is an unattained supremum, so strict
comparison is required.
Since `s>0`, feasible y-intervals form the prefix found by the binary search.
Convex interior density and nonnegative closed atoms justify taking C minima over open
cells; the forbidden axis edge remains excluded.
An explicit reconstruction failure raises an error rather than issuing a positive target
verdict. The reflected physical-parent receipt defect is R1.

**The S filter and thresholds are correctly scoped.** The first owner uses the strict
strip `X<x<=h`; insertion of `X` makes `x_low>=X` select precisely its open cells.
The admitted interior-density argument supplies its boundary minimum.
The code and records retain the distinction between `filter_failed_only` and an actual S
witness.

At scale `W`, the single-corner surplus allowance is `524199`. Therefore C needs integer
charge at least `4524200`, and the S pair needs at least `8524200`. Subtracting the
imported second-owner floor `4000015` gives the first-owner sufficient threshold
`4524185`. H-160, exp-158, and the reader use these exact values.
A low first-owner minimum alone does not reject S or T2. The BC303 coverage floor is
imported; it was not reproved in this admission review.

## Validation and Design Assessment

Python was the checkout’s `.venv/bin/python3`, version **3.14.7**. The initial frozen
`uv run` attempts could not write the sandbox-excluded shared cache; direct execution of
the already provisioned project interpreter avoided that setup issue.

- Existing geometry and charge tests: **7 passed in 1.31 seconds**.
- Pinned `source-check`: passed, reporting **377 atoms, 182 charts**, the expected
  executing revision, and source revision `39714308ce2081abbd76624387d134fee4be6deb`.
- Independent source manifest comparison and real coincident end/start control: passed.
- Independent inverse-reflection tests: two expected regression failures, one per role.
- Narrow feasible-cell reference test: failed with **reference 1 versus exact 0**.

The complete retained admission control reports **3 failed, 2 passed in 1.10 seconds**.
Its output is retained at
[packing/cases/n11_five_dot_cover/evidence/bc303-t2-charge-reader-refusal-2026-09-13.log](../../../packing/cases/n11_five_dot_cover/evidence/bc303-t2-charge-reader-refusal-2026-09-13.log).

The retained controls are now maintained in
[packing/tests/test_bc303_t2_charge_sweep.py](../../../packing/tests/test_bc303_t2_charge_sweep.py).
From the reviewed checkout’s `packing/` directory, the original refusal was reproduced
without charging the source measure.
The maintained tests now include these regressions:

```bash
PYTHONPATH=.:src .venv/bin/python3 -m pytest -q -s \
  tests/test_bc303_t2_charge_sweep.py
```

The source-check command is:

```bash
.venv/bin/python3 -m cases.n11_five_dot_cover.bc303_t2_charge_sweep source-check \
  --expect-implementation-revision cdf854e240aa0068b0a4554f6c20d09385aa02d8
```

The segment-tree design fits the accepted minimum-and-one-attainer scope; replacing it
is unnecessary. A complete direct stratum reference remains the appropriate independent
control. No new library is needed for either repair.

The existing tests do refuse a changed atom row, a missing alias, a wrong expected
execution revision, and a collapsed domain.
They test closed membership and the forbidden axis edge.
They do not independently authenticate a reconstructed parent against its reflected
source chart, which is why R1 passes their replay assertion.
The existing reference’s name and registration claims exceed its evidence because of R2.
Preserve the working nonnegative guard, both aliases, strict wall test, and strict S cut
while repairing these failures.

No CI or full validation run was started by this read-only lane.
The parent bead reports prior Ruff, focused BasedPyright, and records validation success
at the pinned commit; those reports are context, not substituted evidence for this
review’s focused runs.
H-160 must retain `instrument_ready: false` and exp-158 must remain uninvoked until both
repairs receive fresh admission.
Thresholds and scientific claims remain unchanged.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
