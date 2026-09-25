# Strategy-local frontier policy

This is a search-controller change. It does not change certificate conditions,
proof arithmetic, solver tolerances, the verified endpoint, or retained proofs.
A heuristic failure remains evidence about an instrument and its budget, never
an upper bound on s(12).

## Why the policy changed

The supplied campaign log repeatedly verified `windows` near
`3.96196847397814`, while the next global `soft-high` was only a few ULPs higher.
That ceiling belonged to unsuccessful `centre` or `pricing` experiments. The
controller retried those nearby values instead of testing how far `windows`
could go. Comparing only exact float64 keys prevented identical-float repeats,
but still allowed a staircase of different, practically indistinguishable floats.

`frontier_policy` now derives a separate search bracket for each strategy and
search revision from the existing cycle history. The global VERIFIED lower bound
is shared. A strategy's heuristic ceiling comes only from its own UNRESOLVED or
SEARCH_FAILED cycles above that lower bound. Operational ERROR records do not
supply a ceiling. A smaller legacy global search-high produced by another
strategy does not override the configured exploration horizon.

No history is deleted or retroactively relabelled. These brackets are computed
on demand; they do not require a new state schema or a reset of the campaign.
Legacy `soft-high` output remains a historical diagnostic, not the constraint
used to select new geometry. An explicit legacy `--target-width` session stop
still uses that diagnostic; omit it for the continuing campaign.

## Proposals and useful resolution

`--strategy-width` now also controls the minimum useful increment in a new-L
experiment. Its default is `1/100000` (0.00001). There is an additional numerical
floor of 32 ULPs at the current lower bound. Neither threshold is a proof tolerance.
Same-side rationalisation at a genuinely finer scale is exempt and retains
priority; it does not pretend to be progress in L.

A successful strategy with room to explore starts with a probe step of up to
0.0001 (at least the useful resolution, and initially scaled to the configured
interval width). Successive meaningful successes can double the last successful
increment, capped relative to the initial interval. Old microscopic successes
are not counted as grounds to shrink the step back to ULP size.

New targets are exact fractions on the useful-resolution grid. After a failure,
the controller bisects only that strategy's own bracket, keeping a useful gap
from both its proved low and its failed ceiling. Once that interval is exhausted
at the selected resolution, another strategy is used. Exhausting all configured
instruments produces the existing honest idle state, not an impossibility claim.

For the exact low and successful `windows` history in the supplied log, with no
higher `windows` failure, the regression fixture proposes:

```text
previous = 43562304060209/10995116277760
next     = 396207/100000 = 3.96207
strategy = windows
mode     = successful-strategy advance
```

This is a scheduling fixture, **not a newly verified bound**. Actual future
proposals depend on any further results saved by the running campaign.

An already-attempted point within the useful-resolution neighbourhood is not
resubmitted for the same strategy/revision. A new operational error epoch permits
bounded retry after explicit resume. Precision and active recovery are handled
separately from this geometric deduplication.

## Cohorts and wasted continuation

Generation cohorts ask each sibling strategy for its own useful proposal; they
no longer force every strategy to repeat the first strategy's L. A cohort may
therefore contain different sides. `targets=strategy@L,...` in its log makes that
explicit. The shared CPU budget and deterministic per-job result ordering remain
unchanged. Real regression tests compare jobs at two different sides against
separate serial controls.

After a wave has drained and a sibling has passed the existing full gate, further
generation at or below that proved side is retired. Prepared normal/deep/maximum
stages are not launched simply to finish an already superseded search. The
controller emits `[superseded]`, preserves all artifacts, and records an
UNRESOLVED cycle with an explicit `superseded_by` policy disposition. This is not
a fabricated proof or a mathematical refutation. Superseded records do not
supply an instrument ceiling.

A live or unadopted generation wave is never retired by this optimization. The
existing recovery and watchdog paths must adopt it first. Already-active legacy
single cycles and repair jobs keep their recovery precedence.

## Upgrade

Leave the current process alone until a convenient checkpoint. Stop it gracefully
before pulling into its checkout. Do not delete or edit the experiment state.

```bash
cd ~/DEV/squares
git switch work/frontier-autonomy
git pull --ff-only
cd packing
PACK_JOBS=16 uv run --frozen python -m devtools.run_n12_frontier \
  --root ../Experiments/n12-frontier-search --resume --generation-trials 3
```

The proof gate remains the only authority for VERIFIED. A good LP objective or a
large proposed step is neither a certificate nor a prediction of success.
