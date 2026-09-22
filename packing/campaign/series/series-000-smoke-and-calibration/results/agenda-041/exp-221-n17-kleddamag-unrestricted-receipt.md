# Exp-221 n=17 Kleddamag Measure, Read Unrestricted

Status: **bounded-negative**. The external `461300/99853` measure is not an unrestricted
threshold certificate at its own core sides, and an exact witness on one of its own
catalogue rows says so without any change of net or selector.
Nothing was registered and no bound moved.

This is the `A2` cell of
[X-041](../../../../explorations/X-041-after-the-n17-certified-bound.md): verify the
external measure *unrestricted*, in this repository’s own language.
The controls come first, because X-041 is explicit that a fail means nothing until the
translation is proved to preserve the object.

## The instrument

[`devtools/translate_kleddamag_certificate.py`](../../../../../devtools/translate_kleddamag_certificate.py)
reads the retained
[`global-certificate.json`](../../../../../resources/web/n17-kleddamag-certified-bound-2026-09-21/kleddamag-17-squares-certified-bound/global-certificate.json)
(`sha256 0288aaac…d69cec`) and emits a `threshold`-variant record in the schema
`devtools.decide_threshold_certificate` reads.
The point orbits expand to their D4 sites as point atoms, the two-of-three orbits to
their physical triples as `2`-of-`3` threshold atoms, and the parent-centre catalogue is
dropped, which is the whole of what “unrestricted” means here.
Three translation choices are stated in the module docstring and repeated here because
each could have been made differently:

| Choice | Value | Why |
| --- | --- | --- |
| `square_side` | `min` over the 7,853 rows, `0.9983666264515567` | the schema carries one shrink; the row-wise guarantee is only as strong as its weakest core |
| `outer_side` | `4613/1000`, the source’s own container, unscaled | the emitted claim is `s(17) >= 4613/1000`; the external value is a dilation step, not a field |
| atoms | the 6,744 positive sites, not all 8,988 | all 2,244 zero-weight sites are triple sites and still reach the event grid through their threshold atom |

## Controls

| Control | What it decides | Result |
| --- | --- | --- |
| `C1` | the nine expanded counts against the artifact’s own `evidence/structure.json` | 1,134 / 852 point orbits, 8,988 / 6,744 sites, 253 orbits / 2,008 triples, point budget 14,640,116,080, triple budget 2,358,311,276, total 16,998,427,356 — every one exact |
| `C2` | every site distinct and inside the container | 8,988 distinct |
| `C3` | every point orbit a full D4 orbit of one weight; every threshold orbit a full D4 orbit of triples, re-derived here | holds |
| `C4` | point + triple budget against `budget_units`, and the `2^50` headroom | `16998427356` exact |
| `C5` | the artifact’s own counting inequality `17 Γ > M` | holds, surplus 1,921,433 units |
| `C6` | the gate’s `Condition 1` predicate on the emitted atoms | 6,744 atoms closed under D4 |
| `C7` | `Condition 4`, `B(1 + D) < 1` | holds at both nets |
| `C8` | **the artifact’s own per-row minima, recomputed from the expanded sites** | 204 rows on the 1440 emission and 24 on the 288 emission, every one matching the retained Python replay on the minimum, the slab count *and* the cell count; the sampled minimum is `1000020517` units, the artifact’s own declared minimum |
| `C9` | one exact unrestricted witness on the measure’s own row | reproduced an independently derived number to the last digit (below) |

`C8` is the control X-041 names, and it is the reason anything below can be believed.
It is a second implementation of the artifact’s sweep, not a call into its checker: the
same signed expansion `1[i+j+k >= 2] = ij + ik + jk - 2ijk` over a slab sweep with exact
integer polygon crossings, reading the artifact’s `sum(w) + 5 sum(w_t) < 2^50` headroom.
Agreeing on the *cell counts* as well as the minima is the sharp part — a differently
partitioned sweep would not.

## C9: the un-confounded measurement

The sharpest number in this lane, and the one that is free of the confound in the next
section. It holds catalogue row 6512’s own core fixed — its own half-tangent
`t = 706027763/1920000000` (parent band `40.3756°`–`40.3829°`, beside Bidwell’s `39.80°`
tilt), its own side `B`, the artifact’s own sites and triples — and moves only the
centre, to the placement whose rotated core touches the wall,
`(B (c(t) + s(t)) / 2, 109373/50000)`. That centre lies `5.5068e-5` outside the row’s
own parent-centre envelope and inside the container.

| Quantity | Exact value | Float |
| --- | --- | --- |
| captured sites | 561 | — |
| point units | 822,915,871 | — |
| triple units | 176,221,844 | — |
| charge | `199827543/200000000` | 0.999137715 |
| `M / 17` | `4249606839/4250000000` | 0.999907492 |
| shortfall | `13086201/17000000000` | 7.6978e-4 |

The comparison is to `M / n` and not to 1 because both conditions are homogeneous in the
weights: a measure charging below `M / n` anywhere is one no rescaling turns into a
certificate. So **the artifact’s measure is not an unrestricted certificate at its own
row 6512, at its own core, on its own support** — the parent-centre restriction is
load-bearing for it by at least `7.6978e-4` of charge.
Nothing about the net or the selector enters that sentence.

