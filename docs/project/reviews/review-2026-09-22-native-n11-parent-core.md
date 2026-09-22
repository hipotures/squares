# Native Adaptive Parent-Core Verification

`think-d010` implements a candidate complete-coverage method for the retained Kleddamag
`n=11` certificate. The workflow entry is W7, pipeline improvement, followed by W2,
factual verification.
This is Session 153, stacked on PR 222; PR 221’s earlier result identifiers remain
reserved to that work.

## Acceptance Rule and Work Slices

Before the first native run, the acceptance rule is fixed: all 12,028 source rows must
pass the exact premises and the interval coverage decision, with no stalled or
budget-exhausted boxes.
The decision threshold is the source’s exact `Gamma = 999962528/1000000000`, and the
exact counting budget must be strictly less than `11 Gamma`. A partial row selection is
a pilot, even if every selected row passes.
An unresolved box is a refusal to certify; it is not evidence against the external
certificate, which already has a complete event-sweep proof.

The first pilot selects rows 0, 11962 and 12027: first, weakest and last.
Record wall time, boxes, stalls, threshold units, peak process RSS and traced allocation
peak. The default batch holds 2,048 boxes, preserving the existing 16 MiB site-mask and
32 MiB gathered-member and count-array ceilings.
Measure before deciding the full-run schedule.
Exact seam fixtures must refuse unless a separately justified method closes them.
No full-run estimate is itself permission to relax a proof premise.

The integration checkpoint is planned within four hours, with slices of at most 30
minutes. Slice 1 establishes the theorem, importer and domain API; slice 2 adds adverse
tests and runs the pilot; slice 3 resolves any demonstrated completeness obstacle and
sizes the full run; later slices perform complete coverage, independent review, record
reconciliation and the scoped push checks.
The native implementation lane owns source, tool and this report.
The Sol test lane owns `packing/tests/test_fractional_parent_core.py`; the coordinator
independently reviews the mathematics and reconciles PR 221. These are estimates and
integration boundaries, not stop conditions.

## Proof Contract

The source’s four row values `(a,b,t,B)` and final parent side `A` remain separate.
For a parent half-tangent `u`, legal centres form `[h(u),L-h(u)]²`, where

$$
h(u)=\frac A2\frac{1+2u-u^2}{1+u^2}.
$$

On `0 <= u < 1`, the derivative has the sign of `1-2u-u²`, so its only interior
stationary point is a maximum.
The centre domains are nested, and their union over a row is exactly `[r,L-r]²` with
`r=min(h(a),h(b))`. This also covers the source’s last rational endpoint, which lies
slightly beyond `tan(pi/8)`.

The native premise checker projects each core vertex onto a parent axis and minimizes
the resulting rational quadratic on the full interval, including any interior minimum.
The same four extrema cover the other axis by quarter-turn symmetry.
A strictly positive margin places the closed core in the parent’s interior.
Weighted D4 symmetry allows each parent orientation to be folded independently.
A contiguous row partition starting at zero and ending with `b²+2b>=1` covers all folded
parent orientations.

The coverage search uses directed rounding to bound site membership throughout boxes of
centres in the core frame.
It counts threshold tokens directly.
It does not call the external event sweep or use its signed inclusion–exclusion
expansion. The initial box encloses the complete parent-centre domain, domain tightening
only removes proved exterior points, and both children cover each split box.

For each threshold atom, pairwise disjoint closed cores consume disjoint site tokens.
An `m`-token, `k`-threshold feature therefore contributes at most `floor(m/k)` times its
weight. If every parent has a core of charge at least `Gamma` and the total budget is
less than `11 Gamma`, eleven parents cannot fit.
Uniform scaling gives the same exclusion for eleven unit squares at `L/A=31/8`;
compactness and attainment make the lower bound strict.
Complete native coverage and the premise proof together are the claim to review for C4.
Pilot success alone changes no confirmation level.

Attainment follows from bounded translations, compact orientations and closed
containment and non-overlap constraints: a convergent sequence of feasible packings has
a feasible limit. An interior overlap in the limit would persist in sufficiently nearby
packings.

## Reproduction

From `packing/`, with the project Python 3.14 environment:

```shell
PYTHON_CPU_COUNT=2 uv run --frozen --all-extras --group dev \
  python -m devtools.verify_kleddamag_n11_native \
  --pilot \
  --output /path/to/pilot.json
```

The tool binds the input to the reviewed source bytes and records its actual Git commit,
dirty flag, Python, platform, selected rows and memory measurements.
Use `--all` only for a deliberately scheduled complete run.

## Pilot Evidence

The first, weakest and last rows all certify, with 20,255, 14,387 and 11,763 boxes
respectively, zero stalled boxes and no exhausted work budgets.
Their certified lower bounds are `1000047518`, `999962528` and `1000030057` in units of
`1/1000000000`. Pruning at `Gamma` proves the required inequality; these lower bounds
need not equal the source event sweep’s exact minima.

| Batch size | Row 0 seconds | Row 11962 seconds | Row 12027 seconds | Receipt |
| --- | --- | --- | --- | --- |
| 256 | 2.342 | 1.548 | 1.420 | [Serial 256](../../../packing/campaign/agent-sessions/session-153-native-pilot-batch256.json) |
| 512 | 2.246 | 1.602 | 1.194 | [Serial 512](../../../packing/campaign/agent-sessions/session-153-native-pilot-batch512.json) |
| 2048 | 1.659 | 1.140 | 0.928 | [Serial 2048](../../../packing/campaign/agent-sessions/session-153-native-pilot.json) |
| 2048, two workers | 1.832 | 1.312 | 0.887 | [Parallel 2048](../../../packing/campaign/agent-sessions/session-153-native-pilot-two-workers.json) |

These are search times for each row, excluding import and exact-premise validation.
The three batch sizes produce the same lower and upper bounds and box counts.
The complete run will use 2,048 and two workers.
The parallel pilot’s largest individual child-process RSS was 384,925,696 bytes; that
measurement is not a combined-process peak.
At this batch size the source’s site mask uses 10,821,632 bytes, the gathered member
table 27,811,840 bytes and the count array 11,124,736 bytes, each within the existing
temporary-array ceiling.
Independent static caps also bound one-row batches to 8,192 sites and 16,384 padded
member slots.

All 39 focused adverse tests pass, including exact-type rejection, byte-bound source
import, malformed interval partitions, parent-domain refutation checks, D4 token
multiplicity, exact-seam refusal, Gamma-aware budget exhaustion and serial/parallel
agreement. The combined interval regression selection passes 98 tests, with two existing
Linux-only pool tests skipped on macOS and ten slow or exhaustive tests deselected.
No pilot receipt has `accepted=true`, and no confirmation-level promotion has been
recorded.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
