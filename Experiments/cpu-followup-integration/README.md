# Issue #2 CPU integration and follow-up

Input main commit: `e102e35f729eb52be10eabe5ba83428e2a10e1bc`.
All controlled commands run from `packing/` with:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.
```

The original control and vectorized candidate were timed before changing
production. Each paired sample is an adjacent complete-solver batch. Sample 2
reverses order. File loading, Python startup, and JSON output are outside each
timed batch. All batches in `raw/vectorized-*.json` exceed 10 seconds.

```bash
for jobs in 1 16; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/bench_vectorized.py \
    --variant vectorized --workers "$jobs" --target-seconds 24 \
    --output-dir ../Experiments/cpu-followup-integration/raw
done
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_candidate.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_baseline.py
uv run --frozen --no-dev --with pytest python -m pytest \
  tests/test_fractional_generate.py tests/test_fractional_selector.py -q
python3 ../Experiments/cpu-followup-integration/summarize.py
```

The first workers=1 command used the script's 20-second default; workers=16
used 24 seconds. The warmed repeat count was chosen separately for control
and candidate. `raw/p1-equivalence.json` is copied from the all-4,163-direction
research check, and `raw/p1-production-correctness.json` is copied from the
production 1/4/8/16-worker run. Both use the accepted full-state fixture in
`../cpu-post-integration-profile/raw/` and its exact-witness-backed M5 identity.

Stage B, memory observation, and A/B/C batching evidence are added after P1.

Stage B ran against P1 with the same adjacent benchmark script, changing
`--variant prefix`. The first 16-worker set used 24-second target batches;
high candidate CV prompted a retained ~40-second rerun in `raw/prefix-long/`.
The candidate's C library is rebuilt by:

```bash
cc -O3 -fPIC -shared -o ../Experiments/cpu-post-integration-profile/raw/libprefix_rows.so \
  ../Experiments/cpu-post-integration-profile/scripts/prefix_rows.c
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_prefix.py
uv build --wheel --out-dir ../Experiments/cpu-followup-integration/raw/wheel-check
```

The production P2 package was rebuilt locally with
`uv sync --frozen --no-dev --reinstall-package sqpack`, checked by the 29
focused tests and by `verify_baseline.py`, then measured with:

```bash
for jobs in 1 16; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/baseline.py \
    --workers "$jobs" --target-seconds 20 \
    --output-dir ../Experiments/cpu-followup-integration/raw/p2-baseline
done
python3 ../Experiments/cpu-followup-integration/summarize.py
```

The original wheel binary and temporary build outputs are intentionally not
committed; `environment.json` records its digest and contents. Rebuilding the
wheel exercises the build hook. `raw/p2-equivalence.json` and
`raw/p2-production-correctness.json` retain the correctness checks.

The accepted P2 SHA is `2a2efa39edb179128184f19d6a4235a6bbcaebcc`.
The pinned memory and A/B/C studies are preserved under the sibling
`Experiments/cpu-memory-observation/` and
`Experiments/cpu-batching-research/` directories, with their own reports,
scripts, raw samples and JSON summaries. Their research worktrees were kept
isolated from the operator's main working tree.
