# Review: Derived-Artifact Currency on `main` at `9fe9999d`

Reviewed 2026-09-21 in Session 150, read-only, immediately after the agenda-040 stack
(PRs 204–209) merged.
The question is narrow: is every **derived** artifact on `main` current with the source
it is derived from?

Nothing in the repository was written while this ran, and no git state-changing command
was run against `/home/user/squares`. Every measurement below was taken against a
detached read-only clone at `9fe9999d`, for the reason given under “How this was run” —
the working tree was mid-merge at the time and would have reported conflict markers as
record drift.

**This is a dated record, not a live status page.** `main` has since advanced past
`6eb69761`, which carried PR 211 and `T-032`, to `beee2e0f`, which carries `OR-17` from
PR 212 and the retained Kleddamag artifact from PR 213. Two things in this report
therefore have a known successor state, and both are flagged where they appear: finding
1, the ⚠️ banner in the Bentz 2016 transcription, was still live on `main` at the moment
of the audit and is tracked separately; and the section “Will go stale when the n = 17
work lands” describes a branch that has since merged, so read it as the diff it
predicted rather than as pending work.

## Headline

**Main is current, with one exception.** Every generated Markdown view, every register,
every generated figure, every census and the whole document map re-derive byte-for-byte
from their sources. `packing-validate --records --jobs 1` passes, 34 of 34 selected
steps, exit 0. `packing-validate --fast --jobs 2` reports 4 failing steps, and every one
is an artifact of auditing from a clone of a **shallow** repository — run down
individually below, and contradicted by CI’s own green push-to-main run 35632073093.

The one stale artifact is the ⚠️ banner inside
`packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md`: it still declares
**7** annotated passages where the file now carries **9**, and where the archive census
in `packing/resources/README.md` already says 9. The agenda-040 stack put it there.
Nothing in the repository checks that number, which is why a full stack merge, a records
tier and a fast tier all went past it.

## How this was run, and one thing the caller should know first

`/home/user/squares` **is not on main and is not clean.** It sits on
`claude/n17-mira-guzhou-4613-intake` at `ecce10da`, in the middle of an unresolved merge
of `9fe9999d` (`.git/MERGE_HEAD` = `9fe9999d`), with 198 changed paths and **7 files
still carrying conflict markers**:

```
SYNOPSIS.md
docs/project/specs/active/plan-2026-08-23-overnight-cartography-run.md
packing/campaign/ledger.md
packing/campaign/session-close-report.yaml
packing/devtools/controls.yaml
packing/frontier/INVENTORY.md
packing/frontier/results.yaml
```

Any gate run in that tree would have reported conflict markers as record drift.
So the audit was done against a throwaway read-only clone at the real main tip:

```bash
git clone --shared --no-checkout /home/user/squares <scratch>/mainwt
git -C <scratch>/mainwt checkout --detach 9fe9999d     # clean tree, origin/main == 9fe9999d
```

**Update, end of the audit:** another agent finished that merge while this ran.
The tree is now clean at `4479f2f5` on the same branch, `9fe9999d` is an ancestor of it,
and the seven conflicts are resolved.
Nothing in this report was affected — every measurement was taken against the clone, at
the main tip, and none of it was read from the working tree.

with the project venv symlinked in and `PYTHONPATH` pointed at the clone so every import
resolves there rather than at the working tree.
Verified before running anything:

- `sqpack.__file__` → `<scratch>/mainwt/packing/src/sqpack/__init__.py`
- `configured_project_root()` → `<scratch>/mainwt/packing`
- `devtools.__file__` → `<scratch>/mainwt/packing/devtools/__init__.py`

`packing/src/sqpack/**` and `packing/sqsearch/**` are byte-identical between the working
tree and `9fe9999d`, so the editable install and the prebuilt Rust engine are main’s
code.

## Prioritised findings

