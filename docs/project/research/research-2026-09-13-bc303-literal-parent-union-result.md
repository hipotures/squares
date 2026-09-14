# BC303 Literal Parent-Union Mass

Date: 2026-09-13. Experiment:
[exp-159](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md).

**The exact closed parent `Q0=[0,1]^2` has mass `800003/800000` in the frozen BC303
point measure.** At source scale `W=4000000`, its integer mass is `N=4000015`. The
parent-union resource inequality therefore survives both predeclared tests.
It gives no nonextension result for Q0 or the four specified corner copies.

## The Frozen Decision

The
[H-161 registration](../../../packing/campaign/hypotheses/H-161-bc303-literal-parent-union.md)
fixed the tests before the target read.
For eleven hypothetical closed unit-square parents with pairwise disjoint interiors, a
chosen strict core of each parent outside a charged set `I` is disjoint from the union
of the charged parents and the other outside cores.
The imported
[BC303 retained sweep](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-303-first-wave-selection.md)
gives each such core mass at least `1+g`, with `g=3/800000`. The
[raw source](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json)
gives total mass `M=22524199/2000000`. Thus a necessary inequality is

```text
mu(Q_I) + (11-k)(1+g) <= M, where k=|I|.
```

The source scale gives `WM=45048398` and `W(1+g)=4000015`. For one literal Q0, the
inequality requires `N<=5048248`, so `N>=5048249` would reject its extension.
The four corner images of Q0 are pairwise separated by `96/25-2=46/25`; weighted D4
invariance makes their union mass `4N`. The four-parent inequality requires
`4N<=17048293`, so `N>=4262074` would reject that tuple’s extension.
The four-corner comparison is H-161’s primary criterion.

## Exact Result and Replay

The
[target receipt](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union.json)
records `N=4000015`, the frozen source revision
`39714308ce2081abbd76624387d134fee4be6deb`, source SHA-256
`c30b600d3d35f3851f0595e2c42962bf353721f9e72b0539bd691aec522e876f`, and clean execution
head `f27c8ec7c8ebeb8a9b369c1c6f7efef4b531c359`. The reader’s admitted commit was
`641beab7020570e71680950a92535073c8f698bd`; its file bytes were unchanged at execution.
The source is the 17,616-byte Git blob `db8abed8f716a4173b47bcfb19f8e045b44513d1`.

An
[independent raw-source audit](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union-audit.json)
parsed all 377 rational atoms without importing the production reader.
The retained [audit tool](../../../packing/devtools/audit_bc303_parent_union.py)
reproduced the audit JSON byte for byte from the raw source and target receipt.
It confirmed 377 distinct positive sites, total mass, integer weight scale, and the
weight of every atom under all eight D4 maps.
Closed Q0 membership captures 19 sites.
All 19 lie in the already disclosed strict T1 core `[23/20000,19977/20000]^2`; the
parent adds no source atom, and no captured site lies on Q0’s boundary.
Each corner image captures 19 disjoint sites and `4000015` units.
The union has `16000060` units.

| Necessary test | Measured units | Maximum surviving units | Unused budget |
| --- | ---: | ---: | ---: |
| One literal Q0 | 4,000,015 | 5,048,248 | 1,048,233 |
| Four corner copies | 16,000,060 | 17,048,293 | 1,048,233 |

The unused budget is `1048233/4000000` in measure units.
The one target invocation took 0.16 seconds of external wall time.
Before it ran, the source-distinct reader review accepted the 377-atom source, closed
union arithmetic, D4 transport, source and execution binders, and four negative
controls. The preregistered checkout passed all 32 records checks.

## Scope

This is a failure of the two named necessary resource tests to reject.
It does not construct the seven missing parents, prove that Q0 or the tuple extends to
eleven parents, or test other parent poses.
It does not exclude a pose cell: pointwise closed membership gives no uniform lower
bound under perturbation.
The imported universal core floor remains a premise from the BC303 sweep; the raw JSON
declaration alone is not its proof.
The result does not settle owner selection, continuous angles, global routing, or a
stronger bound on `s(11)`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
