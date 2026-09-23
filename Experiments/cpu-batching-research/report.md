# P2 worker buffer and batching experiment

Pinned accepted input: `2a2efa39edb179128184f19d6a4235a6bbcaebcc`.
This is a research-only experiment. Production code was not changed. All
variants replay the same 23 accepted rounds and 181 directions per round from
RAM with persistent pools. A warmup for each variant/count matched the full
accepted coefficient matrix, row order, and centres; every timed replay
matched row order and centres. All important timed batches exceeded 10 seconds;
the batch size, pre-run VM load, min/max/CV, CPU and fault deltas are in
`results.json` and the individual `raw/*.json` files.

## Variants and interpretation

**A** is the production direction task per worker call. **B** keeps the same
tasks but reuses a C-contiguous, geometrically grown grid buffer and compact
mass buffer per worker. The grid is fully zeroed on every call and the compact
values are fully overwritten, preserving the production algorithm. **C** adds
four consecutive directions per task to B, returning results in original
direction order. The optional **D** diagnostic chunks four directions but
keeps A's fresh per-direction allocations. This isolates chunking from reuse.

The output buffers in A request about 36.00 GB per complete replay, based on
the accepted shapes: 20.88 GB grid plus 15.13 GB compact values. B/C move that
large buffer allocation into warmup. Per-replay `scratch_allocated_bytes`
counts only *new growth* after warmup; it does not include smaller NumPy
temporaries, projected arrays, or the resident scratch already held by a
worker. The logical grid/compact byte counters in B/C are workload volume,
not measured DRAM traffic. Summed RSS over workers double counts shared pages.

Fresh warmups requested these cumulative scratch-buffer bytes across all
workers (the buffers grow geometrically, so this includes superseded storage):

| Workers | B scratch growth | C scratch growth |
| ---: | ---: | ---: |
| 1 | 37.8 MB | 37.8 MB |
| 2 | 58.6 MB | 58.6 MB |
| 4 | 83.5 MB | 100.0 MB |
| 8 | 166.6 MB | 182.4 MB |
| 16 | 330.8 MB | 345.5 MB |

The exact one-warmup records are in `raw/warmup-*.json`. A requests about
36.00 GB of fresh large outputs *per replay* instead; comparing these
requested bytes does not directly compare allocator CPU cost or physical
memory traffic.

## Main A/B/C scaling results

Medians of three independent long batches per setting. Worker CPU is the sum
of `/proc` user+system deltas across workers, per complete replay. CPU inflation
compares each variant's worker CPU to its own one-worker result. Every row passed
the accepted row-order/centre replay check; warmup also matched the matrix.

| Variant | Workers | Separation wall | Worker CPU | CPU inflation | Speedup vs own 1 worker | Efficiency | Minor faults/replay |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A current | 1 | 10.057 s | 10.060 s | 1.00× | 1.00× | 100% | 12 |
| B reuse | 1 | 9.961 s | 9.960 s | 1.00× | 1.00× | 100% | 5 |
| C chunk + reuse | 1 | 9.900 s | 9.900 s | 1.00× | 1.00× | 100% | 2 |
| A current | 2 | 6.522 s | 12.800 s | 1.27× | 1.54× | 77% | 525,473 |
| B reuse | 2 | 5.927 s | 11.623 s | 1.17× | 1.68× | 84% | 5 |
| C chunk + reuse | 2 | 5.707 s | 11.210 s | 1.13× | 1.73× | 87% | 1 |
| A current | 4 | 4.010 s | 15.540 s | 1.54× | 2.51× | 63% | 581,489 |
| B reuse | 4 | 3.725 s | 14.404 s | 1.45× | 2.67× | 67% | 3 |
| C chunk + reuse | 4 | 3.573 s | 13.690 s | 1.38× | 2.77× | 69% | 6 |
| A current | 8 | 2.743 s | 20.713 s | 2.06× | 3.67× | 46% | 704,109 |
| B reuse | 8 | 2.701 s | 20.367 s | 2.04× | 3.69× | 46% | 8 |
| C chunk + reuse | 8 | 2.558 s | 19.010 s | 1.92× | 3.87× | 48% | 90 |
| A current | 16 | 2.240 s | 27.466 s | 2.73× | 4.49× | 28% | 527,051 |
| B reuse | 16 | 2.197 s | 26.551 s | 2.67× | 4.53× | 28% | 147 |
| C chunk + reuse | 16 | **1.809 s** | 23.955 s | 2.42× | 5.47× | 34% | 210 |

