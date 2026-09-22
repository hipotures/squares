# Exp-225 n=27, n=28 and n=29 at 548/100 by Re-Bumping the n=29 Atoms

Status: **not retainable, nothing registrable**. The re-bump did what it was meant to do
— it moved Condition 5 from `undecided` to `holds` on the interval route, 272 stalled
boxes to 0 — and `decide_certificate` still refuses, because the gate runs that route in
a mode that asks a strictly harder question than Condition 5.

No bound moves. `s(27)`, `s(28)` and `s(29)` stand where they stood.

## What was tested

[Agenda-039’s retained n=29 candidate](../agenda-039/n29-548-100-auto-windows5-certificate.json)
is a converged covering freeze at `(n, L, B, net) = (29, 137/25, 9977/10000, 181 steps /
182 directions)`, mass `52081879/2000000 = 26.0409395`, 1329 atoms.
Its own receipt records the gate refusing it on 272 stalled interval boxes.

Only Condition 2 mentions `n`, so those atoms are a candidate at every integer above
their mass — `n = 27` included, where the verified lower bound is `5.24264068712`
against this candidate’s `L = 137/25 = 5.48`. The mass sits `0.959` below 27, and that
gap is spendable: scaling every weight up scales the least covered cell mass with it.

## Premise check

Read before anything ran, then checked mechanically against the four modules the two
routes use.

| Module | Where `n` is read | Is it a condition? |
| --- | --- | --- |
| `certificate.py` | `_condition_mass_below_n`, lines 253–259 | Condition 2, and nothing else |
| `certificate.py` | `grid_refutation_order`, `ceiling_side`, `ceiling_side_for_net` | No — separate lemmas, taking `n` as an argument |
| `sweep.py` | nowhere | Condition 5’s engine never sees `n` |
| `interval.py` | line 405, line 783–784 | An `int64` guard, and the interval route’s own Condition 2 |
| `corner_clip.py`, `model.py` | class id and claim strings | No |

`least_size_certified` states the same thing in the source, and
`devtools.decide_certificate` prints it: on the retained n=29 bytes the gate’s own
second line reads `certifies every n >= 27`.

The gate reads `n` in three further places, all of which the restatement has to satisfy
rather than evade: the declared `claim` must read `s(n) >= L`, the declared `id` carries
`n` under the corner clip, and the side must not exceed `ceil(sqrt(n)) * B`. The third
is free here — `ceil(sqrt(27)) = ceil(sqrt(28)) = ceil(sqrt(29)) = 6`, so the ceiling is
`29931/5000 = 5.9862` at all three — and the first two are what the restatement writes.

**The premise holds.** Nothing outside Condition 2 ties this atom set to `n = 29`.

## Baseline

Reproduced exactly, including the box count.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=2 \
uv run --frozen --all-extras --group dev python -m devtools.decide_certificate \
  campaign/series/series-000-smoke-and-calibration/results/agenda-039/n29-548-100-auto-windows5-certificate.json
```

| Quantity | Session-141 | Here |
| --- | --- | --- |
| Enclosure | `(398409/400000, 4000013/4000000)` | `(398409/400000, 4000013/4000000)` |
| Boxes | 4,960,181 | 4,960,181 |
| Stalled | 272 | 272 |
| Interval wall | 65 s | 162 s |
| Verdict | not `RETAINABLE` | not `RETAINABLE`, `EXIT:1` |

The exact route never ran: the gate refuses after the interval route, so it is the
interval route that has to be moved.

## The re-bump

`devtools.rebump_certificate` multiplies every weight by a rational bump, rounds up to a
multiple of `1/scale` the way `rationalise_sites` does, and declares a chosen `n`. It
refuses a bump below 1, a total mass not strictly below `n`, a side above the ceiling,
or any closed-form condition that fails on the result; it writes
`least_cell_mass: null`, so the declaration and the verdict stay where they belong.

```bash
uv run --frozen --all-extras --group dev python -m devtools.rebump_certificate \
  --source campaign/series/series-000-smoke-and-calibration/results/agenda-039/n29-548-100-auto-windows5-certificate.json \
  --n 27 --bump 103/100 \
  --output campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-548-100-bump103-certificate.json \
  --report campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-548-100-bump103-rebump.json
