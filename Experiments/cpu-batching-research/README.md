# P2 memory-flow and batching experiment

All variants replay the same accepted 23-round, 181-direction-per-round
trajectory using the captured weights, points and orbit membership from
`../cpu-post-integration-profile/raw/current-states.npz`. The reference row
order and centres come from that same fixture. The code is research only and
production source remains untouched.

Pinned input: `2a2efa39edb179128184f19d6a4235a6bbcaebcc`.

Variants:

- **A**: current production direction tasks, allocating a new grid and
  compact mass array each direction.
- **B**: same direction tasks and order, with per-process contiguous reusable
  grid and compact value buffers. Each task fully zeroes the grid and writes
  every selected compact value.
- **C**: B's reusable buffers, with four consecutive directions per worker
  call. Chunk results are flattened in the original direction order.
- **D**: optional chunk-only diagnostic, without reusable buffers. It isolates
  the granularity effect if C is appreciably faster than B.

The scratch buffers grow geometrically to fit real shapes. Startup growth is
measured in warmup; post-warmup growth is recorded as actual scratch allocation
per replay. `logical_grid_bytes` and `logical_compact_bytes` count all bytes
materialized by B/C calls; they are *not* physical DRAM traffic. `worker_cpu`
and page faults are Linux `/proc` deltas across persistent workers. Fixture
loading, pool creation and JSON output are outside timed batches. Each timed
batch repeats the complete workload until it exceeds 10 seconds, preferably
20 seconds. Native P2 prefix and selector helpers load from the wheel-built
package in this worktree.

Run from `packing/`:

```bash
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONPATH=.
for jobs in 1 16; do
  for variant in A B C; do
    uv run --frozen --no-dev python \
      ../Experiments/cpu-batching-research/benchmark.py \
      --variant "$variant" --workers "$jobs" --chunk-size 4 --target-seconds 20
  done
done
for jobs in 2 4 8; do
  for variant in A B C; do
    uv run --frozen --no-dev python \
      ../Experiments/cpu-batching-research/benchmark.py \
      --variant "$variant" --workers "$jobs" --chunk-size 4 --target-seconds 18
  done
done
uv run --frozen --no-dev python ../Experiments/cpu-batching-research/benchmark.py \
  --variant D --workers 16 --target-seconds 20
uv run --frozen --no-dev python ../Experiments/cpu-batching-research/benchmark.py \
  --variant B --workers 16 --target-seconds 40 --tag=-long
for variant in A B C; do
  uv run --frozen --no-dev python ../Experiments/cpu-batching-research/benchmark.py \
    --variant "$variant" --workers 8 --target-seconds 30 --tag=-long
done
uv run --frozen --no-dev python ../Experiments/cpu-batching-research/full_solver_chunk.py \
  --target-seconds 20
uv run --frozen --no-dev python ../Experiments/cpu-batching-research/full_solver_chunk.py \
  --target-seconds 40 --tag=-long
python3 ../Experiments/cpu-batching-research/summarize.py
```

Each command produces three independent JSON samples in `raw/`. A zero-sample
correctness warmup uses `--samples 0`. If VM variation warrants longer batches,
the command and original samples must be preserved when rerunning.

The `raw/warmup-*.json` records were produced with `--samples 0` for B and C
at every worker count, redirected to distinct files. Their reported elapsed
warmup is a setup observation, not a primary performance sample. The memory
study has its own pinned worktree and does not share these research buffers.
