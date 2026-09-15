# BC329 Calibration Reader: Source-Distinct Review

**Disposition: REFUSE source-distinct calibration admission at the reviewed revision.**
The exact `n=2` geometry and the 14,404-row contract check out, but the reader admits
records that contradict the producer contract or the retained operational observations.
These are reader admission defects.
They do not refute the fixture mathematics or establish any scientific result.

- Review date: 2026-09-13.
- Reviewer: independent Astra Max review lane, `bc303_surplus_exact_review`.
- Repository: `/private/tmp/squares-n11-bc329-stack`.
- Reviewed Git HEAD: `212e0dfc9f7b2e48743cb84ea21b3803822e50b8`.
- Synthetic fixture’s declared execution revision:
  `faa4085db8fb4cf42154afec0022a0585f59196d`.
- Entry point: read-only implementation review and target-free synthetic readback
  controls. No positive producer calibration profile, scientific target, or BC329 run was
  executed. No repository or bead was edited by this review.

The three-profile run sheet should remain ineligible.
The next admissible task is to repair the admission checks and their maintained mutation
controls, then obtain a fresh review at the resulting exact commit.
Passing the existing tests does not discharge the findings below.

This is the durable copy of the independent review.
The `/private/tmp` control files named below were local review artifacts, not files in
the reviewed commit.
Their substantive mutations must be carried into maintained tests before a later
acceptance claim can rely on them.

## Exact Source Boundary and Retained Evidence

The relevant committed identities are:

| Repository-relative source | Git blob at reviewed HEAD | Bytes |
| --- | --- | ---: |
| `packing/devtools/read_fixed_core_calibration_profile.py` | `ca3e56a405e6ee55d70e97c4d742b6bad0eb6100` | 66,022 |
| `packing/tests/test_read_fixed_core_calibration_profile.py` | `843bb33b766e28885c1362977f59bd54e74ba810` | 36,062 |
| `packing/devtools/calibrate_fixed_core_packet.py` | `a731e23f6f8c7a049480e9cd664478005c082bf7` | 175,259 |
| `packing/devtools/fixed_core_packet.py` | `baaeace549c917bd541f4bf88f7c38d2dba14ef3` | 183,715 |
| `packing/devtools/run_fixed_core_calibration_profiles.py` | `141d4d48e1ce7325e7e970d4639020c6caec32e0` | 93,837 |
| `packing/cases/n02_fixed_core_packet_calibration/fixture.json` | `df6497f35fb91fd4220413b1fd29c0fca94575d3` | 935 |

The reader, its tests, producer, generic packet module, and fixture matched these
committed bytes when the adversarial control run initialized.
The coordinator had concurrent author changes, so its comparison uses `git show` at the
reviewed commit. The author subsequently changed producer and coordinator files as well;
those changes are outside this report.
At the final publication check, HEAD had advanced to
`fc3e314daaeb1cb07705ce4a44ae682e80eafa6a`. The reader and its tests still had no diff
from the reviewed commit, but the integrated producer/coordinator at that later HEAD is
outside this exact-commit review.
A later fix must not be treated as covered by this review.

The fixture SHA-256 is
`1aface38ab79526397b7b9f24325df844e2eb9717d3e29a094fcdefe8822f539`. Git identifies
repository sources; the fixture and retained artifact hashes cross the source/output
trust boundary.

Retained evidence:

- Review controls: `/private/tmp/bc329-reader-exact-review-controls.py`.
- Machine-readable outcomes and source identities:
  `/private/tmp/bc329-reader-exact-review-controls.json`.
- Synthetic row fixture used by the controls:
  `/private/tmp/bc329-reader-exact-review-controls/synthetic-row-fixture`.
- Copy-loaded reader used for the origin-binding control:
  `/private/tmp/bc329-reader-exact-review-controls/copied_reader.py`.
- Original maintained-test output:
  `/private/tmp/bc329-reader-review-pytest-212e/source-distinct-profile0/profile-1`.