```

Run again with `--n 28` and `--n 29`. The three files differ in exactly three lines —
`id`, `n`, `claim` — and in nothing else.

`103/100` is the bump.
The affordable ceiling is `27 / (52081879/2000000) = 1.03682895…`; `1.04` is refused by
the tool, naming Condition 2 and the mass `13541367/500000` it would have produced.

| Quantity | Value |
| --- | --- |
| Bump | `103/100` |
| Scale | `4000000`, the source weights’ own denominator |
| Atoms | 1329, at the same sites, the same net, the same `B` |
| Source mass | `52081879/2000000` = 26.0409395 |
| **New mass** | **`107289303/4000000` = 26.82232575** |
| Headroom below 27 | `710697/4000000` = 0.17767425 |
| Predicted least cell mass | at least `412001339/400000000` = 1.0300033475 |

## Declaration

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
uv run --frozen --all-extras --group dev python -m devtools.declare_least_cell_mass \
  campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-548-100-bump103-certificate.json
```

The one-worker exact sweep accepted all three files at the same number, above the
predicted floor, as the monotonicity argument requires.

| File | Verdict | Least cell mass | Wall |
| --- | --- | --- | --- |
| `exp-225-n27-548-100-bump103-certificate.json` | accepted | `4120021/4000000` = 1.03000525 | 97 s |
| `exp-225-n28-548-100-bump103-certificate.json` | accepted | `4120021/4000000` | 99 s |
| `exp-225-n29-548-100-bump103-certificate.json` | accepted | `4120021/4000000` | 174 s |

## Decision

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PACK_JOBS=1 \
uv run --frozen --all-extras --group dev python -m devtools.decide_certificate \
  campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-548-100-bump103-certificate.json
```

| `n` | Interval verdict | Enclosure | Boxes | Stalled | Wall | Gate |
| --- | --- | --- | ---: | ---: | ---: | --- |
| 27 | `accepted=False` | `(1025913/1000000, 4120021/4000000)` | 4,955,893 | 272 | 291 s | `REFUSED`, `EXIT:1` |
| 28 | `accepted=False` | `(1025913/1000000, 4120021/4000000)` | 4,955,893 | 272 | 205 s | `REFUSED`, `EXIT:1` |
| 29 | `accepted=False` | `(1025913/1000000, 4120021/4000000)` | 4,955,893 | 272 | 115 s | `REFUSED`, `EXIT:1` |

Three refusals each, identical apart from the path: Condition 5, 272 stalled boxes, and
an enclosure with width.
The three runs agree to the box and to the fraction, at three different declared `n` —
which is the premise showing through in the failure as well as in the claim.
The walls differ only with what else the shared four-core host was running.

The exact route again never ran, so none of the three files carries a gate-printed
digest. `decide_certificate` prints a SHA-256 only on a positive full verdict, and by
`OR-16` these artifacts are identified by repository-relative path and Git revision
rather than by a digest written beside them.

## Why the gate still refuses, exactly

The enclosure lower end moved from `0.9960225` to `1.025913` — above 1, and above it by
2.6%. Both ends scaled by the bump, which is what the argument predicted:

|  | Baseline | Bumped | Ratio |
| --- | --- | --- | --- |
| Enclosure lower | `398409/400000` | `1025913/1000000` | 1.0300099 |
| Enclosure upper | `4000013/4000000` | `4120021/4000000` | 1.0300019 |
| Relative shortfall of lower against upper | 0.3980737% | 0.3973038% | — |

**The shortfall is relative, so reweighting cannot close it.** The gate calls
`verify_by_intervals(..., enclose=True)`, and in that mode a box is settled only against
the least admissible point value seen so far — the exact minimum — rather than against
mass 1. A box straddling a seam, one coverage region’s leave-edge on another’s
enter-edge, cannot be split below `RESOLUTION_FLOOR = 1e-12`; it comes back with a bound
short of that minimum by whatever the seam costs, and scaling every weight moves the
bound and the threshold together.

That mode is not arbitrary.
The gate needs a width-zero enclosure so the two routes agree on the *number*, not
merely on the verdict, and `D-435` records what happens when acceptance in one mode is
not asked the other mode’s question.

`devtools.measure_interval_stalls` runs the same route at the other threshold —
`enclose=False`, which settles a box as soon as its bound reaches mass 1, which is what
Condition 5 asks and nothing more.

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
uv run --frozen --all-extras --group dev python -m devtools.measure_interval_stalls \
  --source campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-548-100-bump103-certificate.json \
  --mode condition5 \
  --report campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-interval-condition5.json \
  --dump-stalls campaign/series/series-000-smoke-and-calibration/results/agenda-041/exp-225-n27-interval-condition5-stalls.json
```

Run again with `--mode enclosure` for the gate’s own threshold, and with
`--source ../agenda-039/n29-548-100-auto-windows5-certificate.json` for the control.

