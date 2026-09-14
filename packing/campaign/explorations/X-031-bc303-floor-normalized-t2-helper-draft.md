---
title: X-031 — Floor-Normalized BC303 T2 Helper and H-161 Local Stability
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-031
  title: Floor-Normalized BC303 T2 Helper and H-161 Local Stability
  date: '2026-09-13'
  author: Codex, retaining two source-distinct mathematical reviews
  campaign: packing.squares
  brief: >-
    Record the exact floor-normalized C and actual-S forced-type helper, its
    integer thresholds, the bounded H-161 local-stability consequence, and a
    separate unregistered H-162 analysis proposal without a target result.
  sources:
  - packing/campaign/explorations/X-029-bc303-t2-exact-geometry-draft.md
  - packing/campaign/explorations/X-030-n11-post-t1-proof-obligations-draft.md
  - docs/project/reviews/review-2026-09-13-bc303-t2-global-bridge.md
  - docs/project/reviews/review-2026-09-13-bc303-floor-normalized-t2-independent.md
  - docs/project/research/research-2026-09-13-bc303-t2-charge-bridge.md
  - packing/campaign/hypotheses/H-160-bc303-t2-charge-filters.md
  - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md
  - packing/campaign/hypotheses/H-161-bc303-literal-parent-union.md
  - packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union-audit.json
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md
  proposes: []
---
# X-031: Floor-Normalized BC303 T2 Helper

**Status: reviewed deduction, unmeasured target.** An
[analytic derivation][globalreview] and
[source-distinct independent review][independent] accept the floor-normalized resource
account and its exact integer endpoints under X-029’s closed, symmetric equipment
contract. This exploration adds no H-160 or exp-158 result and registers no H-162
hypothesis. The imported BC303 strict-core floor remains a premise.
No new scan of the frozen 377-atom measure or scientific target was made for this
exploration.

In [the repository’s epistemic vocabulary](../../../epistemics.md), the identity and
local equivalence have proof-audited, V3-type analytic support conditional on that
imported floor. X-031 is an exploration, not a classified whole frontier result.
The cutoff arithmetic is proof-audited; whether the unmeasured C/S minima meet those
cutoffs has no target determination yet.
No new machine-confirmed C3 charge outcome or V4 certificate exists here.

## Eleven-Core Resource Account

Fix a hypothetical packing of eleven unit-square parents in $K=[0,96/25]^2$, with one
coherent admitted selection of closed cores $C_i$ strictly inside their parents.
Parent interiors are disjoint, so these cores are disjoint.
For the frozen nonnegative [BC293 point measure][measure], the imported
[BC303 coverage proof and replay][floor] give every selected core mass at least $1+g$,
where

$$
W=4000000,\qquad WM=45048398,\qquad Wg=15,\qquad
F=W(1+g)=4000015.
$$

The total allowance above eleven unit masses is $W\varepsilon=1048398$. Normalize each
core by its proved floor, $\beta_i=\mu(C_i)-(1+g)\ge0$, and let $U$ be measure outside
all selected cores. Then

$$
U+\sum_{i=1}^{11}\beta_i=E,
\qquad E=\varepsilon-11g=\frac{1048233}{4000000}.
$$

If a displayed opposing-type corner pair has $k$ distinct actual owners and $u$
*globally* unowned marks, its necessary extension condition is

$$
\sum_{i\in I}\beta_i\le E-uw,
\qquad Ww=531255.
\tag{1}
$$

The strict reverse inequality excludes that pair from an eleven-parent packing.
In raw owner surplus $S=\sum_{i\in I}(\mu(C_i)-1)$, it is $S>\varepsilon-uw-(11-k)g$.
The $k$ displayed floors remain in $S$; subtracting all $11g$ from the right while
leaving raw $S$ unchanged would count them twice.
An O role counts as a globally missing mark only when the mark is absent from the
packing, not merely absent from a local fixture.

## Complete Local Helper and Exact Cutoffs

Let $D_C$ be X-029’s full forced-0 role-C domain with its physical parent, and let $D_S$
be its full forced-0 role-S domain with *two simultaneous physical parents*. The C
domain has 182 eligible source charts, both axis aliases, closed atomic membership, and
the forbidden axis edge.
Define

$$
A_g=\min\left\{
\mu(C)-(1+g):C\in D_C;\quad
\mu(C_1)+\mu(C_2)-2(1+g):(C_1,C_2)\in D_S
\right\}.
$$

The minimum exists because the domains are nonempty and finitely many atom-membership
sets occur. The reviewed reduction proves that the strict normalized inequalities for
**all admitted adjacent and opposite opposing-type pairs** hold exactly when

$$
\boxed{A_g>E/2.}\tag{2}
$$

For sufficiency, every full corner contributes at least $A_g$, every O owner has
nonnegative normalized surplus, and $2Ww=1062510>WE=1048233$ makes the one-missing case
follow from $A_g>E/2$. For necessity, reflect an attaining full forced-0 C or actual S
configuration to the opposite corner.
X-029’s parent separation in $x+y$ is $708/3175>0$, so the two local configurations
coexist with surplus $2A_g\le E$ if (2) fails.
This refutes the separate local helper; it does not construct the remaining parents.
The argument does not equate adjacent-only failure with independent local products.

At scale $W$, $WE/2=524116.5$, so a passing normalized full-corner surplus needs at
least 524117 integer units.

