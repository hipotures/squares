# Eleven unit squares: a certified lower bound

This repository gives a reproducible computer-assisted proof that

$$s(11) > \frac{31}{8} = 3.875.$$

Here $s(11)$ is the smallest side length of a square that can contain eleven
unit squares with disjoint interiors. Each unit square may rotate independently;
boundary contact is allowed. The exact minimum remains unresolved, and this
work does not give a better packing.

The result builds on **[Joshua Levy's squares project](https://github.com/jlevy/squares)**,
using its T-026 threshold certificate as the starting point. The second geometric
checker adapts **[Guzhou0806's R038 implementation](https://github.com/Guzhou0806/n17-square-packing/tree/32edfd3da78bf80a309398f552b3b602b9c45d6c/certificates/R038)**.
[Attribution](ATTRIBUTION.md) identifies the source revisions, changes and earlier
contributions. Kleddamag directed the project; OpenAI Codex developed the
mathematical and computational continuation. See [contributions](AUTHORS.md).

[Proof](PROOF.md) · [Verification evidence](VERIFICATION.md) ·
[Release](https://github.com/Kleddamag/11-squares-certified-bound/releases/latest) ·
[Licensing](LICENSING.md)

## How the proof works

After a common rescaling, the certificate assigns a specific strict interior
core to every possible square placement. A core receives a nonnegative charge
according to which weighted sites and site subsets it contains. Every assigned
core receives enough charge that eleven disjoint cores would exceed the total
available budget:

$$11 \times 0.999962528 = 10.999587808 > 10.999479944.$$

The exact scans cover every legal centre and orientation through 12,028 angle
intervals. Strict interior cores handle squares whose boundaries touch.
The [proof](PROOF.md) gives the counting, geometric coverage and boundary arguments.

Two exact geometric implementations passed the full certificate and returned
identical interval-minimum histograms. Separate controls checked 48,112
containment inequalities and 5,586 selected boundary/event centres. The latter
are additional checks, not a substitute for complete coverage. The recorded
checks and their scope are described in [VERIFICATION.md](VERIFICATION.md).

## Reproduce the verification

Install Python 3.12 and Node.js, then run:

```sh
git clone https://github.com/Kleddamag/11-squares-certified-bound.git
cd 11-squares-certified-bound
git checkout v1.0.2
node --version
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python check_integrity.py
.venv/bin/python verify.py --output-dir .replay-runs/my-verification
.venv/bin/python verify_threshold_algebra.py
```

On Windows, use `.venv\Scripts\python.exe` instead of `.venv/bin/python`.
The recorded environment uses Python 3.12.14, NumPy 2.3.5, Numba 0.67.0,
llvmlite 0.49.0 and Node.js 25.6.1. Choose a new output directory for each replay.
The two geometric checkers run sequentially, each using three workers. Allow
tens of minutes, depending on hardware. Run with Python assertions enabled:
do not use `-O`, `-OO` or `PYTHONOPTIMIZE`.

The first run downloads one small, commit-pinned R038 source file, applies
this project's published edits, and checks the source and reconstructed-file
hashes. The [licence scope](LICENSING.md) explains why that upstream source is
not bundled. To prepare from an existing local copy instead:

```sh
.venv/bin/python prepare_secondary.py --source /path/to/exact_parent_side_scan.js
```

The scans then run locally on the fixed rational certificate; no numerical
search or optimization software is needed. A successful full run reports
`PASS_FRESH_PORTABLE_FULL_VERIFICATION`, bound `31/8`, 12,028 intervals, and
counting surplus `107864` in units of $10^{-9}$.

Certificate SHA-256:

```text
57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458
```

## Files

| File | Purpose |
|---|---|
| [PROOF.md](PROOF.md) | Mathematical argument |
| [global-certificate.json](global-certificate.json) | Fixed rational certificate |
| [verify.py](verify.py) | Run both complete scans and the independent controls |
| [exact_mixed.py](exact_mixed.py), [integer_sweep.py](integer_sweep.py) | Python geometry and integer sweep |
| [prepare_secondary.py](prepare_secondary.py), [secondary-adaptation.json](secondary-adaptation.json) | Reconstruct the hash-pinned JavaScript checker |
| [independent_controls.py](independent_controls.py), [verify_threshold_algebra.py](verify_threshold_algebra.py) | Containment, boundary and counting checks |
| [VERIFIED.json](VERIFIED.json), [evidence](evidence/), [VERIFICATION.md](VERIFICATION.md) | Results and detailed verification records |
| [MANIFEST.json](MANIFEST.json), [check_integrity.py](check_integrity.py) | File integrity |
| [ATTRIBUTION.md](ATTRIBUTION.md), [AUTHORS.md](AUTHORS.md), [NOTICES](NOTICES/), [LICENSING.md](LICENSING.md) | Sources, contributions and terms |

Independent reproduction and corrections are welcome through
[GitHub issues](https://github.com/Kleddamag/11-squares-certified-bound/issues).
