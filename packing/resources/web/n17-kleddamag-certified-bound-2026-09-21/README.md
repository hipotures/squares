# Kleddamag’s Certified Lower Bound for `s(17)`, Retrieved 2026-09-21

A single third-party release claiming an exact computer-assisted lower bound on `s(17)`,
the least side of a square holding seventeen unit squares with disjoint interiors.
It is retained here because it is the strongest public claim for this case that the
record has seen, and because its replay is cheap enough to repeat: the whole argument
reduces to a fixed rational certificate and two exact sweeps over 7,853 angle intervals.

Retaining it registers no result and moves no bound.
What the repository makes of it is
[the review](../../../../docs/project/reviews/review-2026-09-21-n17-kleddamag-461300-99853.md),
which records the replay evidence and the findings, and states the rung.

## Provenance

| Field | Value |
| --- | --- |
| Source | <https://github.com/Kleddamag/17-squares-certified-bound> |
| Commit | `a499e2c739ce7853fa04c8bcdc85caf1c2b01b37` |
| Tag | `v1.0.0` |
| Retrieved | 2026-09-21 |
| Release `RESULT.json` | `1410a3c19cf5d3e3c86c04d49b99db23f688f0d17b34d58d37b662ba52991910` |
| Certificate | `0288aaac680131aa675adb63ea6a67e3d363fcca6061d4c788301da7c5d69cec` |

The release is a fresh public history; the authors state that no existing private
repository was made public.
The project was directed by **Kleddamag**, with the research, implementation and
verification work done by **OpenAI Codex**; `AUTHORS.md` in the retained tree sets out
that division and the limits of the word “independent” as the release uses it.

## The claim

$$
s(17) > \frac{461300}{99853} = 4.6197910929065726618\ldots
$$

The container side is `L = 4613/1000` and the hypothetical parent-square side is
`A = 99853/100000`, so the bound is the ratio `L/A`.
Site coordinates have denominator `10^8`; weights have denominator `10^9`.

The release claims no resolution of the minimum and no better packing.
It carries the established Bidwell construction forward unchanged as a rational
reconstruction, `s(17) <= 4675530093604551/10^15 = 4.675530093604551`, and verifies it
exactly rather than improving it.
It makes no literature-priority claim.

Its own stated improvement is measured against `461300/99951`, which `bounds.json`
records as `previous_strict_lower` and `PROOF.md` calls “the preserved bound.”
That baseline is the authors’ own earlier unreleased result, not a published rung; the
review takes this up, and the public priors it clears are Guzhou0806’s R012
(`461300/99999`) and R038 (`461300000000/99974999999`).

## Method

Weighted covering with strict cores, in the lineage the release names itself: Mira,
Guzhou0806/N17, and this repository’s own threshold-atom work.

A nonnegative measure is placed on the container as 1,134 point orbits under the eight
square symmetries, expanding to 8,988 sites; 852 orbits carry positive ordinary weight,
for 6,744 sites. On top of those sit 253 positive **two-of-three** orbits, expanding to
2,008 physical triples of distinct sites. A triple of weight `w` charges a square that
holds at least two of its three sites. Because any two two-element subsets of a
three-element set intersect, two disjoint squares cannot both qualify, so the triple’s
total charge across disjoint squares is still at most `w`.

| Quantity | Exact value |
| --- | ---: |
| Ordinary point budget | 14.640116080 |
| Two-of-three budget | 2.358311276 |
| Total budget `M` | 16.998427356 |
| Minimum core charge `Γ` | 1.000020517 |
| `17Γ` | 17.000348789 |
| `17Γ − M` | 0.001921433 |
| Angle intervals | 7,853 |
| Minimum strict containment margin | `10^−12` |

Seventeen disjoint cores would have to collect at least `17Γ = 17.000348789` while the
whole measure supplies at most `M = 16.998427356`, a contradiction with surplus
`1,921,433` units at denominator `10^9`. Compactness of the feasible parameter space
turns exclusion at `L/A` into the strict inequality.

The continuous part is the claim that *every* legal parent square of side `A`, at any
centre and orientation, contains a strict core charged at least `Γ`. That is discharged
by a catalogue of 7,853 exact half-angle intervals, each assigning a concentric closed
core of side `B`, and by an exact sweep over the whole legal-centre domain for each.
Capture regions are rectangles in core-aligned axes, so charge is a signed integer
weighted rectangle sum under the identity

