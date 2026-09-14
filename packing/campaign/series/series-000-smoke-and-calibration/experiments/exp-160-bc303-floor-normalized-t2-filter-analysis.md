---
title: exp-160 — prospective H-162 analysis of retained BC303 T2 minima
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-160
  series: series-000
  title: Prospective receipt-only analysis of floor-normalized BC303 T2 filters
  date: '2026-09-13'
  hypotheses: [H-162]
  tier: exploratory
  subject:
    label: Frozen BC293 377-atom measure on all 182 eligible BC303 C and S first-owner charts
    engine: Retained exact C and S first-owner minima from the single exp-158 reader invocation
    assurance: verified
    method: exact-algebraic
    host_system: Darwin arm64; project Python 3.14; no additional scientific target invocation
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      Before comparison, bind the analyzer to its clean committed execution head
      and require exp-158's admitted source and executing-revision
      binders, all 377 atom rows and six frozen source files at revision
      39714308ce2081abbd76624387d134fee4be6deb, raw measure SHA-256
      c30b600d3d35f3851f0595e2c42962bf353721f9e72b0539bd691aec522e876f,
      both axis aliases, all 182 first-owner charts, independent adversarial
      controls, complete per-chart coverage, and exact closed-membership, label,
      source-cell, and rational physical-parent replay of any attaining minimum.
      Refuse changed source, missing manifest entries, failed controls, incomplete
      runs, or replay failures.
    candidate: >-
      Read only the admitted retained integer C and S first-owner strip minima
      from exp-158's one target receipt. Compare each to 4524132, in the frozen
      verdict order. Do not use exp-158's H-160 threshold outcomes as H-162 results
      and do not invoke the charge reader again.
    runs_per_condition: 1
    interleaved: false
    operator: Codex BC303 H-162 retained-receipt analyst
    entry_point: packing/devtools/analyze_bc303_h162_receipt.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.analyze_bc303_h162_receipt
      --expect-analysis-revision "$(git rev-parse HEAD)"
      --input campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-158-bc303-t2-charge-filters.json
      --output campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-160-bc303-floor-normalized-t2-filter-analysis.json
    budget: One admitted retained exp-158 receipt and one comparison; zero new target invocations or retries
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-160-bc303-floor-normalized-t2-filter-analysis.json
  effort:
    timebox: One receipt comparison, unspent
    wall_seconds: 0
    stopped_by: dependency
  results:
  - shape: determination
    role: guard
    question: Did an admitted exp-158 receipt exist when the strategy reset paused this route?
    outcome: criterion_missed
    checked_by: >-
      No exp-158 target receipt exists, so the receipt-only analyzer had no scientific
      input and was not invoked before the owner paused BC303 target work.
  verdict:
    decision: blocked
    primary_criterion: >-
      Accept H-162 iff complete admitted C and S first-owner strip minima are both
      at least 4524132 integer units; apply source/control refusal before either
      mathematical branch and replay a low C before any helper rejection.
    reason: >-
      The September 14 strategy reset paused this route with no exp-158 target receipt;
      no H-162 comparison or scientific verdict exists.
---
# Exp-160: Frozen Receipt Analysis Before Target Charge

This is the analysis record for
[H-162](../../../hypotheses/H-162-bc303-floor-normalized-t2-filter.md).
Its [receipt analyzer](../../../../devtools/analyze_bc303_h162_receipt.py) reads JSON
and allocates no charge sweep.
The sole future input is the retained
[exp-158 target receipt](exp-158-bc303-t2-charge-filters.md) after that experiment’s
source, revision, controls, complete coverage, and attaining-cell replay are admitted.
The reader’s own C and S minima are inputs; its H-160 decisions use different frozen
thresholds and cannot be copied as this outcome.
The analyzer’s output is explicitly conditional until exp-158’s separate admission is
checked. It checks 182 distinct receipt rows, but only exp-158’s source-bound admission
confirms that they are the exact eligible chart manifest.
The analyzer checks and records its own clean execution revision separately from the
exp-158 reader’s execution revision retained in the input.

The registration compares C and S first-owner strip minima separately with `4524132`.
First, any source mismatch, incomplete sweep, failed control, or refused replay leaves
the instrument unresolved with no scientific verdict.
A replayed C minimum at most `4524131` rejects H-162 and the normalized local helper
regardless of S. If C passes and S first-owner strip reaches `4524132`, H-162 is
accepted and the strip floor proves the helper under
[X-031](../../../explorations/X-031-bc303-floor-normalized-t2-helper-draft.md).
If C passes and an admitted S strip minimum is at most `4524131`, H-162 is rejected
while actual S and the helper remain unresolved.

The complete actual-S condition instead uses a `8524147` total-pair cutoff and every
compatible admitted second-owner chart, not only the 182 first-owner charts.
It is outside this analysis.
A later joint-S registration can determine the helper after a low strip, but cannot
change the H-162 filter verdict or authorize a second exp-158 target invocation.
The
[mathematical audit](../../../../../docs/project/reviews/review-2026-09-13-bc303-h162-preregistration-math.md)
checks that distinction.

This record contains no target charge, result, or readiness transition.
H-160 and exp-158 keep their original thresholds, budget, and separate verdict.
If this registration is completed after any target receipt is read, that comparison must
be labeled retrospective rather than prospective.

The September 14 strategy reset paused the registration before the input receipt
existed. Its prospective contract and controls remain useful, but the blocked status is
an owner disposition and says nothing about whether H-162 is true.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
