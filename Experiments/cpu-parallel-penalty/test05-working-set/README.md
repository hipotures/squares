# Test 5: active footprint, row strips, and layout

Part A (`scripts/bench_sizes.py`) runs the current row-major prefix and native
top-13 kernels with 256 KiB–32 MiB active arrays. Inputs are slices or
repetitions of the real round-18 direction-90 distribution and are prepared
before timing. Workers are pinned to distinct guest vCPUs. Every sample runs
at least 10 seconds; the size/count matrix is a screen, and size knees used
for conclusions receive three longer samples.

Part B (`scripts/bench_tile.py`) processes the same complete real grid in
row strips. Each strip receives its row cumsum followed by the native
row-major column pass, carrying the already accumulated previous row into
the next strip. This preserves the per-cell operation order. Blocks 32, 64,
128, and 256 are compared with the production two-pass order. The
`scripts/verify_tiles.py` gate checked bitwise equality over all 181 directions
at five retained rounds before performance conclusions.

Part C (`scripts/bench_padding.py`) varies the physical row stride while
keeping logical values, dimensions, and arithmetic unchanged. A research C
helper handles padded strides with the same row-major addition order as
production. It is built from source with:

```sh
cc -O3 -fPIC -shared -o Experiments/cpu-parallel-penalty/test05-working-set/scripts/prefix_stride.so Experiments/cpu-parallel-penalty/test05-working-set/scripts/prefix_stride.c
```

Neither helper is production code. All benchmark JSON and correctness
receipts are retained under `raw/`. `scripts/run_sizes.py` and
`scripts/run_variants.py` produce the screens;
`scripts/run_size_repeats.py` and `scripts/run_tile_repeats.py` produce the
three-sample long controls. `processed/size-screen.json` and
`processed/final.json` give reduced values and their full sample ranges.
