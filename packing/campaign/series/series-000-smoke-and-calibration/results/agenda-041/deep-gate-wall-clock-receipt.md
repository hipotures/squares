# Deep-Gate Wall Clock Receipt (W5 efficiency block, `think-zmos`)

Status: **the 1.38x was not drift, and the instrument that would have said so now
exists.** `think-zmos` measured the deep gate’s `exhaustive-tier` job at 2674 s against
the 1943.05 s `deep-gate.yml` prices it at, and recorded that no rule read either
number. Both halves are now settled.
The gate’s four hosted jobs and its whole wall carry entries in `ci_gates` in
[`gate-budgets.yaml`](../../../../../devtools/gate-budgets.yaml), judged by the same
four rules the local tiers are judged by, and `devtools.check_ci_gate_walls` compares a
finished run against them.
**The 1.38x itself is the hosted runner pool, not a regression**: the same 58 tests run
1.43x slower on the slower class of `ubuntu-latest`, measured test by test from two
runs’ JUnit records, and 1943.05 s is what the job costs on the faster class.

Session W5 lane, branch `claude/happy-johnson-i2ridl`, 2026-09-22. Every figure below is
this session’s own measurement from the GitHub Actions API and the retained
`validation-timings-*` artifacts; nothing is carried over from the bead unverified.

## Commands

From `packing/`, project Python 3.14.7:

```bash
uv run --frozen --all-extras --group dev python -m devtools.check_ci_gate_walls \
  --gate deep-gate --run-id 35579234418

uv run --frozen --all-extras --group dev python -m devtools.check_ci_gate_walls \
  --gate deep-gate --sample \
  --run-id 35632055808 --run-id 35627075872 --run-id 35579234418 --run-id 35480905141 \
  --run-id 35213757305 --run-id 35078581840 --run-id 35012089923 --run-id 34997041426
```

`--sample` prints the register block to paste; that is where every `measured_seconds`,
`spread` and reading list in `ci_gates` came from.
The tool needs a token with `actions: read` and takes about four seconds per run.

## What one deep-gate run costs

Run 35579234418, the run `think-zmos` measured, read back by the tool:

| Job | Wall | Queue | Setup | Work |
| --- | --- | --- | --- | --- |
| `exhaustive-tier` | 2674 s | 67 s | 23 s | 2648 s |
| `deferred-steps` | 2469 s | 74 s | 24 s | 2439 s |
| `deferred-slow-lane` | 999 s | 8 s | 23 s | 974 s |
| `screen` | 909 s | 12 s | 23 s | 884 s |
| `deep-gate-required` | 4 s | 2 s | 0 s | 1 s |
| **the gate’s wall** | **2762 s** |  |  |  |

The gate’s wall is the run starting to its last gating job completing, so it carries the
queue; the aggregate is excluded from that endpoint deliberately, so that adding a step
to the aggregate cannot move the recorded wall.
One invocation is 7,055 s of job wall — about 118 billed runner-minutes — for 2,762 s of
reviewer wait.

## The 731 s gap, and it is not what the bead assumed

`exhaustive-tier` costs 2674 s of wall for 1943.05 s of declared step time.
The decomposition is a measurement:

| Component | Seconds | Share |
| --- | --- | --- |
| Job start before step 1 | 1 | 0.04% |
| `Set up job`, checkout, `uv`, `uv sync` | 22 | 0.8% |
| `Run the exhaustive exact tier` | 2648 | 99.0% |
| Artifact upload, `Post` steps, job finalise | 3 | 0.1% |

**Setup is 22 s of 2674 s, so it explains none of the gap.** The gap is the gate step,
which cost 2648 s where 1943.05 s was declared.

It is not a step that grew either, and that is where the bead’s third hypothesis turns
out to be wrong. Run 35480905141’s `exhaustive-tier` cost 1879 s of wall and 1853 s of
step. Its JUnit record and run 35579234418’s carry **the same 58 tests, none added and
none removed, compared by name**, and every single one is slower on the second run:

