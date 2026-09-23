# Steady-state top-13 CPU selection

Base: `1f58b0f0abca55d4ea2cf0e1cd73d70ebd625659`. This branch contains a research-only C selector and Python benchmark wrapper; production solver code and dependencies are unchanged. The C source is built with the system C compiler into `/tmp` for each run. No binary is committed.

## Result

**PROMISING BUT NEEDS MORE WORK.** The compiled fixed-size max heap scans finite masses and returns the smallest 13 `(mass, flat index)` pairs in ascending order. It ignores NaN and both infinities. The round-zero special case continues through the merged selector unchanged. A randomized stable-reference check covered 64 arrays with ties and nonfinite values. Full solver trajectories were **TRAJECTORY IDENTICAL** to the base: 22 rounds, 5,643 rows, objective 12.21767636660579, least covered 0.9999999999995074, with the same per-round row/objective sequence.

| Mode | Base median wall | Candidate median wall | Saved | Base separation | Candidate separation | LP |
|---|---:|---:|---:|---:|---:|---:|
| Serial | 43.679 s | 30.011 s | 13.668 s (31.3%) | 33.664 s | 19.918 s | 10.135 s candidate |
| 16-process research harness | 17.568 s | 15.616 s | 1.952 s (11.1%) | 7.266 s | 5.193 s | 10.418 s candidate |

Three unprofiled runs per mode are in `full-w{1,16}-{1,2,3}.json` with exact per-round timings. The 16-process result uses the base research harness, since production `solve_rows()` is serial on this branch.

The preserved older late-round array has 958,441 entries; the newly captured current round-18 direction-26 array has 1,104,601. On the current array, serial selector medians were 5.947 ms for the merged NumPy path and 0.590 ms for the heap. At 16 workers, per-worker CPU was 10.662 versus 0.666 ms/call; aggregate worker CPU for 400 calls was 4.265 versus 0.266 s. Finite compaction took 28.159 ms on that array. Pure-NumPy block selectors ranged from 6.172 to 8.522 ms there. The older preserved fixture likewise gave 6.450 ms NumPy versus 0.507 ms heap.

The native selector avoids NumPy's full-sized index array: tracked peak extra allocation on the current array was 9,942,722 bytes for NumPy versus 1,664 bytes for the heap call. Full solver peak RSS was not captured, so this is a per-call memory effect. The branch does not have a packaged extension, cross-platform build, or production integration. That implementation complexity and compiler/build dependency prevent a merge-ready verdict. Memory diagnostics and exact run metadata are in `current-round18-selector.json`, `parallel-selector.json`, and `environment.json`.

## Reproduce

From `packing/` with `OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`, use `PYTHONPATH=.`:

```bash
uv run --frozen --no-dev python ../Experiments/cpu-optimization-top13/bench_select.py --input ../Experiments/cpu-optimization-top13/current-round18-direction26.npz --out /tmp/top13-current.json
uv run --frozen --no-dev python ../Experiments/cpu-optimization-top13/bench_parallel.py
uv run --frozen --no-dev python ../Experiments/cpu-optimization-top13/run_heap.py --workers 1 --selector baseline --out /tmp/top13-serial.json
uv run --frozen --no-dev python ../Experiments/cpu-optimization-top13/run_heap.py --workers 16 --selector baseline --out /tmp/top13-parallel.json
```

The `--selector baseline` switch is reused solely to invoke the benchmark harness worker initializer; `run_heap.py` replaces that initializer with the compiled heap installer in both parent and workers. The captured current score array was made by running the same serial command with `SQUARES_TOP13_CAPTURE=/tmp/current-round18-direction26.npz`; the wrapper saves selector call `18*181+26`. Its uncompressed float64 payload is 8,836,808 bytes, its lossless archive is 850,237 bytes, and its SHA-256 is `c6e774fa4d780395ce4d48dbb535266c92a03fdc26f31fdf2b6a39d8ba0252bd`. It does not duplicate the older retained archive.
