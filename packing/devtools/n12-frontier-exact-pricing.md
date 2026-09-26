# Prepared exact predicates for pricing and ceiling analysis

## Scope

This optimization reduces computation, rather than starting more speculative
searches to make CPU utilisation look higher. It affects exact candidate reduced
costs in `rank_candidates` and repeated exact weighted-depth queries in the
final `check_ceiling` diagnostic. It does not change LP solving, float vertex
ranking, scheduling, candidate geometry, rationalisation or certificate proof gates.

The supplied live `rows.log` had roughly 3-second separations and 5-8-second
carried-row LP solves. That does not establish that an entire 25-30-second serial
interval belongs to LP: pricing and final ceiling work are separate phases.
Without the live `phase.log`, their exact share in that campaign is unknown.

## Exact transformation

A rational square is the intersection of two closed slabs. For each slab,

```text
abs(a*x + b*y - c) <= h
```

prepare integer coefficients `(A, B, C, H)` by multiplying the four fixed
coefficients by their positive least common denominator once. At a query point
`(X/D, Y/D)` with positive `D`, containment is exactly:

```text
(C - H) * D <= A * X + B * Y <= (C + H) * D
```

Python integers are unbounded. This removes repeated Fraction multiplications,
normalisation and comparisons, not precision. Edge inclusion remains closed.
Weights and returned depths/reduced costs remain exact Fractions, with original
square order, duplicates and D4 stabiliser multiplicities preserved.

Preparation is call-local and does not mutate squares or persist a global cache.
Original `Square.covers` and `reduced_cost` remain available. Tests and the
benchmark use them as the independent pre-optimization control.

## Reproducible measurement

From `packing/`, with no other benchmark competing for the same CPUs:

```bash
uv run --frozen python -m devtools.bench_exact_pricing \
  --root ../Experiments/exact-pricing-bench-$(date +%s) \
  --workers 4 --samples 3
```

Each pair runs the real generator in fresh processes with identical parameters,
alternating variant order. The reference variant substitutes only the previous
Fraction predicates. Timings include process startup. All logs, phase timings,
results and explicitly unverified candidates stay under the chosen persistent root.
The comparison requires identical objective/coverage, ordered mathematical round
records, all recorded ceiling fields, and the frozen candidate contents. It never
promotes an artifact or reports a new packing bound.

Three local pairs with a four-CPU budget, Python 3.14.7, side `198111/50000`, grids
`5,7,9`, 24 direction steps, three column rounds and support cap 32 measured:

| Pair | Fraction control | Prepared predicates | Ratio |
| --- | ---: | ---: | ---: |
| 1 | 29.214 s | 3.778 s | 7.733x |
| 2 | 28.264 s | 3.628 s | 7.790x |
| 3 | 29.345 s | 3.982 s | 7.369x |

All mathematical comparisons matched. Almost all savings were in final ceiling
analysis: 26.99-28.12 seconds became 2.34-2.60 seconds. Pricing itself took only
0.15-0.27 seconds in this fixture, so it does not demonstrate a material gain in
that phase. This is deliberately a small coarse-site fixture (objective about 16),
not the live near-12 frontier workload and not a sixteen-core speedup prediction.

Integration CI independently repeated the pair with two workers: 26.678 seconds
versus 3.322 seconds, with identical results. Its regression run passed 175
frontier/exact-predicate tests plus 40 generator/LP/separation tests:

https://github.com/hipotures/squares/actions/runs/36203719195

A larger local reference with grids `26,35,43`, 180 directions, the retained
2097-atom seed and support cap 128 exceeded a 360-second benchmark deadline.
There is no completed paired result for that full-size setting, so no full-size
end-to-end speedup is claimed. The benchmark terminates its own process session
on timeout; it never signals the user's campaign.

## Validation and limits

New regressions compare the prepared predicates against the old expressions on
rational grids, large random denominators, duplicate/signed weights, degenerate
slabs, closed edges/corners and offsets of `2^-200`. Complete ranked candidate
lists and `CeilingResult` values are also compared exactly.

The change preserves the existing float screening algorithm in `check_ceiling`;
it is not a new proof of that screening algorithm. The s(12) retention boundary
still requires the existing full certificate gate. Performance depends on how
much of a workload is spent on repeated exact coverage. Serial LP work, float
surveys and bounded-wave tails remain possible.

## Upgrade

No new runtime option is needed. Stop the existing runner gracefully before
pulling into its checkout, then use the same experiment root and `--resume`.
Do not reset or edit state. This optimization does not implement rolling
backfill or change worker counts, strategy policy, dependencies or proof data.
