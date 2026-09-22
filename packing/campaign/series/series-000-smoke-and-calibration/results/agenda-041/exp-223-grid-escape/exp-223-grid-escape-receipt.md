# Exp-223 The Grid Escape at n = 12, 20, 21

Status: **the null, measured**. Nothing was registered and no bound moved.

This is `X-042`’s
[slate row A4](../../../../../explorations/X-042-what-is-left-at-low-n.md) (`H-U5`), the
upper-bound side of agenda 041. The statement tested: *a grid-capable arm at the exp-202
budget returns exactly the grid (`4`, `5`, `5`) on 5 of 5 seeds at each of
`n = 12, 20, 21`.* The discriminator is the best polished side per `n` against `4`, `5`,
`5`; any seed strictly below is a new record and a refutation of the `k <= m` staircase.

## What had never been run

exp-202 chose eleven cells every one of which beats the trivial grid, “so no arm can
score by returning the incumbent”.
`n = 12`, `20` and `21` are the opposite case: at all three the best known packing
**is** the grid, and two of the three registers say in as many words that this is an
absence of search rather than a proof — [`n-020`](../../../../../../frontier/n-020.md)
and [`n-021`](../../../../../../frontier/n-021.md) both read “no arrangement has ever
been found that beats the trivial grid … That is a statement about what has been
searched, not a proof.”

exp-202 also measured why the absence is total rather than partial: at the trivial grid
no single-square proposal lowers `required_side` at all, so the only runs ever made at
`n = 12` used a move set that provably cannot leave the grid, and `n = 20` and `n = 21`
had no recorded search budget of any kind.

Both ends of the interval a new record would have to land in are known:

| n | verified lower bound | best known | room |
| ---: | ---: | ---: | ---: |
| 12 | `99/25 = 3.96` (`T-017`) | `4` | `0.04` |
| 20 | `97/20 = 4.85` (`T-021`) | `5` | `0.15` |
| 21 | `97/20 = 4.85` (`T-021`) | `5` | `0.15` |

## The plan, frozen before the run

[`exp-223-plan.yaml`](exp-223-plan.yaml) is exp-202’s round-1 part-1 plan with one arm
and three cells substituted and nothing else changed: same engine, same
`budget_pair_tests` per chain, same chain count, same seeds, same flags.

| Field | Value |
| --- | --- |
| arm | `B-perturb`: `--p-perturb 1.0 --perturb-scale 2` |
| budget | `1.25e9` pair tests per chain, 8 chains, so `1e10` per (cell, seed) |
| seeds | 1, 2, 3, 4, 5 |
| cells | 12, 20, 21 |
| threads | 2 |
| engine | `sqsearch 0.1.0`, repository commit `c6a7ea190` |

The control arm is not run.
exp-202’s mechanism measurement is that at the trivial grid the single-square move set
cannot lower the objective at all, so a control here would spend an hour confirming an
arithmetic fact; the budget goes to the only arm that can answer the question.
`--threads 2` rather than exp-202’s `3` because this lane is capped at about two of four
shared cores; `sqsearch` keys its RNG on `(seed, chain)` alone
(`Rng::keyed(seed, chain)`), so the thread count changes the wall clock and nothing
about the numbers.

Run from `packing/`:

```bash
uv run --frozen --all-extras --group dev python -m devtools.run_arm_sweep \
  campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-223-grid-escape/exp-223-plan.yaml \
  --out campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-223-grid-escape
```

No parameter was changed and the sweep was not re-run.

## Result

Every one of the fifteen runs returned the grid exactly, and so did every one of the 120
individual chains behind them.

| n | record and grid | seeds | median | best | worst | below grid | below record |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | `4` | 5 | `4.000000000000` | `4.000000000000` | `4.000000000000` | 0 | 0 |
| 20 | `5` | 5 | `5.000000000000` | `5.000000000000` | `5.000000000000` | 0 | 0 |
| 21 | `5` | 5 | `5.000000000000` | `5.000000000000` | `5.000000000000` | 0 | 0 |