| # | Artifact | What is stale / missing | Evidence | Fix |
| --- | --- | --- | --- | --- |
| 1 | `packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md` | Its own ⚠️ banner says **7** annotated passages; the file has **9**; `resources/README.md` says **9**. **Stale on main now.** | Per-commit trace below | Edit the banner line to `**9**` (hand edit — there is no generator) |
| 2 | The archive annotation census as a whole | **No gate checks it at all.** Neither the per-file ⚠️ count nor the `resources/README.md` table has a checker anywhere in `devtools/`, `tests/` or `.github/`. This is why #1 survived. | `grep -rln "annotated passage" devtools/ tests/ src/` → no match | Build the checker (OR-1); wire into the records tier |
| 3 | `devtools.report_math_startup --check`, `benchmarks.validation_report --check` | Both drift-check a generated view; **neither is wired into any `packing-validate` tier or CI workflow.** Both currently pass. | `grep -rn "report_math_startup\|validation_report" packing/src .github Makefile` → only unit tests | Add both to the records tier |
| 4 | `devtools/check_generated_markdown.py` | Matches its own `BANNER` constant case-sensitively. `docs/tbd/README.md` writes that banner in lower case and is **not** in `.flowmarkignore`, so the checker cannot see it. **Latent, not live.** | Flowmark 0.4.0 on a copy leaves the file byte-identical | Case-fold `BANNER`, or add the file to `.flowmarkignore` |
| 5 | `compound-perfect-squared-squares-1303.0599` | Banner 10, README 10, actual markers 9. **Pre-existing** (last touched `af1dffb1`, 2026-09-08) — not stack-induced. | Marker count below | Resolve when #2 is built |
| 6 | `bentz-2010-optimal-packings-13-and-46` | Banner 1, README 1, actual markers 2. The second is an audit note rather than an extraction annotation, so this may be correct as written. **Pre-existing.** | Marker count below | Decide the counting rule when #2 is built |
| 7 | `docs/project/document-map.yaml` | `last_reviewed: 2026-09-14` predates the stack (2026-09-20/21). Cosmetic — every path, lifecycle and collection resolves. | Recomputed below | Bump on next map pass |

Nothing else is stale.
Items 2–4 are detector gaps, not drift; items 5–7 are cosmetic or pre-existing.
**Only item 1 is drift introduced by the agenda-040 stack.**

Finding 4 has a postscript, found while landing this document rather than while auditing
main. The first draft quoted the banner constant’s value verbatim, which made
`check_generated_markdown` classify this review as a generated view and demand that it
be exempted from the Markdown formatter.
The cell above therefore names the constant rather than quoting it.
That is a second and milder instance of the same detector gap: the check decides what a
document is from a string anywhere in its bytes, with no regard for whether the string
is a banner or a quotation of one.

## 1. Generated Markdown and registers — all current

Two independent methods agree.

**Check mode.** Every generator with a `--check`, run against the clone:

