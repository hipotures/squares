# CPU memory-flow observation

Pinned source: `2a2efa39edb179128184f19d6a4235a6bbcaebcc` (`CPU_ACCEPTED_SHA`). This worktree contains measurement scripts and raw results only; no production solver files were changed. The solver workload is the complete accepted `n=12`, `L=99/25` trajectory: 23 rounds, 181 directions per round, 5,842 held rows. The logical-traffic counter replay verified the saved direction and centre outputs against the captured accepted trajectory.

## Findings

The guest exposes useful bandwidth, but the measurements do **not** establish that the solver is saturating physical DRAM. STREAM-like triad throughput levels near 40 GB/s from 4 through 16 workers, while a read-only stream reaches 77 GB/s at 16. The solver's dominant scans and copies have a software-derived lower-bound traffic estimate around 150 GB per complete separation replay. That number describes array-element movement through the code; it is not measured DRAM traffic. The solver often scans grids of a few megabytes and compacts contiguous row spans from a strided view, so cache residency and locality can make logical traffic differ substantially from memory-controller traffic.

The evidence supports memory-system effects as a plausible contributor to sublinear scaling, especially alongside high page-fault counts. It does not distinguish DRAM bandwidth from cache bandwidth, allocator/page churn, per-core frequency, or VM scheduling. Hardware counters were blocked by the guest security setting, and no host DRAM counters are available.

## Guest-visible bandwidth

The benchmark used three 384 MiB arrays, larger than the guest-reported 256 MiB LLC when combined. Each reported sample lasted at least 10 seconds (minimum 10.0007 s); each operation/worker combination has three independent samples. Workers were pinned to distinct visible vCPUs, CPUs 0 through `workers-1`. Rates use decimal GB/s and count logical stream bytes: read = 1 array read, copy = 1 read + 1 write, write = 1 write, triad = 2 reads + 1 write.

| Workers | Read | Copy | Write | Triad |
|---:|---:|---:|---:|---:|
| 1 | 13.94 | 28.85 | 27.66 | 31.80 |
| 2 | 27.51 | 37.02 | 29.54 | 39.85 |
| 4 | 52.82 | 37.49 | 29.03 | 40.60 |
| 8 | 53.30 | 36.90 | 29.67 | 40.81 |
| 16 | 76.83 | 40.60 | 38.98 | 40.11 |

Values are medians; full sample ranges and durations are in [`stream-summary.json`](raw/stream-summary.json) and [`stream-samples.jsonl`](raw/stream-samples.jsonl). Write at 8 workers had a wide 29.42–42.04 GB/s range; it is retained. The triad curve is the more relevant mixed read/write comparison and is nearly flat from 4 to 16 workers. This is a practical guest-visible result for this benchmark, not a claim about the host's DDR peak.

## Software-derived logical traffic

Counters below were collected by wrapping the production `event_grid`, `_reachable_values`, and selection entry points without replacing their implementations. The complete workload had 2,609,682,816 difference-grid cells, 1,890,769,994 compacted values, and 1,542,301 weighted support-site entries across 4,163 direction calls. The event grid's `mass = grid[:-1, :-1]` is a strided view with the original v-event count as its row stride; compaction copies each reachable v-span into a contiguous output vector.

| Operation | Shape-based accounting | Logical bytes / replay |
|---|---|---:|
| Difference grid initialization | one zero write per grid cell | 20.88 GB |
| Difference scatter | 4 read-modify-write corner updates per weighted site, 16 B/update | 0.10 GB |
| Prefix accumulation | two in-place scans; each cell read and written in each scan (32 B/cell) | 83.51 GB |
| Reachable compaction | read each selected strided source value and write each compact value (16 B/value) | 30.25 GB |
| Top-13 selection | one input read per compact value (8 B/value) | 15.13 GB |
| Compaction interval metadata | three int-sized vectors per interval | 0.07 GB |
| **Counted subtotal** | explicit element traffic listed above | **149.93 GB** |

This subtotal excludes projected coordinates, event and index arrays, domain tests, temporary masks and search arrays, selector output, allocator bookkeeping, write-allocate effects, cache-line fetches, and any extra passes in the zero-weight first round. It is therefore a lower-bound logical model, not a complete cache or DRAM model. Prefix accumulation and compaction dominate the counted bytes. The exact counters and formula are in [`logical-traffic.json`](raw/logical-traffic.json).

