# Exp-215 n=26 53/10 Covering Receipt

Status: **unresolved**. The deadline stopped the row loop before it converged.

Nothing was frozen, so nothing was decided.
This run does not move Nagamochi’s verified floor `5.0` at n=26, and it is not evidence
for or against Green’s unrecovered `5.51`.

[H-225](../../../../hypotheses/H-225-n26-seeded-certificate-at-53-10.md) asks whether a
point-atom certificate exists at `(n, L, B, net) = (26, 53/10, 9977/10000, 181
directions)` on a window-seeded site set.
Confirm only when `devtools.decide_certificate` prints `RETAINABLE` on a freeze of mass
strictly below 26. The record’s own direction says an unfinished loop is unresolved for
the claim, and this loop is unfinished.

## Command

Run from `packing/`, exactly as registered in
[exp-215](../../experiments/exp-215-h225-n26-53-10-seeded-covering.md):

```bash
cd packing && OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 uv run \
  --frozen --all-extras --group dev python -m devtools.run_fractional_colgen \
  --n 26 --side 53/10 --shrink 9977/10000 --direction-steps 181 \
  --grid-counts auto --seed-windows 5 --support-cap 32 --column-rounds 1 \
  --max-rounds 80 --deadline-seconds 3600 --scale 4000000 \
  --freeze campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-covering.json \
  --freeze-family campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-family.json \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-run.json \
  --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10-rows.jsonl \
  --log campaign/series/series-000-smoke-and-calibration/results/agenda-040/exp-215-n26-53-10.log
```

No parameter was changed, and the command was not re-run.

## Site Set

Auto grid counts `(38, 51, 62)` at inset `1/2` on container side `53/10` and square side
`9977/10000`, plus the 5-per-window ceiling lattice, which contributed 625 seed sites.
No seed certificate.
`--support-cap 32` kept the 32 heaviest dual rows while pricing.

| Stage | Orbits | Sites | Dual rows |
| --- | ---: | ---: | ---: |
| Round 0 start | — | — | 508 |
| Round 0 at the deadline | 1125 | 8505 | 17162 |

## Covering

One column round, 48 LP rounds, wall `3754.0` s, stopped `deadline reached after 48
rounds`. The loop never converged: 546 of the separation oracle’s placements were still
violated at the last round, and the least covered mass was `0.9530750900989208`.

`--deadline-seconds 3600` is checked before a round starts, so round 47 — which took
`250.81` s of separation and `65.54` s of LP — ran past the bound and the process ended
at `3754.0` s.

| LP round | Rows | Added | Violated | Support | Objective |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 508 | 508 | 546 | 0 | 18.712066 |
| 1 | 918 | 410 | 546 | 376 | 19.855586 |
| 2 | 1310 | 392 | 546 | 340 | 21.183715 |
| 3 | 1817 | 507 | 546 | 296 | 22.404463 |
| 4 | 2302 | 485 | 546 | 380 | 24.285714 |
| 5 | 2746 | 444 | 546 | 220 | 25.000000 |
| 10 | 4749 | 396 | 546 | 628 | 25.000000 |
| 20 | 8661 | 341 | 546 | 964 | 25.000000 |
| 30 | 12000 | 289 | 546 | 2120 | 25.000000 |
| 40 | 15078 | 352 | 546 | 1416 | 25.000000 |
| 47 | 17162 | 284 | 546 | 2689 | 25.000000 |

Rounds 6 to 46 are omitted from the table only because every one of them reads
`25.000000` with 546 violated; the full 48 rows are in `exp-215-n26-53-10-rows.jsonl`
and in the run JSON’s `lp_log`. The one exception is round 37, which briefly read 543
violated before returning to 546.

| Quantity | Value |
| --- | --- |
| Final float LP objective | 25.000000000040338 |
| Least covered mass | 0.9530750900989208 |
| Rationalised total mass | none — the run returned no candidate |
| Atoms | 0 |
| `least_cell_mass` | null |
| Covering freeze written | no |
| Family freeze written | no |

Between round 4 and round 5 the objective reached `25.000000` and stayed there for
forty-three consecutive rounds while 12,000 further rows were added.
This is the same exact-integer artefact Session 141’s unseeded exp-169 probe hit at
`513/100`: the LP is pinned at `n - 1` on a row set that is not yet complete.
`25.000000000040338` is a float objective on an incomplete row set, not a covering value
and not a bound; the program still has 546 violated placements, so it does not describe
a covering at all.

## Gate

`devtools.declare_least_cell_mass` and `devtools.decide_certificate` were not run, and
could not be: `run_fractional_colgen` returns no candidate when the row loop does not
converge, so `--freeze` wrote nothing.
`--freeze-family` also wrote nothing, because the priced dual support is only recorded
on convergence. There is no artifact for either gate route or either ceiling reader to
read.

## Determination

H-225 remains **unresolved**, and this site set is not even refuted — it was not
measured to convergence.

- Confirmation failed for want of an artifact: no freeze exists, so no `RETAINABLE` line
  exists, and the confirm criterion was never reachable within the declared 3600 s.
- No refutation is claimed: an unfinished loop says nothing about the claim, and the
  record’s direction says so in as many words.
- The `25.000000` plateau is a restricted-LP artefact under an incomplete row set.
  It is not below 26 in any sense that bears on the criterion, because it is not the
  mass of any covering.
  Reading it as `s(26) >= 53/10` would be exactly the error the freeze-then-decide
  boundary exists to prevent.
- What the run did establish is a cost: 48 LP rounds and 17,162 rows in 3754 s got the
  row loop no closer than `0.953075` least covered mass, with per-round separation cost
  climbing from under a second to over four minutes.
  At this rate the row set is the binding constraint, not the site set.

A successor round resumes from this site set — auto `(38, 51, 62)` plus the 5-per-window
lattice at `53/10`, 1125 orbits over 8505 sites — with a larger deadline, or from a
seeded site set, which the H-225 instrument allows and this round did not use.

## Artifacts

Paths are under
`packing/campaign/series/series-000-smoke-and-calibration/results/agenda-040/`.

| File | SHA-256 |
| --- | --- |
| `exp-215-n26-53-10-run.json` | `ec91c9d27237c239a224f16bd86a08f93157b3938a9d946ef478b0d5020e3442` |

Companion logs: `exp-215-n26-53-10.log`, `exp-215-n26-53-10-rows.jsonl`,
`exp-215-n26-53-10.stdout`. No `exp-215-n26-53-10-covering.json` and no
`exp-215-n26-53-10-family.json` were written.

Measured wall: 3754.0 s on one core, sharing four CPUs with exp-213 and exp-214.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
