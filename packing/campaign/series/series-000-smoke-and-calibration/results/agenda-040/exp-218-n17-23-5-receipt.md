# n=17 23/5 T-019-Seeded Ceiling-Family Receipt (exp-218)

Status: **unresolved; the accepted depth-one family has total just below 14, not 17.**
This site set is refuted for point certificates at `23/5`; H-224 is undecided.

Session-144 chunk 1,
[exp-218](../../experiments/exp-218-h224-n17-23-5-ceiling-family-cap32.md): the exp-213
command with `--support-cap 32`, `(n, L, B, net) = (17, 23/5, 9977/10000,
181 directions)`, T-019 atom sites scaled from `459/100`, auto grids, windows 5.

## Covering

| Quantity | Value |
| --- | --- |
| Round 0 rows / orbits / sites | 6133 / 506 / 3749 at the first LP; 928 orbits over 7068 sites at the stop |
| Objective | `17.04234631807338` (float LP; not a bound) |
| Stop | `converged: every placement covers mass 1` after one column round |
| Frozen covering mass | `1704253/100000` over 1384 atoms (above 17; no gate) |
| Wall | 1562.3 s |

## Family

The priced dual (`exp-218-n17-23-5-family.json`, 256 placements, source total
`12.867376646860114`, pointwise depth up to `1.73`) folded to 256 placements with the
total preserved exactly and polished in 45.2 s to a rounded family:

| Reader | Total | Max depth | Vertices | K3 |
| --- | --- | --- | --- | --- |
| `polish_ceiling_family` | `874999999/62500000 = 13.999999984` | `1` | 287456 | fails |
| `independent_ceiling_reader` | `874999999/62500000` | `1` (K0, K1, K2 hold) | 287456 | fails: total weight at least 17 |
| `replay_ceiling_family --check` | `874999999/62500000` | `1` | 287456 | fails |

The fold used the same `t = 1` to `t = 0` rule as the h216 and exp-214 receipts (scratch
script, not a retained tool; the fold changed no weight and preserved the total
exactly); retaining that fold as a devtools command is open work.

## Determination

H-224 remains **unresolved**.

- Confirmation failed: the accepted depth-one family has total `13.999999984 < 17`, so
  it does not obstruct point certificates at `23/5`.
- Refutation failed: no covering below 17 exists (the frozen mass is `17.04`).
- What is established: every point certificate at `n=17, 23/5, B = 9977/10000` on this
  net has mass at least the family’s total, about 14, for every site set; and this
  T-019-seeded site set cannot carry one (restricted optimum `17.04`, consistent with
  Session 140’s `17.12` on the four-grid plus windows 8 set).

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
