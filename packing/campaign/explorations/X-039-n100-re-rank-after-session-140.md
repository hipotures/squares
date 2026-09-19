---
title: X-039 — n<=100 re-rank after Session-140
softschema:
  contract: packing.squares:Exploration/v1
  schema: ../schemas/exploration.schema.yaml
  envelope: exploration
  status: enforced
exploration:
  id: X-039
  title: N<=100 Re-Rank After Session-140
  date: '2026-09-19'
  author: Cursor session-141 coordinator
  campaign: packing.squares
  brief: >-
    Re-rank every open s(n) floor at n<100 using Session-140 masses, the leftover
    raise-only rule, and the other open hypotheses that can run beside one covering
    core. No new instrument. No bound claim.
  sources:
  - packing/campaign/explorations/X-038-n100-lower-bound-survey.md
  - packing/campaign/agent-sessions/session-140-lb-survey.md
  - packing/campaign/series/series-000-smoke-and-calibration/results/agenda-038/leftover-side-ranking.md
  - packing/campaign/hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md
  - packing/frontier/covering-values.yaml
  - packing/frontier/n-012.md
  - packing/frontier/n-017.md
  - packing/frontier/n-018.md
  - packing/frontier/n-019.md
  - packing/frontier/n-020.md
  - packing/frontier/n-021.md
  proposes: [H-219, H-220, H-221]
---
# X-039: What Session-140 Changed About the n<100 Queue

[X-038](X-038-n100-lower-bound-survey.md) ranked the stock colgen against every open
floor at `n <= 100`. Session-140 ran that queue. This report re-ranks from those
masses. It does not replay a named site set whose restricted optimum is already above
`n`, and it does not treat a still-below-`n` unconverged loop as a retain.

Thirty-two sizes in `1..100` stay proved equal. Sixty-eight stay open. First-party
covering still exists only on `11, 12, 17, 18, 19, 20, 21`.

## Session-140 masses that decide the next spend

| n | Side | Named site set | Mass | Crossed `n` |
| ---: | --- | --- | ---: | --- |
| 18 | `187/40` | T-027 auto `(32,43,53)` plus windows 5 | `17.879034` | no; **T-028 retained** |
| 18 | `1871/400` | T-028 auto plus windows 5 | `17.889237` | no; **T-029 retained** |
| 20 | `973/200` | T-021 four-grid `(34,46,56,64)` plus windows 7 | `19.939212` after 2400 s | no |
| 20 | `971/200` | T-021 auto `(34,45,56)` plus windows 6 | `19.910044` | no |
| 12 | `397/100` | T-017 four-grid plus windows 7 | `12.133391` | yes; converged |
| 12 | `3969/1000` | T-017 four-grid `(26,35,43,48)` plus windows 7 | `12.091168` | yes |
| 17 | `23/5` | T-019 four-grid plus windows 8 | `17.120106` | yes |
| 17 | `461/100` | T-019 auto plus windows 5 | `17.195968` | yes |
| 19 | `481/100` | T-020 auto plus windows 6 | `19.132115` | yes |
| 19 | `241/50` | T-020 auto plus windows 6 | `19.247109` | yes |
| 21 | `97/20` | T-021 auto plus windows 6 | `19.814820` | no; same side as T-021 |

Raise-only: remaining rows on a named set raise that restricted optimum. Adding sites
can still lower it. More wall on leftover n=20 `971/200` auto plus windows 6, or on
n=20 `973/200` four-grid plus windows 7, cannot retain.

## Ranked probes

Likelihood is “a `RETAINABLE` freeze this session”, then “a new covering row on an
untried `(n, side, site_set)`”.

