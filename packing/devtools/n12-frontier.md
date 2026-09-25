# Autonomous n=12 frontier controller

An unattended, **rule-based research campaign** on one Linux server. It selects
experiments, responds to numerical and operational outcomes, and preserves evidence.
It does not invent arbitrary mathematical methods or promise a new bound.

## Run and recover

From `packing/`:

```bash
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search

PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search --resume

uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search --status
```

The first Ctrl-C, SIGTERM, or SIGHUP requests a graceful stop. The controller
finishes the current bounded side cycle or repair attempt, saves state, and prints
a summary. A cycle can include several stages and exact verification; stopping is
not instantaneous. Repeated signals do not secretly become a destructive kill.
Watchdogs remain active. An OS hard shutdown cannot be delayed by this program.

Use `tmux` for ordinary SSH sessions. SIGHUP requests a stop rather than promising
that an SSH disconnect will keep the entire campaign running forever. After a
controller crash, a detached supervisor can finish and record the active job;
`--resume` attaches to that job. A reboot loses in-flight computation but not
completed artifacts or the last atomic checkpoint. An incomplete job can be
retried within its budget; a missing outcome is never fabricated as success.

Stop an old version gracefully **before** pulling an upgrade. Schema-2 campaigns
migrate to schema 3 with an untouched backup. Existing history and verified
artifacts remain intact. A legacy best certificate without a digest is fully
reverified once before new work. Never manually edit `verified_low` to bypass this.

## Autonomous decisions

Priority: recover active work; finish a useful same-side precision retry; diagnose
promising rejected candidates; change a stalled instrument; otherwise bisect the
heuristic frontier. SEARCH_FAILED is not a mathematical upper bound on `s(12)`.

| Strategy | Change from baseline |
| --- | --- |
| `baseline` | Production grids; 180 direction steps; B=9977/10000; support cap 32 |
| `centre` | Translate a seed about the centre instead of dilating it |
| `pricing` | Price up to 128 dual-support rows |
| `windows` | Add five sites per axis-aligned overlap window |
| `dense` | Seed grids 31,43,53 |
| `fine-net` | 720 steps and B=4997/5000, preserving strict containment |

`--strategies baseline,centre,pricing` restricts the portfolio. Every choice and
reason is saved. The last successful strategy is preferred at later midpoints.
Numerically indistinguishable binary64 sides are not recomputed with the same
completed instrument merely because their exact fractions differ. Explicitly
increasing row/column budgets on resume creates a new search revision, allowing
stronger trials without erasing old failures.

The policy switches after a measured plateau, several unsuccessful cycles, a narrow
heuristic frontier (`--strategy-width 1/100000`), or binary64 saturation. Same-side
weight precision has priority over saturation/exhaustion. A proved improvement at
or above an old heuristic high supersedes that high and opens a fresh endpoint;
it never leaves an inverted interval that cannot resume.

Column budgets 8/20/40/60 are **additional generation-stage budgets**, not 60 total
rounds. Actual completed rounds are counted. Nonconverged inner rows are UNRESOLVED,
with one bounded larger-row-budget retry, never SEARCH_FAILED. A plateau after the
normal stage abandons further deep stages of that instrument rather than blindly
spending the whole budget.

## Raw weights and repair

New converged generation saves `raw-weights.json`: exact rational geometry plus
hexadecimal binary64 LP weights. If objective <12 but rational mass >=12, scales
are doubled from 1,600,000 up to 25,600,000. `frontier_rationalise` reuses the raw
snapshot with **zero new LP solves**, using the unchanged production rationaliser
and safety bump. Old campaigns without snapshots cannot reconstruct raw weights
from rounded weights: their first stronger trial still needs a fresh LP solve.
Changing the grid, net, shrink, or other search strategy also requires generation.

