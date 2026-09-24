# Proxmox host task: squares CPU Test 8

VM benchmarking is complete. Run this task as root on physical PVE host; no VM load benchmark is active.

1. Locate `package.tar.gz` in this shared directory. Verify SHA-256:
   `515f1414fc7adee48f7f49eea2cc0637135b271dec33ce9fc9e8c4ec63b26a26`.
   If the host pathname differs from the VM's `/srv/ai/benchmarks/squares-cpu-penalty-test08/`, use the backing path of VM 207's virtiofs mapping `ai`.
2. Extract into `/root/squares-cpu-penalty-test08/` and run:
   `cd /root/squares-cpu-penalty-test08 && python3 run.py --outdir host-results`
   Do not recalibrate on the host. Do not run other benchmarks concurrently.
3. Preserve all outputs, including any failures, and copy `host-results/` into this shared directory so the VM can read it.
4. If perf access fails, record the prior `kernel.perf_event_paranoid`, set it to `-1` temporarily, retry, and restore the exact prior value afterward. Do not change persistent PVE configuration.
5. If a sample lasts <10 s or >60 s, report the exact result; do not silently discard it.

Return `DONE` or the exact failure reason to the operator. Do not change VM vCPU pinning or other host settings.
