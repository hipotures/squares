# BC303 T2 Charge Reader: Independent Readmission

Date: 2026-09-13. Review bead: `think-ncn8`.

**ACCEPT instrument admission at `0f20fdcdd5bac7e0734b29cd0b0efef4ffea3699`.** The
source-distinct mathematical and software review accepts the repaired C reader and S
first-owner filter under the frozen H-160/exp-158 contract.
Both findings in the
[earlier refusal](review-2026-09-13-bc303-t2-charge-reader-refusal.md) are resolved.
No new admission blocker was found.

This review evaluated synthetic charges only.
It did not charge the BC293 measure, evaluate either disclosed target witness, invoke
exp-158, or change the source atoms, geometry, hypotheses, thresholds, or experiment
criteria. T2 and the global n11 claims remain undecided by this admission.

## Scope and Identity

The reviewed checkout was clean at the full revision above before and after the
controls. The repair diff against the refused parent
`cdf854e240aa0068b0a4554f6c20d09385aa02d8` contains six files; the executable changes
are confined to the reader and its tests.
The review read both files in full, the retained refusal and regression log, and the
accepted
[X-029 geometry](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md),
[charge bridge](../research/research-2026-09-13-bc303-t2-charge-bridge.md), and
[bridge review](review-2026-09-13-bc303-t2-charge-bridge.md).

| Reviewed File | Git Blob at the Reviewed Revision |
| --- | --- |
| [Charge reader](../../../packing/cases/n11_five_dot_cover/bc303_t2_charge_sweep.py) | `aa9ea57b774713c8ceea0f2b4983b0666df01d82` |
| [Maintained controls](../../../packing/tests/test_bc303_t2_charge_sweep.py) | `f3ece5d7c3bc5ade17081395ce18bff65eae49c8` |

All six frozen source paths named in the earlier review remain byte-identical to
`39714308ce2081abbd76624387d134fee4be6deb`. H-160 and exp-158 are byte-identical to the
refused parent. In the reviewed tree, `instrument_ready` is still false and the
experiment has no result.
Source authentication passes for the same 377 nonnegative rational atoms at scale
4000000, total integer mass 45048398, 182 source charts, and 181 distinct selected
orientations. This authenticates the inputs without charging them.

Execution used the provisioned Python **3.14.7** interpreter with `packing/` and
`packing/src/` from the reviewed checkout first on `PYTHONPATH`. The independent runtime
control confirmed that the reader, geometry, owner manifest, adaptive cells, direction
generator, model, and source sweep all imported from that checkout, despite the
interpreter environment residing elsewhere.
The pinned `source-check` reported the exact reviewed implementation revision and frozen
source revision.

## Repair Dispositions

### R1: Physical Parent Transport and Replay — Resolved

The constructor now transports the folded rational parent through the retained source
reflection. Both C and S use this constructor; S no longer treats its selected core ray
as a physical parent.
This matters at reflected index 180, where the selected ray lies beyond the folded
source endpoint.

The original synthetic controls now return, for both roles,

$$
u=(13568/19193,13575/19193),\qquad
u_x/u_y=13568/13575\in[L_{180},1].
$$

The old C and S parents still fail the maintained wrong-reflection controls.
Their synthetic charges remain 10 and 15; these values are unrelated to BC293.

Replay checks unit length, all physical-parent walls, strict containment of every core
vertex, closed atomic membership, complete labels, the requested ownership role, and
source-cell membership.
The new inverse considers all four quarter turns of the physical ray, undoes the source
reflection, and compares the resulting whole-angle tangent with the inclusive source
interval. This is the correct inverse for a square: reflection reverses quarter turns,
and the full quarter-turn orbit is unchanged by that reversal.

The constructor’s unrotated representative is sufficient for the eligible non-axis
charts. For the reflected axis alias, the returned horizontal parent and the reflected
vertical parent are the same physical square.
The independent controls check both roles on all 182 charts and transport every returned
parent through all eight D4 maps, with the reflection flag toggled exactly for negative
determinant. Direct folded cross-multiplication supplies a separate check of each
non-axis source angle.

Closed source endpoints remain admitted.
Exterior rays on both sides of every source interval are refused under all eight D4
maps. Further full replays accept quarter-turn representatives and reject nonunit parent
forgeries for axis, middle, and reflected-end charts, in both roles.

### R2: Complete Stratum Reference or Explicit Refusal — Resolved

The direct reference now enumerates the Cartesian products of every point stratum and
every consecutive open interval.
It inserts the C/S cut and, for axis charts, the forbidden upper edge before
enumeration. Atom event coordinates are derived directly from the atoms, separately from
the optimized rectangle sweep.

For a non-axis stratum, let

$$
M=a+c x_+-s y_-,\qquad
e=\frac{1+L}{2\sqrt{1+L^2}}.
$$

