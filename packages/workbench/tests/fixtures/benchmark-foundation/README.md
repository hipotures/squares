# Foundation Benchmark Replay Fixture

This is a software-validation fixture, collected from clean commit
`f9099096247271b92320f93bc23a16c7503e7a79` on 2026-09-13. It checks the actual browser
instrument, raw JSONL, geometry admission and disjoint-block reporter together.
It is not a research campaign or evidence of packing performance.

The page was built twice with the committed `devtools.build_workbench_site --check`
command and was deterministic and self-contained.
The six n=5 trials used seeds 0–5, bodies, inflation 1.12, anneal 3 and a 60-second
launch budget.
All six completed and passed repaired-geometry admission; none reached the
retained reference within the report tolerance.
Their source, page digest, effective configuration, browser/runtime, exact poses and
measured costs are in [trials.jsonl](trials.jsonl).
The manifest groups them into three disjoint blocks of two.

Run the reporter from `packing/`:

```bash
uv run --frozen --all-extras --group dev python -m workbench_tools.block_report \
  ../packages/workbench/tests/fixtures/benchmark-foundation/manifest.json \
  ../packages/workbench/tests/fixtures/benchmark-foundation/trials.jsonl \
  --cohort foundation-n5 --out /tmp/workbench-foundation-report.json
```

The package regression test compares that result with [report.json](report.json).
Timing measurements replay as recorded observations; repeating the browser run is not
expected to reproduce wall-clock costs.
The original collection command, run from `packing/` at the source commit, was:

```bash
uv run --frozen --all-extras --group dev squares-workbench-benchmark \
  --n 5 --seeds 6 --seed-from 0 --style bodies --inflate 1.12 --anneal 3 \
  --budget 60 --out /tmp/workbench-foundation-trials.jsonl
```

This fixture does not replace the missing historical campaign trials.
Its small sample was chosen to exercise the software path, so its block intervals are
not offered as research conclusions.

<!-- This document follows common-doc-guidelines.md.
See github.com/jlevy/practical-prose and review guidelines before editing.
-->