```text
1_{i+j+k>=2} = ij + ik + jk - 2ijk,
```

and every geometric comparison is done in unbounded integers after clearing
denominators. Boundary and event centres are covered not by the sweep but by an upper
semicontinuity argument on the closed capture sets.

Two checkers run the sweep: a Python implementation using the rotated legal-centre
polygon’s exact edge projections per vertical slab, and a JavaScript implementation
using clamped-extrema formulas adapted from Guzhou’s R038 scanner, with BigInt for all
comparisons. They partition into slabs differently and agree on the complete histogram
of interval minima.

## What is retained, and what is not

**Retained byte-identical** under `kleddamag-17-squares-certified-bound/`: the whole
release tree, 82 files. That is the 81 files covered by the release’s own
`MANIFEST.json` plus `MANIFEST.json` itself, which does not list its own hash.
`NOTICES/` and `LICENSE` are retained verbatim, as are `ATTRIBUTION.md`, `AUTHORS.md`
and `LICENSING.md`, which carry the upstream source pins and the licence boundaries.
The release’s own `check_integrity.py` passes in the retained copy, so the retention is
self-checking against the authors’ manifest as well as against ours.

**Omitted, each for a reason:**

- `.git/` — the clone’s own history. The release is pinned above by commit and tag and
  internally by `MANIFEST.json`; a nested repository would not be readable through this
  repository’s history and would carry no evidence the pins do not.
- `__pycache__/` — CPython bytecode written by the replay on this machine. Generated,
  machine-specific, and not in the release manifest.
- `.cache/` — created by `prepare_secondary.py` at replay time and excluded by the
  release’s own `.gitignore`. Its single file is retained instead under
  `secondary-checker-inputs/`, below, where it cannot be mistaken for release source.

**Retained alongside the release, and deliberately outside it**, under
`secondary-checker-inputs/`:

| File | Bytes | SHA-256 | What it is |
| --- | ---: | --- | --- |
| `exact_parent_side_scan.js` | 5,594 | `63e858e28c4dee40f5763a832e1cfdf1f1fce3a1e5c632d087525bf1ee20ed14` | Guzhou0806/n17-square-packing at `32edfd3da78bf80a309398f552b3b602b9c45d6c`, `certificates/R038/src/exact_parent_side_scan.js` |
| `secondary_mixed_scan.js` | 6,505 | `b145b1ebbb2d3a0dccba62ee7b5ed64403bf0542ce5e8ee87113977df917faa4` | The reconstructed second checker actually used in the release’s verification |

These two files close a real gap. The release does not bundle the upstream JavaScript:
`prepare_secondary.py` downloads it from that pinned commit at replay time, checks its
SHA-256, applies the byte edits recorded in `secondary-adaptation.json`, and requires
the result to match the verified checker’s hash. A replay therefore needs the network,
and needs that one GitHub path to still resolve. Retaining both the pinned upstream
bytes and the reconstruction makes the second checker reproducible here without either.

**Licensing.** The authors’ `LICENSING.md` states that the pinned R038 source tree
carries attribution and licence-scope notices but that **no general licence grant for
that JavaScript checker was identified**, which is why the release does not redistribute
it. The copy kept here is retained for verification only, on the same understanding:
it is the input a replay of this release’s second checker needs, and nothing about
keeping it is a grant of rights in it. The same applies to the reconstruction, which the
authors describe as remaining subject to applicable upstream rights.

`retained-files.sha256` covers source bytes only — the 82 release files and these 2
checker inputs, 84 entries. This README and the manifest itself are our own outputs and
stay outside it, so the manifest measures exactly what was received and nothing this
repository wrote.

## Replay here

All commands below were run on this machine with the project interpreter (Python 3.14.7)
against the retained bytes, from
`packing/resources/web/n17-kleddamag-certified-bound-2026-09-21/`.

Check the retention against both manifests, ours and theirs:

```sh
shasum -a 256 -c retained-files.sha256
cd kleddamag-17-squares-certified-bound && uv run --frozen python check_integrity.py
```

All 84 entries verify, and `check_integrity.py` reports
`PASS: 81 release files match their SHA-256 manifest.`

Prepare the second checker with no network, which is what the retained upstream file is
for:

