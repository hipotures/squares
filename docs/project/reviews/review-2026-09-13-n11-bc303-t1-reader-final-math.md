# Exact Review of the Repaired BC303 T1 Reader

Date: 2026-09-13. Workflow: W2 independent mathematical and tool review of the W7 reader
repair. Original reviewed commit: `74ec773c5598355d14e97bbb66299d7e37ee69dd`.

**Disposition: ACCEPT the literal T1 reader at
`74ec773c5598355d14e97bbb66299d7e37ee69dd`.** Both admission findings in the prior exact
review are resolved: retained rows are authenticated against their source atoms, and
implementation identity is bound to the executing reader in the input checkout.
No remaining Blocker or High finding was found in this bounded review.

The finite arithmetic agrees with the previously accepted literal witness.
This acceptance admits the repaired instrument for that known candidate.
It does not record a campaign determination or promote T1, T2, global routing, a
minimum, or an n11 bound.

## Reviewed Identity and Evidence

The working tree was clean at the stated HEAD before and after the audit.
The repair commit changes only these two files; their complete working bytes equal their
committed blobs:

| Repository-relative file | Git blob | Bytes |
| --- | --- | ---: |
| `packing/devtools/replay_bc303_t1_witness.py` | `44309b88276b3c4a4607704d8fcdb8e4359d8e5b` | 29583 |
| `packing/tests/test_replay_bc303_t1_witness.py` | `1cf2015d3add2de05b567c97642eff7ce0ad9223` | 11348 |

All eighteen frozen sources were compared as complete byte strings at proposal revision
`39714308ce2081abbd76624387d134fee4be6deb`, the reviewed HEAD, and the working tree.
All comparisons passed, including agreement with the path, Git blob, and length table
from the earlier independent source audit.
The raw measure is
`packing/campaign/series/series-000-smoke-and-calibration/results/agenda-030/bc-293-measure-free-96-25.json`,
blob `db8abed8f716a4173b47bcfb19f8e045b44513d1`, 17616 bytes.
The complete eighteen-source table is embedded in the replay reader and every emitted
receipt. No additional checksum manifest was introduced.

The independent audit program parses the raw atom array.
Its membership oracle uses literal coordinate bounds and `min(x-low, high-x)` slacks;
its label oracle uses closed coordinate quadrants and the adjacent bins of each cardinal
direction. It does not import the reader’s atom parser, membership helper, or label
helper to construct expected values, and it never uses `least_cell_mass` as a charge
oracle.
It then exercises the actual reader helpers and public entry points against those
expectations.

The original clean CLI record was 108171 bytes and byte-identical to captured stdout.
Public validation, public encoding, and a fresh `replay` agreed with that original
record. The
[new-head campaign receipt](../../../packing/campaign/series/series-000-smoke-and-calibration/results/agenda-035/exp-157-bc303-literal-t1-witness.json)
is a separate replay at implementation revision
`81898608213774dcab99a16f776000421b9083ac`.

## Independent Finite Reconstruction

The raw array contains 377 distinct sites in `[0,96/25]^2`, all with positive rational
weights. Explicit reconstruction of the eight container symmetries verifies weighted D4
invariance. The weight-denominator least common multiple is `W=4000000`; summing all
source weights gives

$$
M=\frac{22524199}{2000000},\qquad
\varepsilon=M-11=\frac{524199}{2000000}.
$$

For the disclosed centre `(1/2,1/2)` and axis `(1,0)`, the actual unit parent is
`[0,1]^2`. It is contained in the container with permitted left and bottom wall contact.
Its selected core is

$$
C=[23/20000,19977/20000]^2,
$$

strictly inside that parent.
Both BL marks, `(3152/3175,2336/3175)` and `(2336/3175,3152/3175)`, are source atoms of
weight `106251/800000` and lie strictly inside the core.
There is one role-C owner and zero missing marks.
For each mark the mark-to-centre displacement has two negative coordinates; only the
west-first proper frame applies.
West belongs to both closed bins 3 and 4. The complete labels are therefore
`{3,4,11,12}`, so both 0 and 15 are absent.

Every retained row agrees with the independent raw-source reconstruction: source index,
exact point, exact weight, integer weight, closed membership, and both slacks.
The nineteen captured zero-based indices are

`[0,2,8,10,16,18,24,26,44,46,52,54,60,62,100,102,140,361,373]`.

The independent sum gives

$$
W\mu(C)=4000015,\qquad
\mu(C)=\frac{800003}{800000},\qquad
S(C)=\mu(C)-1=\frac3{800000},
$$

and

