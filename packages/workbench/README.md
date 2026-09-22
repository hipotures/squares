# Square-packing workbench

This package owns the workbench’s typed browser modules and Python adapters.
The
[workbench plan](../../docs/project/specs/active/plan-2026-09-11-workbench-from-spike-to-product.md)
defines the finished product and migration phases; the
[review](../../docs/project/reviews/review-2026-09-12-workbench-stack-architecture.md)
tracks repairs and their evidence.

The package builds a self-contained Animate, Pack and experimental Search page, opening
on Animate. Pack has its own seeded, arbitrary-count session, snapshot import/export and
bounded overlap repair.
Animate retains the catalogue and animation studio.
Search runs a bounded browser preview and can export and resume exact-plan ledgers; its
wider scheduler, calibration and research acceptance remain open in the plan.
The checked JavaScript application is still large, and its historical pair-based Pack
path needs retirement after the remaining consumers migrate.
The source, probes, build tools and workbench-specific Python adapters now live in this
package.

## Development

Use Node 24 (the baseline is pinned in the repository’s `.node-version`) and the
repository’s Python 3.14 environment.
From the repository root:

```bash
npm ci
npm run check --workspace @squares/workbench
```

The package check builds the browser and benchmark bundles, runs Biome and the
type-aware promise floor, type-checks the modules, and runs the Node contract tests.
Python adapters are installed with the repository’s `workbench` extra.
From `packing/`:

```bash
uv run --frozen --all-extras --group dev python -m pytest ../packages/workbench/tests
uv run --frozen --all-extras --group dev python -m workbench_tools.build_site
```

The latter builds the self-contained page in `packing/site/workbench/`. Its publisher
checks the generated full corpus and that the page is self-contained, stamps the source
revision, and with `--check` requires two builds to match byte for byte.
The GitHub Pages deployment is owned by the repository workflow.

## Design system

Every colour, space, type size, weight, line height, radius, border width, shadow, layer
and duration the page uses is a custom property in the `:root` block at the top of
[`assets/workbench.css`](assets/workbench.css).
The rest of the stylesheet refers to those tokens and nothing else.
The block has three families:

- **UI chrome** (`--color-*`, `--space-*`, `--font-*`, `--radius-*`, `--control-*`,
  `--layout-*`): semantic colour roles, a 4 px spacing scale, a five-step type scale and
  one control height. The font families and their names follow kpress.
- **The stage** (`--stage-*`): the 1920 × 1080 poster the video is captured from, in
  stage pixels.
- **Scene and plot colours** (`--scene-*`, `--plot-*`): what is drawn rather than the
  chrome. Square fills are data from `sqpack.render` and are not tokens.

The stage draws one frame around the packing, whichever mode owns it.
The catalogue’s box, the trace of where it just was and the container Pack and the
animation studio draw are all `--scene-frame-width` wide, and the colour is the only
thing that changes: the box is `--scene-frame-locked` where it rests at the best known
side and `--scene-frame` on its way, the trace is `--scene-trace`, and the container is
`--scene-frame`.

**The stage names its sources on request.** Under PROVEN, the CITATION section gives
each bound’s reference and the frontier case record they are held in.
Everything this project has to say about a bound is one grey parenthesis after the
reference, in one vocabulary: `(reported)` where the register carries the bound without
certifying it, `(confirmed T-009)` where a result of ours checks it, and
`(reported; confirmed T-009)` where both are true, which in the whole corpus is n = 29
alone. The words are composed with the data, not at the stage, and the width a line is
checked against counts them.
It is a setting — `show citations`, off until it is asked for, `setCitations` on the
browser API — and its data is
[`bound-citations.json`](../../packing/atlas/known-best/bound-citations.json), read at
build time; a page built without that file has nothing to cite and says so.
`squares-workbench-capture --citations` draws the section for a cut, and the cut’s
receipt records that it was on, the file’s sha256 and the version.
The stage’s bottom right carries that version, `sqpack.release.PUBLICATION_EDITION`, so
every captured frame names the data it was drawn from.

**The panel trades its text rather than dissolving it.** A word both n draw holds at
full ink and swaps at the midpoint; a word that changes leaves before its replacement
arrives, over `TEXT_HANDOVER`, which is seven frames at 60 fps.
Cross-fading the two put the old sentence and the new one in the same place at half ink
each, and neither could be read (`think-0few`). `check_animate_view` holds both halves
of that: two different strings drawn in one place are never both legible, and a slot
with nothing holding it up may be under half ink for `BLANK_DIP_SECONDS` and no longer.

**A grid fill plays faster, by a factor you set.** `speed up simple transitions` is the
toggle and `grid fill speed` the factor, 1 to 8 in halves and 4 by default: a step where
every square is already square to the container has nothing to watch.
`setSimpleSpeed` is the browser API, `squares-workbench-capture --simple-speed` the
cut’s, and the receipt’s `simple_speed` names the clock its step lengths were measured
on — so a length means nothing without it, and a cut that asks for a factor the page
declines is refused.

