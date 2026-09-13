# H-161 Literal Parent-Union Result: Independent Audit

Date: 2026-09-13. Reviewed result head: `73f5f6939fef92eb3a6bbf594343e33b25249bff`.

**Verdict: accept the recorded rejection of H-161 for its two named necessary tests.**
The frozen parent `Q0=[0,1]^2` has `4,000,015` integer mass units.
Its four separated corner images have `16,000,060` units in their union.
Both values are `1,048,233` units below their respective maximums for a hypothetical
eleven-parent extension.
The tests therefore do not exclude either literal configuration.
They also do not exhibit an extension.

The review covers the
[preregistered H-161 claim](../../../packing/campaign/hypotheses/H-161-bc303-literal-parent-union.md),
[exp-159](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-159-bc303-literal-parent-union.md),
the
[target receipt](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union.json),
the
[retained independent audit](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union-audit.json),
and the
[result report](../research/research-2026-09-13-bc303-literal-parent-union-result.md).
It does not redo the prior proof of the parent-union inequality or the imported BC303
universal strict-core floor.

## Checks

The H-161 and exp-159 thresholds, the source revision, and the accepted reader were
committed at `f27c8ec7` before the target receipt existed.
The target receipt binds its execution to that commit.
Git gives the same reader blob `71663a4da2a1ff1d7bb157e1e934248e8112da6a` at the
accepted reader commit `641beab7`, execution commit `f27c8ec7`, and reviewed result
commit `73f5f693`. The post-target change to H-161 adds the measured disposition without
changing its criterion.

I inspected the source-bound reader and the separately implemented
[audit tool](../../../packing/devtools/audit_bc303_parent_union.py), then ran the audit
under the project Python 3.14 interpreter.
It reproduced the retained audit JSON byte for byte from the frozen 377 rational atoms
and the target receipt.
It checks all eight weighted D4 transforms, distinct sites, total measure, closed parent
membership, the four disjoint corner groups, their union, both budgets, and source and
executing-reader Git identities.
All 19 atoms in `Q0` also lie in the disclosed strict T1 core; none is on the parent
boundary. A receipt with the integer mass changed to `4,000,016` was refused with
`AuditError: literal parent mass`.

The preregistered arithmetic is:

```text
W M = 45,048,398,  W(1+g) = 4,000,015
one-parent budget  = 45,048,398 - 10(4,000,015) = 5,048,248
four-parent budget = 45,048,398 -  7(4,000,015) = 17,048,293
N = 4,000,015;  four-corner union = 4N = 16,000,060
slack in each comparison = 1,048,233
```

The four unit parents are separated by `q-2=46/25`, so the audit’s disjoint source
groups agree with the geometric union premise.
The result report and generated registers use the same numbers and describe H-161 as
rejected. The result branch passed its records and edit tiers; the scientific target was
invoked once and was not rerun for this review.

## Limits

The inequality is necessary, so passing it does not construct the seven omitted parents.
The audit does not minimize parent-union mass over other poses or perturbation cells.
The 19 shared core/parent atoms show only that this literal parent adds no source atom
beyond its selected T1 core.
Other parent poses, different weights, other unavailable marks, owner selection, and
complete n=11 exclusion remain open.
The established bound remains the T-026 value.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