The exact comparison first distinguishes $M<e$, $M=e$, and $M>e$ using the positive
clearance and squared rational inequality.
At equality, the maximizing corner is attained precisely when each coordinate with
nonzero coefficient is a point stratum.
An open x interval with $c>0$ or an open y interval with $s>0$ excludes that corner.
This is the correct endpoint-attainment rule.
Axis strata separately exclude $y=\delta$, while an interval ending there remains
eligible.

For an eligible stratum, dyadic representatives approach that maximum from inside the
stratum. A returned point is checked exactly.
If no point is obtained within 256 steps, the reference raises an
unresolved-construction error; it cannot silently omit the stratum or return the minimum
over the remaining strata.
The S reference selects every stratum with $x>X$ and uses its midpoint, since charge is
constant on each point/open-interval product and its parent walls are inactive.

The retained $2^{-100}$ counterexample now returns **reference 0 and sweep 0**. The
$2^{-300}$ control refuses explicitly.
The independent review also checks that this error propagates through
`direct_all_strata_minima`, rather than merely through its representative helper.
A separate rational wall at $e=7/10$ exercises equality inside the valid domain on a
point, horizontal edge, vertical edge, and open cell, with each endpoint policy checked.

The interior coincident end/start regression remains correct: synthetic C minimum 20, S
first-owner minimum 24, and closed event charge 31. Independent fixed-seed fixtures add
27 synthetic atom layouts over axis, interior-angle, and reflected-end charts; all exact
reference minima match the sweep.

## Validation Evidence

| Check | Result |
| --- | --- |
| Maintained geometry and charge controls, plus original admission controls | 20 passed in 1.73 s |
| Independent readmission controls | 198 passed; detailed test durations retained in the log |
| Pinned source-check | Passed: 377 atoms, 182 charts, exact implementation and source revisions |
| Six frozen source files against the reviewed source revision | No differences |
| H-160 and exp-158 against the refused parent | No differences |
| Ruff check and format check on the repaired Python files | Passed |
| Focused BasedPyright with the provisioned interpreter explicitly selected | 0 errors, 0 warnings, 0 notes |

The retained evidence is the
[independent control source](../../../packing/cases/n11_five_dot_cover/evidence/bc303-t2-charge-reader-readmission-2026-09-13.py),
[focused replay log](../../../packing/cases/n11_five_dot_cover/evidence/bc303-t2-charge-reader-readmission-focused-2026-09-13.log),
and
[independent replay log](../../../packing/cases/n11_five_dot_cover/evidence/bc303-t2-charge-reader-readmission-independent-2026-09-13.log).
The independent control source fixes the reviewed revision and forbids source atom
loading and target execution during its synthetic tests.
Its identity assertion is a historical admission control for this exact commit; it is
not a moving branch-head assertion.

To reproduce the independent evidence, check out the reviewed revision, make the
retained control source available outside that checkout, and run from `packing/` with
the provisioned project interpreter: Set `BC303_PYTHON` to that Python 3.14 interpreter
with the project test dependencies, and `BC303_REVIEW_CONTROL` to the external copy of
the retained control source.

```bash
PYTHONPATH=.:src "$BC303_PYTHON" -m pytest -q --durations=8 "$BC303_REVIEW_CONTROL"
PYTHONPATH=.:src "$BC303_PYTHON" -m cases.n11_five_dot_cover.bc303_t2_charge_sweep \
  source-check --expect-implementation-revision 0f20fdcdd5bac7e0734b29cd0b0efef4ffea3699
```

The initial focused BasedPyright invocation could not resolve pytest because this clean
checkout has no local virtual environment.
Selecting the provisioned Python 3.14.7 interpreter with `--pythonpath` resolved that
setup issue; no source or dependency change was made.
No full checkpoint or CI run was performed by this review lane.

## Design and Remaining Scope

The existing exact event sweep and segment tree fit the accepted
minimum-and-one-attainer contract.
The direct stratum reference now provides the separate boundary evidence the bridge
requires. No replacement algorithm or new library is needed for admission.

The finite reconstruction limits are explicit unresolved exits.
This review accepts their failure semantics; it does not prove that a future target run
must finish within either construction limit or the preregistered wall allowance.
Any such error prevents a target verdict and must retain that unresolved outcome.

The C open-cell reduction, clipped events, complete source manifest, strict wall
comparison, and S first-owner implication are unchanged from the accepted portions of
the earlier review. The frozen integer thresholds remain C at least 4524200 and S first
owner at least 4524185. A low S first-owner charge still rejects only that sufficient
filter. The imported second-owner coverage floor is not reproved here.

The coordinator may publish this admission and the repair dispositions, then update
readiness without altering the frozen scientific inputs or criteria.
`think-ncn8` remains open until publication.
This review author made no source edit, target call, push, or PR change.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