The streams and solver work differ in access pattern, core activity, reuse, and allocation. Dividing 149.93 GB by solver wall time would not yield a DRAM rate. At 16 workers the solver's measured separation replay is around 2.0–2.2 seconds in the uninstrumented samples below, which gives a nominal logical rate well above the triad result; that mismatch is a warning that logical element traffic must not be read as physical memory traffic.

## Allocation and page behavior

The workload requests at least 20.88 GB of zero-initialized grid storage plus 15.13 GB of compact-value outputs over one complete replay: about **36.00 GB cumulative output-buffer allocation**, before projections, events, metadata, selection buffers, and placement masks. Buffers are per-direction temporaries; returned result objects do not retain the grid or compact vector. This is requested NumPy buffer volume derived from actual shapes, not allocator RSS growth.

On the accepted SHA, the uninstrumented 16-worker replay samples were 12.20–13.09 seconds for batches of complete replays, or 2.03–2.18 seconds per replay. Summed worker minor faults were 2.48–2.74 million per batch (roughly 0.41–0.46 million per replay); major faults were zero. At sample end, worker RSS was 20,231–24,241 pages (about 79–95 MiB per worker; median 79.4 MiB). Parent peak RSS was 145,276–145,356 KiB. These are resident pages after the measured batch, not per-worker peak RSS. The accepted-SHA instrumented full replay saw 612,545 minor faults and no major faults; it starts fresh workers, so its higher count includes first-touch activity. Raw rows are in [`sample 1`](raw/separation-w16-memory-observation-s1.json), [`sample 2`](raw/separation-w16-memory-observation-s2.json), [`sample 3`](raw/separation-w16-memory-observation-s3.json), and [`logical-traffic.json`](raw/logical-traffic.json).

These fault counts plus modest steady resident sets are consistent with repeated allocation/page activity, but they do not prove that allocator/page churn is the main scaling limit. `tracemalloc`/native allocation tracing was not used: the buffer-volume estimate is explicit and reproducible, while exact allocator call counts and cumulative allocated bytes across all small temporaries remain unresolved.

## Hardware counters and environment

`perf stat -e cycles,instructions,cache-misses -- true` failed with `perf_event_paranoid=4` and “No supported events found.” No settings were changed. The guest is a KVM VM exposing 16 vCPUs on an AMD Ryzen 9 7950X3D model, 256 MiB reported LLC, affinity CPUs 0–15. Host-side DRAM/UMC counters are not exposed, so physical DRAM traffic cannot be measured here. See [`environment.json`](raw/environment.json).

## Proven and unresolved

**Proven by this observation:** the accepted solver's measured real shapes imply about 150 GB/replay of explicit logical element traffic for the listed operations; the guest can sustain about 40.8 GB/s triad and 76.8 GB/s read-only at the measured worker settings; solver replay workers incur substantial minor faults with no major faults; perf hardware counters are unavailable without changing settings.

**Unresolved:** actual DRAM bytes, cache-miss traffic, bandwidth saturation in the solver, the causal share of allocator/page churn versus caches/frequency/VM scheduling, and exact allocation counts for all NumPy and native temporaries.

## Reproduction

From this worktree:

```bash
cc -O3 -march=native -pthread Experiments/cpu-memory-observation/scripts/stream_guest.c -o Experiments/cpu-memory-observation/raw/stream_guest
python3 Experiments/cpu-memory-observation/scripts/run_stream.py
python3 Experiments/cpu-memory-observation/scripts/summarize.py
python3 Experiments/cpu-memory-observation/scripts/environment.py
cd packing
PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-memory-observation/scripts/measure_logical_traffic.py
PYTHONPATH=. uv run --frozen --no-dev python ../Experiments/cpu-post-integration-profile/scripts/replay_separation.py --workers 16 --samples 3 --target-seconds 12 --tag=-memory-observation
python3 ../Experiments/cpu-memory-observation/scripts/collect_replay_raw.py
```

The replay command writes RSS/fault samples under `Experiments/cpu-post-integration-profile/raw/`; the final script copies those JSON rows into this report's `raw/` directory. The initial STREAM calibration was discarded before analysis: its byte counter incorrectly counted each worker's array partition as a full-array pass, overstating throughput by the worker count. `stream_guest.c` now divides aggregate worker passes by the worker count; all reported samples came from the corrected rerun.
