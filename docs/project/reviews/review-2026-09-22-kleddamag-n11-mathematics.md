# Mathematical Review: Kleddamag’s `s(11) > 31/8`

The mathematical reduction in Kleddamag’s release is sound.
The pinned certificate claims the **strict bound** $s(11)>31/8=3.875$ for independently
rotated unit squares with disjoint interiors and boundary contact allowed.
It does not establish the exact minimum.
No blocking mathematical defect was found in the counting argument, the orientation and
centre coverage, the exact arithmetic, or the treatment of boundaries.

The complete local replay, independent premise audit and adverse controls pass.
The replay alone supports **V4/C3**. Two implementations of the same complete event-cell
method and additional premise controls do not supply the different complete method
required for C4. Under [epistemics.md](../../../epistemics.md), C5 requires C3 or C4
plus a mapped review artifact; it does not require C4. The complete rigorous replay and
discharged proof assumptions support $31/8$ in the Frontier’s verified lower-bound
field, with the source and local replay credited separately.
C4 is an additional confirmation level, not a prerequisite for that field.

This is the n=11 lane of the 2026-09-22 W1/W2 external-source research block, tracked by
`think-6xoc`. An Astra Max subagent reviewed the mathematics and checker code, wrote the
independent audit instrument, and completed the full replay.

## Source and Evidence