|  | Test time | Tests |
| --- | --- | --- |
| Run 35480905141 | 1836.1 s | 58 |
| Run 35579234418 | 2621.4 s | 58 |
| Ratio | **1.428x** | — |

Per test the ratio runs 1.15x to 1.60x; the largest test, `test_retained_threshold_
claims_pass_the_standalone_full_sweep[t026]`, is 598.4 s against 843.2 s.
`deferred-steps` tells the same story over its eight steps between runs 35012089923 and
35579234418 — the same eight names, 1543.5 s against 2435.7 s, **1.578x**, each step
between 1.487x and 1.759x.

The same-tree control closes it from the other side.
Runs 35632055808 and 35627075872 are the **identical commit `030d109a`** and read 2608 s
and 2771 s, 1.06x apart, so within one runner class this job is stable to about six per
cent.

So `ubuntu-latest` is at least two classes of machine here, and a CPU-bound 45-minute
job sees the whole difference.
The `exhaustive` job on `main` is bimodal over nine successful runs between 2026-09-13
and 2026-09-21 — 1933, 1957, 2295, 2538, 2624, 2629, 2635, 2670, 2712 s — and the two
low readings average 1944.9 s against the declared 1943.05 s. **1943.05 s was one
reading of a two-class pool written down as the job’s cost**, and the 1.38x is the
distance between the classes.

That is a correction to `OR-17`’s own framing, which reads the 1.38x as drift the CI
jobs were not clocked for.
The clocking was still missing and is the right remedy; what it would have reported on
2026-09-21 is a job inside its band on a slow runner, not a regression.

## Does `deferred-steps` re-run what `exhaustive-tier` decided?

**No step is run twice**, and that is enforced rather than inspected:
`test_the_deep_gate_runs_exactly_what_the_pull_request_surface_defers` resolves each
job’s command through the CLI’s own selector and asserts the four selections are
pairwise disjoint and that their union is every step no pull-request job runs.

**One piece of mathematics is derived twice, deliberately.** Both jobs re-derive T-026’s
threshold certificate by an exact event-cell sweep, through two different
implementations:

| Job | Work | Run 35579234418 |
| --- | --- | --- |
| `deferred-steps` | `dilation_corollary --check-limit-record`, 720 and 1440 steps | 346.5 s + 695.8 s = 1042.3 s |
| `exhaustive-tier` | the claim documents’ embedded standard-library reader, `[t025]` and `[t026]` | 102.6 s + 843.2 s = 945.8 s |

1,988.1 s together: **28.2 per cent of the gate’s job wall**, 38.7 per cent of the two
large jobs.
`_threshold_limit_record`’s own docstring already decides this and decides it
the right way — the embedded reader’s sweeps “supplement rather than replace these
repository replays” — which is `OR-13`’s “expensive re-derivation may still supply
independent evidence that no comparison can replace”.
Two implementations agreeing is the evidence; one implementation run twice would not be.

**Removing either side buys almost nothing, which is the finding that matters.** The
gate’s wall is `exhaustive-tier`:

- drop the two threshold tests from `exhaustive-tier`: 2674 s → about 1728 s, and the
  wall becomes `deferred-steps` at 2469 s. **205 s saved, 7.7 per cent.**
- drop the two dilation-limit records from `deferred-steps`: 2469 s → about 1427 s, and
  the wall is unchanged at 2674 s. **Nothing saved.**

The two large jobs are within 8 per cent of each other, so the gate is already
wall-balanced and deduplication is not the lever.

## What would actually shorten it

Splitting, and unlike the case `OR-14` warns about, splitting works here.
`BC-218` priced a second job at zero wall because the tier was *one step* with the rest
hidden under it. These two jobs are not one step: `exhaustive-tier` is 58 tests and
`deferred-steps` is 8 named steps, both with a measured distribution.