The controls preserve their code and outcomes.
They restore the synthetic baseline between mutations and after the last full readback.
They regenerate affected row digests, record hashes, and inventory sizes, including the
receipt-size fixed point.
Thus the false admissions below are not merely tests that bypass artifact integrity.
Every full readback used the real revision binder with the execution and reader
revisions above.
Only the copied-reader and exceptional-number controls call the relevant
helper directly; their narrower coverage is identified below.

The control script deliberately refuses to reuse an existing work directory and requires
the reviewed source bytes.
To repeat it after a clean exact-commit checkout, use a fresh work directory and result
filename, and first regenerate or retain the synthetic maintained-test fixture.
Do not replace that synthetic setup with a producer profile run.

## Blocking Admission Findings

### F1: Source Manifest Completeness Is Not Checked

**Observed false admission.** A manifest containing only the frozen fixture and
`packing/devtools/calibrate_fixed_core_packet.py` receives `status: accepted` from a
full `read_profile` call.
Both rows have correct Git blobs and SHA-256 hashes at the declared execution revision.

`_validate_sources` at reader lines 348–417 verifies each supplied row, then requires
only those two paths.
It does not reconstruct or compare the complete local import closure or require the
project runtime declarations.
The producer’s `discover_implementation_paths` and `source_manifest`, at committed
producer lines 734–831, declare a recursive closure including package initializers and
the runtime declarations.
That closure contains 23 paths for this implementation.
The relevant producer, kernel, and imported local implementation files have no committed
diff between the synthetic execution revision and the reviewed HEAD.

The admitted record omits these 21 required paths:

```text
packing/.python-version
packing/devtools/__init__.py
packing/devtools/decide_certificate.py
packing/devtools/decide_threshold_certificate.py
packing/devtools/dilation_corollary.py
packing/devtools/fixed_core_packet.py
packing/devtools/measure_net_refinement.py
packing/devtools/measure_threshold_net_refinement.py
packing/pyproject.toml
packing/src/sqpack/__init__.py
packing/src/sqpack/field.py
packing/src/sqpack/fractional/__init__.py
packing/src/sqpack/fractional/certificate.py
packing/src/sqpack/fractional/interval.py
packing/src/sqpack/fractional/model.py
packing/src/sqpack/fractional/sweep.py
packing/src/sqpack/fractional/threshold.py
packing/src/sqpack/fractional/threshold_interval.py
packing/src/sqpack/verify.py
packing/src/sqpack/workers.py
packing/uv.lock
```

**Consequence.** Hashing every supplied row proves its identity.
It does not prove that all the implementation sources were supplied.
In particular, the exact mathematical kernels and worker implementation can be absent
from an accepted source manifest.
The maintained positive synthetic fixture has this same two-row manifest, so the
existing test currently codifies the incomplete contract.

**Minimal repair.** Independently construct the expected path set from the execution
revision’s Git objects.
Start at the calibration entry point, resolve local Python imports and enclosing package
initializers, and add the frozen fixture, `.python-version`, `pyproject.toml`, and
`uv.lock`. Compare the manifest to that full canonical set, then verify each blob and
output-bound hash. Read dependency syntax without executing it.
Do not import the producer’s closure function into this source-distinct reader.
A fixed reviewed path set is sufficient only if the reader also explicitly restricts
execution to the commit for which that set was reviewed.

**Required mutation controls.** Use a positive synthetic manifest containing the full
23-path closure. Parametrize omission of every required path, including each runtime
declaration and package initializer; every omission must refuse.
Also reject an unexpected path, duplicate path, path alias, changed blob, changed
SHA-256, and a manifest from a different execution revision.
Ensure closure discovery reads the execution tree even when the reader checkout contains
different source imports.
Retain a positive control for the legitimate separation of execution and reader
revisions.

The declared runtime scope is deliberately narrower than interpreter-binary,
installed-wheel, operating-system, scheduling, or cross-host equivalence.
This finding does not demand any of those attestations.
It demands the complete source and runtime declaration set already promised by the
producer.

