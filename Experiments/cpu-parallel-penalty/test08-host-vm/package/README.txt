CPU parallel penalty Test 8: standalone Proxmox-host replay

Run from this directory as root on the physical host while the VM's
benchmark is idle:

    python3 run.py --outdir host-results

The runner builds replay.c with the documented x86-64-v3 flags, verifies
data.bin against manifest.json, validates all 181 real direction outputs
during worker warmup, pins worker i to physical CPU i (0..15), attaches
perf stat before timing, and runs three samples for workers 1/2/4/8/16.
The fixed repeats and expected checksums come from plan.json and are
identical to the VM run. Do not recalibrate on the host.

Keep the full host-results/ directory and copy it back to the VM at
/home/user/cpu-parallel-penalty-host/test08-host-results/.

The test makes no permanent host configuration changes. It only reads
topology, kernel, perf, and CPU feature information. If perf fails or a
sample is outside 10–60 seconds, leave the error and raw files intact
and report the exact failure instead of skipping a worker count.
