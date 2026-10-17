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

## Reject: wrapper sparsegraph buffer reuse

Reusing thread-local sparse input/output owners and the CSR fill cursor saved
only about 0.05 µs of input setup and 0.04 µs of residual canonical time.
Measured rates were 72,825 / 143,570 / 282,807 / 550,205 / 961,111 candidates/s.
Relative to sorted insertion this is +1.3 / +2.2 / +0.5 / +1.5 / -1.1 percent.
The result is too small/noisy, with no 16-worker gain; revert the experiment
completely. Raw measurement: `/tmp/sqtopology-sparse-reuse.json`.

## Keep: block-based bucket hashing with exact byte equality

Search caches the standard-library string hash. Human-facing canonical-form
FNV fingerprints and emitted exact-key bytes are unchanged. A forced hash
collision test verifies that full key bytes still decide set membership.
The clean benchmark excludes the rejected sparse buffer experiment.

| Workers | Candidates/s | Relative to sorted insertion |
| --- | --- | --- |
| 1 | 75741.2 | 1.054x |
| 2 | 149038.8 | 1.061x |
| 4 | 291850.2 | 1.037x |
| 8 | 566251.5 | 1.044x |
| 16 | 1021216.5 | 1.051x |

Hash time fell from about 0.68 to 0.10 µs at one worker.
Raw measurement: `/tmp/sqtopology-hash-only.json`.

## Keep: prefer the installed static nauty archive

The installed archive avoids shared-library TLS indirection without changing
nauty code or labeling semantics. CMake retains the discovered dependency usage
requirements and falls back to shared linking when no archive exists. `ldd`
confirms the executable has no dynamic nauty dependency; native tests pass.

| Workers | Candidates/s | Relative to block hashing |
| --- | --- | --- |
| 1 | 81452.7 | 1.075x |
| 2 | 160122.0 | 1.074x |
| 4 | 316811.9 | 1.086x |
| 8 | 613026.9 | 1.083x |
| 16 | 1081407.7 | 1.059x |

Raw measurement: `/tmp/sqtopology-static-integrated.json`.

## Keep: bounded Traces scratch retention

A private, version-gated Traces 2.9.3 source copy skips only the final scratch
array cleanup for graphs up to 4096 vertices. Explicit cleanup and thread-exit
cleanup release the arrays; larger graphs follow stock cleanup. All labeling
operations are unchanged. Other versions fall back to their installed engine.

Before integration, matched `-O3 -fPIC` stock/reuse objects were compared using
the primary benchmark, with both shared and static helper-library linking.
Scratch retention improved the source-built stock control independently of
linking. A 12,000-graph random differential test (each with a vertex permutation)
produced byte-identical keys. The integrated version also passes that differential,
native tests, and changing-size tests crossing the cache limit.

| Workers | Candidates/s | Relative to static stock | Engine µs |
| --- | --- | --- | --- |
| 1 | 85562.3 | 1.050x | 6.16 |
| 2 | 178177.8 | 1.113x | 5.64 |
| 4 | 350232.1 | 1.105x | 5.68 |
| 8 | 674670.1 | 1.101x | 5.90 |
| 16 | 1209272.6 | 1.118x | 6.25 |

The integrated 1-worker engine timer was slower than the first source-cache
control (6.16 vs 5.61–5.69 µs); repeat measurements remain useful. Other widths
agree closely. Source-cache shared/static runs had almost identical summed worker
time at 16 workers (325.60 vs 325.05 s), with a 3% difference in slowest-shard
finish time. Do not infer a linking-policy improvement from that difference.

Raw measurements: `/tmp/sqtopology-traces-stock.json`,
`/tmp/sqtopology-traces-reuse.json`, `/tmp/sqtopology-static-stock.json`,
`/tmp/sqtopology-static-reuse.json`, `/tmp/sqtopology-cache-integrated.json`.

## Keep: direct writes for byte-width SQK4 endpoints

The common endpoint-width-one branch allocates the final string range once and
writes bytes directly. Wider endpoints keep the existing path. Tests decode
keys at 255, 256, and 257 vertices and verify complete graph equivalence and
idempotence on all backends. The 12,000-graph byte differential passes.

