# Issue #2 CPU follow-up: integration log

## P1: vectorized slab intervals — ACCEPT

Input commit `e102e35f729eb52be10eabe5ba83428e2a10e1bc`.
The production `_reachable_values` now computes per-slab interval bounds with
NumPy `searchsorted` arrays. It still copies reachable mass in row order and
uses the same `_REACH_SLACK`, band limits, interval starts, offsets, and native
selection path. No dependency was added.

Three adjacent long-batch comparisons against input main gave these medians:

| Workers | Control wall | Candidate wall | Paired saving | Separation control → candidate | Batch range |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 21.822 s | 16.397 s | 5.390 s | 20.7 → 15.3 s | 21.7–32.9 s |
| 16 | 4.060 s | 3.689 s | 0.417 s | 2.8 → 2.5 s | 23.7–26.1 s |

The individual 16-worker paired savings were 0.417, 0.499, and 0.228 s;
all favor the candidate. The control and candidate wall CVs were 2.84% and
1.16% at 16 workers, and 0.31% and 0.17% at one worker. Use `results.json`
and the raw JSON for exact values and per-solve LP timings.

The pre-integration equivalence run compared all 4,163 direction calls and
1,890,769,994 compact mass values bitwise, including ordering, slab indices,
starts and offsets. It then matched complete row order, centres, and the
coefficient matrix at 1 and 16 workers. After the production port, full
1/4/8/16-worker solves reproduced the accepted 23 rounds, 5,842 rows,
objective `12.217676366606236`, and least covered
`0.9999999999998309`, with identical full state. Focused tests passed:
23 of 23. The exact retained-row/witness result associated with this full
state remains applicable. The measured gain is material at both endpoints.

P1 was committed as `cc83964b`.

## P2: row-major native prefix — ACCEPT

Input P1 commit `cc83964b`.
Only the second in-place prefix pass is changed. The first axis-1 pass remains
NumPy; the new C loop scans adjacent columns in row-major order while retaining
each column's top-to-bottom addition sequence. The source is
`packing/src/sqpack/fractional/_prefix_rows_native.c`. The package build hook
creates an optional platform shared library. A missing native build takes the
NumPy axis-0 fallback; no new dependency is required. The Linux wheel build
was inspected and contained both the C library and its Python wrapper; see
`environment.json` for its SHA-256 and exact build command. No binary is
committed as the only implementation.

Paired full-solver comparisons **after P1**:

| Workers | Control wall median | Candidate wall median | Paired saving median | Pair savings range | Batch range |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 16.372 s | 11.024 s | 5.349 s | 5.333–5.366 s | 22.0–32.9 s |
| 16, first set | 3.758 s | 3.574 s | 0.102 s | 0.089–0.396 s | 20.2–26.4 s |
| 16, longer rerun | 3.710 s | 3.420 s | **0.282 s** | 0.263–0.498 s | 40.0–44.6 s |

The first 16-worker set had 4.62% candidate CV, so it was retained and a
second set used ~40-second batches. All six 16-worker pairs favored the C
pass. The longer control's 3.86% CV reflects a slow third control; the paired
median is based on all three and is not an estimate from the fastest sample.
The longer candidate CV was 0.84%. The 1-worker gain is about 32.7% versus
P1; the longer 16-worker paired median is about 7.6% versus its control. These
are *incremental measurements on P1*, not sums of earlier standalone results.

The pre-integration P1-vs-C check compared 905 real grids and 695,327,309
mass cells bitwise. Full 1/16-worker research solves matched all accepted rows,
centres and coefficients. Packaged production then matched the accepted full
state at 1/4/8/16 workers, with 23 rounds, 5,842 rows, objective
`12.217676366606236`, and least covered `0.9999999999998309`.
The focused Python test run passed 29/29 tests, including native/fallback
prefix checks; Ruff passed on changed source, and the new source/hook passed
basedpyright. The exact witness associated with the unchanged complete state
remains applicable.

Final **unprofiled production** baseline on P2, three independent batches:

| Workers | Wall/solve median (min–max) | Separation | LP | Wall CV | Batch range |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 11.137 s (11.080–11.151) | 10.029 s | 1.078 s | 0.34% | 22.16–22.30 s |
| 16 | 3.390 s (3.369–3.475) | 2.106 s | 1.219 s | 1.64% | 20.22–20.85 s |

P2 is accepted because the measured incremental gain is positive in all long
parallel pairs, substantial serially, bitwise correct on real grids, and
packaged with a NumPy fallback. No Part 3 prototype is included in P2.

P2 was committed as **`2a2efa39edb179128184f19d6a4235a6bbcaebcc`**.
This exact SHA is `CPU_ACCEPTED_SHA` for both independent follow-up studies.

