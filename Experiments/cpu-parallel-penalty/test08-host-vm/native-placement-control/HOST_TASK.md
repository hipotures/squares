# PVE control: same physical cores for VM and native Test 8

Purpose: the physical PVE native replay uses CPUs 0–7 at 8 workers, while
the VM's guest vCPUs currently have unrestricted host placement. This test
temporarily pins QEMU VM 207 vCPU thread `i` to physical PVE CPU `i`, then
repeats the same VM 8/16-worker native replay. It tests whether physical
placement explains the large 8-worker host/VM difference.

The earlier Phase A physical-core pin control used this same verified
affinity mapping. The included `native8-pin.sh` saves the exact original
affinity of all 16 vCPU threads, checks thread identity and SMT topology,
pins each to a distinct physical core, installs independent restore guards,
and publishes `NATIVE_PINNED`. The wrapper waits while the VM measures.
When the VM writes `NATIVE_RESTORE`, the watcher restores all original
affinities and verifies them; the wrapper copies its logs and publishes
`NATIVE_RESTORED`. An 8-minute independent auto-restore timer is active.

As root on physical PVE, in a shell session that can wait several minutes:

1. Find the **host backing directory** of VM 207's virtiofs mapping `ai`
   containing `tail-retest-package.tar.gz`, `native8-pin.sh`, and
   `native8-run-host-side.sh`. This is the same directory used for the
   previous PVE native runs.
2. Run exactly:

   ```sh
   bash /HOST/BACKING/DIRECTORY/native8-run-host-side.sh /HOST/BACKING/DIRECTORY
   ```

3. When it prints `PINNED`, tell the operator `PINNED` and keep the shell
   session running. **Do not launch any host benchmark.** The VM benchmark
   will start after its shared marker appears.
4. Wait for `RESTORED`. The wrapper copies the original and final affinity
   checks and timestamps to `native-placement-host/` in the shared directory.
   Report `RESTORED` or the exact failure. If it fails or hangs, run
   `/root/cpu-parallel-penalty-host/native-placement-control/restore.sh`
   manually and report the verification.

No persistent Proxmox configuration or system-wide setting is changed.
