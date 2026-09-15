---
softschema:
  contract: squares.validation_efficiency:Experiment/v1
  schema: ../experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: VE-005
  title: Parse the branch-cost corpus once per renderer invocation
  registered: "2026-09-14"
  tier: exploratory
  control_label: rollup-corpus-control
  candidate_label: rollup-corpus-candidate
  minimum_samples: 3
  minimum_improvement: 0.15
  maximum_allocation_ratio: 1.25
  target: benchmarks/test_pr_rollup_timing.py
---
# Parse the Branch-Cost Corpus Once

## What Was Measured

The `--check` branch-cost renderer was the last step to finish in seven recent hosted
checks-tier runs. On PR 174’s clean entry revision, the checks tier passed at 192.54
seconds against its 195-second ceiling; the rollup step took 62.76 seconds.
Source inspection found that every branch render reloaded all resource receipts and
sessions, and then reloaded each retained Codex receipt before semantic validation.

VE-005 inherits the campaign’s exploratory rule: alternate three control/candidate
pairs, require every trial to pass, accept only a median reduction of at least 15% with
nonoverlapping ranges and an allocated-work ratio no greater than 1.25, then make a
separate correctness and complexity judgment.
The W5 session froze the additional guard before the candidate was judged: each resource
and session must be parsed once per `--check` invocation, while every branch and the
no-record case still render.

## What Was Tried

The control is clean revision `28b3861c`. The candidate is that revision plus one
invocation-local `RollupCorpus` snapshot in `packing/devtools/render_pr_rollup.py`. The
snapshot retains the parsed resource documents, session declarations, branch-claim
index, and a lazy semantic-validation cache.
Normal one-branch rendering still constructs a fresh snapshot; `--check` shares one
snapshot across all 52 branches and the no-record case.

The maintained opt-in workload is `packing/benchmarks/test_pr_rollup_timing.py`. Each
recorded observation ran it through `benchmarks.validation_timing` with Python 3.14.7,
one pytest worker, one inner worker, one native thread, warm filesystem caches, and a
120-second timeout. The pairs ran in control/candidate order without overlapping heavy
work.

| Pair | Control | Candidate |
| --- | --- | --- |
| 1 | `b0e18d21bf2c4956a76a061d54def2f7` | `380772531daf4c1a9bacafb510fdd01c` |
| 2 | `8cd347b72e0f478091441a1ba124489b` | `9548d7299e50469180f6f37a58027e13` |
| 3 | `3ea1ba12b3314ffa8530235f20062d6f` | `954782ba85ac461e8f046fff6eb454a0` |

## Result

All six observations passed the same one-test workload.
The control median was 47.72 seconds, with a 44.96–50.80-second range.
The candidate median was 2.31 seconds, with a 2.29–3.20-second range.
The ranges do not overlap; the median reduction is 95.2%; and the one-worker allocation
ratio is 0.048, below the 1.25 guard.

The correctness guard passed independently: 28 focused renderer and closeout tests
passed, Ruff and BasedPyright reported zero findings, and a representative cumulative
branch render had the same SHA-256 before and after
(`eb1e00d05664298c66fa4d24a55c6a3e9fb2ec625eb64faa21067ff2c461018f`). The new regression
test fails if `--check` parses more than the two receipt and two session documents in
its fixture.

The candidate is accepted.
The complexity is one small in-memory snapshot, no new dependency, and lazy semantic
validation that preserves the prior error boundary.
That cost is proportionate to removing repeated whole-corpus parsing and restoring tens
of seconds of pull-request headroom.

## What the Prediction Got Wrong

The earlier operational proposal treated late submission as the main problem and
estimated a 12–28-second gain from `start_early`. Queue order was only the reason the
cost became the final tail.
The larger defect was inside the step: its runtime grew with the number of branches
times the entire receipt/session corpus.
Removing that repeated work is both faster and simpler than scheduling the waste sooner.

## Limits

This is an exploratory local warm-cache result, not a confirmatory hosted speedup
estimate. Candidate dirty-diff hashes vary because the append-only receipt journal was
extended between trials; the measured source and benchmark hashes did not change, and
the affected-source audit admits no other candidate implementation change.
The first hosted candidate gate remains the publication checkpoint.
This experiment does not justify raising or recording the 195-second checks ceiling and
makes no scientific claim.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
