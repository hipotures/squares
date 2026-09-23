# Current-main CPU profile: reproduction

This directory profiles commit `14ba672d999fa34b77d422a4a3e1f43e14df572e`
on the n=12, side=99/25 row-generation case. Production source is unchanged.
Run the commands below from `packing/`. Every timed sample contains at least
10 seconds of computation; scripts load captured files before timing and write
JSON only after a batch ends. The standard thread limits are required.

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.
for jobs in 1 4 8 16; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/baseline.py --workers "$jobs"
done
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/capture_workload.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_reference_hashes.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_baseline.py
for jobs in 1 2 4 8 16; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/replay_separation.py --workers "$jobs"
done
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/replay_separation.py --workers 16 --target-seconds 40 --tag=-long
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_profile_grid.py
for jobs in 1 16; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/profile_separation.py --workers "$jobs"
done
for mode in reference profile; do
  uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/profile_lp.py --mode "$mode"
done
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/measure_lp_cpu.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/memory_probe.py
```

`baseline.py` repeats independent complete solves within each batch, including
the solver's normal site and model setup. Python startup and JSON output are
outside the timed region. `replay_separation.py` measures steady-state work on
the complete 23-round/181-direction weight trajectory: fixture loading and
pool startup are outside the timed region. Parent and worker CPU time comes
from Linux `/proc` accounting. `profile_separation.py` injects timers into
research-only functions; `verify_profile_grid.py` checks its event grid bitwise
against current production. `profile_lp.py` replays all 22 row appends from an
in-memory captured matrix. `memory_probe.py` measures allocations, not latency.

The 16-worker separation replay initially had high variation in 20-second
batches. Its original three samples remain in `raw/separation-w16-s*.json`;
the 40-second rerun is in `raw/separation-w16-long-s*.json`.

Research-only CPU candidate commands:

```bash
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_candidate.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/bench_vectorized.py --variant vectorized --workers 1
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/bench_vectorized.py --variant vectorized --workers 16 --target-seconds 40
cc -O3 -fPIC -shared -o ../Experiments/cpu-post-integration-profile/raw/libprefix_rows.so ../Experiments/cpu-post-integration-profile/scripts/prefix_rows.c
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/verify_prefix.py
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/bench_vectorized.py --variant prefix --workers 1
uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/bench_vectorized.py --variant prefix --workers 16 --target-seconds 40
python ../Experiments/cpu-post-integration-profile/scripts/summarize.py
python ../Experiments/cpu-post-integration-profile/scripts/audit.py
```

The candidate benchmark alternates current main and one candidate within the
same process, with a new process pool for every complete solve. The two
candidates are independently applied to current main; their gains must not be
added. The compiled prefix helper is research code and is never loaded by
production.