- `exhaustive-tier`’s floor is its largest single test, `[t026]` at 843.2 s. Its top
  five tests are 1,539.1 s of 2,621.4 s (59 per cent).
  A three-way split by test reaches about 880–900 s.
- `deferred-steps`’s floor is the 1440-step threshold record at 695.8 s. A four-way
  split reaches about 700 s.
- The other two jobs are already 999 s and 909 s and would then set the wall.

**Both must be split or neither is worth splitting**, since whichever is left carries
the wall. Split together the gate lands near 1,000–1,100 s — about 17 minutes against 46
— at roughly the same billed runner time, since the work is divided rather than
repeated. That is a candidate with an arithmetic behind it, not a plan; it is
`think-haam`’s to take or refuse.

## What was changed

| File | Change |
| --- | --- |
| `packing/src/sqpack/gate_budgets.py` | `band_findings` extracted from `judge`, so the four rules have one implementation; `CiGate`, `CiJobBudget`, `CiReference`, their loader, `ci_declaration_problems` and `judge_ci_job` added on top of it |
| `packing/devtools/gate-budgets.yaml` | the `ci_gates` section: one entry per deep-gate job plus the gate’s wall, each with its ceiling, its record, its spread, its readings and its argument |
| `packing/devtools/check_ci_gate_walls.py` | new: reads a run from the Actions API and judges it against those entries, with `--sample` to record a baseline |
| `packing/tests/test_deep_gate_workflow.py` | two contract tests: every job the gate runs has an entry and every entry holds the tiers’ own rule; the aggregate reads the register it is budgeted against |
| `.github/workflows/deep-gate.yml` | the aggregate reports every wall on each invocation; the comments that read 1943.05 s as the job’s cost now say what it is |

### The band, and why it is that number

`drift_ratio: 1.25` per gate, in place of the policy’s 1.5x, and
`enforcement: reporting` rather than enforcing.

The record is the geometric mean over the runner mix rather than one reading, so the
largest reading any job has shown against its own record is 1.12x (`deferred-steps`) and
the smallest is 0.75x (`exhaustive-tier` on the fast class, against a 0.6x stale floor).
1.25x clears the observed maximum with 12 per cent of margin and sits below the 1.5x
that fails a local tier.

The cost of that is stated rather than hidden: **a single hosted reading cannot separate
a 1.5x regression from a slow draw.** A real 1.5x regression reads 1.5x on a typical
runner and fails, and reads 1.125x on a fast one and is missed.
That is the limit of a one-run rule; the instrument that removes it is a recorded median
over samples, which `pull_request_walls` already has and `think-haam` owns for these.

Reporting rather than enforcing for the reason both pull-request walls went advisory on
2026-09-17: a false red on a 45-minute pre-merge gate costs another 45 minutes to clear,
and a gate people cannot afford to re-run is a gate that stops reporting (`OR-14`).
Every step the aggregate gained is additionally `continue-on-error`, its checkout and
its toolchain included, which is a second and different relaxation: the bands are
reported, and nothing in the measurement path can redden the gate.
The verdict is still decided entirely by the prerequisite script, and a contract test
holds that no step after it may decide anything.
Both relaxations name `think-haam`.

The step costs about 21 s of checkout, `uv` and `uv sync` on a warm cache, 0.8 per cent
of a 42-minute gate, and it does not move the recorded wall.

### The number this deliberately does not make red

2,540.6 s of gate wall is 42 minutes on the merge path, which `OR-17` says is
unacceptable whatever a band says.
`OR-14` is explicit that a ceiling goes around the measurement and the target goes in
the agenda, so the ceiling is 3,430 s — 1.35x of the record, a blow-up detector — and
the 42 minutes is a candidate for `think-haam`, not a red check.

## Validation

`uv run --frozen --all-extras --group dev packing-validate --edit` from `packing/`:
**exit 0**, 358 s of wall, 50 of 82 steps selected and passed, on the settled tree.

