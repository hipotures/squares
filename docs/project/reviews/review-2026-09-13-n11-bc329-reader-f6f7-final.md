# BC329 Reader F6/F7: Final Exact-Head Review

**Disposition: ACCEPT the source-distinct reader F6/F7 repair at
`a5701e73ea1edfe8afb7d876910d79c8938ec54f`.** The prior finite phase-sum overflow
admission is closed on this exact reader blob.
This is a scoped reader verdict.
It does not admit the three positive calibration profiles or the BC329 target, and it
does not transfer to the later PR 156 head without checking that head’s exact source and
gates.

The earlier [F6/F7 refusal](review-2026-09-13-n11-bc329-reader-f6f7-overflow.md) was at
`406009647223c9f53c828d5d29707897f12535b1` and found that finite phase durations could
sum to infinity, after which the eight-ULP comparison accepted them.
That report was committed after the reviewed source revision.
The present verdict comes from the exact `a5701e73` code, a clean disposable clone, and
new full readback controls.

## Exact Source Identity

The shared stack checkout advanced to `dbbf8495` while this review ran.
All dynamic reader checks therefore used a local shared-object clone at
`/private/tmp/bc329-reader-a570-exact`, checked out detached at the requested commit.
The clone’s `HEAD` stayed at `a5701e73ea1edfe8afb7d876910d79c8938ec54f`, its tree was
`1d41292744142315a07d58367ace85cf872df2c5`, and its status was clean after the controls.
The reader and producer modules imported from that clone.
Each on-disk source matched its committed Git blob.

| Repository-relative path | Exact Git blob | Bytes |
| --- | --- | ---: |
| `packing/devtools/read_fixed_core_calibration_profile.py` | `34d48ee0004aad26743d9b5ee9f035f8a8be662a` | 80,874 |
| `packing/tests/test_read_fixed_core_calibration_profile.py` | `627df45c383dfecf1c37cb5839ea3495663fdff1` | 75,795 |
| `packing/devtools/calibrate_fixed_core_packet.py` | `d63d4ec57038539b5bb57b8673c4e2eaaa79da3d` | 175,859 |
| `packing/devtools/run_fixed_core_calibration_profiles.py` | `38aa018d298da162499d9a7e6f13ac9e2db02c6b` | 95,931 |

The synthetic receipt declares execution commit
`faa4085db8fb4cf42154afec0022a0585f59196d`, which is an ancestor of this reader head.
Its 23-row source manifest was reconstructed from that execution commit’s Git objects.
Every full control called `reader.read_profile` with the real `_bind_revisions`; no
revision binder was mocked.

## Reader, Producer, and Coordinator Binding

The producer’s `source_manifest` requires the declared execution revision to equal its
checkout `HEAD`, requires a clean source closure and checkout, and binds each source
path to frozen Git and file bytes (`calibrate_fixed_core_packet.py:792–839`). Its
`validate_document` requires finite individual clock fields and coherent invocation
identity, but it does not prove that seven finite worker phases fit their lifetime.

The coordinator checks the supplied execution revision against receipt source and
invocation identity, reconstructs topology and inventory, and binds producer readback,
logs, and the receipt into run records (`run_fixed_core_calibration_profiles.py:666–790,
999–1127, 2091–2278`). Its inventory receipt validator also accepts the synthetic finite
phase-overflow receipt at its own stated surface.
Reader admission must therefore be checked separately before interpreting a run set as
source-distinct evidence.

The reader checks a Git **commit** object, exact reader `HEAD`, running entry-file
origin, and on-disk bytes against the reader commit before it parses the receipt
(`read_fixed_core_calibration_profile.py:392–409, 2014–2032`). It then binds the
receipt’s complete execution import closure to that frozen commit and independently
reconstructs the fixture, direction rows, topology, resources, and inventory.
The `a5701e73` repair rejects nonfinite operands in `_not_later`, nonfinite absolute and
terminal deadlines, nonfinite seven-phase sums, and nonfinite propagated sequential
phase completions (`read_fixed_core_calibration_profile.py:1260–1265, 1520–1541,
1792–1805, 1864–1912`). This closes the specific `40600964` admission path without
adding an arbitrary upper duration cap.

## Independent Full-Readback Controls

The disposable control script `/private/tmp/bc329-reader-a570-independent.py` built a
fresh target-free `n=2` synthetic profile, kept the full direction-row and artifact
inventory, and rebuilt the receipt-size fixed point and affected sidecar hashes for each
mutation. Its Machine-readable outcomes at
`/private/tmp/bc329-reader-a570-independent.json` record all 23 controls.
Every expected acceptance returned a complete `read_profile` proof with the exact reader
and declared execution revisions; every expected refusal raised `ReadbackRefusalError`.
The script returned `PASS=23/23` and left the clone clean.

