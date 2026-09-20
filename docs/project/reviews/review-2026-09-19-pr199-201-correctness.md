# Senior Review of PRs 199–201

Reviewed 2026-09-19. **Original-head verdict: request changes; PRs 199–201 are not
independently ready to merge.** The four retained n=18 certificates pass fresh
mathematical replays.
The lower two PRs nevertheless contain a failing exhaustive assertion, and the stack has
research classification, provenance, and scheduler defects.
Green fast checks do not establish full merge readiness.

| PR | Reviewed head | Base | Layer size | Verdict |
| --- | --- | --- | --- | --- |
| [199](https://github.com/jlevy/squares/pull/199) | `c877006b` | main `fb14f517` | 238 files | Request changes: R1, R2, R8 |
| [200](https://github.com/jlevy/squares/pull/200) | `a85d50ac` | `c877006b` | 58 files | Request changes: inherits R1; introduces R3–R7 |
| [201](https://github.com/jlevy/squares/pull/201) | `2aaa296d` | `a85d50ac` | 135 files | Request changes: fixes R1 at this layer only; repeats R3, R4, R7 and inherits remaining defects |

Scope was each PR’s incremental diff, with three independent mathematical review lanes
and a coordinating engineering/integration review.
The review covered the new mathematical modules, principal command paths, CI changes,
certificate artifacts, tests, survey and hypothesis records, and session handoffs.
Exact replay checks the large certificate payloads computationally.
This was not a new proof of the unchanged verifier implementation or a fresh external
novelty search.

**What the Previous Agent Established**

| Result | PR | Lower bound | Exact total mass | Exact least covered mass | Fresh interval replay |
| --- | --- | --- | --- | --- | --- |
| T-027 | 199 | `s(18) >= 467/100 = 4.67` | `8937839/500000 < 18` | `2000007/2000000 > 1` | Accepted; 2,543,909 boxes, zero stalls |
| T-028 | 200 | `s(18) >= 187/40 = 4.675` | `35758287/2000000 < 18` | `4000013/4000000 > 1` | Accepted; 2,684,845 boxes, zero stalls |
| T-029 | 201 | `s(18) >= 1871/400 = 4.6775` | `17889361/1000000 < 18` | `250001/250000 > 1` | Accepted; 2,997,789 boxes, zero stalls |
| T-030 | 201 | `s(18) >= 4679/1000 = 4.679` | `71573611/4000000 < 18` | `200001/200000 > 1` | Accepted; 3,449,053 boxes, zero stalls |

The exact sweep and interval route agree for each certificate.
The proof bridge is appropriate: nonnegative D4-symmetric atom weights, sufficient
angular coverage, strict containment of a shrunken square inside each unit square, and
coverage of at least one unit of mass force any 18 disjoint unit squares to consume at
least 18 units of mass.
The certificates have less than 18. The claimed bound is the container side L, without
an unsupported division by the shrink factor.
These masses do not certify n=17. Monotonicity to larger n is valid but weaker than
existing results there.

The n=18 verified lower bound moves from 4.59 before this stack to 4.679, an increase of
0.089. The remaining gap to the verified upper bound `(7 + sqrt(7))/2 = 4.8228756555...`
is approximately 0.143876. The n=11 interval remains
`3.826447410572939... <= s(11) <= 3.877083590022814...`. No n=11 improvement or
resolution of the packing problem resulted from these sessions.

Session 139 retained T-027 and delivered mathematical tooling, but Route S encoding
timed out unresolved after about three hours; search did not run.
Session 140 retained T-028 during its lower-bound survey.
Session 141 retained T-029 and T-030 and recorded 15 other probes without retention.
H-219 and H-221 are confirmed; H-218 is abandoned without confirmation, and H-220 is
unresolved. Resource usage beyond session clocks and retained probe timings remains
explicitly unmeasured.
The 180-second CI wall target remains advisory under `think-g4n9`.

**Findings in Merge Order**

**R1 — Blocker — PR 199’s exhaustive n=18 assertion is wrong; PR 200 inherits it.**
[test_fractional_interval.py:405](https://github.com/jlevy/squares/blob/c877006b67d876b8fd6531e738b2318446aba90f/packing/tests/test_fractional_interval.py#L405)
expects 361 directions.
Both lower-layer certificates declare 181 steps, giving 182 half-tangents and 363
doubled directions. The proof replay succeeds; this assertion then fails.
PR 201 corrects it in `dd2b4d7a`, so checking only the top branch conceals the
lower-layer regression.
Related evidence descriptions repeat the incorrect counts.
**Fix:** Move the correction to PR 199, restack 200 and 201, correct the evidence
counts, and obtain passing full checkpoints at each new head/base pair.
Tracker: `think-7061`.

**R2 — High — PR 199 still converts a solver error into scientific infeasibility.**
[produce_threshold_certificate.py:209–212](https://github.com/jlevy/squares/blob/c877006b67d876b8fd6531e738b2318446aba90f/packing/devtools/produce_threshold_certificate.py#L209)
handles HiGHS status 1 as unresolved, but maps status 4 and other unsuccessful outcomes
to `infeasible`. A mocked status 4 on a feasible one-row matrix reproduces this.
The next resolution step emits a refused receipt saying the covering LP is infeasible.
The previous review fixed the analogous piercing path but only the timeout case here.
**Fix:** Only status 2 may report solver infeasibility; preserve status/message and keep
solver or numerical failures unresolved.
Audit the initial point-LP path too.
Tracker: `think-qpcq`.

**R8 — Medium — PR 199 accepts piercing angles outside its geometry’s domain.**
[integral_piercing.py:528–530](https://github.com/jlevy/squares/blob/c877006b67d876b8fd6531e738b2318446aba90f/packing/src/sqpack/fractional/integral_piercing.py#L528)
checks only that the half-angle limit is positive.
Values above 1 introduce negative cosines into a centre-domain calculation that assumes
nonnegative sine and cosine.
For the single site `(1,1)` in a side-2 container, unit squares, two steps, and limit 2,
the encoder returns `[[0]]` and reports `infeasible / killed_coarse_net`. With limit 1/2
it returns `[[1]]` and feasible.
The centre pierces every contained closed unit square: for folded direction components
c,s, its maximum projected offset is `(c+s)*(1-(c+s)/2) <= 1/2`. **Fix:** Refuse limits
above 1 before first-quadrant geometry, or generalize the geometry using absolute
projections. Add this regression control.
Defaults and retained certificates are unaffected.
Tracker: `think-sole`.

**R3 — High — PRs 200–201 treat unfinished searches as site-set refutations.**
[H-218:25–28](https://github.com/jlevy/squares/blob/a85d50ac741b4d001184ef58b7ec4068b7ae1e95/packing/campaign/hypotheses/H-218-existing-colgen-raises-a-small-n-floor.md#L25)
calls unconverged loops and stalled interval checks site-set refutations.
The mistake recurs in H-219, H-220, H-221, the leftover ranking, and
[X-039:59–61](https://github.com/jlevy/squares/blob/2aaa296de815e5048b013ea268cc72d0c273b7ac/packing/campaign/explorations/X-039-n100-re-rank-after-session-140.md#L59).
The n=20 values 19.910044 and 19.939212 are below 20. Adding constraints can raise their
optima and still converge below 20; monotonicity does not show they “cannot retain.”
An interval stall likewise establishes no counterexample.
These statements incorrectly eliminate possible continuations from the research queue.
**Fix:** Classify them as unresolved.
Retain budget-based deferrals as scheduling decisions, and reserve mathematical
refutation for an established obstruction.
Tracker: `think-ujkz`.

**R4 — Medium — PRs 200–201 label float-only experiments as exactly verified.**
[exp-162:23–24](https://github.com/jlevy/squares/blob/a85d50ac741b4d001184ef58b7ec4068b7ae1e95/packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-162-h218-stock-colgen-small-n-floors.md#L23)
and exp-164–170 / exp-172–178 declare `verified / exact-algebraic` even though these
rounds produced float64 HiGHS measurements and no accepted certificate.
Experiment/v2 defines assurance as what the round establishes, not what its planned
pipeline could eventually establish.
Off-sweep successful certificates do not verify those measurements.
**Fix:** Use `numerically-checked / numerical-f64`, actual precision and tolerances, and
explicit scope. Preserve exact assurance for successful certificate decisions.
Tracker: `think-1436`.

**R5 — Medium — PR 200’s covering scheduler permits simultaneous writers.**
[run_covering_queue.py:218–232](https://github.com/jlevy/squares/blob/a85d50ac741b4d001184ef58b7ec4068b7ae1e95/packing/devtools/run_covering_queue.py#L218)
checks for a completed run JSON but reserves neither the queue nor the output prefix.
Two concurrent walkers both start the same absent probe and write to identical result
paths. A barrier-backed runner reproduced two simultaneous starts and two successful
returns. This contradicts the tool’s stated refusal of a second generator and can mix
logs, overwrite results, and oversubscribe the one-core research budget.
**Fix:** Hold an atomic execution lease through the run and refuse conflicting writers;
exercise the simultaneous-start case in a test.
Tracker: `think-ox9l`.

**R6 — Medium — PR 200 drops T-027’s structured producer provenance.**
[results.yaml:1572–1573](https://github.com/jlevy/squares/blob/a85d50ac741b4d001184ef58b7ec4068b7ae1e95/packing/frontier/results.yaml#L1572)
indents `produced_by` into a folded composition string.
Parsing gives no producer mapping, while the prose contains
`produced_by: session: session-139`. The field is optional, so schema validation misses
the loss. **Fix:** Restore the mapping’s indentation and check its parsed value.
Tracker: `think-cat2`.

**R7 — Medium — The n≤100 survey omits three proved cases.**
[X-038:47–50](https://github.com/jlevy/squares/blob/a85d50ac741b4d001184ef58b7ec4068b7ae1e95/packing/campaign/explorations/X-038-n100-lower-bound-survey.md#L47)
reports 32 proved / 68 open; Session 140 and PR 201’s X-039 repeat it.
The same revision’s n=98,99,100 records are already proved with matching bounds of 10.
The correct census is 35 proved / 65 open, and the last open block is 82–97. **Fix:**
Reconcile the surveys and sessions with the frontier and derive this census through the
frontier tooling. Tracker: `think-fixz`.

**Nonblocking Follow-ups and Design Assessment**

The separation between heuristic production and exact acceptance is appropriate, as are
immutable named copies of earlier certificate rungs.
No replacement proof architecture is warranted.
CI’s concurrent installation and print-layout jobs retain both child exit statuses; the
scheduling hint changes order without removing checks.
The chief maintenance problem is manually copied research metadata drifting away from
artifacts. Prefer narrow corrections to the shared record/rendering path over another
parallel source of truth.

- `threshold_separation.atom_columns` accepts general threshold atoms but ignores
  multiplicities in costs and coverage.
  For two sites with multiplicities `(3,3)` and threshold 2, it returns cost 1 instead
  of 3 and misses a charge from one contained site.
  Current callers generate ordinary 2-of-3 atoms, so current outputs are unaffected.
  Guard that restricted input contract or implement token counting before widening use.
- T-029’s receipt still names live `certificate.json`, now T-030. Pin it to
  `certificate-1871-400.json`. The registry itself already uses the named artifact.
- The queue’s interpreter test rejects an executable named `python3` even when it is the
  explicitly permitted project Python 3.14. Test interpreter identity/version, rather
  than this basename assumption.

The n=29 frozen candidate deserves a separate disposition.
A fresh exact-only replay accepts all five conditions at side `137/25 = 5.48`, mass
`52081879/2000000 < 27`, and minimum `4000013/4000000`. If the independent interval
route can also complete, the certificate would improve the current verified floors for
n=27,28,29. The retained interval attempt stalled in 272 directions.
**It remains unpromoted under the two-route retention policy.** This is a possible
follow-up, not a replacement for the owner’s selected next entry `think-qqzs`.

**Validation and Remaining Limits**

- Coordinating engineering checks: 186 passed in 60.57 seconds.
- New mathematical-module checks: 62 passed in 16.79 seconds.
- PR 201 focused fractional checks: 80 passed, 19 deselected; full new-certificate
  decisions were run separately.
- A positive floor-only relational certificate passed both routes.
  A larger optional floor stress replay was interrupted and is not counted as passing
  evidence.
- Initial local failures came from an incomplete submodule checkout, a missing workbench
  import path, denied process inspection, and the executable-basename test.
  The complete 186-test rerun passed after correcting the local setup.
- The initial review snapshot made no application-source or lower-branch edits.

At dispatch, all three PRs were conflict-free and their fast validation and page
aggregators were green.
Their existing deferred workflows had skipped all substantive jobs.
Full checkpoints were launched for the actual PR merge refs:

| PR | Merge revision at review | Deferred checkpoint |
| --- | --- | --- |
| 199 | `e6222161288bda44adb31866fda70ce9c760995e` | [35476505136](https://github.com/jlevy/squares/actions/runs/35476505136) |
| 200 | `41947f0ba06b9284f6bd9d99194e9e3bc56e16bd` | [35476506427](https://github.com/jlevy/squares/actions/runs/35476506427) |
| 201 | `b9cc9ce737d3e26681eb77d0c3feb71764d78c54` | [35476507563](https://github.com/jlevy/squares/actions/runs/35476507563) |

All three checkpoints completed with failures.
PR 199 failed only the incorrect 363-versus-361 exhaustive assertion; its slow lane and
deferred steps passed.
PR 200 failed that assertion and both atlas rebuild surfaces.
PR 201 passed the exhaustive mathematical lane, but failed the slow atlas test and the
deferred atlas rebuild.
Its remaining deferred checks passed, including 167 negative controls, finer-net and
threshold records, and the n=40 rigidity check.
Later fixes or base changes require fresh evidence for the affected checks.

The initial recommendation was to repair each owning layer and restack.
The user subsequently requested a new correction PR above 201 instead.
That instruction governs implementation: the old heads remain unchanged, and checks on
the corrected tip do not retroactively validate the two lower heads.
Review tracking is `think-x2n7`, with the initial eight findings tracked individually
above. The selected research continuation and the existing open beads `think-qqzs`,
`think-g3j7`, `think-gyzw`, `think-jwb1`, and `think-g4n9` remain open.

## Correction Pass

The dispatched checkpoints found an additional finding, **R9 / think-63r2**:
`test_known_best_composite_contains_every_case_and_square` failed because both retained
composite SVGs still display `s(18) >= 4.67`, while the current case and figure data
declare `4.679`. PR 201’s slow lane completed 145 other tests successfully.
PR 200 failed the same test with expected label `4.675` and retained label `4.67`. This
was generated-artifact drift, not an infrastructure or time-budget failure.
The correction regenerates the owned SVG/PNG/PDF export families and adds a cheap
claim-label consistency check to the existing fast atlas surface.

[Session 142](../../../packing/campaign/agent-sessions/session-142-stack-correctness.md)
records the W2 correctness review and a bounded W7 pipeline-improvement phase under
`think-gz4k`. The new branch is `codex/stack-review-corrections`, based on PR 201. The
implementation addresses R2–R9, the repeated R1 evidence counts, and all three smaller
findings. It adds computational boundary and queue-ownership regression tests without
changing retained certificate payloads or the scientific acceptance criteria.
[PR 202](https://github.com/jlevy/squares/pull/202) publishes this correction layer.
The following dispositions apply to the corrected tip, not the unchanged lower heads:

| Finding | Correction-layer disposition |
| --- | --- |
| R1 | The top already contains the corrected exhaustive assertion; repeated evidence counts are reconciled. Lower PRs 199–200 still fail their original assertions. |
| R2 | Solver status and diagnostics are preserved; malformed vectors remain unresolved. Raw marginal shape and finiteness are checked before sign clipping. |
| R3–R4 | Unfinished computations remain unresolved, and sixteen numerical subjects carry numerical assurance. |
| R5 | Kernel-held leases prevent overlapping queue writers and survive walker death while the generator is alive. |
| R6–R7 | T-027 provenance and the 35-proved/65-open census are corrected. |
| R8 | Unsupported half-angle limits are rejected before first-quadrant geometry. |
| R9 | Eight atlas exports are regenerated; fast checks now reject stale visible bound labels. |
| Smaller findings | Weighted column inputs are refused, the T-029 receipt pins its own certificate, and the queue test uses the project interpreter. |

At baseline `4c202aeb`, hosted fast validation
[35479932912](https://github.com/jlevy/squares/actions/runs/35479932912) and the page
build [35479932911](https://github.com/jlevy/squares/actions/runs/35479932911) passed.
The hosted merge revision `564d5dbc437bc0aa9801d210d2ae4de91bf101c3` has the same Git
tree as that head. These checks do not certify the subsequent final-review edits.
The first deferred dispatch was cancelled for those edits; final-head validation remains
pending.

The first integrated fast checkpoint at `d1c54a6a` passed every behavioral assertion,
but failed the Ruff formatting check and a per-test duration ceiling.
The allowlist existence test spent 12.38 seconds generating a full reference report
despite using only declared constant names.
It now reads the declarations directly; reference matching remains covered by the
existing positive and negative controls.
No timeout ceiling or slow-test exemption was changed.

The pre-push non-test floor passed at `4c202aeb`. Its serial selection of 72 of 350 test
files hit the 900-second command timeout without a reported assertion failure.
A ten-worker retry completed in 814.31 seconds with 1,858 passes and one failure: a
timeout fixture assumed a Python child would print within 200 milliseconds under load.
The fixture now injects a timeout after writing to the real artifact stream; separate
real-subprocess controls still cover output transfer and process-tree termination.
All 125 validation CLI tests pass.
Worker allocation for costly partial selections is tracked separately under
`think-1i1x`; no global ceiling is relaxed by this correction.

The final adversarial mathematical review found one additional malformed-solver case:
clipping a positive infinite marginal turned it into zero before the finiteness check.
The new positive-infinity regression failed on the old code; both infinity signs are now
checked before clipping.
All four boundary/queue suites pass together with 52 tests.
The review found no further flaw in the retained proof arguments.
The n=29 receipt now states 181 steps and 182 directions and distinguishes its
historical decision from the later exact replay and possible future
interval-verification budget.

The integration pass also corrected exp-171’s numerical restricted-optimum subject and
its verification follow-up.
Its rational freeze passes the exact route, but that does not make the floating LP
optimum exact or resolve the stalled interval route.
Sixteen numerical subjects are corrected in total; accepted certificate results retain
their existing assurance.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
