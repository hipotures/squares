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