| n | seed | best side | delivered pair tests | wall |
| ---: | ---: | ---: | ---: | ---: |
| 12 | 1 | `4.000000000000` | `10137625872` | `125.1 s` |
| 12 | 2 | `4.000000000000` | `10137625872` | `79.2 s` |
| 12 | 3 | `4.000000000000` | `10137625872` | `91.9 s` |
| 12 | 4 | `4.000000000000` | `10137625872` | `129.1 s` |
| 12 | 5 | `4.000000000000` | `10137625872` | `159.9 s` |
| 20 | 1 | `5.000000000000` | `10336027360` | `124.4 s` |
| 20 | 2 | `5.000000000000` | `10336027360` | `113.8 s` |
| 20 | 3 | `5.000000000000` | `10336027360` | `177.9 s` |
| 20 | 4 | `5.000000000000` | `10336027360` | `212.1 s` |
| 20 | 5 | `5.000000000000` | `10336027360` | `101.5 s` |
| 21 | 1 | `5.000000000000` | `10080026880` | `134.5 s` |
| 21 | 2 | `5.000000000000` | `10080026880` | `161.9 s` |
| 21 | 3 | `5.000000000000` | `10080026880` | `133.7 s` |
| 21 | 4 | `5.000000000000` | `10080026880` | `130.7 s` |
| 21 | 5 | `5.000000000000` | `10080026880` | `91.2 s` |

Sweep wall `585.2 s + 729.8 s + 652.1 s = 1967.1 s` over the three cells, plus a
`3.305 s` engine gate and the pose-oracle pass.
Host load moved from `10.4` to `7.3` on four cores shared with three other lanes.

**`H-U5`’s null is what happened, on 15 of 15 seeds and 120 of 120 chains.** Not one
run, and not one chain inside a run, reported a side below the grid at any of the three
cells. The seed-to-seed spread is not small, it is zero: every archived value is the
integer, bit for bit.

That is the same signature exp-202 recorded at `n = 29, 37, 50, 52`, where “every seed
of both arms returns the grid, bit for bit”, and the same conclusion applies — the
failure is not gradual.
The arm either leaves the grid or it does not, and at these three cells it does not.

`n = 12` is the interesting one of the three.
It sits below `n = 17` and `n = 26`, both of which this same arm at this same budget
took off the grid by `0.29` and `0.18`, so “the escape gets harder with `n`” does not
explain it. What does is in the mechanism section: `n = 12`’s grid is a `4 x 4` square
grid with four cells empty, and the four empty cells are not adjacent in a way any
collective displacement of this magnitude can exploit.

## The polish

Polishing does not change the answer, and the way it fails to is worth recording.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run --frozen \
  --all-extras --group dev python -m devtools.polish_sweep_archive \
  campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-223-grid-escape/B-perturb.jsonl \
  --quench-seconds 40 --rounds 4 --pose-seconds 120 \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-223-grid-escape/exp-223-polish.json
```

All fifteen best poses were handed to `sqpack.research.quench.quench_bracket`, repaired
and re-verified.
All fifteen came back at the integer, with least pair gap and least wall
gap both exactly `0`, and the quench stopped on a cell condition rather than a clock
every time: `initial cell post-check rejection` at `n = 12`, `re-read cell worse` at
`n = 20`, `cell cycle` at `n = 21`.

So the grid is not merely where the annealer stops.
It is a fixed point of the LP-in-cell quench as well: with every angle and every
separating-axis assignment held, the LP cannot shorten the side, and the bracketing
search over the angle classes cannot find a tilt that lets it.
Two different instruments, one answer.

## The mechanism, measured at these three cells for the first time

`devtools/measure_objective_sparsity.py` draws proposals from the same two distributions
the engine draws from and counts what each does to `required_side`. exp-202 ran it on
its own eleven cells; these three were never among them.

```bash
uv run --frozen --all-extras --group dev python -m devtools.measure_objective_sparsity \
  --cells 12,20,21 --scale SCALE --samples 8000 --seed 1