### F2: Revision Binding Does Not Bind the Running Reader File

**Observed gap.** The control loads a copy of the reader from
`/private/tmp/bc329-reader-exact-review-controls/copied_reader.py`, with an added
comment so its bytes differ from the committed reader.
Calling that module’s `_bind_revisions` with the legitimate repository and reviewed HEAD
succeeds.

At reader lines 335–345, the binder checks `repository/packing/devtools/...py` against
the Git blob. It does not compare that path to the file from which the executing module
was loaded. In contrast, the producer’s committed `_validate_loaded_modules` checks the
actual running entry point and local module origins.

**Consequence.** The proof’s `reader_revision` can describe a file in a checkout rather
than the reader module that performed admission.
The demonstrated change is only a comment; the concrete defect is failure to bind
executing source bytes, not evidence that this review ran a malicious reader.
This is an ordinary wrong-copy/import-origin failure and does not require a
malicious-host attestation model.

**Minimal repair.** Capture the reader’s actual resolved `__file__` and require it to
equal the resolved expected repository entry point before binding its bytes to the
reviewed commit. Keep the exact HEAD check and byte comparison.
Make the binding work for both the supported module invocation and the direct script
invocation.

**Required mutation controls.** The actual in-repository reader should bind
successfully. A copy outside the repository, a copy in another checkout, and an altered
running file must refuse even when an unrelated clean checkout is supplied as
`--repository`. The copied-module reproduction here covers the binder directly; add an
end-to-end CLI control to verify the public entry point produces no acceptance JSON on
refusal.

### F3: Dense/Slab Witness Agreement Is Weaker Than the Producer Contract

**Observed false admission.** In normalized exact direction 0, replace only
`slab_witness` with `["9/32", "9/32"]`, retaining dense witness `["3/8", "3/8"]`, both
charges `"1"`, and `agree: true`. Rebind the row digest and inventory.
Full source-distinct readback accepts it.

Both witnesses are admissible and have the correct charge.
At direction 0 the first core is `[1/8,5/8]^2`, which captures all three sites of each
cross. The second is `[1/32,17/32]^2`, which captures the center and the negative
endpoint of each cross, but excludes the positive endpoint.
Both two-of-three threshold charges fire, so both normalized charges are exactly 1.

The generic producer row reader `_exact_row` rejects this same row with
`PacketError: normalized exact agreement flag disagrees with its row`. Its agreement
contract compares the complete `(charge, witness)` pair.
The committed three-profile coordinator also explicitly requires
`slab_witness == witness` in `_known_answer_row`. The source-distinct reader, at lines
521–537, checks equal charges and independently valid witnesses, but omits witness
equality.

**Consequence.** An accepted `agree: true` can contradict the exact producer and
coordinator definition.
The known minimum is still correct in this control; it is the claimed reader agreement
that is false. Do not turn this finding into a claim that different valid minimizers
invalidate the underlying mathematical certificate.

**Minimal repair.** Require equality of the canonical dense and slab witness pairs
alongside the existing equal-charge and separate membership/admissibility checks.
Keep separate replay of both witnesses; equality must not replace replay.

**Required mutation controls.** Use the two distinct admissible witnesses above with
equal charges and `agree: true`, with all artifact bindings updated.
Refuse it. Retain positive equal-witness controls and separate controls for
`agree: false`, unequal charges, a noncanonical rational, a misplaced witness, and a
boundary witness whose membership depends on closed inequalities.

### F4: Equality Admits Boolean and Floating-Point Schema Substitutions

**Observed false admissions.** A full readback accepts the following coherent changes to
the synthetic record:

