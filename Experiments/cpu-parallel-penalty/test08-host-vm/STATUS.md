# Test 8 status — host half blocked at Phase D checkpoint

The VM half is complete: three 23.79–26.54-second samples for each of
1, 2, 4, 8, and 16 workers. All 15 outputs match the fixed plan checksum,
and all perf events ran at 100% enabled time. The captured data, C source,
fixed iteration plan, reproducibility runner, VM raw results, and VM summary
are preserved here. The C warmup verified exact difference-grid, mass-grid,
and selected top-13 checksums on all 181 real round-18 directions.

Host package (also copied to the shared virtiofs directory):

`/srv/ai/benchmarks/squares-cpu-penalty-test08/package.tar.gz`

SHA-256:
`515f1414fc7adee48f7f49eea2cc0637135b271dec33ce9fc9e8c4ec63b26a26`

On the Proxmox host, extract the package and run `python3 run.py --outdir
host-results` as root. The runner compiles the source, validates captured
data, checks every warmup output, attaches perf, and takes three long fixed
iteration samples at each worker count. Do not recalibrate on the host.
Copy `host-results/` into the shared directory after the run. Then import
it here and execute `scripts/summarize.py --host-dir <path>`. The direct
SSH probe to `root@192.168.100.1` timed out, and the operator-supplied
`/home/user/cpu-parallel-penalty-host/` contained only the earlier Phase A
host receipts. The exact host task and package have been handed off. Under
the goal's host-access failure policy, the physical-host half is BLOCKED
until those results arrive; no host result is claimed in this checkpoint.
