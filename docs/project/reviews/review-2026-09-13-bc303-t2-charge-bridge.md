# Source-Distinct Review of the BC303 T2 Charge Bridge

Date: 2026-09-13. Review bead: `think-pcxo`. The Astra Max mathematical review was
read-only. It inspected the clean X-029 source head
`4f897b7b506e62d9a68670870469b844fecddf3f` and accepted Deductions 1–3 of the
[charge-bridge analysis](../research/research-2026-09-13-bc303-t2-charge-bridge.md)
under the closed, symmetric source equipment contract in
[X-029](../../../packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md).
The accepted note incorporates the corrections recorded below.

The review compared these six frozen source paths against revision
`39714308ce2081abbd76624387d134fee4be6deb` and found no change at the reviewed head:

- [BC293 atom measure](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json)
- [owner-footprint manifest](../../../packing/devtools/owner_footprints.py)
- [adaptive source cells](../../../packing/src/sqpack/fractional/adaptive.py)
- [exact atom and direction model](../../../packing/src/sqpack/fractional/model.py)
- [unconditioned sweep](../../../packing/src/sqpack/fractional/sweep.py)
- [wall-containment contract](../../../packing/cases/n11_five_dot_cover/wall-containment-contract.md)

The review did not re-run the imported BC303 coverage floor, inspect a new charge
receipt, or execute a target.
The source-bound model has rational atom coordinates and weights and a
nonnegative-weight guard.
The future reader must invoke that guard before using the monotonicity argument.

## Accepted Deductions

| Deduction | Reviewed conclusion | Boundary of acceptance |
| --- | --- | --- |
| C boundary monotonicity | Each feasible C boundary pose has a nearby feasible open atom cell of no greater charge. The C domains are convex with a strict interior anchor; absent atoms remain absent nearby, and nonnegative closed-atom weights let present membership only shrink. | This applies to X-029’s C domains, including the included axis boundary. It does not discard the forbidden axis edge or establish the same property for jointly realizable S pairs. |
| Exact C open-cell oracle and sweep | On each non-axis open cell, parent existence is exactly `4M²(1+L²)>(1+L)²`, where `M=a+c x₊−s y₋>0`. Equality is infeasible for that open cell. Feasible y intervals form a prefix, so an exact event sweep can decide the C minimum or threshold. | All 182 source charts and both axis aliases remain explicit. Closed-edge and vertex predicates are still needed when replaying a witness. |
| S first-owner sufficient test | The forced-0 first owner lies in X-029’s strict strip, where its parent walls are inactive. Its individual minimum admits the same open-cell reduction. If that integer mass is at least `4524185`, the imported second-owner floor `4000015` gives total mass at least `8524200`, above the S allowance. | A lower first-owner cell only fails this sufficient test. It does not produce a jointly feasible S pair or reject T2. |

The C minimum claim is a finite-arrangement statement, not a charge value.
The review accepted the nonnegative-weight and interior-density proof, the exact strict
wall comparison, and the first-owner S implication under the reviewed source contract.

## Required Specification Corrections

The accepted note now specifies the following conditions for a maintained reader:

1. Clip each closed atom-membership rectangle to the sweep domain.
   Discard zero-width or zero-height intersections only for open-cell charging, while
   retaining every source atom for closed witness replay.
   Deduplicate event coordinates.
   Apply every coincident start and end update before querying the following open strip,
   including atoms whose rectangles cover the full domain.
2. Limit the `O(m log m)` arithmetic and `O(m)` working-storage claim to computing a
   minimum, threshold verdict, and one attainer per chart.
   Materializing all `K=O(m²)` low-charge cells has output cost at least proportional to
   `K`; the shared C/S grid has at most `(2m+2)²` open cells.
3. Reconstruct a rational physical parent by testing a half-angle tangent `0≤t<1`
   exactly against `L<2t/(1−t²)<U` and `(1+2t−t²)/(2(1+t²))<zₓ`, then apply source
   reflection and quarter-turn transport and replay containment.
   Retain closed source-chart aliases and endpoint policy.
4. Authenticate the atom rows, nonnegative integer weights, complete source manifest,
   source-cell policy, and executing reader revision before any target charge run.

These are part of the reviewed proposed method, not evidence that the reader has been
built or admitted. The
[bridge note](../research/research-2026-09-13-bc303-t2-charge-bridge.md) retains the
exact experiment thresholds and synthetic controls.
No C or S charge was computed here.
C and S minima, adjacent-only and opposite T2, global owner availability and routing, V3
alignment, and a stronger `s(11)` bound remain unresolved.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
