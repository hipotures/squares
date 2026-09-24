# Test 4: current phase interference

`scripts/workload.py` captures one real late-round direction (round 18,
direction 90) from the accepted replay states. It reconstructs the exact
pre-prefix difference grid and checks its complete prefix output bitwise
against the production event grid. The phase targets are:

- `prefix`: preallocated destination, difference-grid copy, row cumsum, and
  production native row-major column prefix;
- `slab`: production `_reachable_values` on the real mass grid;
- `top13`: production native selector on the real compact values;
- `direction`: complete production `placement_cells`;
- `register`: C xorshift/multiply loop with register-sized state.

Background types are sleeping, register, 64 MiB-per-array streaming,
prefix, slab, and top-13. The target is pinned to guest vCPU 0; backgrounds
are pinned to vCPUs 1 onward. All input construction, allocation, and warmup
occur before timing. Each target is timed for at least 10.5 seconds in the
screen, with perf attached to only the target. Counter enabled/running
fractions are checked. `scripts/run_repeats.py` repeated every screen cell
showing at least 20% slowdown, plus all idle controls, in three 20-second
samples. The criterion and complete plan are retained in
`processed/repeat-plan.json`.

The initial screen intentionally shares the read-only captured inputs among
background workers via fork; each worker still creates its own outputs.
Because production directions normally have distinct grids,
`scripts/run_distinct.py` also tested three same-phase cases with 14
background workers on separate real direction grids.
`scripts/run_register_controls.py` tested the register-only target under
four important backgrounds. `processed/final.json` includes the long
sample distributions and per-call counters. The register-only target
bounds general all-core effects.

`register.so` is a disposable build from `scripts/register.c`:

```sh
cc -O3 -fPIC -shared -o Experiments/cpu-parallel-penalty/test04-interference/scripts/register.so Experiments/cpu-parallel-penalty/test04-interference/scripts/register.c
```