That wall is itself worth recording, because it is 1.49x the `edit` tier’s 240 s ceiling
and the gate says so rather than failing: this box was sharing four CPUs with three
concurrent research runs, and the run’s shape (4 cpus, `--jobs 4`) is not the tier’s
declared reference (2 cpus, `--jobs 2`), so the band was reported and not enforced.
The gate’s own attribution names `type floor (basedpyright)` at 356.7 s and
`browser floor` at 267.8 s, which are the two that soak up a contended box.
It is the same rule this session extended to the CI jobs, doing on a local tier exactly
what it is now able to do on a hosted one.

Also run, all clean: `devtools.check_gate_budgets` (12 tiers, every declaration
passing), `devtools.check_documentation` (0 problems),
`pytest tests/test_deep_gate_workflow.py` (11 passed),
`pytest tests/test_gate_budgets.py tests/test_validation_cli.py` (168 passed), and
`ruff`, `ruff format` and `basedpyright` at zero findings over the three changed Python
files.

## On the merge-path question

A recommendation, not an implementation, as asked.

**Keep it pre-merge.** The gate exists because `6bd136b0` merged green and left `main`
red across three merges for five hours, and `OR-13` says the full checkpoint is obtained
before final pre-merge review.
Moving it after the merge restores exactly the gap it was built to close, and the daily
backstop is not a substitute — its own comment concedes it reports “up to 24 hours
late”.

**Make it once per tree, not once per pull-request event.** The waste `think-zmos` found
is not the gate’s content, it is that PR 208 paid for it twice, once on a head that was
then force-restored, and that runs 35632055808 and 35627075872 both ran 45 minutes on
the byte-identical commit `030d109a` — the second of which is visible in this session’s
own baseline as two readings of one tree.
`OR-17`’s fourth obligation already states the rule and nothing implements it.
A tree-keyed skip that reports the earlier verdict is the cheapest large win available
and is independent of everything else here.

**Do not move it to once per stack tip unless the stack merges as a unit.** If the stack
merges as one commit the tip’s coverage is sound.
If the pull requests merge individually — which is what happened on 2026-09-21, six
merges in an hour — every pull request below the tip would merge with no deep coverage,
which is `6bd136b0` again with more chances to occur.

**And make the label say what it is for.** `OR-17` requires selection to be per
invocation and recorded; a label is recorded but it does not state the evidence wanted,
so a 45-minute gate still looks like a checkbox.
That is a small change to the workflow and to the session record, and it is the
obligation `think-haam` carries that this session did not discharge.

## What this session did not establish

- **Nothing was run on the deep surface.** The gate was not invoked; every figure comes
  from finished runs already in the API. The CI step added to `deep-gate-required` has
  therefore never executed, which is why it is `continue-on-error`.
- **The two runner classes are inferred from timing, not identified.** The jobs API
  reports the label, not the machine, so “two classes” is the shape of nine bimodal
  readings plus two uniform test-by-test ratios.
  It is not a claim about GitHub’s fleet.
- **The record is eight readings, not a median over fifteen.** `pull_request_walls`
  requires fifteen comparable samples before it judges a relative regression; these
  bands judge on one run against a mean of eight, and that is the weaker instrument.
- **The split arithmetic is arithmetic.** No shard was built or measured; the floors are
  the largest single test and the largest single step, which is a lower bound on what a
  split can reach, not a measurement of one.
- **`packing-validate --budgets` still prints only the tiers.** The CI entries are read
  by `check_ci_gate_walls` and by the contract test, not by that view, and
  `sqpack/cli/validate.py` was outside this lane’s file set.
  One rendering call would close it.
- **`think-haam` is not discharged.** This session built the third of its four
  obligations, the clocking.
  The wall ceiling as a policy rather than a band, the per-invocation selection record,
  and the never-re-decide-a-tree rule are untouched.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