```sh
uv run --frozen python prepare_secondary.py \
  --source ../secondary-checker-inputs/exact_parent_side_scan.js
```

This reports `PASS: reconstructed checker matches completed verification` and writes
bytes identical to the retained `secondary-checker-inputs/secondary_mixed_scan.js`.
Confirmed here byte for byte, with no outbound request.

The two standard-library checks need nothing else:

```sh
uv run --frozen python verify_upper.py upper-packing-certificate.json
uv run --frozen python independent_controls.py global-certificate.json --output OUT.json
```

`verify_upper.py` passes: 17 exact unit squares, 68 vertices contained, all 136 pairs
separated, at exact side `4675530093604551/1000000000000000`.
`independent_controls.py` passes in 2 min 12 s with status
`PASS_INDEPENDENT_EXACT_CONTROLS`, over 7,853 intervals, all 31,412 rational quadratic
containment inequalities, and 3,403 exactly evaluated boundary and event centres whose
least charge is `1002070341` units against the required `1000020517`.

The full two-checker replay is the expensive one and needs the release’s own recorded
environment (Python 3.12, NumPy, Numba, Node.js), not the project interpreter:

```sh
python3.12 -m venv .venv && .venv/bin/python -m pip install -r requirements.txt
.venv/bin/python verify.py --jobs 2 --output .replay-runs/my-verification
```

Run in full here on 2026-09-21: **16 min 41 s**, producing a `RESULT.json` byte-identical
to the committed one (SHA-256
`1410a3c19cf5d3e3c86c04d49b99db23f688f0d17b34d58d37b662ba52991910`), all 7,853 intervals
passing in both checkers, and both checkers’ complete histograms of interval minima
identical at 509 distinct values. The exact counting arithmetic recomputes as
`17 × 1000020517 = 17000348789 > 16998427356`, surplus exactly `1921433`.

What that replay does **not** establish is independence of method.
Both checkers run the same weighted-covering sweep with the same range-minimum idiom,
and so does this repository’s own kernel; the review records what that costs the rung
and what would buy it back.

## Retrieval hashes

Hashes of this packet’s copies, which are the source’s bytes unchanged.
The full list is `retained-files.sha256`.

| File | SHA-256 |
| --- | --- |
| `kleddamag-.../README.md` | `4e0c18827e283672746d54f2ce79143c13f0fc7efa24fe49fc30404d5fee3b5b` |
| `kleddamag-.../PROOF.md` | `a14c7c68edb14148aed5cb7c5cfc8349718a48152d97b68cd2e21bc7b9c3c977` |
| `kleddamag-.../VERIFICATION.md` | `4f88dcf1eef779b08fc6b18ef917a03499888e4da8857cc421ae0e90ee36337e` |
| `kleddamag-.../ATTRIBUTION.md` | `50f2b7badaf398d2408589142e8d51973a365bbb6700a9fe89d3b9173bf56e65` |
| `kleddamag-.../AUTHORS.md` | `ec4840c6c45dc83fd062221d387f9ac9ab921aaaaf2a7489c12a8697a4a8ebeb` |
| `kleddamag-.../LICENSING.md` | `af631071fd416798fb706db693e5f1318eb05afc4d9d1f1b289e30894b8a0219` |
| `kleddamag-.../LICENSE` | `3658a57c304f53d0c2be0009232e3622fab7013a13bebea180cfbe8c7608f31c` |
| `kleddamag-.../MANIFEST.json` | `0b200b9ea5ae55cb4be66e06868919e650179c528911f414213959c22d719eb7` |
| `kleddamag-.../global-certificate.json` | `0288aaac680131aa675adb63ea6a67e3d363fcca6061d4c788301da7c5d69cec` |
| `kleddamag-.../RESULT.json` | `1410a3c19cf5d3e3c86c04d49b99db23f688f0d17b34d58d37b662ba52991910` |
| `secondary-checker-inputs/exact_parent_side_scan.js` | `63e858e28c4dee40f5763a832e1cfdf1f1fce3a1e5c632d087525bf1ee20ed14` |
| `secondary-checker-inputs/secondary_mixed_scan.js` | `b145b1ebbb2d3a0dccba62ee7b5ed64403bf0542ce5e8ee87113977df917faa4` |

Retained for private research use.
Consult the authors before redistribution; the R038 checker input carries no identified
general grant, and is kept for verification only.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
