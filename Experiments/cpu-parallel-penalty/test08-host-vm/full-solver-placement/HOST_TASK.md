# PVE host task: temporary physical placement for the full 8-worker solver

The native round-18 replay showed that placing VM 207 vCPU `i` on physical
PVE CPU `i` changed 8-worker VM wall from 0.1472 to 0.04284 seconds per
replay, matching physical PVE. The same placement made the 16-worker VM
replay match PVE. The original vCPU affinities were restored and verified.
This control measures whether the improvement transfers to the **complete
23-round n=12 solver**. The guest's unpinned 8-worker reference was measured
in three 20-second batches at about 4.08 seconds/solve; the unpinned
16-worker reference was also measured in three 19-second batches.

As root on physical PVE, find the same host backing directory of VM 207's
virtiofs `ai` mapping that contains `solver8-pin.sh` and
`solver8-run-host-side.sh`. In a shell session that can wait several minutes:

```sh
bash /HOST/BACKING/DIRECTORY/solver8-run-host-side.sh /HOST/BACKING/DIRECTORY
```

When it prints `PINNED`, tell the operator `PINNED` and let the shell wait.
Do **not** run any host benchmark. The VM will run three controlled 20-second
solver batches with the solver restricted to guest CPUs 0–7, verify 23 rounds
/ 5842 rows / accepted objective on every solve, then publish
`SOLVER8_RESTORE`. The host watcher restores each of the
16 vCPU threads to its exact original affinity; the independent 8-minute
timer provides a second restore path. The wrapper copies the affinity checks
and timestamps to `solver8-placement-host/` and writes `SOLVER8_RESTORED`.

Report `RESTORED` or the exact failure. If the wrapper fails or hangs, run
`/root/cpu-parallel-penalty-host/full-solver8-placement/restore.sh` manually
and report the verification. No persistent PVE setting is changed.
