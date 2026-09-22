# Exp-224 n=19 at Ten Times the Budget

Status: **in flight.** The `10x` sweep is running; this receipt carries the two parts
that are complete — the polished `1x` baseline the sweep is judged against, and the
adjunct one-sided tilt slopes — and will carry the sweep’s per-seed table when it lands.
Nothing here is registered and no bound moved.

This is `X-042`’s
[slate row A5](../../../../explorations/X-042-what-is-left-at-low-n.md) (`H-U2`), the
upper-bound side of agenda 041: `n = 19` is the low-`n` record that no computer search
on record has ever reached.

## The correction this receipt leads with

`X-042` states that the repository’s best at `n = 19` is `4.958948`, “`0.073` short, the
worst relative performance at any low non-grid `n`”.

**That number is the annealer’s stopping point, not the repository’s best.** Running
exp-202’s own archived `n = 19` poses down to a fixed-cell local optimum with
`sqpack.research.quench.quench_bracket` — no new search, no new budget, the same bytes
that have been in the tree since 2026-09-08 — gives `4.915912971524`.

| Quantity | Value |
| --- | ---: |
| Wainwright 1979, `3 + (4/3) sqrt(2)` | `4.885618083164` |
| `X-042`’s quoted repository best (engine stop) | `4.958947728075` |
| **Same archive, polished and re-verified** | **`4.915912971524`** |
| Gap quoted by `X-042` | `+7.333e-02` |
| **Gap after polish** | **`+3.029e-02`** |

The `0.073` is `2.4` times the real figure.
It does not change the qualitative claim — no search here has reached `4.885618`, and
`n = 19` remains the worst-served low non-grid cell — but a lane that is priced against
`0.073` is pricing against an artefact of not polishing.

## The baseline: exp-202 at `1x`, polished

Every archived `n = 19` pose from all five exp-202 arms (`A-control`, `A-slow`,
`B-perturb`, `B-perturb-slow`, `C-pressure`), best per seed, quenched, repaired and
re-verified. Run from `packing/`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run --frozen \
  --all-extras --group dev python -m devtools.polish_sweep_archive \
  campaign/series/series-000-smoke-and-calibration/results/exp-202-round-1/part-1/B-perturb.jsonl \
  campaign/series/series-000-smoke-and-calibration/results/exp-202-round-1/part-2/B-perturb-slow.jsonl \
  campaign/series/series-000-smoke-and-calibration/results/exp-202-round-1/part-1/A-control.jsonl \
  campaign/series/series-000-smoke-and-calibration/results/exp-202-round-1/part-2/A-slow.jsonl \
  campaign/series/series-000-smoke-and-calibration/results/exp-202-round-1/part-3/C-pressure.jsonl \
  --cells 19 --quench-seconds 40 --rounds 6 --pose-seconds 150 \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-224-n19-10x/exp-224-baseline-exp202-1x-polish.json
