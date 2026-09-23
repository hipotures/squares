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
