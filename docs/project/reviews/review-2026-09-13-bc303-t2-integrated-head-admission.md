# H-160 T2 Reader: Integrated-Head Target-Free Admission

**ACCEPT the unchanged, independently reviewed T2 instrument at clean integrated head
`771d480512d9d31c85ab84d5ef4db1d90dd1e0d2`.** This decision covers source identity,
registration identity, chart manifest, retained review evidence, and synthetic reader
controls. No BC293 C/S target charge or exp-158 run was performed.

The merge is `771d4805` with parents `0d729486` (independent T2 readmission) and
`367cdd15` (H-161 result).
`git status --porcelain=v1` was empty before and after the controls.
Relative to reviewed reader revision `0f20fdcdd5bac7e0734b29cd0b0efef4ffea3699`, the
H-161 integration changes no charge-reader, maintained-test, H-160, or exp-158 file.
Relative to frozen source revision `39714308ce2081abbd76624387d134fee4be6deb`, it
changes none of the six source-contract files.
Relative to readmission commit `0d729486`, it changes none of the refusal or readmission
reports and evidence files.
Each scoped `git diff --quiet` returned exit code zero.

| Identity | Git blob at `771d4805` | Comparison |
| --- | --- | --- |
| T2 charge reader | `aa9ea57b774713c8ceea0f2b4983b0666df01d82` | Same as independently accepted `0f20fdcd` |
| Maintained charge controls | `f3ece5d7c3bc5ade17081395ce18bff65eae49c8` | Same as independently accepted `0f20fdcd` |
| H-160 registration | `28359f560a1d5396248d5bd683f09b1f1441d761` | Same as `0f20fdcd`; thresholds C `>=4524200`, S first owner `>=4524185` |
| exp-158 registration | `40f271fa6f2068305f84bfe1d833c888d7022225` | Same as `0f20fdcd`; no result, one registered target invocation |
| Frozen BC293 atoms | `db8abed8f716a4173b47bcfb19f8e045b44513d1` | Same as `39714308`; SHA-256 `c30b600d3d35f3851f0595e2c42962bf353721f9e72b0539bd691aec522e876f` |
| Refusal review and log | `510c2f22d210a4a8133b1fb19b53d73564c2d51e`; `8e79edee0bde14aa73fd594d41e9f48d17bfc99f` | Same as `0d729486` |
| Readmission review and retained control, focused log, independent log | `7008390e862633531f4daa0d7edfee1733bb1b40`; `22864bcece7f922196f56ce1f59173e363432cdf`; `e462ae99ab4e770042eaea89e4fc97bf2d0a08ca`; `8433fe87d0cd2788304f52193ffde7cb8a4072ed` | Same as `0d729486` |

The other five frozen source blobs also equal the readmission/refusal table:
`owner_footprints.py` `65501ad186a463eb5e7e16978daf03e603149fbd`, `adaptive.py`
`d80f6e060904bc5e01c21f5f23eba87ede456422`, `model.py`
`a5df6094eadfe441dba66fee8fe37a4e5530b6f6`, `sweep.py`
`6bd5c56564a8f1a0681213c9b083cf62e4621a95`, and `wall-containment-contract.md`
`24e00f7cbbbb07c26347e22a4b2b3467cea701fa`.

## Exact-Head Controls

From this checkout’s `packing/` directory, with project Python 3.14.7 and this checkout
first on `PYTHONPATH`:

```bash
PYTHONPATH=.:src /opt/homebrew/bin/python3.14 -m cases.n11_five_dot_cover.bc303_t2_charge_sweep source-check --expect-implementation-revision 771d480512d9d31c85ab84d5ef4db1d90dd1e0d2
```

Passed with `atoms: 377`, `eligible_source_charts: 182`, frozen source revision
`39714308...`, exact executing revision `771d4805...`, and explicit scope
`source and manifest only; no target charge`. The source parser checks all rows, integer
weights, and total integer mass `45048398`. A separate manifest-only read reported 181
distinct selected orientations, both axis aliases `(0, false)` and `(0, true)`, and
reflected endpoint `(180, true)`.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=.:src /Users/levy/.codex/worktrees/97ff/squares/packing/.venv/bin/python3 -m pytest -q -p no:cacheprovider tests/test_bc303_t2_charge_sweep.py
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONPATH=.:src /Users/levy/.codex/worktrees/97ff/squares/packing/.venv/bin/python3 -m pytest -q -p no:cacheprovider tests/test_bc303_t2_geometry_control.py
```

Both target-free suites passed: 13 charge-reader cases in 3.00 seconds and 2
geometry-control cases in 4.36 seconds.
A module-path check showed the reader, geometry, and adaptive modules imported from
`/private/tmp/squares-bc303-t2-reader-repair`, despite the test interpreter living in
another checkout’s virtual environment.
The historical independent 198-control readmission remains tied to `0f20fdcd`; its
source and logs are unchanged, but that exact-revision control was not rerun on
`771d4805`.

The normal `uv run --frozen --all-extras --group dev` path could not initialize the
sandboxed user cache.
An offline cache reroute lacked the pinned `nodejs-wheel-binaries` wheel.
The direct Python 3.14 source check and provisioned Python 3.14 test environment avoided
changing tracked files; they do not constitute a full repository validation gate.

## Remaining Boundary

At this head, H-160 still says `instrument_ready: false`, and exp-158 still has
`results: []` and `decision: in-progress`. The coordinator must record the readiness
transition and run its exact source/revision check on the committed target head.
The command’s `--expect-implementation-revision` must use that target head’s full
40-character hash, not the historical accepted reader hash `0f20fdcd`. This admission
does not predict whether either C/S threshold will pass or whether the preregistered
30-minute wall allowance will suffice.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
