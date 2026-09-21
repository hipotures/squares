# n=17 23/5 T-019-Seeded Ceiling-Family Receipt (exp-213)

Status: **unresolved; the process was lost before any freeze**. No family, no freeze, no
run summary. H-224 is undecided in both directions.

Session-144 chunk 1,
[exp-213](../../experiments/exp-213-h224-n17-23-5-ceiling-family.md): BC-191 auto grids
unioned with T-019’s atom sites scaled from `459/100` to `23/5`, plus
`--seed-windows 5`, `(n, L, B, net) = (17, 23/5, 9977/10000, 181 directions)`, every
positive dual row kept (`--support-cap 0`).

## Command

The registered command in the experiment record, started 2026-09-20T07:15Z from
`packing/` with `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`.

## What ran

| Quantity | Value |
| --- | --- |
| Round 0 rows / orbits / sites | 10678 / 928 / 7068 |
| LP rounds in round 0 | 44 |
| Objective at the end of round 0 | `17.042346318` (float LP; not a bound) |
| Least covered mass at the end of round 0 | `1.000000000` |
| Wall to the end of round 0 | 1583.2 s |
| Stop | The column round started (one orbit added); the container restarted before the 2400 s deadline and the process did not write `exp-213-n17-23-5-run.json`, a freeze, or a family |

The row log (`exp-213-n17-23-5-rows.jsonl`) and the driver log (`exp-213-n17-23-5.log`)
are retained; the stdout shows only the settings block.

## Determination

H-224 remains **unresolved**.

- Confirmation failed for want of an artifact: no family was frozen, so neither
  `independent_ceiling_reader` nor `replay_ceiling_family` ran.
- Refutation failed for the same reason: no covering below 17 exists to decide.
- The round-0 restricted optimum `17.042346318` on this site set refutes point
  certificates at `23/5` on this site set only, consistent with Session 140’s
  `17.120106` on the four-grid plus windows 8 set.
- Keeping every positive dual row cost 1583 s for round 0 alone; a resumed attempt needs
  a new experiment id and a support cap.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