$$
\varepsilon-S(C)=\frac{1048383}{4000000}>0.
$$

All nineteen inclusions are strict; the smallest captured coordinate slack is
`28671/24460000`. Thus the literal witness falsifies the named universal local
inequality `S(X)>epsilon` on the declared bottom-left role-C domain with labels 0 and 15
absent. Equality conventions cannot reverse this particular charge or its labels.

The audit also independently checks the four reviewed axis centres, producing
`{1,2,13,14}`, `{0,7,13,14}`, `{1,2,8,15}`, and `{3,4,11,12}` respectively.
Synthetic mark-at-centre, zero-coordinate, vertex, and just-outside controls preserve
the expected closed labels under both axis aliases.
Literal core-edge and core-vertex membership passes; parent-only and just-outside-core
points fail. The nonliteral centres are geometric controls only; their charges were not
evaluated.

## R1: Source-Atom Authentication Accepted

At `packing/devtools/replay_bc303_t1_witness.py:629`,
`validate_record(record, repository)` first authenticates the eighteen source files,
checks the executing reader, and parses the authenticated measure.
Its loop at line 719 reconstructs an expected row from each source atom and compares the
entire supplied row with it.
It also requires actual integer types for source indices and integer weights and an
actual Boolean membership flag.
The aggregate captured mass is summed from the authenticated atoms.

This closes `think-fvvt`: a record can no longer substitute its own coordinates or
weights as the source of its expected values.
The public `encode_record` at line 772 calls this same authoritative validator.
No structural-only serialization path remains in the public API.

The following independently constructed controls all raise `T1ReplayError` through
**both** `validate_record` and `encode_record`:

| Retained-record mutation | Observed refusal |
| --- | --- |
| Add `1/W` to captured row 0, updating its integer weight | Row 0 differs from bound source atom |
| Add `1/W` to captured row 0 and subtract `1/W` from captured row 2 | Row 0 differs from bound source atom |
| Add `1/W` to excluded row 1 and subtract `1/W` from excluded row 3 | Row 1 differs from bound source atom |
| Give excluded row 1 weight `-1` and integer weight `-4000000` | Row 1 differs from bound source atom |
| Move excluded row 1 to `(10,10)`, recomputing its slacks | Row 1 differs from bound source atom |
| Flip captured row 0’s membership | Row 0 differs from bound source atom |
| Substitute integer `1` for a membership Boolean | Row 0 differs from bound source atom |
| Substitute Boolean `false` for source index 0 | Row 0 differs from bound source atom |
| Substitute a numerically equal float for an integer weight | Row 0 differs from bound source atom |

Both balanced controls preserve the captured total and total measure mass; the altered
weights remain positive.
Their refusal demonstrates source identity checking beyond an aggregate-mass check.
The out-of-container mutation remains excluded and has consistent slacks, so its refusal
also depends on source binding.

The maintained test at `packing/tests/test_replay_bc303_t1_witness.py:67` retains the
three previously accepted tampering cases as refusal regressions.
This review’s receipt retains every additional mutation and its exact error.

## R2: Executing-Reader Identity Accepted

`_bind_implementation` at `packing/devtools/replay_bc303_t1_witness.py:331` requires the
executing module’s resolved `__file__` to equal the input checkout’s regular reader
path. It reads that path’s committed blob at the reported HEAD and compares the entire
file. `validate_record` also requires the retained implementation revision to equal that
authenticated HEAD. This closes `think-9buk` under the chosen policy that source and
implementation must be in the same checkout.

| Independent provenance control | Observed result |
| --- | --- |
| Original reader, original input checkout | Complete; correct implementation HEAD |
| Original reader, separate checkout at the same HEAD | `replay`, `validate_record`, `encode_record`, and CLI refuse the reader-path mismatch |
| Reader executed locally in the separate checkout at the same HEAD | Complete; reports `74ec773c...`; file equals stdout |
| Byte-identical reader copied to a different path, original input checkout | CLI refuses the reader-path mismatch |
| Reader in its own checkout with an appended comment and unchanged HEAD | CLI refuses bytes differing from implementation revision |
| Source revision checkout with no reader file | Public replay refuses the reader-path mismatch |
| Current reader materialized and executed at source revision, where HEAD lacks that path | CLI refuses: executing reader is absent at implementation revision |
| Dirty source-measure bytes with a clean local reader | CLI refuses proposal/HEAD/worktree source disagreement |
| Retained implementation revision set to forty zeroes, proposal revision, or the previous reader commit | Both public validators refuse the revision mismatch |