The same centre on row 6237 — the tight row, the one attaining the global minimum —
charges `256359651/250000000 = 1.025438604`, above `M / 17`. The failure is a property
of particular rows near `40°`, not of every wall-touching placement.

## The gate

`Condition 1`, `Condition 1'`, `Condition 2'`, `Condition 3` and `Condition 4` all hold
on the emitted bytes at both nets.
`Condition 5'` is where it ends.

VERDICT_PLACEHOLDER

## The confound, named

A plain fail of the 1440-net gate would **not** measure what the parent-centre
restriction carries, and must not be read that way.
The run varies two things at once: it drops the restriction *and* it replaces the
artifact’s adaptive per-row selector — a core angle within `0.006°` of the parent band
and a per-row `B` anywhere in `[0.9983666, 0.9985262]` — with fixed net directions and
`B_min` everywhere. Its least charge is therefore an **upper bound** on what the
restriction alone costs, not a measurement of it.
`C9` above is the measurement, because it changes one thing.

The one-sided implication X-041 leans on does survive: the restricted centre domain is a
subset of the core’s own admissible domain, so a pass would have been decisive.
It did not pass.

## Bound bookkeeping

Even a pass would not have reached the external value.
The emitted certificate claims `s(17) >= 4613/1000`, and the T-022 dilation corollary
lifts `(L, B, D)` to `L sqrt(1 + D^2) / (B (1 + D))`:

| Net | `D` | `B(1 + D)` | dilation supremum | against |
| --- | --- | --- | --- | --- |
| 288 | `207107/144000000` | 0.999802520 | 4.613916 | `T-032` = 4.613046 |
| 1440 | `207107/720000000` | 0.998653805 | 4.619219 | external = 4.619791 |

So the 1440 net at `B_min` was never worth the external `4.619791`; it was worth
`4.619219`, about `5.7e-4` less.
Matching `4.619791` unrestricted on the 1440 net needs `B <= 0.9982429`, a smaller core
than any row of the catalogue carries.

## H-235: are the triples load-bearing at these weights?

A screen folded into the same tool, and independent of everything above: it runs
*restricted*, on the artifact’s own rows, with every two-of-three atom dropped and every
point weight left where it is.
By homogeneity the point part rescales to a point certificate at the same
`(L, B, catalogue)` exactly when its least charge exceeds
`M_p / 17 = 183001451/212500000 = 0.861183299`.

H235_PLACEHOLDER

The screen is one-sided and about *these* weights only: a point-only linear program with
the triples’ budget returned to the sites is a different question and this says nothing
about it.

## Commands and wall times

All from `packing/`, all `uv run --frozen --all-extras --group dev`.

| Wall | Command |
| --- | --- |
| 8.7 s | `python -m devtools.translate_kleddamag_certificate --direction-steps 288 --control-rows 24 --output …-net288.json --report …-report-net288.json` |
| 87.9 s | `python -m devtools.translate_kleddamag_certificate --direction-steps 1440 --control-rows 200 --quiet --output …-net1440.json --report …-report-net1440.json` |
| 23.0 s | `python -m devtools.translate_kleddamag_certificate --direction-steps 1440 --control-rows 24 --quiet --charge-at 6512 wall 218746/100000 --charge-at 6237 wall 218746/100000 --report …-witness-control.json` |
| 1.3 s | `python -m devtools.decide_threshold_certificate --quick --workers 1 …-net1440.json` |
| DECIDE_WALL | `PACK_JOBS=2 python -m devtools.decide_threshold_certificate --exact-only --workers 2 …-net288.json` |
| H235_WALL | `python -m devtools.translate_kleddamag_certificate --point-only-rows 400 --control-rows 0 --report …-h235-point-only-screen.json` |

The machine carried a load average of 15 to 20 on four cores throughout, from other
lanes; every wall above is a contended wall and none of them is a cost measurement.

Emitted bytes beside this receipt:

| File | sha256 |
| --- | --- |
| `exp-221-n17-kleddamag-unrestricted-net288.json` | `b88d10e89e79068567e945b72f3e65d1a9d63f25a6637a60a7de059c202a028c` |
| `exp-221-n17-kleddamag-unrestricted-net1440.json` | `969a1909933ca80e80b3f74775742eb5c2743451f116144b4bc7523363f5d3b1` |

## What this did not establish

- **No complete 1440-net decision.** `Condition 5'` over all 1,441 directions is about
  2.6 hours of gate on two uncontended workers and was not run; what ran is the nested
  288-net decision, whose directions are every fifth direction of the 1440 net, so its
  refutation is a refutation there too.
- **No `C4` or `C5` rung for anything.** Nothing here is registered, and the emitted
  records are candidates, not certificates.
- **The interval route never decided this object.** `MAX_INTERVAL_ATOMS` is 4,096 and
  the translation carries 6,744 point atoms, so the two-route gate cannot reach
  `RETAINABLE` or a two-route refusal on any object of this size.
  That is a tool limit and not a verdict.
- **Nothing about a re-priced measure.** Whether an LP priced unrestricted on this
  support reaches `4.6198` is cell `A1`, untouched here.
- **The receipt is not in the document map.** `docs/project/document-map.yaml` is
  outside this lane’s write scope; the entry
  (`role: research-report, authority: record, lifecycle: retained`) is the
  coordinator’s.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