| Intended field | Admitted substituted value |
| --- | --- |
| Invocation and identity `run_order` | `true` instead of integer `1` |
| Raw `observed_argmin` | `false` instead of integer `0` |
| First two raw completed directions | `[false, true]` instead of `[0, 1]` |
| Raw `witness_admissible` | integer `1` instead of `true` |
| Effective worker counts | `true` instead of integer `1` |
| Raw direction 0 row label | `false` instead of integer `0` |
| Interval lower/upper enclosure | `8.0` instead of integer `8` |
| Interval `stalled` | `false` instead of integer `0` |

A separate full-readback control changes normalized candidate `n` to `2.0`,
`direction_steps` to `2880.0`, and both threshold counts to `2.0`, rebinding the
candidate and its dependent record hashes.
It is also accepted.

Representative sites are raw direction comparison at line 508, interval enclosure and
stall checks at lines 565–572, candidate dictionary equality at lines 785–788, and
invocation/effective-worker/identity dictionary equality at lines 1433–1530. Other
reconstructed dictionaries need the same audit.
Python’s `True == 1`, `False == 0`, and `2.0 == 2` make structural equality insufficient
for a typed JSON schema.

**Consequence.** A closed key set is not a closed value schema.
The normalized threshold float even causes the candidate budget calculation to leave
exact rational arithmetic through floating-point floor division.
Its small known answer happens to compare equal; that does not satisfy the intended
exact schema. Some producer and coordinator comparisons share equality-based weaknesses,
so repairs should make the retained contract consistent across consuming boundaries
rather than copying a weak comparison into another reader.

**Minimal repair.** Validate scalar types before equality or arithmetic.
Use `type(value) is int` for integer counts and directions, `type(value) is bool` or
`is True`/`is False` for Boolean fields, canonical strings for exact rationals, and
finite nonnegative `int`/`float` values only where the contract permits measured real
numbers.
A recursive typed comparison can centralize this for fixed expected objects; its
treatment of measured numbers must be explicit.
Ensure threshold counts remain integers before budget arithmetic.
Do not coerce input with `int()`, `bool()`, or `float()` to make a malformed record fit.

**Required mutation controls.** Parametrize each typed field independently with Boolean,
floating-point, string, and null alternatives as applicable.
In particular, exercise every `0`/`1` field and every fixed integer in nested
candidates, route summaries, resource summaries, invocation identities, and supervision
records. Each semantically invalid substitution must refuse even after hashes are
updated. Retain positive finite measured-time floats and exact conversion of interval
witness floats; those are allowed by the contract and must not be rejected by an
indiscriminate all-floats ban.

**Related refusal-contract edges.** `_number(10**1000, "clock")` raises an uncaught
`OverflowError` while attempting `math.isfinite`. A JSON integer containing 5,000 digits
causes `_json_bytes` to raise the interpreter’s integer-limit `ValueError`. The public
`main` catches only `OSError` and `ReadbackRefusalError`, so these helper exceptions do
not take its declared `REFUSED`/exit-2 path.
They do not produce a false acceptance proof, and should be distinguished from the false
admissions above.
Normalize expected conversion/parser failures to `ReadbackRefusalError`
locally and add CLI controls asserting exit 2, a concise refusal, and empty standard
output. Do not broadly catch all exceptions and conceal implementation defects.

### F5: Mathematical Dilation Fields Are Present but Unverified

**Observed false admission.** Keep the accepted factor and side squared fields, but
change the factor defining polynomial to `x - 1`, the side defining polynomial to
`x - 7`, and both decimal presentations to `999`. Rebind the dilation record and
inventory hashes. Full readback accepts the contradictory record.

`_validate_dilation`, at lines 866–998, enforces exact keys and checks the source, two
rational multipliers, factor and side surds/squares, relation, and selected Booleans.
It does not verify the polynomials or decimal values.
Several retained domain, containment, invariant, and proof fields are also accepted
merely because their keys exist, without a value-type check.
The maintained synthetic fixture uses placeholder prose in those fields, further
weakening its positive contract.

The committed producer’s `_check_dilation_record`, lines 651–657, compares the entire
record to a reconstructed exact record.
The reviewed design’s source-distinct admission obligation 5 requires every mathematical
dilation field to be rederived.