| Workers | Candidates/s | Relative to integrated scratch cache | Key build µs |
| --- | --- | --- | --- |
| 1 | 94265.8 | 1.102x | 0.34 |
| 2 | 187143.5 | 1.050x | 0.35 |
| 4 | 363805.6 | 1.039x | 0.35 |
| 8 | 710020.7 | 1.052x | 0.36 |
| 16 | 1266792.4 | 1.048x | 0.38 |

Key construction fell from ~0.84 to ~0.34 µs at one worker. Its engine timer
returned to 5.57 µs, consistent with the earlier source-cache controls.
Raw measurement: `/tmp/sqtopology-byte-writer.json`.

## Keep: small sparse-row bitset ordering

For graphs with at most 256 vertices, four 64-bit words order each exact forward
neighbor set by occupied-word and set-bit iteration. Larger graphs keep local
comparison sorting. Duplicate/range/self-loop checks remain. This is bounded
row-local storage, not an O(V²) bit-by-bit adjacency scan. Native tests and the
12,000-graph byte differential pass.

| Workers | Candidates/s | Relative to direct byte writer | Output µs |
| --- | --- | --- | --- |
| 1 | 97509.6 | 1.034x | 1.08 |
| 2 | 190693.5 | 1.019x | 1.12 |
| 4 | 374960.5 | 1.031x | 1.15 |
| 8 | 732844.1 | 1.032x | 1.17 |
| 16 | 1304655.8 | 1.030x | 1.23 |

Output ordering fell from 1.44–1.61 to 1.08–1.23 µs across widths.
Raw measurement: `/tmp/sqtopology-row-bitsets.json`.

## Keep: request only the canonical labeling from Traces

The matching source confirms `canong == NULL` skips only inverse-label copying
and canonical sparse graph materialization. The wrapper applies the returned
labeling directly to the input CSR, exactly matching `updatecan_tr`. Sparse nauty
retains its original output-graph path. Native tests and the 12,000-graph exact
byte differential pass.

| Workers | Candidates/s | Relative to row bitsets | Engine µs | Output µs |
| --- | --- | --- | --- | --- |
| 1 | 100603.4 | 1.032x | 5.02 | 1.27 |
| 2 | 197729.7 | 1.037x | 5.11 | 1.30 |
| 4 | 390620.1 | 1.042x | 5.11 | 1.32 |
| 8 | 752275.2 | 1.027x | 5.28 | 1.37 |
| 16 | 1348990.0 | 1.034x | 5.66 | 1.45 |

Engine time falls, while output preparation includes the explicit inverse map.
The combined canonical block improves. Raw measurement: `/tmp/sqtopology-label-only.json`.

## Reject: inline tiny Traces split-array sorts

A temporary histogram found ~117 sort calls per candidate, mostly lengths 1/2/3.
An inline sorting-network experiment passed native tests and the byte differential,
but the primary benchmark improved only ~1% with mixed widths. A repeat at 1/16
workers remained tiny/noisy and gave no aggregate 16-worker gain; discard it.
No production source change from this experiment is retained.

The repeats showed slowest-shard variance: shard 3 grew from ~19.5 to 21.5–23 s,
while most workers stayed near their usual ~18–19 s. The complete workload and
unique counts were unchanged. Add cold-path process CPU time, page-fault, and
context-switch accounting to distinguish scheduler/host effects in later runs.
Raw reports: `/tmp/sqtopology-small-sorts*.json`.

## Measurement refinement: optional CPU affinity

The accounting run showed near-100% CPU/wall utilization at one worker, despite
~10% uniformly higher stage costs. This is consistent with per-core/frequency
variation, not added cold-path accounting cost. Add opt-in `--pin-workers` and
`--cpus` controls for close comparisons; the primary benchmark remains unpinned.
The native affinity smoke run processed its exact 32-candidate bound and recorded
CPU 0 correctly. LTO comparisons use the primary benchmark plus pinned repeats.
