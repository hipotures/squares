# Leftover First-Wave Sides

Status: **ranked**. `think-7igz`. Start `leftover-queue.yaml` only after
`first-wave-queue.yaml` finishes (n=20 2400 s, then n=21).

A restricted optimum already above `n` cannot retain on more wall of the same site set.
Remaining rows raise that value.
Adding sites can still lower it, so the side stays open, but leftover wall goes to an
untried side or an untried site set, not to a replay that is already above `n`.

The n=20 `973/200` four-grid plus windows 7 2400 s follow-up stopped at `19.939212`
unconverged. That set stays below 20 and is not a retain.
Leftover n=20 is `971/200`.

## Queue

| Rank | Bead | n | Side | Site set | Why |
| ---: | --- | ---: | --- | --- | --- |
| 1 | think-zoq4 | 19 | `241/50` | T-020 auto plus windows 6 | Two cents above `24/5`. No covering row. Same recipe as `481/100` at `19.132115`. |
| 2 | think-5q81 | 17 | `461/100` | T-019 auto plus windows 5 | Two cents above `459/100`. No covering row. The `23/5` constructions are already above 17. |
| 3 | think-d2ad | 20 | `971/200` | T-021 auto plus windows 6 | Between the T-021 floor and `973/200`. No stock row. Skip if the 2400 s `973/200` freeze is RETAINABLE. |
| 4 | think-h02v | 12 | `3969/1000` | T-017 four-grid `(26,35,43,48)` plus windows 7 | Nearest side above `99/25`. Auto and four-grid reached `12.116` without windows. |
| 5 | think-avmz | 18 | `1871/400` | T-028 auto plus windows 5 | One step above `187/40`. `117/25` still sits on the `18.000000` plateau. |

## Do not replay

| n | Side | Why leftover wall is wasted for retain |
| ---: | --- | --- |
| 17 | `23/5` | Best stock row is `17.042346` (windows 5, 9 violated). Already above 17. |
| 12 | `397/100` | Cert-seed `12.016263`; session-140 four-grid plus windows 7 converged at `12.133391`. |
| 19 | `481/100` | Session-140 auto plus windows 6 stopped at `19.132115`. |
| 19 | `97/20` | `19.808958`, worse than `481/100`. |
| 18 | `117/25` | Locked at `18.000000` on every named seed. |
| 18 | `469/100`, `47/10` | Plateau or above 18. |
| 12 | `398/100`, `3985/1000`, `399/100` | Grid rows at `16.000000` are dual-feasibility artifacts. |
| 20 | `973/200` H-062 sets | Auto-grid `20.001502` and cert-seed `20.000223` already crossed. |
| 21 | `997/200` | Grid artifact at `25.000000`. |
| 11 | any side above T-026 | Covering-only. Not this campaign’s floor win. |

A longer wall on n=17 `23/5` windows 5, n=12 `397/100` `(26,35,43,48)` plus windows 7,
or n=19 `481/100` is a new named set only when the grids or windows differ.
Those sets can still lower the covering value.
They are not the first leftover spend: each already has a restricted optimum above `n`.

## Second wave

`second-wave-nagamochi-triage.md` keeps n=32, 31, 30, 26, 27, 29, 45, 44. An audit left
those eight sides in the floor-to-ceiling interval.
n=28 is in the 26–32 block and is omitted.
n=61 and n=78 stay deferred.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