**Minimal repair.** Derive both reduced rational squares and their positive-root
polynomials independently, validate the positive surd, and validate decimal presentation
under a declared precision/rounding contract.
Construct and compare the remaining fixed mathematical domain/inequality/endpoint
fields, with explicit types, from the reviewed formulas.
Keep the reader free of producer helper imports.
If a presentation field is intentionally outside admission, narrow the record and proof
contract explicitly; silently retaining unchecked contradictory mathematics is not a
suitable repair.

The correct polynomials for the present fixture are `33189121*x^2 - 132710404` and
`132756484*x^2 - 298598409`.

**Required mutation controls.** Independently change each polynomial coefficient, root
sign, exact square, decimal value, factor domain, strictness relation, and
endpoint/compactness statement.
Include wrong scalar types in previously unchecked fields.
Update hashes in each control.
Maintain a complete positive synthetic record whose values match the stated schema
rather than placeholder mathematical prose.

### F6: Clock and Process-Topology Records Can Contradict Their Own Lifetimes

**Observed false admissions.** Three full readback controls pass:

1. `raw_seconds = 1000000`, `worker_elapsed_seconds = 1`, `worker_exit_seconds = 0`, and
   `external_lifetime_seconds = 1.2`.
2. Process-pool raw and normalized-exact task traces start at 1,000,000 seconds after
   the invocation origin, although the declared external lifetime is 1.2 seconds.
3. A process-pool route reports child PID 101 with PPID 101 while the coordinator’s PID
   is also 101. It is admitted as its own child.

The topology controls contain all 2,881 direction observations in each route, matching
child summaries, complete sidecar hashes, and matching inventory.
Each has one observed child under two configured workers, which is otherwise an allowed
distinction between configured workers and observed task execution.

The receipt schema currently checks nonnegative finite clocks,
`worker_elapsed < calibration_allowance`,
`external_lifetime + terminal_admission < external_allowance`, and
`worker_elapsed <= external_lifetime`. It does not compare phase durations or observed
worker exit to those lifetimes.
Topology reconstruction checks parent/group identity, direction coverage, per-PID
nonoverlap, child summaries, and simultaneous task counts, but not child/coordinator
distinctness or task times against worker/phase lifetimes.

**Clock meaning matters.** In the committed producer, `worker_exit_seconds` is
`exit_observed - invocation_started`, a timestamp relative to the common origin.
It is not an additional cleanup duration.
`parent_final_readback_seconds` is a duration after worker exit;
`external_lifetime_seconds` ends at completion of that readback.
These meanings follow the producer’s supervision code at lines 3695 and 3759–3826. A
repair must follow these definitions instead of summing every field.

**Minimal repair.** Independently enforce the necessary relationships, allowing only a
justified tolerance for subtracting measured floating-point clocks:

- Worker elapsed time is no later than observed worker exit, which is no later than the
  external lifetime.
- Parent final-readback duration fits between observed worker exit and the external
  lifetime.
- Each worker phase duration fits inside worker elapsed time.
  Where the producer guarantees phases are disjoint, their total must also fit; do not
  naively add parent preflight/launch intervals that may overlap other observations.
- Every task’s start and finish lie within the worker lifetime.
  Each route’s observed task span fits within its reported phase duration, and raw task
  completion precedes the subsequent normalized-exact task observations.
- Route worker PID differs from coordinator PID, and process identities cannot make a
  process its own parent.
  Keep the existing strict PID/count types, group/parent checks, direction coverage,
  per-PID nonoverlap, and event ordering at touching interval endpoints.

**Required mutation controls.** Cover each inequality separately, including equality at
allowed boundaries and refusal at the declared deadline.
Cover impossible exit ordering, an oversized single phase, an oversized sum of disjoint
worker phases, tasks outside the worker lifetime, reversed raw/exact ordering, a route
span exceeding its phase, and self-parent identities.
Add a valid synthetic pooled topology with multiple children and overlapping tasks, a
legal touching-task boundary, a legal single observed child under two configured
workers, and a valid serial topology.
Reconstruct all summaries and hashes in both positive and negative cases.

