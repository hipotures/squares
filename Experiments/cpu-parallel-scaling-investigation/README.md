# CPU parallel scaling investigation (n=12 square packing)

This directory preserves the completed 2026-09-23 CPU research campaign, its real input bytes, diagnostic code, raw measurements, and the detailed [report](report.md). The question was why identical NumPy separation work consumes substantially more aggregate CPU time as concurrency rises. The experiments kept **whole solver**, **separation**, and **individual operation** timings distinct. GPU work was outside scope.

## Environment and original baseline

The measurements ran on a KVM VM exposing 16 guest vCPUs as an AMD Ryzen 9 7950X3D. It used project-pinned Python 3.14.7 and NumPy 2.5.2 via `uv run --frozen`, Linux 7.0.0-31-generic, and `OPENBLAS_NUM_THREADS=1` for the controlled sweeps. Guest cache and CPU topology labels do not establish the physical CCD/LLC layout. Hardware performance counters were unavailable (`perf_event_paranoid=4`). Exact environment and topology records are in [`raw/environment.json`](raw/environment.json) and `raw/lscpu*.txt`.

| Original solver | Wall | Separation | Serial LP | Rounds | Rows | Objective |
|---|---:|---:|---:|---:|---:|---:|
| Serial | ~71.19 s | ~59.41 s | ~11.78 s | 23 | 5,481 | 12.217676366606284 |
| 16 processes | 21.341 s | 9.361 s | 11.964 s | 23 | 5,481 | 12.217676366606284 |

The serial LP limits whole-program scaling even if separation becomes ideal.

## Main findings

- **H1, supervisor/task feed:** Refuted as the main cause. Independently launched pinned executables, with no ProcessPool or timed-region task IPC, reproduce the high-concurrency slowdown: 16-way speedup is ~6.76× for real late-round argpartition and ~6.30× for double cumsum, while aggregate CPU time grows ~1.9–2.0×.
- **H2, all-core frequency/VM capacity:** A verified register-only C loop loses ~6.3% target-core throughput with 14 compute-only backgrounds. That is a minor contributor compared with the NumPy penalty.
- **H3/H4, shared memory and cache:** Fourteen large independent memory streamers roughly double one pinned NumPy target's latency; 14 register-only backgrounds raise it only ~6–10%. Arrays up to ~2 MiB show little per-call inflation at 16 workers, while ~7–12 MiB inputs inflate markedly. Shared read-only input pages and cache-line footprint controls confirm a capacity effect. The exact split among physical DDR, LLC, and VM-host effects remains unresolved.
- **H5, allocation/page faults:** Reused cumsum buffers remove almost all repeated-call minor faults and improve absolute latency, but most of the concurrency penalty remains.
- **H6/H7, NumPy selector and input order:** The round-0 zero/+inf array is ordered so optional SIMD argselection samples poor pivots. Three value-preserving swaps at pivot-sample positions change ~172 ms to ~7.3 ms. Disabling optional SIMD selection dispatch changes the identical input from ~170 ms to ~2.5 ms. Ties or infinities alone do not cause the slowdown.
- **H8, decomposition/layout:** C/F order and guest-vCPU pinning do not materially restore scaling. Shared physical input pages help a diagnostic with duplicated data, while actual directions have distinct grids.
- **H9, library threads:** Default NumPy/library threads distorted some early CPU accounting; the controlled sweeps set `OPENBLAS_NUM_THREADS=1`, and the slowdown persists.

The fastest **research-only** 16-process combination of generic NumPy selection and in-place cumsum took 15.646 s wall and 5.563 s separation versus 21.341 s and 9.361 s originally. It converged to the same packing condition, with 22 rounds/5,517 rows and an objective 1.75×10⁻¹¹ above the original because equal-valued tie choices changed. This is preserved as evidence, not installed in the solver.

## Contents

