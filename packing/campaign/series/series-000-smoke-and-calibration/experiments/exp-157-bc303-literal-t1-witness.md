---
title: exp-157 — literal bottom-left BC303 T1 witness
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-157
  series: series-000
  title: Literal bottom-left BC303 T1 witness
  date: '2026-09-13'
  hypotheses: [H-159]
  tier: exploratory
  subject:
    label: Disclosed bottom-left role-C parent against the named universal local
      surplus inequality
    engine: Source-atom and executing-reader-bound literal replay of all 377 BC303 atoms
    engine_commit: 81898608213774dcab99a16f776000421b9083ac
    assurance: verified
    method: exact-algebraic
    host_system: Darwin arm64; project Python 3.14; one deterministic CLI invocation
    selftest_passed: true
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      The reviewed source table fixes eighteen complete Git blobs at proposal revision
      39714308ce2081abbd76624387d134fee4be6deb. The executing reader must equal
      its committed blob in the same checkout. The focused 11-test suite and a separate
      audit reconstruct all 377 source rows and exercise 17 retained-record mutations
      and 10 provenance controls at this new execution revision.
    candidate: >-
      Replay the already disclosed centre (1/2,1/2), axis (1,0), parent [0,1]^2 and
      selected core [23/20000,19977/20000]^2 once. Test the complete closed label set
      and exact S(X) > epsilon comparison. No optimizer or continuous-domain search ran.
    runs_per_condition: 1
    interleaved: false
    operator: Codex Sol implementation and record; source-distinct mathematical review
      at the original reader head by Astra Max
    entry_point: packing/devtools/replay_bc303_t1_witness.py
    command: >-
      cd packing && uv run --frozen --all-extras --group dev python -m
      devtools.replay_bc303_t1_witness --repository .. --output
      /private/tmp/bc303-t1-81898608-record.json >
      /private/tmp/bc303-t1-81898608-stdout.json
    budget: One deterministic replay of the fixed disclosed candidate; no retry,
      parameter sweep, or BC303 full-coverage certificate replay.
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-157-bc303-literal-t1-witness.json
    commit: 81898608213774dcab99a16f776000421b9083ac
    dirty: false
  effort:
    timebox: One deterministic literal replay, without a scientific search clock
    wall_seconds: 1.92
    stopped_by: criterion
  results:
  - shape: determination
    role: outcome
    question: Does the named universal bottom-left role-C inequality S(X) > epsilon
      survive this disclosed admissible local witness?
    outcome: criterion_missed
    checked_by: >-
      The fresh 108171-byte CLI record at execution HEAD 81898608213774dcab99a16f776000421b9083ac
      matches captured stdout and its retained copy byte for byte. The independent
      new-head audit reconstructed all 377 rows from the raw measure, checked the 19
      captured atoms and complete labels {3,4,11,12}, and refused 17 altered records
      through both public validators plus 10 provenance controls. The exact captured
      mass is 800003/800000, so S(X)=3/800000 and epsilon-S(X)=1048383/4000000>0.
  verdict:
    decision: rejected
    primary_criterion: A single admissible bottom-left role-C parent with labels 0
      and 15 absent and exact selected-core surplus S(X) <= epsilon.
    reason: The fixed parent has S(X)=3/800000 < epsilon=524199/2000000, so the named
      universal local inequality is false; no continuous-domain or global claim follows.
    commit: 81898608213774dcab99a16f776000421b9083ac
---
# Exp-157: Literal BC303 T1 Witness

This is a retrospective record of one disclosed candidate.
The
[accepted reader review](../../../../../docs/project/reviews/review-2026-09-13-n11-bc303-t1-reader-final-math.md)
was conducted at the original reader head `74ec773c5598355d14e97bbb66299d7e37ee69dd`.
The code was then ported onto PR156’s local base; the fresh
[complete receipt](../results/agenda-035/exp-157-bc303-literal-t1-witness.json) and
independent readback bind the new execution head
`81898608213774dcab99a16f776000421b9083ac`. The result JSON records that historical
execution head even after this documentation commit advances the branch.
A timed repeat at the same committed head reproduced the retained JSON and stdout byte
for byte in 1.92 seconds of external command wall (`/usr/bin/time -p`). This timing
covers the deterministic reader, not a search or the independent audit.
To validate it under the reader’s identity rule, check out that execution commit and
call `validate_record(record, repository)` there, or replay at a later head for a new
implementation revision.

The parent is `[0,1]^2`, its selected core is `[23/20000,19977/20000]^2`, and both
bottom-left marks lie strictly inside.
The complete labels are `{3,4,11,12}`. Nineteen of 377 atoms are captured, with mass
`800003/800000`; therefore `S(X)=3/800000` is below `epsilon=524199/2000000`. This
rejects only H-159’s universal local inequality.
It does not determine the least surplus over the full role-C domain, whether the parent
occurs in an eleven-parent packing, T2, global routing, or a stronger `s(11)` bound.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