These checks establish internal consistency of retained observations.
They cannot prove that a hostile process monitor or operating system reported the truth.
That stronger claim is outside this reader’s scope and is not required to reject the
contradictions demonstrated here.

## What the Review Verifies Mathematically

The following are exact derivations, separate from the computed admission outcomes.
They explain why the known answers are valid and why the witness-disagreement control
does not depend on an invalid placement.

### Frozen Geometry and Exact Charge

Let the parent side be `L = 3/4`, the core side be `B = 1/2`, and the cross center be
`o = (3/8,3/8)`. The raw measure has mass `1/2` at `o`, plus two threshold atoms of
weight `3/4` each: the horizontal and vertical triples at offsets `-3/16, 0, 3/16`, each
with threshold 2.

For a core orientation with nonnegative sine and cosine, write `S = c+s`. Its physical
center must lie in `[BS/2,L-BS/2]^2`. Therefore each coordinate differs from `o` by at
most `(L-BS)/2 <= 1/8`. The center atom is at squared distance at most `1/32` from the
core center, strictly below `(B/2)^2 = 1/16`, so it lies in the inscribed disk and is
captured by every admissible core.

For the horizontal triple, select the endpoint on the same side of `o` as the
core-center horizontal displacement.
Its horizontal distance from the core center is at most `3/16`, and its vertical
distance at most `1/8`. The squared distance is at most `13/256 < 1/16`. It is captured
along with `o`. The same argument applies to the vertical triple.
Thus both two-of-three thresholds fire at every admissible placement.
Admissible placements exist at every orientation because `L^2 - 2 B^2 = 1/16 > 0`.

Every raw charge is exactly

```text
1/2 + 3/4 + 3/4 = 2.
```

Each threshold atom has budget multiplier `floor(3/2) = 1`, so the raw budget is also 2.
At `n=2`, the strict comparison is `2 > 2/2 = 1`. Multiplying every weight by `1/2`
gives normalized point weight `1/4`, two threshold weights `3/8`, budget 1, minimum 1,
and integer scale `lcm(4,8) = 8`.

The reader independently computes rational rotations, physical containment, and closed
point/threshold membership.
Interval witness floats are interpreted as the exact rationals represented by their
binary values. This is appropriate: it checks the retained witness without an arbitrary
epsilon. The intended threshold comparison is `count >= 2`, and every core boundary is
closed.

The reader does not independently rerun dense/slab minimization or replay an interval
subdivision tree. For this fixture, the uniform geometric argument supplies the lower
bound at all admissible placements; exact witness replay supplies the retained placement
check. That scope is sufficient for the fixture’s known mathematical answer, but it does
not by itself prove that a particular set of retained rows came from an actual
generic-kernel execution.

### Net, Reflections, and the 14,404 Direction Rows

For `k = 0,...,2880`, the rational half-angle parameter is `t = k/5760`. The reader uses

```text
c = (1 - t^2)/(1 + t^2),  s = 2t/(1 + t^2).
```

Primed interval labels exchange `c` and `s`. The maximum tangent of an adjacent half-gap
is

```text
(1/5760)/(1 + t_k t_(k+1)),
```

attained at `k=0`, hence `D=1/5760`. The final parameter `1/2` exceeds `sqrt(2)-1`,
since `t^2+2t-1=1/4>0`; the forward net reaches past `pi/4`. The coarse containment
value is `B(1+D)=5761/11520<1`.

The required label collections are:

| Route | Labels | Retained direction rows |
| --- | --- | ---: |
| Raw | `0` through `2880` | 2,881 |
| Normalized exact | `0` through `2880`; dense and slab share one row | 2,881 |
| Normalized interval | `0` through `2880`, then `1'` through `2880'` | 5,761 |
| Dilation | `0` through `2880` | 2,881 |
| Total | `3*2881 + 5761` | **14,404** |