The page has one structure in every mode.
The controls are a single column inside `--layout-gutter`. Every block in it (the mode
panel, a `.panel-row` of `.subpanel`s, a `.workspace`) spans the same two edges and sits
`--layout-stack-gap` from the next.
Within a block, a `.row` holds controls and a `.box-title` names a panel.

Three contracts hold it:

- [`tests/design-system.test.ts`](tests/design-system.test.ts) refuses a raw design
  value outside the token block.
  It also refuses an inline style write in `src/` or the template beyond the counted,
  reasoned allowances in [`design-allowlist.json`](design-allowlist.json), which may
  only shrink. It checks every text, control, focus and stage colour pair against WCAG
  AA. The machinery is in [`tools/design-contract.ts`](tools/design-contract.ts), with
  its negative fixtures in `tests/design-contract.test.ts`.
- `workbench_tools.check_layout` measures Animate at rest and mid-step, the animation
  studio, Pack and Search in Chromium at 1440 × 900, 1024 × 768 and 390 × 844. It checks
  the shared edges, gutters and gaps, one height per control kind, horizontal overflow,
  panel overlap, the stage panel’s OPEN and badge rules (one type, with `new result`
  alone in the star’s scarlet), one type for the PROVEN, CITATION and OPEN heads, the
  CITATION section inside its column and above what it is set over, the one frame width
  in its three colours, and that the attribution stands one legend line under the legend
  at its left edge, with the shared version on its baseline at the column’s right edge,
  both clear of what each mode draws.
  It runs inside `check_stage_resize`’s browser session in `check_frontend`, and
  `tests/test_check_layout.py` proves each rule refuses a page that breaks it.
- `workbench_tools.layout_gallery` photographs every view at every review viewport and
  writes a side-by-side comparison page for design review.

## The transition contract

`workbench_tools.check_transitions` samples every frame of a step at 60 fps and holds it
to the rules in `transition_contract`. A blend shows no hue that neither of its ends
has, and a hue turns only through grey.
A shade blends rather than snapping.
The view moves one way, the box only shrinks once the move starts, and the new square
arrives saturated scarlet.
`check_frontend` runs it on every pull request over the steps that have broken; `--all`
runs every step in the corpus.

When a transition looks wrong, trace it before changing anything.
This prints one square through one step, frame by frame, in OKLCH, with the schedule it
ran on:

```bash
uv run --frozen --all-extras --group dev squares-workbench-check-transitions --trace 11 --square 5
```

## Contracts and ownership

- `src/api` defines the public browser API. Runtime installation and probe declarations
  consume this contract.
- `src/core` owns seed semantics, snapshot checks and navigation.
  Packing poses use radians internally; the retained public browser API uses degrees.
- `src/data` validates the versioned corpus and its stable identities.
  The builder supplies palette/shades from `sqpack.render`; workbench angle clustering
  has a separate declared tolerance.
- `src/animation` computes timing, arrival, range progress and deterministic seeking.
  These operations do not call a solver or require a DOM.
- `probes` holds checked browser instruments.
  Python code does not embed their programs in string literals.
- `tools/workbench_tools` contains Python import, geometry, trial and report contracts.
  Numerical admission retains the exact checked snapshot and its tolerance.

## Reproducible block reports

From `packing/`, a cohort manifest and a JSONL envelope file produce the report:

```bash
uv run --frozen --all-extras --group dev python -m workbench_tools.block_report \
    /path/to/manifest.json /path/to/trials.jsonl --out /path/to/report.json
```

The manifest schema is `squares.workbench.cohort/v1`. It declares the full source
commit, repository-relative benchmark path (`instrument`), catalogue directory
(`reference_source`), purpose (`research` or `software-validation`) and cohorts.
Each cohort declares its ID, n, style, requested parameter overrides, tuning/held-out or
exploratory partition, block size, step and repair budgets, and ordered seed slots.
Slots explicitly say completed, failed, cancelled or not-started.
Completed slots have exactly one JSONL envelope: `{"cohort":"cohort-id","trial":{...}}`,
with an `AnnealingTrial/v2` receipt.
The [contract tests](tests/test_block_report.py) include an executable complete example.

The report admits geometry through the same rule as run/replay/sweep, checks effective
settings and source/runtime agreement, and preserves unsuccessful blocks and partial
tails.
Rates name their denominators; distributions conditioned on valid outcomes say so.
Wilson intervals describe independent-block sampling assumptions rather than
establishing that a deterministic seed campaign sampled independently.
Zero reference-to-grid gaps have no normalized score.
Unknown cost stays unknown.

Historical summaries are audited by `workbench_tools.historical_summary_audit`; they
cannot be used as raw trials.
See the [annealing runbook](../../packing/campaign/results/annealing/README.md) for
record validation and the limits of the retained evidence.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
