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
      From packing/, PYTHONPATH=. /usr/bin/time -p
      /opt/homebrew/bin/python3.14 - with the receipt-serialization stdin
      program recorded below; stdout to
      /private/tmp/bc303-parent-union-target-f27c8ec7.json and timing to
      /private/tmp/bc303-parent-union-target-f27c8ec7.time.
    budget: One deterministic literal Q0 target invocation; no pose sweep or retry
    record: packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-159-bc303-literal-parent-union.json
    commit: f27c8ec7c8ebeb8a9b369c1c6f7efef4b531c359
    dirty: false
  effort:
    timebox: One deterministic invocation
    wall_seconds: 0.16
    stopped_by: criterion
  results:
  - shape: determination
    role: outcome
    question: >-
      Does the exact literal Q0 mass violate the four-corner parent-union budget,
      and does it separately violate the one-parent budget?
    outcome: criterion_missed
    checked_by: >-
      packing/devtools/audit_bc303_parent_union.py independently replayed all
      377 raw source atoms and found
      19 closed Q0 sites of mass 4000015 units, no boundary or parent-only sites
      beyond the T1 core, and four disjoint D4 images with 19 sites and 4000015
      units each. It confirmed the retained source SHA-256, frozen and execution
      blobs, exact budgets 5048248 and 17048293, and 1048233 units of slack in
      each necessary inequality.
  verdict:
    decision: rejected
    primary_criterion: >-
      Accept H-161 iff N>=4262074; separately report whether N>=5048249.
    reason: >-
      N=4000015 is below both first-rejecting integers, so the literal
      four-corner and one-parent resource tests survive with 1048233 units
      of slack each; neither extension is established.
    commit: f27c8ec7c8ebeb8a9b369c1c6f7efef4b531c359
---
# Exp-159: Literal BC303 Parent-Union Mass

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

The
[source-bound receipt](../results/agenda-035/exp-159-bc303-literal-parent-union.json) at
preregistered execution head `f27c8ec7c8ebeb8a9b369c1c6f7efef4b531c359` reports
`N=4000015`, or `mu(Q0)=800003/800000`. It used the admitted reader file from commit
`641beab7020570e71680950a92535073c8f698bd`, unchanged at the execution head.
The independent
[377-row audit](../results/agenda-035/exp-159-bc303-literal-parent-union-audit.json) was
reproduced byte for byte by the
[replay tool](../../../../devtools/audit_bc303_parent_union.py).
It found the same 19 Q0 sites as the T1 core, no sites on Q0’s boundary or in its
parent-only annulus, and 19 sites of equal mass in each of the four disjoint D4 corner
images. The
[timing receipt](../results/agenda-035/exp-159-bc303-literal-parent-union.time.txt)
records 0.16 seconds of external wall time for the one target invocation.

The measured four-corner union has `4N=16000060` units against `17048293` allowed by the
necessary inequality.
The one-parent mass has `4000015` units against `5048248`. Each test has `1048233`
units, or `1048233/4000000`, of slack.
H-161 is rejected: this resource test excludes neither the literal four-corner tuple nor
one literal Q0 parent from an eleven-parent packing.
It also supplies no extension, pose-neighborhood exclusion, continuous selection
routing, or new lower bound on `s(11)`.

The executed Python 3.14 stdin program called the committed `literal_q0_mass` tool once
and serialized the result.
Its retained JSON includes N, exact mass, source and implementation revisions, source
SHA-256, closed bounds, both budgets and signed differences, both Boolean decisions, the
source atom count, and the response scope.

The one target invocation ran from `packing/`:

```bash
PYTHONPATH=. /usr/bin/time -p /opt/homebrew/bin/python3.14 - <<'PY' > /private/tmp/bc303-parent-union-target-f27c8ec7.json 2> /private/tmp/bc303-parent-union-target-f27c8ec7.time
import json
from fractions import Fraction
from pathlib import Path
from devtools.read_bc303_parent_union import (
    Q0, TOTAL_MASS, WEIGHT_SCALE, literal_q0_mass,
)
n, bound = literal_q0_mass(Path(".."))
one_budget = 45_048_398 - 10 * 4_000_015
four_budget = 45_048_398 - 7 * 4_000_015
receipt = {
    "schema": "bc303-literal-parent-union/v1",
    "source_revision": bound.source_revision,
    "source_sha256": bound.source_sha256,
    "implementation_revision": bound.implementation_revision,
    "atom_count": len(bound.atoms),
    "weight_scale": WEIGHT_SCALE,
    "total_mass": str(TOTAL_MASS),
    "closed_parent_bounds": [str(v) for v in Q0],
    "integer_mass_N": n,
    "mass": str(Fraction(n, WEIGHT_SCALE)),
    "one_parent_budget_units": one_budget,
    "four_parent_budget_units": four_budget,
    "four_corner_union_units": 4 * n,
    "one_parent_excess_units": n - one_budget,
    "four_corner_excess_units": 4 * n - four_budget,
    "one_parent_nonextension": n > one_budget,
    "four_corner_nonextension": 4 * n > four_budget,
    "scope": "literal Q0 and its four specified D4 corner images only",
}
print(json.dumps(receipt, indent=2, sort_keys=True))
PY
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