| Generator | Result |
| --- | --- |
| `devtools.render_defects --check` | `defects.md matches defects.yaml (507 defects)` |
| `devtools.render_results --check` | `packing/frontier/RESULTS.md agrees with results.yaml` |
| `devtools.render_agenda_map --check` | `matches 356 commitments across 37 agendas` |
| `devtools.render_certificate_reach --check` | clean, exit 0 |
| `devtools.render_research_tables --check` | `6 generated report tables and frontier/STATUS.md match frontier/ (400 data rows)` |
| `devtools.render_evidence_inventory --check` | `inventory agrees with 85 evidence records` |
| `devtools.render_document_map --check` | `synopsis document map matches docs/project/document-map.yaml` |
| `devtools.render_operating_rules --check` | `AGENTS.md mirrors all 16 rules in operating-rules.md` |
| `devtools.render_results_headline --check` | `synopsis headline carries all 31 registered results` |
| `devtools.render_verifiable_claim --check` | `the verifiable-claim documents and the proof card are current` |
| `packing-ledger check` | `OK 1 series, 38 reports, 170 hypotheses, 155 rounds, 148 agent sessions, 37 agendas, 2 logbook entries` |
| `devtools.close_session --check` | `148 terminal sessions: 94 declare rollups that exist, 10 explicitly unmeasured, 44 predate the requirement` |
| `devtools.check_generated_markdown` | `every generated view is exempt from the Markdown formatter` |
| `devtools.check_synopsis` | `SYNOPSIS.md agrees with the artifacts, the ledger and the defect log` |
| `devtools.check_documentation` | `documentation map covers 1401 durable documents; footers and links resolve` |
| `devtools.report_math_startup --check` | clean, exit 0 (**not gated — finding #3**) |
| `benchmarks.validation_report --check` | clean, exit 0 (**not gated — finding #3**) |

**Write mode, the stronger test.** Every generator was then run in *write* mode inside
the clone and the tree diffed against the commit.
This catches a `--check` that has silently drifted from its own writer:

```
packing-ledger render; render_defects; render_results --update; render_agenda_map;
render_certificate_reach; render_research_tables; render_evidence_inventory --update;
render_document_map; render_operating_rules; render_results_headline;
render_verifiable_claim; report_math_startup; benchmarks.validation_report;
cases.stromquist.five_point_obstruction
→ git status --porcelain --ignore-submodules=all
→ (empty)
```

Zero bytes changed. Every generated view on main reproduces exactly.

Note: `packing-ledger render --check` is not a flag — the check mode is the separate
subcommand `packing-ledger check`. Worth knowing if a runbook says otherwise.

The one generated file with no checker **by declaration** is
`packing/atlas/known-best/video/spikes/v2-transitions/stats-summary.md`, whose banner
says so: frozen at `0281a508`, nothing rebuilds or checks it.
That is a recorded decision, not drift.

## 2. SVGs and figures — all current, including the un-sampled ones

The repository holds 360 SVGs.
20 are ours and generated; the rest are the literature archive under
`packing/resources/` (third-party), plus one workbench test fixture.

The structural risk here is real and worth naming: **the gate only samples the atlas.**
`known-best atlas records and sample` runs `build_known_best_atlas --check --sample` —
every Nth case — because the full rebuild measured 691.19 s of a 703.28 s step and was
moved to the deferred surface.
So on a pull request, an un-sampled `n` can drift unseen.

I ran the full rebuild anyway.
It passes:

```
python3 -m devtools.build_known_best_atlas --check
→ known-best atlas check passed: 324 sources/plans, witnesses, renders, 2 composites, and links
→ EXIT=0
```

That covers all 324 `packing/atlas/known-best/rendering/n-*.svg` and both composites.
The rest:

| Figure(s) | Generator | Data it reads | Drift-checked by | Result |
| --- | --- | --- | --- | --- |
| `atlas/known-best/rendering/n-001..324.svg` (324) | `build_known_best_atlas` | `atlas/known-best/` sources + `witnesses/known-best/` | sampled in fast tier; **whole** only on deferred surface | pass (full run) |
| `known-best-1-100.svg`, `-1-324.svg` + 4 PNG + 2 PDF | `build_known_best_atlas`, `build_composite_figure_data`, `render_composite_pdf` | `composite-figure.json`, frontier, catalogue | `known-best atlas records and sample` (fast) | `composite figure record check passed`; `known-best-1-100.pdf` and `-1-324.pdf` match their SVGs |
| `atlas/known-best/contact-overlays/n-{011,028,040,068,089}.svg` | `render_known_best_contact_overlays` | calibration strata | same step | `5 house-rendered calibration strata` |
| `atlas/known-best/evidence/non-grid-chunk-evidence-profile.svg` | `profile_known_best_chunks` | 36 non-grid calibration cases | same step | pass |
| `atlas/enumerated/rendering/contact-scaffolds-size5-overview.svg` | `build_contact_scaffold_atlas` | enumerated orbits | `abstract size-five contact-scaffold atlas` (fast) | `21 topologies, 11013 abstract orbits` |
| `atlas/prospective/source-coverage-101-324.svg` | `map_prospective_sources` | `resources/web/` availability | `prospective n=101..324 source map` (fast) | `224 cases, availability and SVG` |
| `atlas/rendering/{trump11,kingbird29,gobel10,n5-exact-face-trajectory}.svg` + `atlas/n-003-optimal-moduli.svg` | `render_packing_gallery` / `render_packing_svg` | built-in sources, `exp-014` replay | `deterministic SVG rendering`, `cases.small_n.optimal_moduli --check-svg` | `SVG GALLERY CHECKED: 5 examples` |
| `cases/n11_fractional_certificate/t-018-proof-visual.svg` | `render_t018_proof_visual` | `certificate.json` | fast tier | `T-018 PROOF VISUAL CHECKED` |
| `cases/stromquist/five-point-obstruction.svg` | `cases.stromquist.five_point_obstruction` | its own `.json` | unit test on the JSON | regenerated in clone → identical |
| `campaign/.../agenda-032/four-owner-five-dot.svg` + `.png` | `render_owner_five_dot_figure` | retained agenda-032 sources | fast tier | `matches the retained sources` |
| `witnesses/schadt-n029-2025-decimal.svg` | `packing-witness inspect --svg` | `schadt-n029-2025-decimal.yaml` | **no gate found** | regenerated → byte-identical |

Plus `devtools.check_svg_rendering --check` →
`SVG RENDERING CHECKS PASSED: 90 controls`.

**Did the stack move any figure’s source data?** No.
The stack’s records are lower-bound work (`T-031`, `H-222`…`H-232`, `X-040`). The
known-best atlas renders *upper-bound constructions*, which did not move.
Confirmed by the full rebuild passing unchanged.

**On the explainer / certificate page.** There is nothing to go stale:
`render_explainer` writes to `packing/site/index.html`, and `/packing/site/` is
gitignored — the page is rebuilt on every run and never committed.
The `explainer-unchanged` job in `.github/workflows/pages.yml:181` is a **skip-notice
job**, not a drift check: it fires only when `scope.outputs.explainer != 'true'` and
just prints why the explainer was not built.
What matters for the page is its *inputs* — the composite SVG/PNG/PDF — and those are
verified above.

## 3. Cross-record consistency

```
packing-validate --records --jobs 1
→ 34 of 81 STEPS PASSED (a named tier; this is not the full gate)
→ EXIT=0
→ 70.17s wall of a 300s ceiling (23%)
```

Every step passed. No failing step to report verbatim.
The only notes emitted were advisory and are recorded policy, not drift:

- Two pull-request walls (`packing-validation`, `certificate-page`) are **advisory under
  live bead `think-g4n9`** — reported, not enforced, by owner decision 2026-09-17.
- `session-044` phase 7 starts before phase 6 — a delegated lane in a worktree does this
  legitimately.
- 17 terminal sessions are `UNCHECKABLE` for gate ancestry because the clone is shallow.
  That is a fact about the checkout, not about the sessions.
- 5 stopped sessions remain uncertified with named follow-up owners (`think-ta8s`,
  `think-g4n9`, `think-qqzs`).
- The records tier has no recorded cost at this run’s shape, so its band was reported
  and not enforced.

**On the known `attic/` issue.** It did **not** fire.
Run in the real working tree, `python -m devtools.check_readme` returns
`README.md agrees with the directory, reports, defect and result sources, work model and
its own links`, exit 0. The bead is `is-01m2qmg9avc4a8yvkg5tvbn8vr` ("check_readme scans
the gitignored attic for retired workflow identifiers"); `attic/` currently holds
`17-squares-certified-bound`, which contains no retired workflow identifier.
The bug is real and still open, but it is latent today and is **not** masking any drift.

### `packing-validate --fast --jobs 2`

```
1080.30s TOTAL (wall); 4 STEPS FAILED; EXIT=1
  - workbench browser behavior in Chromium
  - fast behavioral tests, shard A
  - fast behavioral tests, shard B
  - provenance: recorded commits are reachable
```

**All four are artifacts of auditing from a clone.
None is drift on main.** Each is run down below, and the decisive external evidence is
CI’s own push-to-main run **35632073093** (the predecessor commit `6fcd06b9`), whose
full `packing-validate` job `validate` concluded `success`.

**1. `provenance: recorded commits are reachable`** — the interesting one, because it
looks real until it is chased down.

```
exp-002-baseline-n10-positive-control.md: engine commit 1e70bc8 is unavailable in local history
```

`_commit_state` (`validate.py:3047`) tests `git merge-base --is-ancestor <commit> HEAD`.
Locally `1e70bc8` resolves unambiguously to `1e70bc8223136d8dab605ee5b73edc3a0956a144`
("stack: price the pipeline, then put Python first", 2026-08-22), which is **not** an
ancestor of `9fe9999d`, and `exp-002` has no `## Annotation` section to excuse it.
That reads exactly like a real orphaned-provenance failure.

It is not. **`/home/user/squares` is a shallow repository** — `.git/shallow` exists and
`git rev-parse --is-shallow-repository` returns `true` — so main’s history is truncated
locally and the graph path from `9fe9999d` back to `1e70bc8` is cut at the shallow
boundary. With full history, CI prints:

```
== provenance: recorded commits are reachable ==
  UNAVAILABLE exp-001-baseline-sweep.md -> d6a1057 (historical loss is annotated)
  ok          exp-002-baseline-n10-positive-control.md -> 1e70bc8
  ok          exp-003-baseline-n11-target.md -> 1e70bc8
  ok          exp-004-baseline-n12-negative-control.md -> 1e70bc8
```

The same shallow boundary is why the records tier reported 17 sessions as
`UNCHECKABLE here (shallow checkout)`, and it is why `git fetch --unshallow` is the
remedy the tool itself names.

**2. `workbench browser behavior in Chromium`**

```
ValueError: could not determine whether the workbench source is dirty
  workbench_tools/build_site.py:177 in source_dirty()
```

Self-inflicted: I had copied the `vendor/kpress` submodule contents over its gitlink,
which made `git status --porcelain` exit 128 across the whole clone.
Removing the stale `vendor/kpress/.git` pointer restored `git status` to exit 0.
(Separately, Playwright’s browsers are not installed here, so the Chromium half could
not have run regardless.)

**3–4. `fast behavioral tests, shard A` / `shard B`** — 11 failures and 110 errors, and
every one traces to git history the shallow clone does not have:

| Test | Cause |
| --- | --- |
| `test_read_fixed_core_calibration_profile.py` (110 errors) | fixture runs `git cat-file --batch` at `EXECUTION_REVISION`; the revision is absent, so the batch reply has 2 fields not 3 |
| `test_release.py::test_the_revision_names_a_commit_this_repository_has` | `git cat-file -t 277f8b1a` → `fatal: Not a valid object name`. Confirmed absent from `/home/user/squares` too — it is the shallow cut, not the clone |
| `test_release.py::test_the_revision_is_the_length_this_repository_abbreviates_to` | asserts 8 == 9; `git rev-parse --short HEAD` yields 9 characters in a clone with a different object count. Purely environmental |
| `test_review_trump_local_theorem.py` (2) | git content binding to an absent revision |
| `test_fixed_core_packet*.py` (2), `test_math_startup.py` (2), `test_prepare_explainer_math.py`, `test_rounded_measure_audit.py`, `test_segment_cover_replay.py`, `test_capture_and_export.py` | same family: `git status` / recorded-revision lookups |

After repairing the submodule pointer, 36 of the re-run tests passed and the residue is
exactly the revision-dependent set above.

**No step failed for a reason that implicates main.** The budget notes are also
advisory, not failures: the tier ran 1080.30 s against a 600 s ceiling, reported and not
enforced because this run’s shape (4 cpus, `--jobs 2 --inner-jobs 1`) is not the tier’s
declared reference (4 cpus, `--jobs 3 --inner-jobs 1`), and two shards are 88.7 per cent
of it on a box also running this audit’s other jobs.

CI’s run for `9fe9999d` itself (**35633611751**) was still `in_progress` at the time of
writing, with `macos-portability` already green.

## 4. Census and counts — every one recomputes

`SYNOPSIS.md` lines 144–151, against the artifacts, recounted by hand:

| Row | SYNOPSIS | Recomputed | Source |
| --- | --- | --- | --- |
| Agendas | 37 | 37 | `ls packing/campaign/agendas/*.md` |
| Commitments | 356 | 356 | `render_agenda_map --check` |
| Sessions | 148 | 148 | 149 files − `README.md` |
| Explorations | 38 | 38 | `ls packing/campaign/explorations/*.md` |
| Hypotheses | 170 | 170 | `ls packing/campaign/hypotheses/*.md` |
| Experiments | 155 | 155 | `packing-ledger check` |
| Frontier results | 31 | 31 | `T-001`…`T-031` in `frontier/results.yaml` |

Every breakdown sums to its total: agendas 17+14+5+1 = 37; sessions 90+58 = 148;
explorations 24+14 = 38; hypotheses 29+31+55+17+5+29+2+2+0 = 170.

Defect census (SYNOPSIS lines 5081–5117), recomputed straight from `defects.yaml`:

| Claim | SYNOPSIS | Recomputed |
| --- | --- | --- |
| total | 507 | 507 rows, and the file’s own `count:` field is 507 |
| soundness | 103 | 103 |
| validity | 127 | 127 |
| bookkeeping | 190 | 190 |
| robustness | 68 | 68 |
| performance | 19 | 19 |
| “79 of the 103 soundness defects pointed in the flattering direction” | 79 | 79 |
| “the automated gate has caught eighty defects in 507” | 80 | `detected_by == 'gate'` → 80 |
| “and no soundness defect ever” | 0 | soundness ∧ gate → 0 |

Classes sum to 507. `D-505`, `D-506`, `D-507` are all present.

**Archive annotation census — `packing/resources/README.md`.** This is where the one
real finding is. Counting `<!-- GARBLED` / `<!-- NOTE` occurrences per file:

| File stem | Own ⚠️ banner | Actual markers | README table |
| --- | ---: | ---: | ---: |
| `arslanov-improved-packings-n-n-1` | 1 | 1 | 1 |
| `bentz-2010-optimal-packings-13-and-46` | 1 | **2** | 1 |
| **`bentz-2016-optimal-packings-22-and-33`** | **7** | **9** | **9** |
| `compound-perfect-squared-squares-1303.0599` | 10 | **9** | 10 |
| `erdos-graham-1975-on-packing-squares-with-equal-squares` | 17 | 17 | 17 |
| `friedman-ds7-packing-unit-squares-in-squares` | 3 | 3 | 3 |
| `kearney-shiu-2002-efficient-packing-unit-squares` | 1 | 1 | 1 |
| `mcclenagan-2026-optimally-packing-large-square` | 2 | 2 | 2 |
| `square-packing-x06-wasted-area-2508.04603` | 6 | 6 | 6 |
| `stromquist-2003-packing-10-or-11-unit-squares` | prose: “Three” | 0 | 3 |

`stromquist-2003` is correct as written — it annotates in prose, not HTML comments.

The `bentz-2016` row is drift, and the stack caused it.
Per-commit trace:

| Commit | Banner | Markers | README |
| --- | ---: | ---: | ---: |
| `fb6be453` (before the stack) | 3 | 3 | 3 |
| `3dc129e0` (stack: X-040, agenda-040, Bentz transcription repair) | 7 | 7 | 7 |
| `2aef9421` (stack: chunk-1 verdicts, one-spare inventory port) | **7** | **9** | **9** |
| `9fe9999d` (main tip) | **7** | **9** | **9** |

`3dc129e0` updated all three together.
`2aef9421` added the eighth and ninth annotations — the factor-2 repair to the Theorem 9
budget line (this is `D-507`) and the case-2 end-point note — updated the README census
to 9, and left the file’s own banner at 7.

The n=17 branch has not fixed it either: the working tree copy also reads 7 with 9
markers.

Fix (hand edit; there is no generator for this banner):

```
packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md, line 13
-> This transcription contains **7** annotated passage(s) where the PDF extraction was
+> This transcription contains **9** annotated passage(s) where the PDF extraction was
```

Note that `.flowmarkignore` excludes `packing/resources/`, so this edit will not be
reformatted — but it also means the commit hook will not touch it, and nothing will
warn.

## 5. Document map — clean

`docs/project/document-map.yaml`, recomputed:

- 507 document entries; **0 paths that do not resolve**
- 0 entries without a `lifecycle`
- 180 entries with `role: review`; **0 reviews without a lifecycle**
- lifecycle spread: retained 402, maintained 53, transient 23, superseded 15, generated
  14
- 10 collection patterns; **0 that match nothing**
- `render_document_map --check` → the SYNOPSIS map block matches the YAML
- `check_documentation` → `documentation map covers 1401 durable documents`

Everything the stack added is mapped — spot-checked `agenda-040`, `session-143`,
`session-148`, `X-040`, `H-222`, `H-232`, `frontier/n-011.md`: all exist, all covered by
an entry or a collection pattern.

Only nit: `last_reviewed: 2026-09-14` predates the stack.

## 6. Link integrity — zero broken links

An independent sweep (GitHub’s slug rule: lowercase, strip non-alphanumerics, spaces →
`-`, no collapsing of consecutive hyphens — the naive collapsing variant produces four
false positives on headings containing `=` or an em dash):

| Surface | Documents | Broken |
| --- | ---: | ---: |
| Reader tier: `README.md`, `TUTORIAL.md`, `SYNOPSIS.md`, `conventions.md`, `development.md`, `defects.md`, `AGENTS.md`, `operating-rules.md`, `epistemics.md` | 9 | **0** |
| Newly merged records: agenda-040, X-040, all hypotheses, all agent sessions, `n-011.md`, `n-017.md`, `RESULTS.md`, `STATUS.md`, `INVENTORY.md`, `CERTIFICATE-REACH.md` | 327 | **0** |
| `docs/project/**` | 176 | **0** |

512 documents, both file targets and heading anchors, zero broken.
Consistent with `check_documentation` ("footers and links resolve", 1401 documents) and
`check_synopsis` check 8.

## Will go stale when the n=17 work lands

Distinct from anything above: the external n=17 bound `461300/99853` is on
`claude/n17-mira-guzhou-4613-intake`. Diffing that branch against `9fe9999d` shows
exactly what it moves.

**Figures — the composites only, and all nine move together:**

```
packing/atlas/known-best/composite-figure.json
packing/atlas/known-best/known-best-1-100.svg / .png / @2x.png / -card.png / .pdf
packing/atlas/known-best/known-best-1-324.svg / .png / .pdf
```

**Not** the 324 per-n renderings —
`git diff --name-only 9fe9999d -- packing/atlas/known-best/rendering/` returns **0
files**. That is the right shape: a lower bound moved, the known-best packing did not,
and only the composites annotate bounds per `n`.

**Records and prose:** `packing/frontier/{results,evidence}.yaml`, `n-017.md`,
`n-018.md`, `RESULTS.md`, `STATUS.md`, `INVENTORY.md`, `CERTIFICATE-REACH.md`;
`SYNOPSIS.md`, `README.md`, `defects.md`, `docs/project/document-map.yaml`;
`packing/campaign/{ledger.md,session-close-report.yaml}`.

**Code and controls:** `packing/devtools/controls.yaml`, `check_rung_figures.py`,
`audit_ds7_lower_bounds.py`, and
`packages/workbench/tools/workbench_tools/check_layout.py` (the “star the n=18 stage”
change, `48a3ad23`).

All of these are already regenerated on that branch.
The regeneration command for the composites, when the merge is resolved, is:

```bash
# from packing/
uv run --frozen --all-extras --group dev python -m devtools.build_composite_figure_data
uv run --frozen --all-extras --group dev python -m devtools.build_known_best_atlas
uv run --frozen --all-extras --group dev python -m devtools.render_composite_pdf
```

**The merge itself is the near-term risk, not staleness.** Four of the seven conflicted
files are generated views or registers (`ledger.md`, `session-close-report.yaml`,
`INVENTORY.md`, `results.yaml`). Those must be resolved by regenerating from the merged
sources, never by hand-editing the conflict — hand-resolving a generated view is what
`check_generated_markdown`’s docstring records as `D-027`.

## What could not be verified in this environment

Stated so a clean result above is not read as broader than it is:

- **Browser-dependent gates did not run.** Playwright browsers are not installed
  (`Executable doesn't exist at /opt/pw-browsers/chromium_headless_shell-1234/...`), so
  `check_motion_lab_pages`, `check_frontend` in Chromium, `check_print_layout`, the
  typography and font-loading checks, and the whole `pages.yml` browser surface are
  unverified here. CI covers them.
- The `workbench_tools` editable install points at the working tree, whose
  `check_layout.py` differs from main by the n=18 change.
  Irrelevant to every check reported above, none of which imports it.
- **`/home/user/squares` is a shallow repository.** Every check that resolves a recorded
  historical revision — the provenance step, `test_release.py`,
  `test_read_fixed_core_calibration_profile.py`, `test_review_trump_local_theorem.py`,
  and gate-ancestry for 17 terminal sessions — cannot be decided here and is decided by
  CI. `git fetch --unshallow` is what would make them checkable locally.

## Appendix: commands

```bash
# records tier (passed, exit 0, 34/34 steps, 70.17s)
packing-validate --records --jobs 1

# full atlas, the deferred check the PR surface only samples (passed)
python3 -m devtools.build_known_best_atlas --check

# generated views, check mode and then write-mode-and-diff
python3 -m devtools.render_{defects,results,agenda_map,certificate_reach,research_tables} --check
python3 -m devtools.render_{evidence_inventory,document_map,operating_rules} --check
python3 -m devtools.render_{results_headline,verifiable_claim} --check
packing-ledger check ; python3 -m devtools.close_session --check
python3 -m devtools.{check_generated_markdown,check_synopsis,check_documentation}

# figures
python3 -m devtools.check_svg_rendering --check
python3 -m devtools.{build_composite_figure_data,render_composite_pdf} --check
python3 -m devtools.{render_known_best_contact_overlays,profile_known_best_chunks} --check
python3 -m devtools.{build_contact_scaffold_atlas,map_prospective_sources,build_prospective_atlas} --check
python3 -m devtools.{render_t018_proof_visual,render_owner_five_dot_figure,render_packing_gallery} --check
packing-witness inspect witnesses/schadt-n029-2025-decimal.yaml --svg /tmp/x.svg

# the one fix
#   packing/resources/papers/bentz-2016-optimal-packings-22-and-33.md line 13: **7** -> **9**
```

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