| Test | First passing mass | Last failing mass | Status of the test |
| --- | ---: | ---: | --- |
| Complete C minimum | $4524132$ | $4524131$ | Necessary and sufficient for C’s half-budget condition |
| Complete **actual S-pair** minimum | $8524147$ | $8524146$ | Necessary and sufficient for S’s half-budget condition |
| S first-owner strip minimum | $4524132$ | $4524131$ | Sufficient filter for actual S only |

The integer endpoints can be checked against the total mass:

$$
\begin{aligned}
2(4524131)+9F&=45048397<WM,&2(4524132)+9F&=45048399>WM,\\
2(8524146)+7F&=45048397<WM,&2(8524147)+7F&=45048399>WM.
\end{aligned}
$$

Every actual S second owner has at least $F$ integer mass.
Hence first-owner strip mass at least $4524132$ implies actual S total mass at least
$4524132+F=8524147$. A lower strip cell only defeats that sufficient filter; it does not
yield a jointly realizable S pair.
A low C cell needs exact closed-membership, complete-label, and rational physical-parent
replay. A low actual S pair needs simultaneous-parent replay.
The C open-cell proof does not discard joint S boundary strata.

The frozen [H-160][h160] and [exp-158][exp158] registration instead requires C at least
$4524200$ and S first-owner strip mass at least $4524185$. These are distinct criteria.
The normalized C cutoff is 68 integer units lower, and the normalized sufficient S
cutoff is 53 lower. No measured charge is known to fall between either pair of cutoffs.
H-160 and [exp-158][exp158] remain unchanged, with `instrument_ready: false`, empty
results, and no scientific target invocation at the inspected source head.

## H-161 Local Stability Has a Smaller Scope

The [H-161 target][h161] and [independent audit][h161audit] found that the closed
literal $Q_0=[0,1]^2$ captures 19 atoms of mass $F$ and has no atom on its boundary.
Finite support and continuity of square-membership inequalities imply an open
rigid-motion neighborhood of $Q_0$ in which *all* atom memberships stay fixed.
Only its intersection with contained, admitted physical poses is relevant; $Q_0$ touches
two container walls, so an ambient neighborhood includes infeasible poses.
The independent review proves existence, not a numerical radius or a certified finite
pose cell.

Sufficiently small inward axis translations keep the selected T1 core’s mark ownership,
complete labels $\{3,4,11,12\}$, and 19-atom mass.
Four independently perturbed corner copies retain a positive inter-parent gap and union
mass $4F$. The one-parent and four-parent necessary budgets therefore still have
$1048233$ integer units of slack in a sufficiently small admissible neighborhood.
This does not prove an eleven-parent extension.
Changes of selected-core direction or angular chart need separate label checks, even
while parent mass is constant.
The T1 literal role offers neither forced label 0 nor 15, so it is not a refuter of the
normalized C/S helper.

## Bounded H-162 Registration Proposal

H-162 is **proposed, not allocated or registered** here.
Before any analysis treats the normalized thresholds as prospective target criteria, its
owner should freeze a separate contract with the exact source revision, 377 atoms, all
182 eligible C and S first-owner charts, both axis aliases, physical-parent conventions,
and the unchanged H-160/exp-158 registration.
An actual S second owner ranges over every admitted compatible chart satisfying its
ownership and absence-of-15 conditions; the 182-chart first-owner manifest does not
bound that quantifier.
Its claim would be equation (2), with C mass at least $4524132$ and actual S-pair mass
at least $8524147$ as the complete criteria.
The cheap S first-owner cutoff $4524132$ is a sufficient filter, not the definition of
the actual S condition.

The contract should record these outcomes before using a target receipt:

- A C minimum at most $4524131$: reject the helper only after a rational physical
  parent, closed membership, and complete labels replay, regardless of S.
- If C passes and the S strip minimum is at least $4524132$: accept the normalized local
  helper after source, revision, and control admission; the strip bound supplies the
  needed lower bound on every actual S pair.
- If C passes and the S strip minimum is at most $4524131$: the sufficient filter fails,
  and the helper stays unresolved until actual simultaneous S pairs are controlled.
  A replayed actual S pair at most $8524146$ rejects the helper; a complete admitted
  lower-bound proof that every actual S pair has mass at least $8524147$ accepts it.
  One high S pair alone cannot establish that lower bound.
- An incomplete sweep, revision mismatch, or control refusal: retain an unresolved
  instrument outcome, without a scientific verdict.

The intended input is the single preregistered exp-158 C/S target invocation after its
own exact-head readiness transition.
Reading its retained minimum receipt for a second mathematical comparison needs no
rerun; an actual-S pairing decision would require a separately controlled method.
If H-162 is registered after that target read, its use of the receipt must be marked
retrospective. Neither positive local helper nor H-161 stability establishes local
availability, coherent owner selection for every packing, adjacent-only T2 on its own,
or a stronger $s(11)$ bound.

[globalreview]: ../../../docs/project/reviews/review-2026-09-13-bc303-t2-global-bridge.md
[independent]: ../../../docs/project/reviews/review-2026-09-13-bc303-floor-normalized-t2-independent.md
[measure]: ../series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json
[floor]: ../series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md
[h160]: ../hypotheses/H-160-bc303-t2-charge-filters.md
[exp158]: ../series/series-000-smoke-and-calibration/experiments/exp-158-bc303-t2-charge-filters.md
[h161]: ../series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md
[h161audit]: ../series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union-audit.json

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
