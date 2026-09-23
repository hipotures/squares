# Post-selector n=12 CPU baseline for a future GPU prototype

The [report](report.md) answers which current CPU separation operations consume time after the round-zero selector fix. This experiment contains CPU measurements and data-transfer requirements only. It changes no solver, mathematical algorithm, or dependency.

## Contents

| Path | Purpose |
|---|---|
| `results/baseline-w{1,16}-r{1,2,3}.json` | Three unprofiled complete solver runs per worker count, including exact per-round timings and pricing. |
| `results/profile-serial.json`, `profile-16.json` | Per-direction operation CPU timings, worker intervals, shapes, and complete solver outcomes. |
| `results/profile-round0-w*.json`, `round0-control.json` | Independent round-zero profile and unprofiled serial control. |
| `results/replay-round18.json` | Three timed repetitions of each 181-direction replay at one and sixteen workers, with per-direction CPU timing. |
| `results/trajectory.json`, `summary.json`, `data-contract.json` | Derived trajectory, decomposition, Amdahl limits, and transfer sizes. |
| `scripts/` | Reproducible profiling, replay, and reduction scripts. |
| `manifests/` | Source, environment, and artifact provenance. |

The replay reads the existing lossless archives at `../cpu-parallel-scaling-investigation/workloads/capture-round18-*.tar.zst`. It extracts them to `/tmp/post-round0-round18` and adds no duplicate binary to this experiment. The original archive and file hashes are in `../cpu-parallel-scaling-investigation/manifests/workload-sha256.json`.
Every artifact in this directory is below 50 MiB; sizes and SHA-256 hashes are in `manifests/artifacts.json`. No Git LFS is used.

## Reproduce

Run from `packing/` with the already locked environment. All commands use `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`. Give `--out` a scratch path when reproducing to preserve the committed results.

```bash
cd packing
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
uv run --frozen python benchmarks/round0_selector/solver_benchmark.py --workers 1 --out /tmp/post-round0-serial.json
uv run --frozen python benchmarks/round0_selector/solver_benchmark.py --workers 16 --out /tmp/post-round0-parallel.json
uv run --frozen python ../Experiments/post-round0-gpu-baseline/scripts/profile_solver.py --workers 1 --out /tmp/post-round0-profile-serial.json
uv run --frozen python ../Experiments/post-round0-gpu-baseline/scripts/profile_solver.py --workers 16 --out /tmp/post-round0-profile-parallel.json
uv run --frozen python ../Experiments/post-round0-gpu-baseline/scripts/replay_round18.py --out /tmp/post-round0-replay.json
```

The profiler copies the current `event_grid`, selector, and `placement_cells` functions into memory with timing calls. It checks exact source fragments before patching and leaves repository source untouched. Both profiled full runs reproduced the baseline trajectory. The replay runs the merged selector on the archived late-round inputs and runs the production nested double cumsum on the archived difference grids. The archives are from the earlier trajectory, so the current round-18 full solver trace supplies the current shape and byte contract separately.
