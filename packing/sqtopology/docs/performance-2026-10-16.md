# Target-host optimization session, 2026-10-16

Starting HEAD: `91a415a7`. Release build, GCC, stock nauty 2.9.3, Ryzen 9
7950X3D guest with 16 vCPUs. Existing unrelated work outside this directory is
preserved. All comparisons use immutable executable snapshots on this host.

Primary benchmark: `tools/bench_scaling.py`, `grid-4x4-minus-one`, Traces,
workers 1/2/4/8/16, 30 seconds per width, unlimited candidates and unique states,
depth 3, 256 additions, canonical microprofiling enabled. Rates include worker
startup and teardown. Stage times are summed worker time per raw candidate.

## Starting measurement

| Workers | Candidates/s | Generation µs | Validation µs | Graph µs | Canonical µs | Dedup µs |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 35852.2 | 1.74 | 11.63 | 0.47 | 13.01 | 0.60 |
| 2 | 71734.6 | 1.75 | 11.49 | 0.48 | 13.07 | 0.63 |
| 4 | 139681.3 | 1.76 | 11.88 | 0.49 | 13.34 | 0.66 |
| 8 | 270257.1 | 1.81 | 12.40 | 0.51 | 13.59 | 0.70 |
| 16 | 494826.6 | 1.90 | 14.09 | 0.55 | 14.42 | 0.64 |

At 16 workers, average exact key size is 908.7 bytes and retained key payload
is 6589.7 MiB across 7,603,108 locally unique states. This excludes hash table,
frontier, allocator, and topology overhead. All generated candidates are valid.

At one worker the canonical microprofile is: input 0.83 µs, partition 0.99 µs,
engine 7.95 µs, output 1.47 µs, key build 0.85 µs, hash 0.68 µs.

Raw measurement: `/tmp/sqtopology-baseline.json` (session-local).

## Keep: construction-by-invariant rewrite path

External seeds remain fully validated; generated children can be checked with
`--validate-generated`. Native tests check every child across fixture rewrites,
multiple depths, and checked/trusted exact search keys on three shards. A fixed
10,000-candidate run (shard 3/16) matches the starting binary byte for byte.

| Workers | Candidates/s | Relative to start |
| --- | --- | --- |
| 1 | 61817.5 | 1.724x |
| 2 | 122750.3 | 1.711x |
| 4 | 239848.7 | 1.717x |
| 8 | 464241.5 | 1.718x |
| 16 | 849884.4 | 1.718x |

Raw measurement: `/tmp/sqtopology-trusted.json`.

## Keep: stable counting placement for color partitions

The common byte-color partition preserves the exact old ordering; arbitrary
integer-color graphs retain a comparison-sort fallback. Native tests pass.

| Workers | Candidates/s | Relative to trusted path |
| --- | --- | --- |
| 1 | 62357.5 | 1.009x |
| 2 | 126336.9 | 1.029x |
| 4 | 251129.3 | 1.047x |
| 8 | 478544.6 | 1.031x |
| 16 | 870549.4 | 1.024x |

Raw measurement: `/tmp/sqtopology-partition.json`.

## Keep: discard topologies at the depth bound

Every candidate still undergoes exact deduplication. Only expandable topologies
enter the frontier. The one-level search test verifies its exact retained keys
against an independent enumeration and checks that no topology is queued.
Reports now include Linux peak RSS and peak frontier state counts. Summed worker
RSS peaks are an upper bound on simultaneous worker RSS, excluding the harness.

| Workers | Candidates/s | Relative to counting partition | Peak RSS sum MiB |
| --- | --- | --- | --- |
| 1 | 66778.4 | 1.071x | 1018.8 |
| 2 | 129289.1 | 1.023x | 1934.9 |
| 4 | 257126.8 | 1.024x | 3778.6 |
| 8 | 496538.0 | 1.038x | 7227.8 |
| 16 | 887813.8 | 1.020x | 12558.9 |

Raw measurement: `/tmp/sqtopology-leaf.json`.

## Keep: insert added contacts into normalized order

Additions allocate the final child list once and insert at a binary-searched
position, replacing full child normalization/copy/sort. Tests compare its exact
contact ordering to append-and-normalize, including reversed endpoints. The
10,000-candidate baseline exact-key comparison still passes.

| Workers | Candidates/s | Relative to depth-bound cleanup | Generation µs |
| --- | --- | --- | --- |
| 1 | 71893.5 | 1.077x | 0.26 |
| 2 | 140498.1 | 1.087x | 0.27 |
| 4 | 281362.8 | 1.094x | 0.26 |
| 8 | 542337.5 | 1.092x | 0.26 |
| 16 | 971772.5 | 1.095x | 0.27 |

Raw measurement: `/tmp/sqtopology-insert.json`.
