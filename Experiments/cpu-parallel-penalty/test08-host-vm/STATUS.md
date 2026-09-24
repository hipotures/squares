# Test 8 status — complete on VM and physical PVE

The same captured 181-direction round-18 native replay was executed on the
VM and physical PVE host. Both verified all warmup difference/mass/selection
checksums and used the same source, data, x86-64-v3 build flags, fixed
iteration counts per worker count, and result checksums. GCC versions differ
between machines, but executed instructions agree within 0.14% per replay.

The first PVE run yielded three valid samples at 1, 2, and 4 workers. Its
first 8-worker sample lasted 7.902868434 seconds, below the required 10
seconds. That failed attempt is retained under `host-results/` and excluded
from the performance summary. The `tail-retest/` plan raised the counts to
350 complete replays at 8 workers and 620 at 16, identically on VM and PVE.
Both completed three valid 15–57-second samples at each endpoint with 100%
perf-event enabled time. Original and retest binaries are identical within
each machine.

Primary processed result: `processed/summary-complete.json`. Original
receipts are in `vm-results/` and `host-results/`; new receipts are in
`tail-retest/vm-results/` and `tail-retest/host-results/`. The retest archive,
preparation script, checksum derivation, and exact PVE instructions are
preserved in `tail-retest/`.

Physical PVE reproduces a large 16-worker CPU-time inflation (3.79× serial)
for essentially the same instructions. The VM's 16-worker wall/CPU is similar
in absolute terms, while its 8-worker endpoint is much slower than PVE.
Host physical CPU placement differs from the guest vCPU's unpinned QEMU
placement, so the 8-worker difference cannot be attributed specifically to
virtualization. Neither machine exposes a working physical memory-controller
PMU, so DDR saturation remains unproven.
