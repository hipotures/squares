# Weighted Certificates for `s(17)` Above `459/100`, Retrieved 2026-09-20

Two public GitHub repositories, each claiming a weighted lower bound on `s(17)` above this
repository’s verified `459/100 = 4.59`, and each descended from this repository’s own
certificate.
Neither was in the record before 20 September 2026.

The Guzhou0806 repository was pointed out to the owner on 2026-09-20.
Its attribution file names Mira’s `17squares` at a pinned September commit, and following
that pointer found Mira’s weighted certificate of 7 September.
That certificate was published hours after the GitHub check of 7 September that produced
the earlier packet ([`n17-github-certificates-2026/`](../n17-github-certificates-2026/README.md)),
so the check missed it: Mira’s two September commits carry author timestamps of 18:58 and
19:41 on 7 September in `-0700`, which is 01:58 and 02:41 UTC on 8 September, and the
earlier packet retained Mira’s repository at its 11 August commit.

Both values in this packet are **above** this repository’s verified `459/100` (`T-019`,
2026-09-04), and both descend from it.
Mira’s certificate starts from the `T-019` atom measure, retains the exact `T-019`
certificate file unchanged inside its own package, and credits it under CC BY 4.0.
Guzhou0806’s R012 starts from Mira’s measure, so it inherits the same lineage at one more
remove, and credits both.
Neither result is verified here.
What follows records what each source claims, in its own numbers, and what this packet
retains; the replay instruments and their outcomes are separate, and are named in
[Replay here](#replay-here).

## Chronology of 2026 lower-bound claims for `s(17)`

The eight public claims from 18 July to 21 August 2026 are tabulated in the earlier
packet’s [chronology](../n17-github-certificates-2026/README.md#chronology-of-2026-lower-bound-claims-for-s17)
and are not repeated here.
The table below picks up where that one ends.

| Date | Author | Type | Value |
| --- | --- | --- | --- |
| 2026-07-18 – 2026-08-21 | eight earlier public claims | see the [2026-09-07 packet](../n17-github-certificates-2026/README.md) | up to `9141/2000 = 4.5705` |
| 2026-09-04 | this repository | weighted atomic-measure certificate (`T-019`), 1184 atoms | `459/100 = 4.59` |
| 2026-09-07 | Mira | weighted atomic-measure certificate, 1200 atoms (GitHub; not retained here) | `4.607028598640` |
| 2026-09-07 | Mira | weighted atomic-measure certificate, 1620 atoms (GitHub; retained) | `4.613028635886` |
| 2026-09-18 | Guzhou0806 | nonuniform 197-direction net over the `T-019` atoms (GitHub; retained) | `4.59004266897263595052…` |
| 2026-09-20 | Guzhou0806 | parent-angle catalogue over Mira’s measure (GitHub; retained) | `461300/99999 = 4.61304613046130…` |

Dates are the sources’ own author timestamps in their own offsets: Mira’s two September
commits at `-0700`, Guzhou0806’s at `+0800`.

## Mira-acc/17squares: `s(17) > 4.613028635886`

Selected tree of <https://github.com/Mira-acc/17squares> at commit
`0266c9936a303817ac7da0802364034a34fb2558`, author date 2026-09-07 19:41:18 `-0700`,
“Publish reviewed 4.613 weighted certificate and update paper”.
Retrieved 2026-09-20.

### What is retained, and what is not

Retained: `certificates/lower_bound_4p613/` minus its `search/` subdirectory, the top-level
`README.md`, `VERIFY.md`, `CITATION.cff` and `verify_all.sh`, and `paper/`.
That is 63 files and 1,924,905 bytes of the source’s 181 files and 13,283,165 bytes.
Every retained file is byte-identical to the source commit, checked file by file against
the clone.

Not retained, with the reason in each case:

- `certificates/lower_bound_4p613/search/`, 38 files and 9,054,111 bytes of numerical
  discovery code, seeds and `.npz` checkpoints.
  The package’s own README calls these “optional numerical discovery code” and its trust
  boundary excludes the optimizer, so they are not part of the proof.
  The retained `MANIFEST.sha256.json` still lists all 38 of them by name, size and
  SHA-256, so the manifest names files this packet does not hold.
  Its other 55 entries are all present here and all hash-match.
- `certificates/lower_bound_4p607/`, 58 files and 1,883,809 bytes: the intermediate
  weighted certificate claiming `s(17) > 4.607028598640`, published at commit
  `f290643a6fe011094cf171780c38bb600da49c77`, author date 2026-09-07 18:58:42 `-0700`.
  It remains retrievable at that commit.
- `certificates/lower_bound_4p468292/`, 20 files and 418,529 bytes: the August
  triangle-witness certificate already archived in the earlier packet.
  `git diff` between commit `0872d3ac` and this commit reports no change to that
  directory, so the copy in the earlier packet is the same bytes.
- `.github/workflows/verify-weighted-cover.yml` and `.gitignore`.

### The claim

The strict claim is `s(17) > 4.613028635886`.
The base certificate excludes a packing at side `4613/1000`; uniform dilation gives the
weak form

```text
s(17) >= (4613/1000) * sqrt(1 + h^2) / ((19997/20000) * (1 + h)),   h = 207107/1440000000,
```

equivalently `s(17) >= sqrt(17650291964463886688094912400 / 829429719507765981945905041)`,
about `4.61302863588611076617…`.
The inequality at the radical endpoint is weak; the displayed twelve-decimal bound is
strict, and the source checks that by rational squaring.

The measure has 1620 rational atoms in 206 positive `D4` orbits, total mass
`849899249/50000000 = 16.99798498 < 17`.
The core side is `19997/20000 = 0.99985`, the direction net has 2881 rational directions
(`h = T/2880` with `T = 207107/500000`), the least core mass over all of them is
`1000002103/1000000000`, and the sweep covers 9,116,871 centre slabs.
`result.json` records all of these, and the expected checker line is

```text
EXACT_CERTIFICATE_VALID atoms 1620 directions 2881 total_mass 16997984980/1000000000 minimum 1000002103/1000000000 slabs 9116871
```

### Method

`PROOF.md` gives the argument in the standard weighted form: a nonnegative measure on
`Q_L` with total mass under 17 and mass at least 1 in every contained unit-square interior
cannot admit 17 interior-disjoint unit squares.
The finite reduction is the part that carries the work.
A half-tangent net `t_k = k*T/2880` with the fixed rational endpoint `T = 207107/500000`
fixes 2881 directions; the condition `B^2 (1+h)^2 < 1+h^2` makes a closed side-`B` core at
the nearest net angle fit strictly inside the open interior of a unit square at any
intervening orientation, so the gaps between net directions are paid for by an exact
inequality rather than by sampling.
At each direction the translations are reduced exactly to an event arrangement of centre
slabs and cells in rotated coordinates, and the mass is accumulated in integers.

The improvement over the preceding `4.607` package is in the spatial support and its
weights, not in the core side, the direction net or the kernel.
The package reports two exact diagnostics bounding that claim: at `L = 4.61` the older
356-orbit support dictionary needs mass at least `17.009583872717` to cover just 106
specified cores, and deleting the 19 orbits priced during the final stage drops this
certificate’s least core mass to `0.939043209`.
Both are statements about the specified dictionary and the fixed certificate, and the
package says so.

### Checker requirements

Python 3.10 or newer with only the standard library, a C++17 compiler, and Boost headers.
No optimizer and no network.
`python3 certificates/lower_bound_4p613/verify.py --source` compiles both accumulation
backends, runs 13 geometric controls on each, runs eight diagnostic controls, replays the
new certificate, replays the unchanged Levy source data as a further control, and prints
`EXACT_REPLAY_AND_DIAGNOSTIC_PASSED`.
The two backends are a segment-tree engine and a direct-prefix engine that share one
geometric partition, and the package states plainly that their agreement audits weight
accumulation rather than supplying a second independently authored geometric proof.
`exact_sweep.cpp` here has SHA-256
`1bb626a560e3c67620b2aa7851bc467db72b3530f6cae394c1d9d9f034910f4b`, which the package
reports is byte-identical to the `4.607` kernel.

### Upstream credit and licensing

`ATTRIBUTION.md` credits the initial 1184-atom measure to this repository, naming
`packing/cases/n17_fractional_certificate/certificate.json` with git blob SHA-1
`f454e44dee1f2318af45e02efdfff5fcd7dbfbe1` and SHA-256
`461cb731917bdaf7a58f54be651ca2c782bc519790d79d0fe4941c24fdd4c652`, under CC BY 4.0.
That file is retained unchanged in the package as `source/jlevy-certificate.json`, and its
SHA-256 matches this repository’s `T-019` certificate byte for byte, checked here.
The attribution also credits this repository’s `T-022` note for the sharp uniform-dilation
corollary, and credits Sam Burns and Gustavo Massaccesi for the weighted covering
principle and the LP viewpoint, neither of which it claims as new.
Sixteen historical points from `Mira-Cult/17squares` are credited as optional columns in
an exploratory covering LP, not as part of the accepted certificate.

The repository carries no top-level licence file.
The grant that exists is in `ATTRIBUTION.md`: the derived certificate data are offered
under CC BY 4.0 with that attribution, and no endorsement by this repository’s author is
implied.

### Disclosed AI assistance

The paper’s attribution paragraph states that the earlier computation and exposition were
developed with assistance from OpenAI’s GPT-5.6 Pro under human direction, and that the
September patch and this integration also used AI assistance.
`REVIEW.md`, dated 7 September 2026, describes itself as a repository integration review
with AI assistance rather than external peer review or an independently authored second
geometric verification.
`ATTRIBUTION.md` repeats that AI assistance is not independent mathematical peer review.
External peer review is stated as pending.

## Guzhou0806/n17-square-packing: `s(17) >= 461300/99999`

Selected tree of <https://github.com/Guzhou0806/n17-square-packing> at commit
`931a0dfd64302e277057006e99388fe5c00b7f53`, author date 2026-09-20 04:13:50 `+0800`,
“Publish R012 parent-angle lower-bound certificate and public replay”.
Retrieved 2026-09-20.
The repository’s first commit is dated 2026-09-18 01:37:42 `+0800`, which is 2026-09-17
17:37 UTC, and its whole history is six commits.

### What is retained, and what is not

Retained: `certificates/R012/` in full, the top-level `README.md`, `RESULTS.md`,
`NOTICE.md`, `CHANGELOG.md`, `CITATION.cff` and `R012_PUBLICATION.json`, `docs/` in full,
and from `evidence/M19/` only `PROOF.md`, `README.md`, `REPORT.md`,
`FINAL_ACCEPTANCE.json` and `research/m19_work/`.
That is 29 files and 117,934 bytes of the source’s 198 files and 3,025,058 bytes.
Every retained file is byte-identical to the source commit, checked file by file against
the clone.

Not retained, with the reason in each case:

- `archives/M12_global_lower_bound.zip` and `archives/M19_nonuniform_direction_lower_bound.zip`,
  770,805 bytes: zipped duplicates of material that is either retained in expanded form or
  excluded below.
- The rest of `evidence/M19/`, 122 files and 1,556,959 bytes.
  Most of the weight is `research/proofs/M12_global_lower_bound/` and `workers/`, which
  contain copies of this repository’s own `sqpack` sources (`fractional/certificate.py`,
  `fractional/sweep.py`, `fractional/model.py`, `workers.py`), a copy of this repository’s
  `uv.lock`, a copy of the `T-019` certificate, and a copy of the `T-022` dilation note.
  We hold the originals.
- `verification/`, 32 files and 488,934 bytes of the source’s own run logs and coverage
  dumps, together with `RELEASE_MANIFEST.json`, `EVIDENCE_MANIFEST.json`,
  `provenance/INPUTS.json`, `scripts/`, `tests/`, `requirements-optional.txt`, `.github/`,
  `.gitattributes` and `.gitignore`.
- The top-level `verify.py`, 12,451 bytes, which is the M19 verifier rather than the R012
  one. The R012 verifier, `certificates/R012/verify.py`, is retained.

One consequence to know before reading the retained files: relative links in them point at
paths this packet does not hold.
`NOTICE.md` links `evidence/M19/research/proofs/M12_global_lower_bound/`, `RESULTS.md`
links `evidence/M19/research/m14_work/CERTIFICATE.json`, `docs/M19_PROOF_EN.md` links
`verification/PACKAGING_REPORT.md`, `docs/M17_FAILURE.md` links
`evidence/M19/research/m17_work/` and `evidence/M19/workers/`, and
`docs/REPRODUCIBILITY.md` gives M19 commands that use the unretained top-level `verify.py`
and `scripts/source_crosscheck.py`.
All of those resolve at the source commit.

### The claims

R012 claims `s(17) >= 461300/99999`, with the source’s own bracket

```text
4.61304613046130461304 <= 461300/99999 < 4.61304613046130461305,
```

stated explicitly as a bracket on the lower-bound constant and not on `s(17)`.

The measure is fixed: 206 integer `D4` orbit rows in `orbits.json` expanding to 1616
distinct atoms, of total mass `424969/25000 = 16.99876`.
It is Mira’s measure with coordinates rounded to `10^-5`, weights rounded upward to
`10^-6` and coincident points aggregated; the attribution states that and gives the
canonical SHA-256 of the sorted expanded atom table,
`ae469399ced8580ddddcef6edc234cf9becd7e94df7752aa8b4f9cefcbaf3643`.
The container side is `L = 4613/1000` and the parent side is `A = 99999/100000`, so the
claimed constant is `L/A = 461300/99999`.

M19, the earlier milestone, claims
`s(17) >= 45900*sqrt(73062612901466039895961496449)/2702984545455608711`, bracketed by the
source as `4.59004266897263595052 <= S19 < 4.59004266897263595053`.
Its own acceptance record is dated 2026-09-17 13:10:38 UTC and was published in the
repository on 2026-09-18.
`docs/M17_FAILURE.md` retains the negative result it came out of: a proposed uniform
refinement to 361 directions failed at its seventeenth computed direction with captured
mass `197153/200000` against the required `423327/425000`, and M19 keeps only the 16
midpoint directions that had passed, giving a nonuniform 197-direction net over this
repository’s `T-019` atoms.

### Method, for R012

The novelty the source claims is the selector, not the measure.
Instead of requiring one core recipe to work at every orientation, `catalogue.json`
partitions the reduced parent-angle range `[0, T]`, `T = 207107/500000`, into 2925 closed
intervals, and gives each interval its own core direction and core side: 60 explicit
rational entries, then midpoint cells in three bands with core sides `6249/6250`,
`49992449/50000000` and `19997/20000`.
For each interval the checker proves strict containment of the chosen closed core inside
every parent square of side `A` at every angle in that interval, using an exact rational
inequality evaluated at the two endpoints together with a monotonicity argument, so the
interval is covered rather than sampled.
For each interval it then sweeps the whole legal parent-centre envelope, a nested square
`[r, L-r]^2` whose inset comes from the endpoint minimum of an explicit rational function,
by an exact event arrangement in the core frame, recounting atoms at a reconstructed
rational point inside each minimising cell.
Every entry clears the common charge `gamma = 250023/250000`, and the contradiction is
`17*gamma - M = 701/250000 > 0`, with all entries drawing on the same mass budget.

`counterexamples.json` retains five legal parent centres at which specified inferior core
recipes fail, at charges `.988704`, `.999638` and `.998421`.
The source says these refute those core choices and not the parent poses.
`PROOF.md` also compares against Mira’s pinned endpoint by an exact positive rational
squared difference, and says the comparison is against that one named source rather than
an exhaustive record survey.

### Checker requirements

Python 3.10 or newer, standard library only.
No compiler, optimizer, account or network.
`certificates/R012/verify.py` resolves its data relative to its own location, takes
`--workers` and a `--output` directory that must not already exist, and prints
`PASS_COMPLETE_PARENT_CATALOGUE_GLOBAL_LOWER_BOUND` only on a complete run.
`--records` prints `PASS_RECORDS_ONLY` and does not recompute coverage; the source warns
against treating it as a replay, and against `-O`, `-OO` or `PYTHONOPTIMIZE`.
`certificates/R012/MANIFEST.json` covers the ten files of the R012 package, and all ten
hash-match here.

### Upstream credit and licensing

`certificates/R012/ATTRIBUTION.md` credits Mira’s `17squares` at the pinned commit
`0266c993` for the spatial support, weighted certificate and comparison endpoint, and
credits this repository at pinned commit `fb14f5174fdf675b296b442c98b7127fccc8a84d` for
weighted covering, exact event sweeps, interior-core counting and dilation, naming the
`n11_five_dot_cover` parent-centre contract as prior work for parent-aware domains.
Both pinned commits exist: `0266c993` is the Mira commit archived here, and `fb14f517` is
in this repository’s history, dated 2026-09-17.
`NOTICE.md` credits this repository for M19’s atoms, source algorithm and dilation
argument at pinned commit `035d84c655b4047bc9986c9a3db5106780d92f77`, also a real commit
here, dated 2026-09-16.

There is no repository-wide licence.
`certificates/R012/LICENSE-MIT.txt` is this repository’s own MIT notice, retained because
`sweep.py` descends from this repository’s MIT-licensed code, and it covers that code
only.
`NOTICE.md` sets the boundaries explicitly: MIT for the code of that lineage, CC BY 4.0
for the Levy-origin non-code material, no blanket re-licensing of the repository, and no
redistribution of Mira’s C++ because its terms were not established.
That is why the Python replay exists at all: it re-encodes the same mathematical object
rather than shipping the original mixed-language package.

### Disclosed AI assistance

The README, `NOTICE.md` and `certificates/R012/ATTRIBUTION.md` all attribute the work to
“Guzhou0806 / N17 project, with AI assistance”.
The repository states repeatedly that it asserts no optimality, no new packing, no
external peer review, no formalization and no public priority, and that re-execution in
another language and per-witness cross-checks are not an independently designed second
geometric proof.

## Replay here

Two first-party instruments live beside this README, and their receipts in `receipts/`.
Neither is the source’s own checker: each is this repository’s own harness around the
retained bytes.

- `replay_mira_4613_first_party.py` — Mira’s `4.613` package.
  Replay result: recorded in the frontier evidence register.
- `replay_guzhou_r012_first_party.py` — Guzhou0806’s R012 package.
  Replay result: recorded in the frontier evidence register.

The R012 package also ships its own replay entry point, which needs nothing beyond the
standard library and so runs under the project interpreter.
From `packing/`:

```bash
uv run --frozen python -X utf8 -B -S \
  resources/web/n17-weighted-certificates-2026-09-20/guzhou0806-n17-square-packing/certificates/R012/verify.py \
  --workers 4 --output <new directory>
```

The output directory must not already exist.
The source’s own instructions give the same command as
`python -X utf8 -B -S certificates/R012/verify.py --workers 4 --output <new dir>` from its
repository root; the verifier resolves its data from its own path, so the location of the
command does not matter.

That replay was run here on 2026-09-20 under Python 3.14.7 and passed.
It recomputed all 2925 parent-angle intervals over their full centre envelopes on 8
workers, reported a catalogue minimum charge of `250023/250000` over 9,231,165 centre
strips, and printed `PASS_COMPLETE_PARENT_CATALOGUE_GLOBAL_LOWER_BOUND` in 340 s.
The minimum it reports equals the `gamma` the proof requires, exactly.
Receipts are `receipts/guzhou-r012-source-replay-2026-09-20.log`,
`receipts/guzhou-r012-source-replay-2026-09-20.result.json` and
`receipts/guzhou-r012-source-replay-2026-09-20.coverage.jsonl.xz`.
This is the source’s own checker accepting the source’s own bytes under a different
interpreter: it is evidence that the published package runs and is internally consistent,
not an independent verification of `461300/99999`.

Mira’s `4.613` package needs a C++17 compiler and Boost headers for its two accumulation
backends, which is the same obstacle the earlier packet recorded for three of its stages.

## Evidential status

Everything in the two sections above is **source-reported**: it is what the retained files
say, checked for internal consistency against each other and against the source commits,
not a verification of either bound.
What this packet has checked directly is narrow and worth separating out:

- Every retained file is byte-identical to its source commit.
- Mira’s `MANIFEST.sha256.json` holds for all 55 of its non-`search/` entries, and names
  38 `search/` files this packet does not retain.
- `certificates/R012/MANIFEST.json` holds for all ten of its entries.
- The `T-019` certificate retained inside Mira’s package as `source/jlevy-certificate.json`
  is byte-identical to this repository’s
  `packing/cases/n17_fractional_certificate/certificate.json`.
- `certificates/lower_bound_4p468292/` is unchanged between Mira’s August commit
  `0872d3ac` and the September commit archived here.
- The two commits of this repository that Guzhou0806 pins, `fb14f517` and `035d84c6`,
  exist in this repository’s history.
- R012’s own checker was run here on 2026-09-20 and passed, on all 2925 intervals, under
  an interpreter the source never used. That is a **replayed-here** result about the
  source’s program, and it is the only computation in this packet that has been run.

Neither `4.613028635886` nor `461300/99999` is verified here.
A source’s own checker accepting its own bytes does not make its bound this repository’s,
and nothing in this packet changes this repository’s verified lower bound.

## Retrieval hashes

[`retained-files.sha256`](retained-files.sha256) carries the SHA-256 of every retained
file in this packet, as packet-relative paths, in `sha256sum` format.
It is named for what it holds: unlike the earlier packet’s
`raw-hashes-of-compressed-files.sha256`, nothing here was compressed, so there is no raw
form to record separately.
Check it from this directory with `shasum -a 256 -c retained-files.sha256`.
The two first-party replay scripts and `receipts/` are deliberately outside it, since they
are this repository’s own output rather than retained source bytes.

The few hashes worth having in prose, all of them the sources’ own published values and
all checked against the retained bytes:

| File | SHA-256 |
| --- | --- |
| `mira-17squares/certificates/lower_bound_4p613/best-certificate.json` | `749f13335980a66a27a2304f212b5d8796390c81b962149647a4d9ff43a228ec` |
| `mira-17squares/certificates/lower_bound_4p613/exact_sweep.cpp` | `1bb626a560e3c67620b2aa7851bc467db72b3530f6cae394c1d9d9f034910f4b` |
| `mira-17squares/certificates/lower_bound_4p613/source/jlevy-certificate.json` | `461cb731917bdaf7a58f54be651ca2c782bc519790d79d0fe4941c24fdd4c652` |
| `guzhou0806-n17-square-packing/certificates/R012/sweep.py` | `96efe91895ab14d80c6b7162aee91d4687e5d11a60093a9935043a88d4713965` |
| `guzhou0806-n17-square-packing/evidence/M19/research/m19_work/CERTIFICATE.json` | `4326a84caec0a60c0f70226c7a79bf4bbede2d1c032af8ca2aef319d2c91c806` |

Retained for private research use.
Consult the authors before redistribution.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
