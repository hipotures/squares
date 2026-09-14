# The annealing benchmark’s runbook

The campaign asks which declared packing strategies improve the distribution of valid
outcomes under equal work on cases not used for tuning.
The
[workbench plan](../../../../docs/project/specs/active/plan-2026-09-11-workbench-from-spike-to-product.md)
governs implementation; the
[annealing plan](../../../../docs/project/specs/active/plan-2026-09-11-annealing-as-a-search.md)
defines the experimental comparison.

## What is retained

`summaries.json` holds one entry per run file: the median `closed` and the best of the
first k runs, per cell.
It was kept when 185 MB of per-trial JSONL was removed from the branch at `6e191a35`.

- **Cells marked `resolved: true`** were repaired to packings and checked before
  scoring. They are the only cells any finding may cite.
- **Cells marked `resolved: false`** were scored before any validity check, on
  arrangements with overlapping squares.
  They are void.
- **Best-of-k is a prefix of one seed stream**, not a distribution, and several files
  replay the same seeds.
- **No trials or final poses survive**, so no cell can be re-checked or split into
  disjoint blocks.

What those cells show is written up in
[X-029](../../explorations/X-029-the-workbench-physics-as-a-search.md).

## One round

1. Choose a registered hypothesis, control, candidate, held-out cases, seed blocks and
   work budget before running.
   Declare the accept rule and stop condition.

2. Run the instrument’s guards, including finite geometry, exact square count, positive
   container side, pair and wall checks.
   Record source revision, dirty state, configuration version, effective seed,
   environment and measured elapsed time.

3. Retain the raw trial receipt and displayed geometry, with separate raw and repaired
   checks. Repair may stall or exhaust its budget; it is not guaranteed to produce a
   packing. Invalid or incomplete outcomes never enter ranking.

4. Replay the retained receipt through the same admission contract.
   Group equal-work trials into disjoint seed blocks and report best-of-k median, range,
   valid/refused counts, leftover trials and cost.
   One prefix best-of-k is one observation.

5. Write the experiment artifact, preserving negative results and the original
   criterion. Record the raw artifact location; if too large for Git, retain an
   accessible immutable artifact reference and manifest rather than deleting the only
   inputs to the report.

6. Regenerate and validate the record immediately, from `packing/`:

   ```bash
   uv run --frozen --all-extras --group dev packing-ledger render
   uv run --frozen --all-extras --group dev packing-ledger check
   uv run --frozen --all-extras --group dev packing-validate --records
   ```

The current legacy harness can be invoked from `packing/`:

```bash
uv run --frozen --all-extras --group dev python -m devtools.bench_annealing \
    --n 5 10 11 17 26 29 --seeds 2000 --anneal 6
uv run --frozen --all-extras --group dev python -m devtools.bench_annealing \
    --replay /path/to/retained-trials.jsonl
```

The Phase 1 admission repair and Phase 3 shared kernel replace this legacy instrument
before new comparative conclusions are accepted.
Existing commands are reproduction routes, not evidence that their known defects are
fixed.

## Metrics and acceptance

`closed = (grid - side) / (grid - record)` is the fraction of the record-to-grid gap
closed by a checked arrangement.
One is the record, zero is the grid and a negative value is worse than the grid.
Cases where the denominator is zero need an absolute side metric instead.
A numerically checked improvement is not a proved new bound.

Compare control and candidate distributions at equal declared work and report their
spread. Keep tuning and held-out cases separate.
A better median, a single lucky seed, or a visually flat tail does not by itself
establish the registered claim.

Continue from the open hypotheses
[H-207 through H-211](../../ideas.md#workbench-physics-as-a-search), the
[ledger](../../ledger.md), and the governing plan.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