Only primed zero is omitted by this route contract.
Geometric coincidences among other labeled directions do not authorize deleting retained
labels. The reader correctly reconstructs the full sets and hashes in prescribed order.
The direction count excludes candidate, dilation record, receipts, RSS records, and
topology sidecars. Dense and slab do not double the normalized-exact row count.

Every interval row must carry the integer enclosure `[8,8]`, yielding normalized
`[1,1]`, certified status, a positive box count, zero stalls, and no exhausted budget.
The reader checks these values and aggregates box counts, with the integer type defect
described in F4. The synthetic test’s 5,761 boxes are invented test data, not a measured
interval workload.

### Exact Dilation and Endpoint Meaning

The strict scaled containment test is

```text
q^2 B^2 (1+D)^2 < 1+D^2.
```

The exact quantities are:

```text
B^2 (1+D)^2 = 33189121/132710400
1+D^2       = 33177601/33177600
q_sup^2     = 132710404/33189121
q_sup       = 2*sqrt(33177601)/5761
(L q_sup)^2 = 298598409/132756484
L q_sup     = 3*sqrt(33177601)/11522.
```

The positive root is irrational because `5760^2 < 33177601 < 5761^2`. Strict positive
rational subfactors yield the family of bounds, and rational density plus monotone
embedding gives the non-strict supremum conclusion.
No individual endpoint certificate is supplied: at the supremum, the strict containment
test is equality. Thus the retained relation `>=`, `endpoint_certificate: false`, and
`requires_compactness: false` are consistent.
These facts do not excuse contradictory polynomials or decimal values in the same
record.

## Resource, Publication, and Scope Checks That Are Present

The reader uses only standard-library imports and does not import the producer’s
fixture, normalization, membership, direction, or dilation routines.
This is an appropriate source-distinct implementation boundary.
The review controls use producer or generic helpers only to compare contracts and build
artifact bookkeeping; the reader under review remains independent.

The reader requires a real output directory outside the repository.
It preflights the complete artifact inventory and exact direction filenames, refusing
symlinks and special files before reading row contents.
It rejects duplicate JSON object keys, non-finite JSON constants, unexpected outer
schema fields, scientific-target receipt schemas/vocabulary, and noncanonical rational
strings. It independently reconstructs route digests, source-record hashes, file counts,
byte sizes, and receipt size.
These checks are useful and remain necessary after the repairs.

CPU summaries are recomputed from retained start/end observations for coordinator
process time and reaped direct-child user/system time.
They are not process-group CPU measurements, and parent readback CPU is excluded.
The reader correctly preserves that stated scope.
CPU time need not be bounded by wall time in the presence of multiple processes or
threads; no such unsupported inequality is requested here.

RSS summaries are reconstructed from sampled time/PID/byte observations, including
counts, error records, sampled peak, phase coverage, maximum observed gap, leading and
trailing gaps, and sidecar digest.
The reader requires at least two positive, error-free terminal samples and binds the RSS
observation lifetime to the declared external lifetime.
This is sampled process-group RSS: transient peaks can be missed, and shared pages can
be counted more than once.
Missing sampled phases are reported; they are not automatically proof of an unexecuted
phase.

For raw and normalized-exact routes, the reader reconstructs configured workers,
observed child identities, task coverage, child summaries, and maximum simultaneous task
execution. Serial routes require no child tasks or children.
A process pool need not show all configured workers actually executing a task.
On non-Linux execution platforms, the effective generic interval/dilation worker setting
is one; Linux uses the requested setting.
Actual route-worker observations cover raw and normalized exact, so the reader must not
describe the interval/dilation settings as observed child counts.