## Memory observation at CPU_ACCEPTED_SHA

The separate Luna observer worked in a detached worktree at the accepted SHA,
without changing production. Its full [report](../cpu-memory-observation/report.md),
scripts, and raw records are preserved. The strongest supported finding is
that memory-system effects are plausible, while **physical DRAM bandwidth
saturation is not proven**. The guest-visible STREAM-like triad median was
40.81 GB/s at 8 workers and 40.11 GB/s at 16; read-only throughput reached
76.83 GB/s at 16. These are sustained guest benchmark rates, not host DDR
peak values. All 60 corrected samples lasted strictly more than 10 seconds;
an erroneous calibration pass was excluded before analysis and its error is
documented in the observer report.

The accepted separation workload has 2.610 billion grid cells and 1.891
billion compact values across 4,163 direction calls. Explicit element-pass
accounting gives about **149.93 GB of lower-bound logical traffic** per
replay: prefix 83.51 GB, compaction 30.25 GB, grid zeroing 20.88 GB, native
selection input 15.13 GB, with smaller scatter/metadata. This is not measured
DRAM traffic; cache reuse and omitted small arrays prevent converting it into
a hardware bandwidth claim. Warmed 16-worker replays incurred roughly
0.41–0.46 million minor faults per replay and no major faults. Hardware
performance counters were blocked by `perf_event_paranoid=4`; settings were
left untouched. Physical DRAM bytes, cache misses, and frequency effects
remain unresolved.

## A/B/C memory and batching study at CPU_ACCEPTED_SHA

The independent [batching report](../cpu-batching-research/report.md) and
[results](../cpu-batching-research/results.json) retain 72 audited primary
timed samples, each 14.93–44.74 seconds. All variants replay the same accepted
23-round/181-direction workload in order. Every warmup matched the full row
matrix, direction order, and centres; every timed replay matched order and
centres. No batching prototype was merged.

| Variant | 1-worker separation / CPU | 16-worker separation / CPU | 16-worker CPU inflation | 16-worker minor faults/replay | Verdict |
| --- | ---: | ---: | ---: | ---: | --- |
| A current | 10.057 / 10.060 s | 2.240 / 27.466 s | 2.73× | 527,051 | Reference |
| B reusable buffers | 9.961 / 9.960 s | 2.197 / 26.551 s | 2.67× | 147 | No stable 16-worker win |
| C chunks + buffers | 9.900 / 9.900 s | 1.809 / 23.955 s | 2.42× | 210 | Strong replay gain |
| D chunks only | — | **1.799 / 23.653 s** | — | 452,832 | Isolates chunk gain |

B's longer 16-worker batch median was 2.247 s (2.218–2.469,
6.0% CV), essentially tied with A's 2.240 s median despite eliminating
almost all its minor faults. D retained 452,832 faults but matched C's
low wall time. This makes **task granularity**, including fewer dispatches and
less repeated argument transport, the main measured 16-worker factor among
these variants. Reuse helps at 2 and 4 workers; the 8-worker ranking remains
uncertain after a longer rerun because sets shifted under VM variation.
The chunks-only diagnostic does not isolate dispatch versus serialization or
cache state within a chunk.

An ordered four-direction **research-only full-solver** prototype reproduced
the accepted complete row state and objective. Two sets of three adjacent
long control/candidate pairs all favored chunking. Savings ranged
**0.199–0.521 s per solve**; the initial paired median was 0.227 s and the
longer set median 0.402 s. Both sets had variable control wall (4.2% and
3.8% CV), so **about 0.20 s / 6% is the conservative observed end-to-end
opportunity**, with a larger VM-dependent upside. The steady-state replay
gap is not substituted for the full-solver gain. The prototype remains in
the research directory and is not part of P2.

## Final CPU decision

**MODERATE remaining opportunity.** P1 and P2 are accepted and committed as
separate sequential production changes. Their final controlled P2 baseline is
11.137 s wall / 10.029 s separation / 1.078 s LP at one worker, and
3.390 s wall / 2.106 s separation / 1.219 s LP at 16 workers, with wall CV
0.34% and 1.64% respectively. No tested memory result proves a DRAM ceiling,
and reusable buffers alone are not a supported 16-worker integration.

**Next CPU action:** implement an ordered four-direction chunked worker path
in production as a separate integration task, preserving one pool per solve,
and retest full solver correctness and three long adjacent 16-worker batches.
The conservative measured opportunity is roughly 0.20 s per solve; the
actual gain after production integration must be measured. Test worker counts
and chunk sizes on the new path before choosing a default. No Part 3 prototype
was merged here, and no push was performed.
