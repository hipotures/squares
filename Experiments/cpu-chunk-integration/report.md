# Ordered four-direction chunks: accepted production integration

## Decision and correctness

**ACCEPT.** The input production commit was
`5f10bffeb207d5bc598a6244f11375cee3418d62`; ordered chunks were committed
separately as `011aa1b5f39457de1e2d9f5589b3df3f04e36575`. One persistent
production process pool still serves every round. Each task handles up to four
consecutive directions, and the parent flattens ordered `pool.map` results.
The serial path, worker-count convention, row math, and LP path are unchanged.
There is no reusable-buffer machinery.

The final accepted commit was checked at workers 1, 4, 8, and 16. Every run
had **23 rounds, 5,842 rows, objective `12.217676366606236`, least covered
`0.9999999999998309`**, and coverage convergence. Per-round held rows, added
rows, violations, support, and the reported objective sequence matched the
pre-change control. Final direction order, centres, every coefficient, and
the full per-round weight sequence matched the accepted retained fixtures
bitwise. [`raw/correctness.json`](raw/correctness.json) has the decisions and
matrix hashes. The identical matrix lets the previously retained exact
row/witness checks apply. Focused tests covered 0, 1, 3, 4, 5, and 9 directions,
including the final partial chunk, both serial and process-pool solving,
result order, and a worker exception. Thirty-one focused tests passed; Ruff
and source type checks passed with only two private-helper test warnings.

The primary 16-worker acceptance evidence is three **adjacent long full-solver
pairs**, with sample 2 in reverse order. All batch durations were 18.3–21.7
seconds. Paired savings were **0.372, 0.204, and 0.489 s/solve**; median
**0.372 s**, or **10.5%** of the paired control median 3.534 s. Even the
smallest pair saved 5.9%. The fresh unpaired controls drifted during the VM
run (16-worker wall CV 3.8%), so their larger median difference is not used
as the production gain. The serial median was 11.172 → 11.144 s, a 0.028 s
change well within normal variation, with no semantic serial change.

## Final production baseline

Each entry is the median of three independent unprofiled batches. The complete
solves include pool startup and LP. Every timed sample lasted at least 18
seconds, and the raw files record pre-run load and all per-round timings.

| Workers | Batch wall | Wall/solve | Separation | LP | Other | Wall CV |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 22.288 s | 11.144 s | 10.024 s | 1.083 s | 0.027 s | 0.17% |
| 4 | 20.239 s | 5.060 s | 3.853 s | 1.165 s | 0.040 s | 0.18% |
| 8 | 20.506 s | 4.101 s | 2.877 s | 1.180 s | 0.045 s | 0.83% |
| 16 | 21.362 s | **3.052 s** | **1.821 s** | **1.182 s** | **0.048 s** | 1.89% |

The final 16-worker wall range is 3.011–3.149 s. Sixteen remains fastest
among the tested worker counts. In that configuration, separation is **59.7%**,
LP **38.7%**, and other setup/bookkeeping **1.6%** of solver wall. At one worker,
separation remains about 90.0% of wall. The current first round costs about
0.44 s at 16 workers and 1.14 s serial (separation plus LP).

## What chunking changed

A fresh 16-worker, in-memory replay of the same 23 accepted rounds used one
direction per task as the control. It kept the same 181 directions per round
and complete row reconstruction; only pool granularity differed. The later
three-sample replay set is used here because it is adjacent to the short
profile and has lower VM variation. It excludes pool startup and LP.

| 16-worker replay | One direction/task | Four directions/task | Difference |
|---|---:|---:|---:|
| Separation wall | 2.208 s | **1.775 s** | 0.433 s / 19.6% |
| Aggregate worker CPU | 26.876 s | **23.393 s** | 3.483 s / 13.0% |
| Parent CPU | 1.258 s | **0.466 s** | 0.792 s / 63.0% |
| Parent result processing | 0.349 s | **0.134 s** | 0.214 s |
| Parent dispatch | 0.050 s | **0.015 s** | 0.035 s |
| Parent `next(result)` | 1.791 s | **1.619 s** | 0.172 s |
| Worker CPU inflation vs current serial | 2.54× | **2.21×** | 0.33× less |

`next(result)` includes computation, waiting, transport, and deserialization;
it is not itself a pure IPC measure. These intervals and parent CPU overlap
worker execution. The replay establishes that task granularity was a real
bottleneck: fewer result objects and submissions sharply reduced parent work,
and aggregate worker CPU fell. A previous set, retained in `raw/`, had more VM
variation but also placed all chunked wall samples below all one-direction
samples. The concurrency penalty remains substantial; chunking reduced it
without eliminating it.

## Short current separation profile

The timer copy of the current event-grid routine uses the packaged row-major
second prefix pass. It matched production **bitwise on 543 real calls and
619,414,779 mass cells** from rounds 0, 18, and 22. The complete profiled
replay also matched the accepted row order and centres. The profiled 16-worker
wall median was 1.787 s; the nearby unprofiled replay median was 1.775 s,
about **0.7% timer overhead** at the observed VM load. The earlier unprofiled
16-worker set was 1.89 s, showing why old and distant readings are not used
to claim exact profiler overhead.

