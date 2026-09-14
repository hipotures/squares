---
title: exp-209 — a compaction pass over repaired runs, run inline and not kept
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-209
  series: series-000
  title: A compaction pass over repaired runs, run inline and not kept
  date: '2026-09-12'
  hypotheses:
  - H-211
  tier: exploratory
  subject:
    label: the resolved arrangements, tested for local compactness
    engine: workbench page, branch claude/annealing-search-benchmark
    engine_commit: f91fc7d4
    assurance: numerically-checked
    method: numerical-f64
    tolerance: a move is accepted only if it creates no overlap deeper than 1e-9
    host_system: macOS on Apple silicon, one headless Chromium
    selftest_passed: true
    precision: unrecorded-historical
    migration_annotation: '2026-09-13: source reference mapped from pre-purge 6ed8bd56 to reachable
      f91fc7d4; the retained harness and workbench source trees compare equal in Git. Original
      run provenance was not recaptured.'
  instance:
    axis: n
    point: 11
    role: target
  method:
    operator: claude-opus-5, unattended
    control: the same arrangement scattered outward by 0.15 of a side, then compacted
    candidate: the resolved arrangement, compacted
    trials: 3320
    interleaved: true
    commit: f91fc7d4
    entry_point: packing/devtools/bench_annealing.py
    command: a compaction pass over the resolver's output, with a scatter control
    record: run inline; the pass is not retained in the harness
  results:
  - shape: conditions
    metric: closed at the best of 800, resolved against resolved-then-compacted, n = 5
    control_median: 0.958
    candidate_median: 0.958
    control_range:
    - 0.958
    - 0.958
    candidate_range:
    - 0.958
    - 0.958
    change_pct: 0.0
    overlapping: true
  - shape: determination
    question: does walking every square toward the box centre, as far as it will go without
      overlapping, shrink the container the resolved arrangement needs
    role: guard
    outcome: no_progress
  complexity:
    lines_changed: 0
    notes: The compaction pass was run inline; its code and outputs were not kept.
  verdict:
    decision: unresolved
    primary_criterion: closed at the best of 800, with and without compaction
    reason: The historical compaction program and outputs were not retained, so its null result
      and the inference that the resolver is not the ceiling cannot be reproduced or used to
      exclude an optimization.
    commit: f91fc7d4
  effort:
    stopped_by: dependency
    wall_seconds: unrecorded-historical
    migration_annotation: '2026-09-13: no complete elapsed-time receipt was retained. Per-trial
      median milliseconds and approximate prose budgets cannot recover total wall or operator
      time. This marker records missing history and is unavailable to new experiments.'
---
# exp-209 — A Compaction Pass Over Repaired Runs, Run Inline and Not Kept

**Rewritten 2026-09-14.** An earlier version drew a conclusion this round cannot
support. The previous text is at commit `a40d272c`.

## What Was Tried

After repair, each square was walked toward the centre of the bounding box as far as it
would go without overlapping, at a shrinking step.
As a control, the same pass ran on the same arrangements after scattering them outward
by 0.15 of a side.

## What Was Seen

On the repaired runs the pass did not change `closed` at `n = 5`, 10, 11 or 17, to four
decimal places. On the scattered control it shrank the container, for example from 3.279
to 3.028 at `n = 5`.

## Why It Supports No Conclusion

The pass was written inline, and its code, inputs and outputs were not kept.
The observation cannot be reproduced, so it does not show that the repaired arrangements
are locally compact, and it does not rule out a better repair, translating or rotating.
`think-3hb7` builds the pass as a retained instrument before anything depends on it.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
