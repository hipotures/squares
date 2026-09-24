# Test 2: guest and host CPU placement

`raw/host-snapshot/` contains the Proxmox agent's original read-only VM,
topology, cgroup, and perf-PMU inspection. `raw/host-pinning/` contains the
actual vCPU-thread pin/restore script and logs. The agent re-identified VMID
207's QEMU process and 16 `CPU i/KVM` threads, saved each original affinity,
verified `i -> host CPU i` during the test, and verified exact `0-31`
restoration afterward. An eight-minute automatic restoration guard was active.

The guest runs are repeated complete 23-round separation replays. Files
`raw/adjacent-unpinned/`, `raw/adjacent-pinned/`, and
`raw/adjacent-restored/` preserve three 35-second batches in each state;
`scripts/summarize.py` writes min, median, max, and CV to
`processed/summary.json`. The copies also remain under Test 1's raw directory.
`raw/rejected-premature-pin-attempt.json` records an interrupted attempted
measurement before active pinning was confirmed; it provided no complete
timed sample and is excluded.

The 16 guest vCPUs are numbered 0–15, but guest numbers alone do not establish
physical placement. The host has 16 cores and 32 SMT threads; CPUs 16–31 are
siblings of 0–15. The VM's host vCPU threads were initially free to migrate
among 0–31. The host and guest CPU cgroups report no quota or throttling.
The host PMU list contains no executable UMC/DF PMU, so physical DDR
bandwidth cannot be inferred from the guest cache-fill counters.
