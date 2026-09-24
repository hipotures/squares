# PVE host retest: squares CPU Test 8, only 8 and 16 workers

The original PVE run succeeded at 1, 2, and 4 workers. Its first 8-worker
sample lasted 7.902868434 seconds, so that short sample is retained as a
calibration/failure receipt and excluded from the performance comparison.

The VM has now completed three valid samples each at 8 and 16 workers using
this revised **fixed** plan: 350 repeats at 8 workers and 620 at 16. Each VM
sample lasted 50–57 seconds. The source, data bytes, compiler flags, and
algorithm are unchanged. The expected checksums are:

- 8: `6dcf5659d2bc7924`
- 16: `9f46094101fd3341`

As root on physical PVE, when no VM benchmark is running:

1. Locate `tail-retest-package.tar.gz` in the same shared virtiofs `ai`
   directory as the original `package.tar.gz`. SHA-256 must be
   `3bb51aad4c158181a9a41a067a91226777a92b82fc4fab8207c8e7d1006d05af`.
2. Extract the archive into a **new** directory
   `/root/squares-cpu-penalty-test08-tail/`. Preserve the original directory
   and original `host-results/` unchanged.
3. Run sequentially, with no other benchmark active:

   ```sh
   cd /root/squares-cpu-penalty-test08-tail
   python3 run.py --outdir host-results-tail --only 8
   python3 run.py --outdir host-results-tail --only 16
   ```

4. Copy the entire `host-results-tail/` to the shared directory beside the
   package, named `host-results-tail/`. Preserve error logs and any partial
   outputs if either command fails. Do not recalibrate or change the plan.
5. If perf access fails, temporarily use the original task's permission
   procedure and restore the exact prior `kernel.perf_event_paranoid` value.

Report `DONE` only if both commands complete; otherwise report the sample
duration and exact error. Do not change VM vCPU pinning or persistent PVE
configuration.