Declaration-rejected below-12 candidates are eligible for diagnosis. Structured
reports distinguish invalid input/preconditions, coverage deficits, interval stalls,
and full-gate refusals. For mass M and exact minimum q, a uniform repair is possible
only when q>0 and M/q<12. The first boost then targets a sufficient mass strictly
below 12. Other gate refusals use the bounded six-step margin ladder. Invalid or
insufficient repairs are abandoned. Every positive proposal still needs the full gate.

Repair steps share ordinary jobs' durable lifecycle, nested orphan detection,
watchdogs, and receipts. Completed diagnoses/boosts are reused. A crash after a
successful boost but before frontier promotion does not lose that proof.

## Proof boundary and visible results

Only acceptance by **both existing exact routes** in `devtools.decide_certificate`
can produce VERIFIED. Promotion checks n, exact side, atom mass, and SHA-256 against
a structured full-gate receipt. The verifier binds its source fingerprint and
unchanged candidate bytes. A timeout, zero exit alone, missing report, or unbound
RETAINABLE text is not proof. Pending/rejected candidates never get verified names.
The original retained certificate in `cases/` is not overwritten.

An improved bound prints a multi-line `VERIFIED LOWER BOUND IMPROVEMENT` banner:
exact/decimal side, improvement, mass, certificate path, and digest. It is obvious
without colour. `findings.json` and `findings.md` separately retain those results.
Opportunity lines are not proofs. Full logs are plain text; normal stage boundaries,
plan reasons, and five-minute heartbeats stay concise.

## Operational limits

| Option | Default | Meaning |
| --- | ---: | --- |
| `--stage-seconds` | 3600 | Total generation-job wall budget, including retries |
| `--verify-seconds` | 7200 | Total verification-job wall budget, including retries |
| `--no-progress-seconds` | 1200 | No changes to generation logs; 0 disables |
| `--heartbeat-seconds` | 300 | Status interval, not a timeout |
| `--retries` | 2 | At most two retries after a failed first attempt |
| `--backoff-seconds` | 5 | Exponential backoff, capped at 60 seconds |
| `--max-rss-mib` | auto | min(24 GiB, 75% guest RAM), summed process-group RSS |
| `--min-free-mib` | 512 | Reserve for evidence writes |
| `--row-rounds` | 60 | Initial inner row-round budget |
| `--max-row-rounds` | 120 | Cap on a nonconvergent inner-row retry |

Summed RSS may double-count shared pages: this is a conservative guard, not a
physical bandwidth measurement. A memory-guard failure reduces workers on the next
retry. Termination targets only a job-owned process group carrying a random token.
Boot ID and process start ticks prevent using stale foreign PIDs. The token can
rediscover an unrecorded child created just before a crash. Live pre-supervisor
children block duplicates, but are never blindly killed.

Execution failures never shrink the mathematical lower bound or become SEARCH_FAILED.
Repeated errors open a resumable BLOCKED circuit. Missing dependencies do not retry
forever. Fix the environment and explicitly resume to reset the circuit. Broken
storage, permissions, power loss, and externally stopped VMs can require intervention.

After all configured useful trials are exhausted, the default is IDLE_EXHAUSTED:
low-frequency status and no repeated identical work. This is **not mathematical
exhaustion**. `--stop-when-exhausted` exits instead. `--max-cycles N` caps completed
cycles over the whole campaign. `--max-hours H` and `--target-width Q` are optional
session limits evaluated at safe boundaries; current proof attempts are not
truncated into claimed successes.

## Evidence and tests

Atomic fsync/rename writes maintain `state.json`, a previous state, and migration
backups. History, reports, findings, raw weights, job specs/receipts, and exact logs
live under `--root`, never only `/tmp`. The runner does not automatically commit
changing research files; ordinary Git commits and pushes remain available.

```bash
uv run --frozen pytest tests/test_run_n12_frontier.py tests/test_frontier_autonomy.py -q
```

The suite combines explicit receipt doubles for controller branches with real
subprocess tests, generator/freezing, snapshot refinement, and a small retained
certificate through the exact two-route gate. No long frontier campaign or new
mathematical result is claimed by these smoke tests.