| Bytes | Mode | Directions | Boxes | Stalled | Condition 5 | Wall |
| --- | --- | ---: | ---: | ---: | --- | ---: |
| agenda-039 original | `condition5` | 363 | 4,890,517 | 272 | `undecided` | 186 s |
| exp-225 bumped | `condition5` | 363 | 2,707,989 | **0** | **`holds`** | 116 s |
| agenda-039 original | `enclosure` (the gate) | 363 | 4,960,181 | 272 | `undecided` | 162 s |
| exp-225 bumped | `enclosure` (the gate) | 363 | 4,955,893 | 272 | `undecided` | 152 s |

The control is the first row against the second.
At the theorem’s own threshold the bump clears the stall completely, over the full
doubled net, and the stall dump is empty.
The margin was the obstruction to Condition 5; it is not the obstruction to the gate.

The last row is `--mode enclosure`, which reproduces the gate’s own interval numbers to
the box — 4,955,893 and 272, the same as the `decide_certificate` runs above — and adds
what the gate does not print: **every one of the 272 stalled boxes is in direction
`0`**, the axis-parallel one, and that direction is also where the least point mass
`4120021/4000000` is attained.
The other 362 directions certify.
The stall dump records two further unsplittable boxes at each of directions `142` and
`142'`; neither counts as a stall, because their bounds already reach the threshold.

Direction `0` is where a seam is most likely by construction: the atom sites lie on
rational grids, and at zero rotation a coverage region’s leave-edge at `x + B/2` can
land exactly on another’s enter-edge at `x' - B/2`. That is a fact about the
coordinates, and no reweighting touches it.

## What is established, and what is not

Established, on frozen bytes, by the repository’s own tools:

- Only Condition 2 mentions `n`, in both routes.
  The same atom set is a candidate at 27, 28 and 29.
- A candidate at `L = 137/25` exists at `n = 27` with total mass `107289303/4000000`,
  strictly below 27 by `710697/4000000`, whose exact event-cell sweep accepts with least
  covered cell mass `4120021/4000000`.
- The interval route, at the Condition 5 threshold over the full 363-direction doubled
  net, certifies that candidate with zero stalled boxes.

**Not established, and not to be read into the above:**

- `s(27) >= 137/25`, `s(28) >= 137/25` and `s(29) >= 137/25`. No `RETAINABLE` verdict
  was printed for any of them.
  Nothing here is a bound, and nothing here is registrable.
- That the candidate would survive the gate under any change to the gate.
  What the enclosure mode fails to pin is a real gap in the interval arithmetic’s
  knowledge of this atom set, and whether accepting on the Condition 5 threshold alone
  is sound policy is a question for the owner of that gate, not for this lane.
- Any dilated figure. `L = 137/25` flat is the only side in play;
  `devtools.dilation_corollary` was not run.
- Anything about `n = 29`’s own bound beyond the arithmetic: `137/25 = 5.48` is above
  its verified `5.472135955`, so the same bytes would move it too if they were ever
  retained. `n = 29` at `548/100` is **not** currently registered as a result; it appears
  only as a covering row in `frontier/covering-values.yaml`, marked
  `frozen_artifact: null`.

## More-walling

The register row and the agenda-039 receipt say “Do not more-wall this set.”
That is a scheduling instruction against spending further column-generation wall on the
same `(n, side, site_set)`, and the same receipt says what is allowed: *“No new LP run
is needed for the existing candidate; a future interval-verification budget may retry it
as specified by exp-171.”* No LP ran here.
The covering, the site set, the net and `B` are untouched; only the rational weights on
the frozen atoms were re-rounded.

## Next

The candidate is one gate mode away from a decision, and the question is now about the
gate rather than about the certificate.
Two routes a coordinator could take:

1. **Close the seam.** All 272 stalled boxes sit in direction `0` and their coordinates
   are dumped in `exp-225-n27-interval-enclosure-stalls.json`, so the atom pairs whose
   axis-parallel edges coincide can be read off without another search.
   Whether a small D4-symmetric site adjustment removes them is answerable from that
   file; acting on the answer needs the covering re-run, which is a `more-wall` decision
   the register currently forbids.
2. **Decide the policy.** Ask whether a certificate whose Condition 5 is certified by
   the exact sweep and by the interval route at the mass-1 threshold, but whose
   enclosure cannot be pinned, should be retainable — and if so, under what recorded
   escape and with what soundness argument.
   That is a `W7` question, not a research slice.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