```

| seed | engine stop | polished | kept | quench |
| ---: | ---: | ---: | ---: | --- |
| 1 | `4.971854791865` | `4.944934863883` | `4.944934863883` | 2 rounds, 21.3 s, `re-read cell worse` |
| 2 | `4.958947728075` | `4.925390647054` | `4.925390647054` | 2 rounds, 5.9 s, `cell cycle` |
| 3 | `4.984416587363` | `4.915912971524` | `4.915912971524` | 2 rounds, 63.2 s, **converged** |
| 4 | `5.000000000000` | `5.000000000000` | `5.000000000000` | 2 rounds, 2.8 s, `cell cycle` |
| 5 | `4.991997643233` | `4.955058032143` | `4.955058032143` | 2 rounds, 46.0 s, `cell cycle` |

Median `4.944934863883`, best `4.915912971524`, best gap `+3.029e-02`. Every kept pose
was repaired by scaling centres apart about their centroid — which can only raise the
side — and accepted by `sqpack.verify` at tolerance `1e-9` in the same process.
No pose is below any standing best.

Two things the table says that the single best number does not.
The polish is worth `0.027` to `0.069` of side on four of the five seeds and exactly
nothing on the fifth, which on the four is more than the `0.016` the whole `1x`
collective-move arm bought over the control at this cell.
And the second quench round never improved on the first on any seed: the loop restarts
from the repaired pose and lands in the same cell fixed point, so the `--rounds 6`
budget was not the binding constraint — the solver’s own cell conditions were, on four
of five seeds.

## Provenance of the engine

`sqsearch` keys its RNG on `(seed, chain)` alone (`Rng::keyed(seed, chain)` in
`sqsearch/src/search.rs`), so the thread count and the host change the wall clock and
nothing about the numbers.
That was checked rather than assumed: a fresh single run at `n = 19`, seed 1, `1.25e9`
pair tests per chain, 8 chains, `--threads 2`, at engine commit `c6a7ea190`, returned
`4.971854791864539`; exp-202’s archived seed-1 pose, at commit `9ae7700` with
`--threads 3` on a different machine, reads `4.971854791865`.

## Adjunct: the one-sided tilt slopes (`H-U1`)

Not part of `H-U2`. It is the third task of this lane, it is cheap, and it shares this
receipt because it has no experiment id of its own.

Three retained records are *axis-plus-one-angle*: `n = 19` is 11 squares at `0` and 8 at
`45`, `n = 26` is 17 at `0` and 9 at `45`, `n = 18` is 10 at `0` and 8 at `24.2951889`.
Inside that family the side is a function of the one tilt once the centres are
re-optimised, and re-optimising the centres at a fixed tilt is the LP the quench solves.
So local optimality within the family is two numbers per cell: move the common tilt by
`+delta` and by `-delta`, re-solve, and ask whether the side rose both times.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run --frozen \
  --all-extras --group dev python -m devtools.measure_tilt_slopes \
  --cells 19,26,18 --deltas 1e-2,3e-3,1e-3,1e-4,1e-5 \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-224-n19-10x/exp-224-adjunct-tilt-slopes.json
```

The LP reproduces every published side from the published centres, which is an
independent reading of all three records:

| n | tilt (deg) | tilted | published side | LP at `delta = 0` | LP − published |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 19 | `45.0000000` | 8 | `4.885618083164` | `4.885618083164` | `+0.000e+00` |
| 26 | `45.0000000` | 9 | `5.621320343560` | `5.621320343560` | `+0.000e+00` |
| 18 | `24.2951889` | 8 | `4.822875655532` | `4.822875655532` | `+8.882e-16` |

**All six one-sided slopes are strictly positive.
There is no sub-record packing in the axis-plus-one-angle family at any of the three.**
The `delta`-scaling separates two different local shapes, which is the part worth
keeping:

| n | shape | evidence | one-sided slope as `delta -> 0` |
| ---: | --- | --- | --- |
| 19 | smooth quadratic minimum | `s - s0` falls `100x` per `10x` in `delta`: `3.14e-5`, `2.83e-6`, `3.14e-7`, `3.14e-9`, `3.14e-11` | `0`, with curvature `0.3143` |
| 18 | smooth quadratic minimum | same `delta^2` law, branches differing by `0.76%` at `delta = 1e-2` | `0`, with curvature `0.753` to `0.756` |
| 26 | **kink** | `s - s0` falls `10x` per `10x` in `delta`: `5.11e-3`, `1.51e-3`, `5.01e-4`, `5.00e-5`, `5.00e-6` | `+1/2` on **both** branches |

`n = 26` is the `H-019` shape — the genuine corner measured at `n = 11`, where the two
one-sided slopes were `0.175` and `0.384`. Here the corner is symmetric and the slope is
`1/2` to five digits on each side.
A smooth local model is misspecified at that point, which is why this was run
branchwise; a central difference would have reported `0` there and said nothing.

At `n = 19` and `n = 18` the opposite holds: the tilt is an interior stationary point of
its own family, so the record is *not* defended by a large first-order penalty there —
it is defended by there being no first-order direction at all, and the family has to be
left to improve on it.

## What this does not establish

- Nothing here is exact.
  The quench is `f64` throughout and the verifier ran at tolerance `1e-9`;
  `sqpack.verify`’s own docstring is explicit that a float check cannot be made into a
  proof by raising precision.
- The polished baseline is a **lower** figure for the repository’s best at `n = 19`, not
  a new record and not a new register value.
  It is exp-202’s own archive read better.
- The tilt slopes are measured **within** the axis-plus-one-angle family, holding the
  cell assignment free but the angle *pattern* fixed.
  They say nothing about a packing with two tilts, and nothing about global optimality.
- The `n = 26` slope of `1/2` is a numerical reading at five `delta` values, not a
  derivation.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
