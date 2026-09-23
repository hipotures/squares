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

P1 commit SHA is recorded in the final section after the sequential decision.