Deadline validation includes the declared calibration and external allowances,
invocation-origin arithmetic, strict terminal deadline comparisons, successful worker
exit, and the retained cleanup flags.
The phase-duration scope explicitly states where external lifetime and measured terminal
admission stop, and that final staging and atomic replacement remain subject to fresh
producer checks. Retained flags and timestamps are evidence of those observations;
readback is not a second execution of the process supervisor.
F6 addresses contradictions that can be rejected from the existing retained observations
without pretending to rerun supervision.

This CLI admits one supplied profile.
It does not read the coordinator’s complete three-profile run record, establish the
prescribed run sequence, or authorize a scientific task.
Its returned receipt digest and invocation identity can be joined to the coordinator’s
separately bound run records.
The absence of a three-profile aggregate decision in this single-profile reader is a
scope boundary, not a new bug.

## Validation Performed and Missing Controls

From `packing/`, using the repository’s Python 3.14 interpreter:

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python3 -m pytest -q -p no:cacheprovider --basetemp /private/tmp/bc329-reader-review-pytest-212e tests/test_read_fixed_core_calibration_profile.py
```

Result: **8 passed in 17.92 seconds**. The test fixture writes synthetic known-answer
rows. It does not invoke a raw sweep, exact minimizer, interval search, dilation
producer, or calibration supervisor.
Reading a complete synthetic artifact shape is not evidence of a successful positive
calibration execution.

The eight tests cover synthetic row/digest/resource reconstruction, static
source-distinct imports, duplicate/nonfinite JSON and scientific-schema refusals,
selected deadline/RSS relationships, symlink/FIFO preflight, selected coherent
mathematical and operational mutations, execution/reader revision distinctions, and CLI
refusal output. The maintained positive readback helper mocks `_bind_revisions`; the
supplemental controls in this review used the actual binder.

The retained supplemental run reports:

| Control | Observed outcome at reviewed HEAD |
| --- | --- |
| Two-row source manifest | Full readback accepted |
| Equal charges, distinct valid dense/slab witnesses, `agree: true` | Full readback accepted; generic producer row reader refused |
| Boolean/float schema substitutions | Full readback accepted |
| Candidate integer fields serialized as floats | Full readback accepted |
| Contradictory dilation polynomials and decimals | Full readback accepted |
| Impossible phase/exit lifetimes | Full readback accepted |
| Task observations after declared invocation lifetime | Full readback accepted |
| Coordinator reported as its own child | Full readback accepted |
| Running reader loaded from a modified external copy | Revision-binding helper accepted |
| Integer too large for finite-number conversion | Unnormalized `OverflowError` |
| JSON integer beyond interpreter digit limit | Unnormalized `ValueError` |

The combined mutation cases demonstrate false admission but should become separate
parametrized controls in the maintained suite.
That prevents one repaired check from hiding an unfixed neighbor.
A complete positive synthetic source/dilation record is also needed, since the current
positive fixture contains omissions and placeholders that stricter validation must
reject.

The author’s wider suite, lint, and type-check results are useful integration evidence
but do not substitute for these missing behavioral controls.
This review did not run the full project validation surface or any positive producer
workload.

## Disposition and Next Admissible Task

**REFUSE** the reader at `212e0dfc9f7b2e48743cb84ea21b3803822e50b8` as sufficient
source-distinct admission for the planned calibration run set.
The specific blockers are complete source binding, running-reader origin binding,
dense/slab agreement, typed value schemas, complete mathematical dilation validation,
and internally consistent lifecycle/topology observations.
The exceptional-number paths also need normal refusal behavior.

Repair those checks without importing producer validation as the reader’s oracle.
Update the positive synthetic fixture, add the independent mutation controls described
above, and run the focused target-free suite plus the relevant static checks.
Then freeze a commit and request exact-head rereview.
Do not infer eligibility merely from the current eight passing tests or this review’s
exact fixture derivations.

No conclusion is drawn about BC329 acceptance, runtime, memory needs, any `n=11`
mathematical role, or a global packing bound.
No actual calibration execution has been admitted by this review.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
