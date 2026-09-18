# n=18 467/100 T-019-Seeded Covering Receipt

Status: **covering below 18 on this site set**. Freeze and decide are a
follow-up. The side stays open until a frozen candidate is decided.

Session-139 probe: BC-191 auto `(32, 43, 53)` unioned with T-019's 1184 atom
sites scaled from `459/100` to `467/100`,
`(n, L, B, net) = (18, 467/100, 9977/10000, 181 directions)`.
`--support-cap 0`. The unseeded auto grid locked at `18.000000` unconverged.
The seed's row loop crossed below 18 and converged at `17.875567` with
`least_covered = 1` (44 LP rounds, 6853 sites / 920 orbits). Column generation
then called `check_ceiling` on the untruncated dual and was interrupted after
31 minutes. T-019 at `459/100` is unchanged.

## Command

From `packing/`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`:

```bash
uv run --frozen --all-extras --group dev python -m devtools.run_fractional_colgen \
  --n 18 --side 467/100 --shrink 9977/10000 --direction-steps 181 \
  --grid-counts 32,43,53 --scale 4000000 --support-cap 0 \
  --column-rounds 1 --max-rounds 60 --deadline-seconds 900 \
  --seed-certificate cases/n17_fractional_certificate/certificate.json --seed-map scale \
  --json campaign/series/series-000-smoke-and-calibration/results/agenda-037/n18-467-100-t019-seed-run.json \
  --row-log campaign/series/series-000-smoke-and-calibration/results/agenda-037/n18-467-100-t019-seed-rows.jsonl \
  --log campaign/series/series-000-smoke-and-calibration/results/agenda-037/n18-467-100-t019-seed.log
```

`--freeze-family` was not requested on this invocation. The row-loop log and
the round-0 line in the log file are the record; `run.json` was not written.

## Covering

| Quantity | Value |
| --- | --- |
| Restricted optimum | `17.875567` |
| Sites / orbits / rows | 6853 / 920 / 11528 |
| Seed sites | 1184 |
| LP rounds | 44 |
| Crossing | stayed below 18; round 10 at `17.818182` |
| Wall (row loop) | 420.5 s |
| `least_covered` | 1 |
| Converged | yes (`violated == 0`) |

`devtools.decide_certificate` was not run: no frozen candidate yet.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