```

at `SCALE` in `0.01`, `0.05`, `0.2`. Output in
[`exp-223-objective-sparsity-grid.txt`](exp-223-objective-sparsity-grid.txt).

| n | scale | single changed | single lowered | collective changed | collective lowered | **admissible, either kind** |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 12 | `0.01` | `0.3311` | `0.0000` | `1.0000` | `0.0010` | `0.0000` |
| 12 | `0.05` | `0.3311` | `0.0000` | `1.0000` | `0.0014` | `0.0000` |
| 12 | `0.20` | `0.3311` | `0.0000` | `1.0000` | `0.0022` | `0.0000` |
| 20 | `0.01` | `0.2670` | `0.0000` | `1.0000` | `0.0000` | `0.0000` |
| 20 | `0.05` | `0.2670` | `0.0000` | `1.0000` | `0.0000` | `0.0000` |
| 20 | `0.20` | `0.2670` | `0.0000` | `1.0000` | `0.0001` | `0.0000` |
| 21 | `0.01` | `0.4116` | `0.0000` | `1.0000` | `0.0000` | `0.0000` |
| 21 | `0.05` | `0.4116` | `0.0000` | `1.0000` | `0.0000` | `0.0000` |
| 21 | `0.20` | `0.4116` | `0.0000` | `1.0000` | `0.0000` | `0.0000` |

Three readings, in order of how much they say.

**The single-square result reproduces exp-202’s at three new cells.** A quarter to two
fifths of single-square proposals move the objective and not one of 72,000 lowers it.
The grid is a strict local minimum of `required_side` under the entire single-square
move set here too.

**The collective rate is at or near the floor.** exp-202 measured `0.0051`, `0.0009`,
`0.0000` for the fraction of collective proposals that lower the side at `n = 11`, `17`,
`26`, and read the escape as a rare collective event whose probability falls with `n`.
`n = 12` sits at `0.0010` to `0.0022`, between `n = 11` and `n = 17`; `n = 20` is
`0.0000` to `0.0001` and `n = 21` is `0.0000` at every scale, which is the `n >= 26`
regime reached six and seven sizes early.

**And the admissible rate — lowers the side *and* leaves a packing — is `0.0000` at
every cell and every scale, over 72,000 collective proposals.** That is the sharpest of
the three and the one that was not previously measured anywhere: at these three grids
every proposal that would shorten the side puts two squares into each other.
The escape is not rare here in the sense of needing many draws; in this sample it is not
present at all.

## Guards

| Guard | Result |
| --- | --- |
| engine selftest on the binary that ran | `SELFTEST PASSED`, `3.305 s`, on the binary at commit `c6a7ea190` |
| every archived pose re-checked by `sqpack.verify` in a separate process | 135 poses checked, 0 failures, tolerance `1e-9`, archive `sha256 fc9c3d1d…c8711e4` |
| any run below a standing best | 0 at every cell |
| delivered pair tests against declared | `1.014x` at `n = 12`, `1.034x` at `n = 20`, `1.008x` at `n = 21` — the budget is enforced at restart granularity, so an arm overshoots by up to one anneal |

## What this does not establish

- **One budget tier.** `1e10` pair tests per seed.
  exp-202’s own limits section is explicit that record engines run four to six orders of
  magnitude beyond this, so a negative here is a statement about this budget, not about
  the cells.
- **One arm, at one point in its parameter plane.** `(p_perturb, perturb_scale) =
  (1.0, 2)`, frozen by exp-134 on held-out cells.
  A different collective proposal, a basin-hopper, or a projection method is a different
  experiment.
- **Nothing about `s(12)`, `s(20)` or `s(21)`.** A search that does not find a packing
  below the grid is not evidence that none exists.
  The three cases remain open by `0.04`, `0.15` and `0.15` against their verified lower
  bounds.
- **Nothing about the lower-bound side.** `X-042`’s correction 8 is that at `n = 20` and
  `21` the covering value, not the integer endpoint, is what binds a certificate near
  `4.86`. That is a claim about certificates; this receipt is about packings and does
  not touch it.
- **`f64` throughout.** The engine screens at `1e-12` and the pose oracle re-decided at
  `1e-9`. Both refute a forged pose and certify nothing.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