| Location | Contents |
|---|---|
| [`report.md`](report.md) | Full hypothesis matrix, controls, numerical results, limitations, and recommendation. |
| [`scripts/`](scripts/) | Main benchmark drivers, isolated worker, C/C++ diagnostic sources, workload packer, and hash verifier. `scripts/prior/` retains earlier profiling drivers as provenance. |
| [`workloads/`](workloads/) | Lossless zstd tar archives of all 376 captured NumPy files plus capture manifest and 22 synthetic/derived workload files. |
| [`raw/`](raw/) | Original JSON/CSV-like results, environment/topology snapshots, NumPy source excerpts, and solver run outputs from the completed investigation. |
| [`results/prior/`](results/prior/) | Machine-readable measurements and analysis from preceding profiling steps, including `/tmp/squares-parallel-analysis.json`. |
| [`profiles/prior/`](profiles/prior/) | Nonempty profiler outputs, stdout, timing snippets, and `pstats` from those steps. |
| [`manifests/workload-sha256.json`](manifests/workload-sha256.json) | Original size and SHA-256 for **every** archived file; archive sizes and SHA-256; restore targets. |
| [`manifests/prior-artifacts.json`](manifests/prior-artifacts.json) | Previous `/tmp` artifact inventory, copied paths, identical duplicates, and transient omissions. |
| [`manifests/file-inventory.json`](manifests/file-inventory.json) | Size and SHA-256 for every candidate committed file except the inventory itself. |

The original capture under `/tmp/squares-numpy-capture-20260923/` had the same manifest as the persistent research copy; it was not added twice. Empty stderr files, PID files, readiness markers, compiled helper executables, and Python caches were omitted as transient. The independently timed worker details remain in `raw/independent.json`. **No artifact was excluded because its compressed size exceeded 50 MiB**; the largest archive is below 50 MiB. No Git LFS is needed.

## Restore and verify the exact workload bytes

From the repository root, with already-installed `tar` and `zstd`:

```bash
EXP=Experiments/cpu-parallel-scaling-investigation
for archive in "$EXP"/workloads/capture-*.tar.zst; do
    tar -I zstd -xf "$archive" -C "$EXP/raw"
done
tar -I zstd -xf "$EXP/workloads/synthetic-workloads.tar.zst" -C "$EXP/workloads"
python3 "$EXP/scripts/verify_workloads.py"
```

This restores `raw/squares-numpy-capture-20260923/*.npy` and the synthetic/derived `.npy`/`.bin` files into `workloads/`. The SHA-256 verifier checks both archives and all original files. The packer source is `scripts/archive_workloads.py`; it accepts the completed local investigation directory if the archives ever need regeneration.

To check all archived file bytes without extracting them, run `python3 "$EXP/scripts/verify_workloads.py" --archives-only` from the repository root.

## Reproduce the discriminating measurements

Compile the user-level diagnostics from the repository root, then run Python from `packing/` so `uv run --frozen` uses the project-pinned Python 3.14 environment:

```bash
EXP=Experiments/cpu-parallel-scaling-investigation
cc -O3 -std=c11 -o "$EXP/scripts/stress" "$EXP/scripts/stress.c"
cc -O3 -std=c11 -o "$EXP/scripts/cache_latency" "$EXP/scripts/cache_latency.c"
c++ -O3 -std=c++17 -o "$EXP/scripts/selection_trace" "$EXP/scripts/selection_trace.cpp"
cd packing
EXP=../Experiments/cpu-parallel-scaling-investigation
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/independent.py"
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/target_stress.py"
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/working_set.py"
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/distribution.py"
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/pivot_swap.py"
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/cumsum_buffers.py"
OPENBLAS_NUM_THREADS=1 NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4,AVX512_ICL uv run --frozen python "$EXP/scripts/dispatch_scaling.py"
```

These commands repeat the measurements and overwrite the corresponding `raw/*.json` files in a working tree; use a separate checkout if preserving the committed results locally matters. `scripts/full_solver_options.py` and `scripts/full_solver_inplace.py` hold the temporary full-solver interventions used for the reported outcomes. For example, the original 16-process baseline and the best research variant are:

```bash
OPENBLAS_NUM_THREADS=1 uv run --frozen python "$EXP/scripts/full_solver_options.py" --workers 16 --out "$EXP/raw/recheck_baseline.json"
OPENBLAS_NUM_THREADS=1 NPY_DISABLE_CPU_FEATURES=X86_V3,X86_V4,AVX512_ICL SQUARES_CUMSUM_INPLACE=1 uv run --frozen python "$EXP/scripts/full_solver_inplace.py" --workers 16 --out "$EXP/raw/recheck_generic_inplace.json"
```

The archives retain identical input bytes for future CPU or GPU implementation comparisons. This preservation task did not rerun the research campaign, alter production solver code, or change project dependencies.