| Rank | Claim | n | Side | Site set | Deadline | Likelihood |
| ---: | --- | ---: | --- | --- | ---: | --- |
| 1 | H-219 | 18 | `1871/400` | T-028 seed, auto, windows 5 | 1200 s | T-029 retained |
| 1b | H-219 | 18 | `1871/400` | T-028 seed, four-grid `(32,43,53,60)`, windows 5 | 1800 s | medium; only if rank 1 stays below 18 unconverged |
| 2 | H-218 | 20 | `971/200` | T-021 seed, four-grid `(34,46,56,64)`, windows 7 | 2400 s | done; 19.857588 unconverged |
| 3 | H-218 | 20 | `243/50` | same four-grid plus windows 7 | 1200 s | done; 19.887914 unconverged |
| 4 | H-220 | 32 | `29/5` | auto, windows 5, no seed | 1200 s | done; 29.803318 unconverged |
| 5 | H-220 | 31 | `57/10` | auto, windows 5, no seed | 1200 s | done; 28.331329 unconverged |
| 6 | H-220 | 30 | `559/100` | auto, windows 5, no seed | 1200 s | done; 27.178193 unconverged |
| 7–11 | H-220 | 26, 27, 29, 45, 44 | queued Nagamochi sides | auto, windows 5, no seed | 1200 s | low |

n=18 is off the H-218 sweep `{12, 17, 19, 20}`. A retain at `1871/400` is the next T-id
and does not confirm H-218. Rank 2 finished `19.857588` unconverged; remaining rows
raise. Rank 3 finished `19.887914` unconverged; remaining rows raise. H-218 stays
unconfirmed. exp-162 is abandoned; the reopen is exp-164 then exp-165, both
unresolved. The live probe is exp-169 / H-220 at n=26 `513/100`.

n=11 stays T-026. H-216 at n=6 is calibration, not an n=11 result. n=21 `97/20` is the
same verified side as T-021.

The 68 open sizes include `26–32`, `37–45`, `50–61`, `65–78`, and `82–100` with no
first-party covering. This session takes the eight queued Nagamochi sides after n=18 and
the n=20 new-site probe. After those, `rank-queue.yaml` walks n=19 `481/100` four-grid plus windows 7,
n=12 `793/200` auto plus windows 7, n=12 `397/100` auto plus windows 7, n=19
`241/50` four-grid plus windows 7, n=12 `793/200` four-grid plus windows 7, and
n=18 `4679/1000` T-029-seeded auto plus windows 5. n=17 `231/50` stays off the
walker: nearby auto plus windows 5 already crossed 17 at `461/100`. n=13–16 and
n=22–25 are proved; no runway. n=28, n=61, and n=78 stay deferred. Register a
new experiment before the n=18 `4679/1000` probe starts.

## Other hypotheses beside the covering core

One CPU. Sequential colgen. Sub-agents own audit, registration, and W5.

| Claim | This session | Why |
| --- | --- | --- |
| H-219 | first covering probe | Same class as T-028; unused leftover side |
| H-218 | reopen after exp-163 terminals | exp-164 at `971/200` four-grid `19.857588` and exp-165 at `243/50` `19.887914` unconverged; do not replay those sets |
| H-220 | live after exp-168 | exp-166/167/168 at n=32 `29.803318`, n=31 `28.331329`, n=30 `27.178193` unconverged; live probe n=26 `513/100` as exp-169 |
| H-221 | after ranked H-218 long-shots | T-029-seeded next rung at `4679/1000` |
| H-210 / H-211 | off-CPU if Node permits | Workbench determinations; not a floor |
| H-163 / exp-161 | `--check` only | Encode already timed out; no `--search`; do not steal the covering core |
| H-217 | reader tests only | Blocked on sites-1; do not close `think-g3j7` or `think-gyzw` |
| H-216 | parked as n=11 | Two site sets already cover `>= 6` |
| H-153 / H-017 / M3 | parked | One-body pause; packing-campaign NO-GO; encoding-bound |

Block 4 is the efficiency block: harvest hosted Packing and Pages walls under
`think-g4n9`. Do not edit `gate-budgets.yaml`. Do not flip enforcement.

## Autonomous loop

`python -m devtools.run_covering_queue` over
`results/agenda-039/rank-queue.yaml`. Skip a probe whose run JSON exists. Halt on freeze
mass `< n`, then `declare_least_cell_mass` and `decide_certificate`. T-id only on
`RETAINABLE`. First walker `--stop-at` is the Block 4 start. Resume the same queue after
W5. Do not walk `leftover-queue.yaml` (ranks 1–4 already have run JSONs; its default
`stop_at` is Session-140’s wall).

Coordinator owns identifiers, covering-values, T-id landing, ledger, and the stacked
PR. Covering stays one process, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=1`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
