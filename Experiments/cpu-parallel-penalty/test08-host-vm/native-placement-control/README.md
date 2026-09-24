# Matched physical placement control

This control resolves the initial 8-worker native host/VM discrepancy.
`pin.sh` and `run-host-side.sh` ran on physical PVE as root, with exact
original vCPU affinities recorded, all 16 mappings verified, an independent
8-minute restore timer, and exact original affinities verified after the
guest benchmark. The copied host receipts are under `host-evidence/`.

While pinned, the VM ran `run-pinned-vm.py`, which invoked the same
`tail-retest/package/run.py` at workers 8 and 16, with the same fixed counts
of 350 and 620, respectively. It published `NATIVE_RESTORE` in a `finally`
block. The VM raw JSON and perf CSV are under `vm-results/`. The unpinned VM
and physical PVE controls are under `../tail-retest/*-results/`. No production
source, package source, data, or compiler flags changed.

The same directory also contains contemporaneous default 8/16-worker full
solver baselines. The physically pinned 8-worker and guest-affinity-only
controls are under `../full-solver-placement/`. Regenerate all processed
comparisons and verify the affinity/correctness assertions with:

```sh
python3 Experiments/cpu-parallel-penalty/test08-host-vm/native-placement-control/summarize.py
```

This script writes `processed/summary.json` and checks the exact 23-round
decision trajectory across all 66 complete full solves.