The table is the initial 15–30-second set. A's 8-worker wall CV was 6.0%,
and B's 16-worker CV was 8.5%. Their longer retained reruns gave:

| Setting | Batch range | Wall median (min–max) | Wall CV | Interpretation |
| --- | ---: | ---: | ---: | --- |
| A, 8 workers | 28.2–28.6 s | 2.577 (2.561–2.598) s | 0.7% | Stable control |
| B, 8 workers | 32.1–35.0 s | 2.491 (2.466–2.692) s | 4.8% | Mixed; small apparent gain uncertain |
| C, 8 workers | 29.5–29.8 s | 2.686 (2.679–2.711) s | 0.6% | Shifted slower than first set; ranking unresolved |
| B, 16 workers | 35.5–39.5 s | 2.247 (2.218–2.469) s | 6.0% | Tied with A's 2.240 s median |

All retained samples are shown; none was silently discarded. CPU-pressure
snapshots were low before the 8-worker samples, so the source of the
between-set shift is unresolved. The variability prevents a confident
buffer-only or chunked ranking at eight workers. It does not alter the
16-worker conclusion, where A, C, and D have low within-set CV and a large gap.

At 16 workers, chunk-only D took **1.799 s** (1.770–1.846, 2.1% CV), with
23.653 s aggregate worker CPU and 452,832 minor faults per replay. C took
1.809 s (1.793–1.851, 1.7% CV), with 23.955 s CPU and only 210 faults.
The two chunked variants are effectively tied. B removed almost all A's
minor faults yet its longer wall median remained near A. Thus the tested
16-worker gain comes mainly from processing multiple directions per worker
call, not from retaining the grid and compact buffers. Chunking can reduce
task dispatch, serialization, and cross-task cache disruption; this
experiment does not isolate those sub-mechanisms further.

The 16-worker C/A replay wall difference is about 0.431 s (19.2%). Aggregate
worker CPU falls by about 3.51 s (12.8%) and CPU inflation from 2.73× to
2.42×. This is a *steady-state replay* result. Pool startup and the complete LP
are absent, so the full-solver comparison below is the operational measure.

## Full-solver chunk-only validation

`full_solver_chunk.py` temporarily replaces `colgen.ProcessPoolExecutor` in a
research process with an ordered four-direction chunk wrapper. It leaves
production source untouched and uses fresh per-direction arrays, matching D.
A separate 16-worker solve compared directions, centres, and the complete
coefficient matrix against the accepted fixture. The solver remained at 23
rounds, 5,842 rows, objective `12.217676366606236`, and least covered
`0.9999999999998309`. Three adjacent full-solver batches then compared P2
and the chunk-only prototype. The first set included one slow third control;
it is retained in `raw/full-solver/`. A second paired set increased each batch
to about 40–45 seconds. All 12 control/candidate batches exceeded 20 seconds,
and every individual solve converged to the accepted mathematical result.

| Paired set | P2 wall median | Chunk wall median | Paired saved median | Paired saving range | Batch duration range |
| --- | ---: | ---: | ---: | ---: | ---: |
| Initial | 3.427 s | 3.159 s | 0.227 s | 0.199–0.506 s | 20.1–22.4 s |
| Longer | 3.608 s | 3.183 s | 0.402 s | 0.274–0.521 s | 40.1–44.7 s |

The control slowed during both sets (wall CV 4.2% initial, 3.8% longer), so
the paired gain is best reported as a **positive but variable 0.20–0.52 s**
on this VM. The smallest observed paired saving, 0.199 s, is about 5.9% of
its adjacent control. The 0.227 s initial paired median is about 6.6% of
that set's control median. The longer paired median is larger, but the
variation prevents treating 0.402 s as a stable expected gain. Production P2
itself remains at its prior robust 3.390 s median; no chunk change was merged.

LP medians were 1.186/1.210 s in initial control/candidate and
1.164/1.173 s in longer control/candidate. The improvement is in separation:
initial medians 2.190 → 1.893 s and longer medians 2.398 → 1.942 s. Timing
differences between a frozen-weight replay and full row generation explain
why the 0.431 s steady-state replay gap must not be used as the predicted
end-to-end saving.

## Decision

The tested 16-worker gain is a task-granularity opportunity. A four-direction
chunked worker is the best next CPU integration candidate; buffer reuse alone
is not justified at 16 workers by these data. It helps at 2 and 4 workers and
could be revisited only if those counts become important. The prototype is
**research only** and no Part 3 change was merged.