The `critical path proxy` sums each phase on the worker that finished last in
each round. It is useful for ranking but is not a causal wall partition: other
workers and parent work overlap. The worker elapsed column sums operation
durations across all tasks; it is **not aggregate CPU**. Aggregate worker CPU
for the nearby unprofiled replay was 23.393 s.

| Worker phase | Critical path proxy | % of 3.052 s solver | Aggregate worker elapsed | Confidence |
|---|---:|---:|---:|---|
| Prefix accumulation | 0.613 s | 20.1% | 8.803 s | Medium; phase timer, path proxy |
| Slab reachability and compaction | 0.425 s | 13.9% | 6.141 s | Medium; phase timer, path proxy |
| Native top-13 selection | 0.239 s | 7.8% | 3.601 s | Medium; phase timer, path proxy |
| Difference scatter/grid setup | 0.198 s | 6.5% | 2.844 s | Medium; phase timer, path proxy |
| Candidate reconstruction | 0.059 s | 1.9% | 0.846 s | Medium; phase timer, path proxy |
| Projection, sorting, domain bounds | ~0.059 s | ~1.9% | ~0.839 s | Medium; grouped small phases |

The profiled parent spent about 0.142 s/replay processing returned rows,
0.014 s dispatching, and 1.584 s in ordered result waits. The unprofiled
nearby values were 0.134, 0.015, and 1.619 s. The full-solver separation
timer is 1.821 s; the replay is 1.775 s because pool startup and LP
interleaving are outside the steady-state replay. The remaining event-grid
work is mostly its already-in-place prefix over 2.61 billion grid cells.

## Current scaling

All entries are medians of three 15–22-second unprofiled replay batches over
the full 23-round workload. Worker CPU is measured from `/proc` CPU ticks;
effective cores = worker CPU / wall. Inflation uses the same current serial
replay's 10.565 worker CPU seconds.

| Workers | Separation wall | Worker CPU | Effective cores | Speedup | Efficiency | CPU inflation |
|---:|---:|---:|---:|---:|---:|---:|
| 1 | 10.569 s | 10.565 s | 1.00 | 1.00× | 100% | 1.00× |
| 4 | 3.784 s | 14.582 s | 3.85 | 2.79× | 70% | 1.38× |
| 8 | 2.683 s | 19.950 s | 7.43 | 3.94× | 49% | 1.89× |
| 16 | **1.775 s** | **23.393 s** | **13.18** | **5.95×** | **37%** | **2.21×** |

The guest VM still shows strong CPU-time inflation under concurrency. Its
specific cause remains unresolved; the counters do not establish physical
DRAM saturation.

## Memory, remaining opportunity, and limits

Chunking did not change per-direction arrays: about **20.88 GB** of fresh grid
arrays and **15.13 GB** of compact float arrays are requested over one complete
separation replay. These are cumulative logical allocation sizes, not peak
RSS or measured DRAM traffic. In the nearby 16-worker replay, minor worker
faults were ~504,000/replay for one-direction tasks and ~405,000 for chunks.
Workers' observed RSS was roughly 80–94 MiB each; summed RSS would double
count shared pages. Full-solver parent high-water RSS was about 570–596 MiB
at 16 workers. `perf_event_paranoid=4` blocked guest PMU counters, so no
physical DDR bandwidth claim is made. The earlier STREAM-like and logical
traffic measurements remain context, not a fresh hardware measurement.

**MODERATE OPPORTUNITY, unproven.** Chunking has already removed the one clear
dispatch bottleneck. The current LP consumes 1.18 s/solve and previous direct
LP profiling found it dominated by retained-basis HiGHS reoptimization.
Prefix accumulation remains the largest separation phase, but it already uses
in-place NumPy plus the packaged row-major C pass. The one credible next
research target is **direct top-k selection from slab intervals without the
15.13 GB compact float output**. Current slab compaction plus top-13 selection
account for about 0.664 s of the 16-worker path proxy (21.8% of total wall).
That is an upper bound on a standalone saving, not a predicted gain: a direct
scan could have poorer cache or concurrency behavior. It should be tested
separately against exact stable-selection semantics before integration.
No further optimization was implemented in this task.

**Proven:** ordered chunks preserve the accepted deterministic trajectory;
three adjacent full-solver pairs favor them; fresh replay reduces parent work
and aggregate worker CPU; 16 workers remain fastest among 1/4/8/16; LP is now
38.7% of solver wall; the current event-grid timer copy is bitwise faithful.

**Unresolved:** exact causal split within ordered result waits; physical memory
traffic and DRAM saturation; whether a direct slab selector improves full
solver wall; the source of short-term VM scheduling drift.

All benchmark and profile data, scripts, environment information, and
correctness evidence are retained here. Experimental instrumentation was
limited to research scripts and was not installed in production. No GPU work
was performed. No push was performed.
