---
title: exp-159 — prospective literal BC303 parent-union mass
softschema:
  contract: packing.squares:Experiment/v2
  schema: ../../../schemas/experiment.schema.yaml
  envelope: experiment
  status: enforced
experiment:
  id: exp-159
  series: series-000
  title: Prospective literal BC303 parent-union mass
  date: '2026-09-13'
  hypotheses: [H-161]
  tier: exploratory
  subject:
    label: Closed Q0 and its four separated D4 corner parents in the frozen BC303 measure
    engine: Source-bound exact rational parent-union reader
    engine_commit: 641beab7020570e71680950a92535073c8f698bd
    assurance: verified
    method: exact-algebraic
    host_system: Darwin arm64; project Python 3.14; one deterministic target invocation
    selftest_passed: true
  instance: {axis: n, point: 11, role: target}
  method:
    control: >-
      Before target, independently check all 377 frozen source rows, weighted D4
      invariance, closed/contact union arithmetic, separated synthetic corner
      arithmetic, source and executing-reader binders, and four forgery refusals.
      The reader must equal its committed blob at the executing HEAD.
    candidate: >-
      Read N=4000000*mu([0,1]^2) exactly once through literal_q0_mass. Compare the
      unchanged result to the frozen integer cutoffs 4262074 for four corners
      and 5048249 for one parent.
    runs_per_condition: 1
    interleaved: false
    operator: Codex source-distinct reviewer, then exact target operator
    entry_point: packing/devtools/read_bc303_parent_union.py:literal_q0_mass
    command: >-
      From packing/, run one Python 3.14 process importing
      devtools.read_bc303_parent_union.literal_q0_mass with repository '..';
      serialize returned N, source revision, source SHA-256, and implementation
      revision to /private/tmp/bc303-parent-union-target.json.
    budget: One deterministic literal Q0 target invocation; no pose sweep or retry
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union.json
  lease:
    expires: '2026-09-15T00:00:00Z'
  results: []
  verdict:
    decision: in-progress
    primary_criterion: >-
      Accept H-161 iff N>=4262074; separately report whether N>=5048249.
    reason: The source-bound literal target has not run.
---
# Exp-159: Frozen Decisions Before the Target

The accepted parent-union lemma gives `mu(Q_I)+sum(outside core masses)<=M` for
hypothetical eleven-parent packings with disjoint interiors.
The imported BC303 floor is `1+3/800000` for each outside strict core.
At scale `W=4000000`, the source total is `WM=45048398` and one outside-core floor is
`4000015` units.

The one-parent budget is `45048398-10*4000015=5048248`. The four-parent union budget is
`45048398-7*4000015=17048293`. Weighted D4 symmetry and the positive gap `q-2=46/25`
between corner copies give four-parent union mass `4N`. Thus the first rejecting
integers are `5048249` for one literal parent and `4262074` for the four-corner tuple.
The primary H-161 decision uses the four-corner cutoff.

The source, reader, and executed checkout revisions will be retained with the target
receipt. An independent raw-source replay will check the mass and D4 union afterward.
A cutoff failure means only that this necessary resource test survives.
A cutoff rejection means only nonextension of the named literal parent or tuple.
Neither result settles a pose neighborhood, continuous selection routing, or a global
lower bound on `s(11)`.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
