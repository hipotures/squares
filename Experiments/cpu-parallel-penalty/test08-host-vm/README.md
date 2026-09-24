# Test 8: identical native replay on VM and physical host

This self-contained package replays all 181 real round-18 directions. It
contains captured scatter coordinates/weights and exact slab interval
ranges. The C executable performs the same four scatter passes, in-place
row prefix, row-major column prefix, slab compaction, and stable finite
top-13 survey as production. Warmup checks the difference grid, mass grid,
and selected indices/masses against checksums written by the packer.

`package/replay.c`, `package/data.bin`, `package/plan.json`, and
`package/run.py` are the authoritative portable contents. Build with the
same flags on VM and host:

```sh
cc -O3 -std=c11 -fno-fast-math -march=x86-64-v3 -mtune=generic -o replay replay.c -lm
```

The runner uses only Python's standard library and `perf`. Every worker
receives a fixed share of directions and is pinned to CPU `i`; arrays are
loaded, allocated, prefaulted, and warmed before the timed start. It attaches
`perf stat` to the worker PIDs before releasing them and records per-process
CPU, wall, instructions, cycles, IPC, and checksums. Three samples per worker
count use the same fixed iteration plan on host and VM. All final sample
timed regions must last 10–60 seconds. The agent should preserve outputs and
topology/ISA/compiler records under `host-results/`; the VM run is under
`vm-results/`.

The guest vCPUs are pinned within the guest. Host workers are pinned to
physical CPUs 0–15, matching the distinct-core physical control in Test 2.
The host's QEMU vCPU threads are normally unpinned; Test 2 measured about a
5% VM placement effect, which is included in the interpretation uncertainty.
No system-wide setting or production source is changed.