The source-revision control executes the copied module from inside that fixture.
It therefore reaches the absent-committed-implementation check, in addition to testing
the outer path guard.
Each refused CLI exits 2, writes no stdout, and creates no output record.
Complete subprocess commands, module search roots, stderr, and output-presence checks
were recorded by the original audit and repeated at the new execution head.

## Public Paths, Validation, and Design

The inspected paths are the real implementation paths: `replay` authenticates before
constructing evidence, `encode_record` reauthenticates before serialization, and CLI
`main` calls both.
`_publish_record` atomically writes the encoded record, parses it with
the strict JSON reader, and authenticates the retained copy.
The CLI success control exercises the complete publication path.
No mocked binding or patched validator was used for the admission audit.

The maintained suite passed **11 tests in 33.87 seconds**. It includes strict JSON
duplicate-key rejection, source-byte mutation, a same-total D4-preserving measure
perturbation that changes the literal charge, unique-owner enforcement, and the
geometric boundary controls.
`git diff --check HEAD^ HEAD` passed.
The independent audit adds **17 retained-record mutations through two public entry
points**, all refused, and **10 provenance controls**, including the clean own-checkout
positive control.

The two new required repository arguments intentionally strengthen the public verifier
and encoder contract.
Repository search found their consumers in this reader and its tests, all updated
together. The module documentation identifies `validate_record(record, repository)` as
the authoritative retained-record entry point and distinguishes frozen-source revision
from reader revision.

The literal-reader design remains appropriate: exact rational arithmetic, a complete
finite source scan, and a fixed reviewed witness suffice for this task.
A generalized optimizer or another provenance manifest would add no required capability.
No additional source or documentation change is required for this bounded admission.
This original review made no claim about repository-wide gates or campaign registration.

## New-Head Port and Readback

The two reader-only commits `88d54d85` and `74ec773c` were cherry-picked, in order, onto
the settled local PR156 base `9c56e9019b97be0511d5afe590790b362b93e9e4`. The resulting
execution head is `81898608213774dcab99a16f776000421b9083ac`. The reader and test blobs
still equal the two accepted blobs above.
At this new head, all eighteen frozen source paths again match the proposal revision,
committed base, committed execution head, and working-tree bytes, including their
recorded lengths.

The new-head focused suite passed 11 tests in 36.56 seconds.
A new CLI replay wrote the 108171-byte campaign receipt, byte-identical to captured
stdout.
The original independent audit was rebound only to the new execution revision and
then run against this fresh record and checkout.
It reconstructed all 377 rows from the raw measure, matched every retained row, and
passed 17 retained-record mutation refusals through both public validators and 10
provenance controls.
The audit reported the same exact mass, labels, captured indices, and surplus.
This new readback establishes the port’s execution evidence; the original W2 acceptance
remains an exact review of the old head, not an assertion that reviews automatically
transfer between commits.

## Reproduction

At execution commit `81898608213774dcab99a16f776000421b9083ac`, use the project’s Python
3.14 environment. The retained record is historical evidence bound to that commit.
Checking it against a later documentation HEAD requires checking out the execution
commit; replaying at a later HEAD produces a new implementation revision.

```bash
cd packing
uv run --frozen --all-extras --group dev python -m pytest \
  tests/test_replay_bc303_t1_witness.py -q
uv run --frozen --all-extras --group dev python -m \
  devtools.replay_bc303_t1_witness --repository .. --output /tmp/bc303-t1-replay.json
```

## Mathematical and Admission Limits

The accepted arithmetic concerns a known local parent and selected core.
It does not establish that the parent extends to an eleven-parent packing.
Consequently it supplies no conclusion about local availability restricted to actual
eleven-parent packings, existential equipment selection, or another global
owner-selection argument.

The reader does not replay the full BC303 coverage certificate.
Its comparison with `least_cell_mass` is a frozen-source identity check; the literal
charge is independently summed.
The arithmetic alone proves no global mass floor or exact minimum.
The record correctly retains `minimum_surplus`, `global_routing`, and `n11_lower_bound`
as `not-claimed`; independent promotions of all three were refused through both public
validators.

This review evaluates no T2 charge, split-owner threshold, surplus search, BC329 target,
or new packing bound.
It verifies a disclosed T1 candidate rather than conducting a target-blind discovery.
Independent rational implementations remain the same evidence method under
`epistemics.md`; source independence does not imply distinct-method confirmation.
The retrospective
[H-159](../../../packing/campaign/hypotheses/H-159-bc303-one-corner-surplus.md) and
[exp-157](../../../packing/campaign/series/series-000-smoke-and-calibration/experiments/exp-157-bc303-literal-t1-witness.md)
record only rejection of the named local inequality.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