| Item | Identity |
| --- | --- |
| Repository | [Kleddamag/11-squares-certified-bound](https://github.com/Kleddamag/11-squares-certified-bound) |
| Reviewed commit | `6a733f339395c3514f2ab63d8c4aa64cf63c0b5a`, tag `v1.0.2` |
| Certificate | `global-certificate.json`, SHA-256 `57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458` |
| Container and parent sides | $L=191/50$, $A=764/775$, $L/A=31/8$ |
| Coordinate and weight denominators | $10^{10}$ and $10^9$ |
| Secondary source | Guzhou0806 R038, commit `32edfd3da78bf80a309398f552b3b602b9c45d6c` |
| Secondary source SHA-256 | `63e858e28c4dee40f5763a832e1cfdf1f1fce3a1e5c632d087525bf1ee20ed14` |
| Reconstructed secondary SHA-256 | `c1e76f97a9288b3ad7537a282fbf24437a96980ae66c5414bca0793ad5d39c0e` |

The
[retained source tree](../../../packing/resources/web/external-square-certificates-2026-09-22/kleddamag-11/README.md)
is immutable upstream material.
The
[independent audit receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/n11/independent-audit.json)
and
[replay directory](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/n11/full-replay/)
hold repository-generated evidence.
The executable audit is
[`audit_kleddamag_n11.py`](../../../packing/devtools/audit_kleddamag_n11.py).

The complete review covered the proof, `exact_mixed.py`, `integer_sweep.py`, the
reconstructed JavaScript checker and its R038 source, both replay coordinators,
`verify.py`, `independent_controls.py`, the threshold algebra check, the certificate,
the source’s verification receipts, and the attribution and reconstruction files.
The numerical optimizer and search history are not supplied as proof premises and are
not needed to verify the fixed certificate.

## What the Certificate Establishes

The certificate expands 679 site orbits to 5,284 distinct sites.
Most sites carry only threshold membership, rather than ordinary point weight.
The independent audit reconstructed every orbit and budget:

| Charge family | Positive orbits | Physical features | Budget in $10^{-9}$ units |
| --- | ---: | ---: | ---: |
| Ordinary points | 66 | 496 | 2,247,714,156 |
| Two of three | 132 | 1,020 | 3,188,007,592 |
| Two of five | 10 | 76 | 989,672,288 |
| Three of five | 142 | 1,124 | 4,574,085,908 |
| Total | 350 | 2,716 | 10,999,479,944 |

Every assigned closed core must receive at least 999,962,528 units.
Eleven such cores would require 10,999,587,808 units, exceeding the budget by exactly
**107,864 units**. The minimum charge is slightly below one; this is harmless because
the counting condition is $11\Gamma>M$, with no requirement to normalize $\Gamma$ to
one. The source reports these constants in
[`PROOF.md`, lines 7–27](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/PROOF.md#L7-L27).

There are 12,028 contiguous half-angle intervals, starting at zero and ending at
$T=207107/500000$. The exact excess $T^2+2T-1=309449/250000000000>0$ proves that their
union covers $\tan(\pi/8)=\sqrt2-1$. The certificate’s least strict core margin is
$10^{-12}$.

## Proof Audit

### Counting, including the two-of-five capacity

For a feature with $m$ distinct sites and threshold $k$, suppose $q$ pairwise disjoint
closed cores each contain at least $k$ sites.
The captured subsets belonging to those cores are disjoint, so $qk\le m$. A feature of
weight $w\ge0$ therefore contributes at most $\lfloor m/k\rfloor w$ across the cores.

In particular, two-of-five has budget **$2w$**, not $w$. The source uses the correct
capacity in both its mathematical argument and its budget computation.
Features may share sites with other features: each individual budget inequality remains
valid, and adding valid inequalities does not require independence of their supports.
[`PROOF.md`, lines 31–39](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/PROOF.md#L31-L39)
and
[`exact_mixed.py`, lines 26–47](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/exact_mixed.py#L26-L47).

The inclusion–exclusion coefficients are correct.
If exactly $h$ of the $m$ sites are captured, the signed expansion evaluates to

$$
\sum_{j=k}^{h}(-1)^{j-k}\binom{j-1}{k-1}\binom hj
=\mathbf1_{h\ge k}.
$$

The first difference in $h$ equals one at $h=k$ and zero thereafter, by the binomial
theorem. The proof’s first-difference formula follows from
$\binom{j-1}{k-1}\binom{h-1}{j-1}
=\binom{h-1}{k-1}\binom{h-k}{j-k}$. For two-of-five, the coefficients are $1,-2,3,-4$ on
subsets of sizes two through five; their absolute total is 49. For three-of-five it is
31, and for two-of-three it is five.
The exhaustive Boolean and disjoint-assignment checks passed locally.
[`PROOF.md`, lines 53–71](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/PROOF.md#L53-L71).

### Coverage of independently rotated parents

The eight square symmetries preserve the complete weighted charge system.
The checker expands each point orbit and checks every threshold orbit against all eight
images, including equal weights and absence of repeated sites within each feature.
One may therefore reflect or rotate a single parent placement into the folded angular
range, choose its certified core there, and pull that core back.
This does not assume that the eleven-square packing is symmetric.
[`exact_mixed.py`, lines 16–41](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/exact_mixed.py#L16-L41).

At half-angle $u$, write $c(u)=(1-u^2)/(1+u^2)$ and $s(u)=2u/(1+u^2)$. For a row
$(a,b,t,B)$, the rotated core fits strictly inside every associated parent when

$$
B\left(\cos\delta+|\sin\delta|\right)<A,
\qquad \delta=2\arctan u-2\arctan t.
$$

The endpoint dot/cross checks put the relative angles in $[-\pi/4,\pi/4]$. Because
$u\mapsto2\arctan u$ is increasing, the same range holds throughout the interval.
On that range, $\cos\delta+|\sin\delta|$ increases with $|\delta|$, whose maximum is at
an endpoint. The endpoint bound is consequently valid throughout the interval.
Strict containment is rechecked at the final parent side $A$; no remembered search
parameter is trusted.
[`exact_mixed.py`, lines 91–102](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/exact_mixed.py#L91-L102).

The independent audit also bypasses this endpoint-extremum argument.
It projects each of the four core vertices onto a parent axis, clears the positive
denominator $1+u^2$, and minimizes each resulting rational quadratic over $[a,b]$,
including an interior vertex when present.
All 48,112 strict inequalities pass.
The two parent axes have the same four extremal values by the core’s quarter-turn
symmetry.

### Coverage of every legal centre

At parent orientation $u$, its legal centres form $[A(c(u)+s(u))/2,L-A(c(u)+s(u))/2]^2$.
For $0\le u<1$, the corresponding angle lies in $[0,\pi/2)$, and $\cos\theta+\sin\theta$
has its only interior stationary point at its maximum.
Its minimum on an interval is therefore at an endpoint.
The union of the nested centre domains is exactly $[r,L-r]^2$, where

$$
r=\frac A2\min\{c(a)+s(a),c(b)+s(b)\}.
$$

The independent audit verifies the associated envelope inequality as a rational
quadratic on every interval.
It also checks that the centre domain has positive area.
The calculation covers every parent centre, even though the core side and orientation
are fixed separately for each row.

In core-aligned coordinates, a site is captured on a closed axis-aligned rectangle of
possible centres. Intersections of these rectangles implement the threshold expansion.
Their edge coordinates and the rotated domain’s vertex coordinates partition the
horizontal axis into slabs.
Within each slab, the polygon boundary is linear, so its complete vertical projection is
determined by the edge values at the slab endpoints.
A vertical open cell intersects the domain if and only if its upper edge exceeds the
projection’s lower endpoint and its lower edge is below the projection’s upper endpoint.
Convexity and positive area justify this use of the projection, including slabs incident
to polygon vertices.

The source computes precisely these strict intersections.
Its integer floor/ceiling expressions in the binary searches are exact because event
coordinates are integers: comparison with a rational projection endpoint is equivalent
to comparison with the appropriate floor or ceiling.
Both bounds are included in the review’s separate polygon-clipping control.
[`exact_mixed.py`, lines 50–89](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/exact_mixed.py#L50-L89).

The JavaScript scanner reaches the same extrema by a different formula.
For a centred physical domain $[-H,H]^2$ and positive $c,s$, its lower and upper
boundaries in rotated coordinates are

$$
v_-(u)=\max\{(cu-H)/s,(-H-su)/c\},\qquad
v_+(u)=\min\{(cu+H)/s,(H-su)/c\}.
$$

The lower boundary has its minimum at $u=H(c-s)$ and the upper boundary its maximum at
$u=-H(c-s)$. On a slab, clamping those two abscissae to the slab endpoints gives the
required extrema. The implementation’s factors of the rational rotation denominator
rescale these same formulas exactly.
Its separate $s=0$ branch returns the horizontal domain edges.
This explains why the JavaScript partition need not split at the two interior
polygon-vertex abscissae.
The geometry comes from the pinned
[R038 scanner, lines 18–21](https://github.com/Guzhou0806/n17-square-packing/blob/32edfd3da78bf80a309398f552b3b602b9c45d6c/certificates/R038/src/exact_parent_side_scan.js#L18-L21);
the published adaptation changes the charge rectangles and n=11 input constants.

### Arithmetic and boundary points

Python geometry uses arbitrary-precision integers after exact denominator clearing; only
event indices and accumulated weights enter fixed-width arrays.
The reconstructed JavaScript uses `BigInt` for geometric comparisons.
Its coordinate expansion through `Number` is exact for these pinned integer coordinates,
whose container extent is 38,200,000,000, below $2^{53}$.

The independently reconstructed total absolute expansion weight is **184,231,386,320**,
below the checked $2^{50}$ limit.
This bounds partial rectangle accumulations and leaves ample room in both signed 64-bit
integers and exact integer `Number` values.
The segment-tree query sentinels exceed all possible real charges.
JavaScript arithmetic involving its sentinel need not itself be exact when a positive
lazy increment is added, but such a value remains far above every genuine candidate and
cannot win a minimum query.
No numerical tolerance decides a geometric comparison or a theorem inequality.
The accumulators are in
[`integer_sweep.py`, lines 8–38](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/integer_sweep.py#L8-L38)
and the pinned
[R038 scanner, lines 16–17](https://github.com/Guzhou0806/n17-square-packing/blob/32edfd3da78bf80a309398f552b3b602b9c45d6c/certificates/R038/src/exact_parent_side_scan.js#L16-L17).

Dropping zero-area capture rectangles is valid only with the separate boundary argument.
Each original threshold charge is the indicator of a finite union of closed
intersections of site-capture sets.
Nonnegative weighted sums of these indicators are upper semicontinuous.
Every point of the closed positive-area centre domain is a limit of generic interior
points; hence a lower bound on all generic charges extends to every event line, tangency
and container-boundary centre.
Applying a positivity argument directly to the signed expansion would be invalid, and
the source correctly does not do so.
[`PROOF.md`, lines 73–77](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/PROOF.md#L73-L77).

Finally, each certified closed core lies in its parent’s interior.
Parent interiors are disjoint, so the closed cores are disjoint even when parents touch.
Counting therefore excludes a packing at $L/A=31/8$. Feasible packings with container
side at most four form a closed subset of a compact centre/orientation/side parameter
space; an interior overlap in a limit would persist under a small perturbation.
The minimum side is attained.
Exclusion at $31/8$ yields the strict inequality $s(11)>31/8$.
[`PROOF.md`, lines 79–85](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/PROOF.md#L79-L85).

## Replay and Adverse Controls

The local environment uses CPython 3.14.7, NumPy 2.3.5, Numba 0.67.0, llvmlite 0.49.0,
and Node.js 24.19.0. The numerical packages are isolated from the project environment.
The R038 scanner was reconstructed without a network request from the already retained
pinned source; its digest matched exactly.
The source and reconstruction hashes are mandatory in
[`prepare_secondary.py`, lines 15–51](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/prepare_secondary.py#L15-L51).
`check_integrity.py` accepted all 54 manifest entries.
The exhaustive threshold algebra checker passed.
The first-party instrument independently pins the release manifest and verifies all 54
files before importing source code or probing the launcher.
It refuses modified checkers and injected modules, and uses a fresh bytecode-cache path
so existing execution caches cannot override the reviewed source.

The independent instrument verifies all 48,112 containment inequalities, all 12,028
centre envelopes, the complete orbit structure, exact budgets, accumulation headroom,
and the gap calculation.
It also exercises the upstream verifier on malformed input:

- Negative ordinary or threshold weight, duplicate point orbit, incomplete charge orbit,
  repeated feature site, and out-of-range feature index are refused.
- An understated budget, missing angle interval, truncated angle range, incorrect
  container side, and insufficient counting margin are refused.
- A core equal to its parent, a core with exact zero containment margin, ambiguous
  charge schemas, and expansion weights exceeding the arithmetic guard are refused.
- Doubling the required minimum passes the structural checks but fails the exact
  coverage comparison: row zero has 1,000,047,518 units against 1,999,925,056 required.
- Invoking the complete launcher with `-O` refuses before any verification; its
  assertion guard also covers `PYTHONOPTIMIZE` and `-OO` through `__debug__`.

The instrument reconstructs the centre polygon using rational rotations, then uses
general polygon clipping on **all 34,909 slabs** of five selected rows.
It compares the resulting query ranges with the source scanner and compares the source’s
segment tree with direct integer array accumulation.
All comparisons pass:

| Row | Minimum units | Independently clipped slabs |
| --- | ---: | ---: |
| 0 | 1,000,047,518 | 6,385 |
| 1 | 1,000,047,518 | 6,415 |
| 6,014 | 1,000,047,518 | 7,267 |
| 11,962 | 999,962,528 | 7,421 |
| 12,027 | 1,000,047,518 | 7,421 |

Row 11,962 attains the published global minimum.
These controls cover 210,272,149 represented cells across the selected rows.
They validate implementation details on those rows and do not replace the complete
12,028-row sweeps.

The
[complete launcher receipt](../../../packing/resources/web/external-square-certificates-2026-09-22/receipts/n11/full-replay/RESULT.json)
records `PASS_FRESH_PORTABLE_FULL_VERIFICATION`. Both complete sweeps cover all 12,028
intervals, have identical 11-bin charge histograms, and recover the exact minimum and
budget stated above.
Every JavaScript range has no escape rows.

| Local replay phase | Coverage | Recorded seconds |
| --- | --- | ---: |
| Python exact sweep | 86,299,918 slabs; 511,649,694,680 represented open cells | 1,501.120 |
| JavaScript BigInt sweep | 86,275,862 slabs across all three ranges | 1,790.011 |
| Exact premise and boundary controls | 48,112 quadratic inequalities; 5,586 direct boundary centres | 277.972 |

The recorded phase times sum to 3,569.104 seconds, about 59.5 minutes, under concurrent
research and validation work.
The boundary samples have minimum charge 1,000,047,518 units.
They are controls on selected rows, while the complete sweeps and boundary argument
establish the universal coverage claim.
The local slab and cell totals match the source’s published totals.
The difference is **24,056 slabs, exactly two per interval**. The code explains it:
Python inserts all four polygon-vertex abscissae, whereas the JavaScript sweep inserts
only the two horizontal extrema and handles the other two vertices through its clamp
formula. Both implementations exclude exterior slabs.
Python also merges and cancels identical charge rectangles, so its rectangle-edge set is
a subset of JavaScript’s unmerged edge set; it can gain at most those two interior
vertex cuts per row.
The observed aggregate difference attains that upper bound on every row.
The required agreement is the certified minimum and charge histograms, not equality of
this partition-dependent diagnostic.
See
[`exact_mixed.py`, lines 55–77](https://github.com/Kleddamag/11-squares-certified-bound/blob/6a733f339395c3514f2ab63d8c4aa64cf63c0b5a/exact_mixed.py#L55-L77)
and the
[R038 clamp sweep, lines 18–21](https://github.com/Guzhou0806/n17-square-packing/blob/32edfd3da78bf80a309398f552b3b602b9c45d6c/certificates/R038/src/exact_parent_side_scan.js#L18-L21),
retained in the hash-pinned n11 reconstruction.

The retained audit can be reproduced from the repository root with:

```shell
packing/.venv/bin/python3 packing/devtools/audit_kleddamag_n11.py \
  packing/resources/web/external-square-certificates-2026-09-22/kleddamag-11/global-certificate.json \
  --upstream-tree /path/to/writable/pinned-source-copy \
  --upstream-python /path/to/upstream-runtime/bin/python \
  --output /path/to/new-audit-receipt.json
```

Use the source README’s complete `verify.py --output-dir` command in that writable copy,
with the pinned packages above.
The audit’s optional `--full-replay` argument checks the fresh launcher receipt, exact
row coverage, both histograms, interval partition, certificate identity, and counting
constants. It also checks the bound and parent-side headers against the certificate and
reconstructs the Python slab/cell and boundary-sample totals.
Each JavaScript range receipt must match its declared span and that span’s Python
histogram; the sum of its slab counts must match the JavaScript aggregate.
These checks establish consistency of the recorded computation; they are not signed
attestations of execution.
The source’s immutable archive should not acquire generated caches or replay files.

The first-party auditor and its
[six focused tests](../../../packing/tests/test_kleddamag_n11_audit.py) pass Ruff,
BasedPyright and pytest.
The tests cover an interior quadratic minimum missed by endpoint checks, an oblique
clipped domain with internal vertices, an understated two-of-five budget, a core that
touches its parent exactly, altered or injected checker code, and replay headers
detached from their certificate or interval range.

## Integration Findings

**No mathematical blocker was identified.** The following distinctions should survive
integration into the frontier and future research tools.

1. **Record the strict rational bound.** The source proves $s(11)>31/8$, while the
   looser statement $s(11)\ge3.875$ is also true.
   Retain the strict theorem in the result record rather than rounding it to an
   unexplained decimal.
   Keep the existing verified Trump upper bound.
   The exact minimum remains unresolved.

2. **Keep assurance separate from numerical strength.** The fresh complete replay
   supports V4/C3. Its larger lower bound supersedes T-026 numerically, while T-026’s
   V4/C5 evidence remains valid historical evidence.
   The Frontier’s verified lower-bound field denotes the largest bound the repository
   can certify on its own evidence; its admission rule requires a rigorous proof or
   replay with discharged assumptions, not C4. This review and complete exact replay
   therefore support updating that field to $31/8$, while preserving the historical
   T-026 record and the source/replay distinction.
   See the [case schema](../../../packing/frontier/square-packing-case.schema.yaml) and
   [Frontier admission rule](../../../packing/frontier/README.md#adding-or-reviewing-a-result).
   The source itself now states that the two scanners provide implementation diversity
   within one method. A different complete coverage decision, such as interval branch and
   bound, is needed for C4. Neither this review, the quadratic premise audit, nor
   selected event-centre tests supplies that decision.
   A result mapped to this review may satisfy the separate C5 review-artifact predicate
   without satisfying C4.

3. **The adaptive parent-centre catalogue must remain part of the theorem.** The
   existing native T-026 format uses a uniform direction net, one core side, and its own
   admissible-centre contract.
   This release assigns a separate side $B$ and direction $t$ to each parent interval
   and scans a parent-centre envelope.
   Importing only the sites and weights into the old format would discard proof
   premises. A native adapter must preserve and check all four row values and the final
   parent side, or the pinned external checker should remain the decision procedure.
   There is also a measured size mismatch: all 5,284 sites are active, exceeding
   `interval.MAX_INTERVAL_ATOMS = 4096`. The positive feature table has 2,716 rows of
   width five, or 13,580 slots, above `threshold_interval.MAX_MEMBER_SLOTS = 8192`. A
   native interval implementation needs a measured batching or memory change as well as
   the new domain contract.
   Removing unused sites cannot close this mismatch, and raising the guards without
   measuring their allocation assumptions is not a verified adaptation.
   A concrete candidate is a 2,048-box batch: the site mask would occupy 10,821,632
   bytes, the gathered member mask 27,811,840 bytes, and the `int16` count array
   11,124,736 bytes, all below the existing respective 16, 32 and 32 MiB ceilings.
   Those are dimension calculations, not a measured implementation; a parameterized
   batch limit still needs peak-allocation and runtime measurements.
   Before attempting all 12,028 rows, test the first, last and weakest rows for the
   native interval method’s documented inability to resolve some exact event seams.

4. **General threshold atoms already exist in this repository.**
   [`sqpack.fractional.threshold`](../../../packing/src/sqpack/fractional/threshold.py)
   already states the same $\lfloor m/k\rfloor$ budget and general inclusion–exclusion
   formula, including two-of-five and three-of-five.
   The source credits T-026 at `7ccb679cc0827d10ee80e2cd1988c8a07d65dfdc`, rounds and
   expands the site supports, reoptimizes weights, and replaces the angle/core
   catalogue. Those new fixed certificate data and the resulting bound are the
   contribution this review verifies; it does not establish novelty of the general
   threshold principle or a reproducible search algorithm.
   The final certificate changes several ingredients together.
   It does not provide an ablation attributing the improvement to five-site features,
   movable supports, the parent-centre restriction, or the adaptive angle catalogue
   individually. Such an attribution would require controlled certificates or reruns.

5. **Use the complete launcher for admission.** The JavaScript scanner is a range
   coverage checker. It relies on other stages for full D4 validation, strict core
   containment and global angle coverage, and its parent side is a command-line
   argument. Its partial-range `PASS` must never be interpreted as a global theorem.
   The complete launcher pins the certificate, propagates the final $A$, runs the
   premise checks, requires full interval coverage and matching histograms, and refuses
   optimized Python execution.
   The pin also closes generic JSON parsing ambiguities for the fixed release.
   A future general importer should reject duplicate keys and nonexact numeric fields
   explicitly.

6. **Preserve the external-source boundary.** The JavaScript source is reconstructed
   from a pinned Guzhou file because the source release identifies no general code
   licence for that file.
   Keep its provenance and scope notices attached, retain the verification input, and do
   not silently treat the derivative as project MIT code.
   The Python adaptation and the imported certificate also retain their stated code and
   data attribution. This review makes no new legal determination.

7. **Reprioritize n=11 numerical targets below 3.875.** Such targets are now dominated
   as improvements to the global lower bound.
   They may remain useful controls or experiments on a different method.
   A new bound campaign should declare its target relative to 3.875; a confirmation
   campaign should target the independent method needed to increase this result’s
   confirmation level.

## The Tweet’s Numerical Comparison

Using T-026’s exact expression

$$
C=\frac{955000\sqrt{518400042893309449}}{179696714646249}
=3.826447410572939744\ldots
$$

and the retained upper approximation $U=3.877083590022814177\ldots$ gives

$$
100\frac{3.875-C}{U-C}=95.88517529274348\ldots\%,
\qquad U-3.875=0.002083590022814177\ldots.
$$

The stated **95.89%** is the correctly rounded fraction of that particular
lower-to-upper interval removed.
It is not a probability of optimality or a statement that 95.89% of a mathematical proof
is complete. The exact rational bound and the unchanged upper construction should carry
the frontier entry; the percentage is useful context.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