| Obligation | Adversarial and boundary results |
| --- | --- |
| F6a nested clocks | Source loading `0.9` inside preflight `0.1` refused; equality at `0.1` accepted. Launch `1.1` after observed worker exit `1.05` refused; equality at `1.05` accepted. Cleanup `0.16` after the `0.15` post-exit interval refused; `0.15` accepted. Parent final readback `0.16` refused. |
| F6b disjoint phase lengths | The serial baseline and seven `2e307` phases totaling `1.4e308` accepted. An ordinary finite total above a `1.3e308` worker lifetime refused. Seven individually finite `4e307` phases whose binary-float total is infinity refused with `worker phase total is not a finite nonnegative number`. The producer schema and coordinator inventory receipt validator accept this same finite-input mutation at their narrower surfaces. |
| F6b sequential tasks | A legal one-child pooled baseline accepted. Delayed raw tasks with insufficient normalization gap before exact tasks refused; a nearby delayed-exact control with enough gap accepted. A separate case had a **finite** seven-phase total but placed exact tasks near `1.6e308`, so the propagated phase completion overflowed; it refused with `worker phase schedule is not a finite nonnegative number`. All affected sidecar and receipt hashes were rebound. |
| F6b other derived sums | A terminal external duration sum of two finite `1e308` inputs refused; an absolute calibration deadline formed from finite `1e308 + 1e308` refused. |
| F6c child identity | A coherent parent-child PID cycle, rebound in both route sidecars and summary, refused. One-child and separate two-child pooled full readbacks accepted. |
| F7 revision type and override | Coherently rebound execution tree and blob IDs refused as `not a Git commit`. A reader revision override to `HEAD^` refused on the exact-HEAD check; changing the expected execution argument to a valid other commit without changing the receipt refused on receipt identity. A copied reader file outside the checkout refused on running-source origin. |

One deliberately nonancestor control rebounded the receipt and complete source manifest
to valid commit `dbbf8495082137e4b26a8531ff21e14d2cce5678` and accepted under the older
reader `a5701e73`. Git confirms `dbbf8495` is **not** an ancestor of `a5701e73`. This is
not an F7 regression: F7 requires a commit object and an exact caller-supplied execution
identity, not an ancestry relation between the execution and reader commits.
The proof binds the declaration and retained source bytes; it cannot prove historical
execution from a synthetic receipt alone.
The actual admission process must freeze and carry its expected execution commit
independently.

## Maintained Tests and Reproduction

The maintained full real-binder selection passed **17/17** in 66.11 seconds.
The broader reader suite passed **111/111**, with one intentional source-write test
deselected, in 265.70 seconds.
A separate full real-binder two-child control accepted, and a copied-reader origin
control refused. The exact-head CLI emitted an accepted JSON proof for the baseline; for
the execution tree object it returned status 2, printed no JSON to stdout, and wrote a
`REFUSED` diagnostic to stderr.
All checks used CPython 3.14.7 from the project’s virtual environment, with bytecode and
pytest cache writes disabled.
The following commands reproduce the checks from the exact detached clone:

```bash
cd /private/tmp/bc329-reader-a570-exact/packing
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/private/tmp/bc329-reader-a570-exact/packing:/private/tmp/bc329-reader-a570-exact/packing/src \
/Users/levy/.codex/worktrees/88e2/squares/packing/.venv/bin/python3 \
  -m pytest -q -p no:cacheprovider \
  --basetemp /private/tmp/bc329-reader-a570-full-pytest \
  -k 'not running_reader_origin_and_cli_copy_refusal' \
  tests/test_read_fixed_core_calibration_profile.py

PYTHONDONTWRITEBYTECODE=1 \
/Users/levy/.codex/worktrees/88e2/squares/packing/.venv/bin/python3 \
  /private/tmp/bc329-reader-a570-independent.py

PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/private/tmp/bc329-reader-a570-exact/packing:/private/tmp/bc329-reader-a570-exact/packing/src \
/Users/levy/.codex/worktrees/88e2/squares/packing/.venv/bin/python3 \
  -m pytest -q -p no:cacheprovider \
  --basetemp /private/tmp/bc329-reader-a570-pytest \
  -k 'real_binder' \
  tests/test_read_fixed_core_calibration_profile.py
```

The excluded maintained test temporarily writes and restores the repository reader
source. This review left all source bytes untouched.
It separately checked running origin with a disposable copied reader and verified
committed/on-disk byte identities; it did not rerun the changed-byte mutation.
No full `packing-validate` checkpoint, live PR-head equality check, positive calibration
profile, minimizer, interval search, dilation execution, or BC329 target was run by this
reviewer.
The controls establish acceptance only for this exact reader blob and synthetic
retained evidence. Later integrations and the other admission gates still require their
own verdicts.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
