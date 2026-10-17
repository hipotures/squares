# sqtopology: discrete square-contact topology experiment

`sqtopology` is the phase-1 native experiment for a graph-first view of congruent-square
packing.

The ordinary packing formulation lives in a continuous configuration space with variables
such as `(x_i, y_i, theta_i)`. This experiment does **not** replace that space by a finite
set and does not claim that a graph uniquely determines a packing. Instead it studies a
quotient-like discrete layer:

~~~text
continuous configuration q
          |
          v
combinatorial topology Sigma
          |
          +---- realization space R(Sigma), not implemented here
~~~

Many, potentially uncountably many, geometric configurations can map to one topology.
Phase 1 asks whether these topology classes can be represented canonically, rewritten,
deduplicated, sharded, inspected, and searched at useful throughput before any continuous
geometry is introduced.

## Scope

Implemented in this phase:

- semantic square/contact topology;
- isolated squares are legal;
- corner-corner, corner-side, side-side, and square-wall contact events;
- colored incidence-graph encoding;
- native nauty canonical labeling;
- quotienting of square permutation, each square's local `D4`, and container `D4`;
- deterministic versioned canonical encoding;
- bounded add/remove-contact rewrites;
- deterministic coarse first-level sharding;
- bounded in-memory search with local deduplication;
- JSON and Graphviz DOT inspection exports;
- a process-scaling harness with no per-candidate IPC;
- fixtures and native tests.

Not implemented:

- coordinates, angles, distances, or overlap lengths;
- geometric realizability;
- containment or non-overlap decisions;
- optimization of container side;
- rigidity, jamming, stress, or mobility analysis;
- SAT/SMT/NLP/LP;
- GPU work;
- a proof that the topology state space searched here is exhaustive;
- distributed networking.

A topology generated here may be geometrically impossible. That is expected.

## Semantic encoding

Each square is converted to a colored graph gadget: an alternating eight-cycle of ports,
with no separate object vertex:

~~~text
corner0 - side0 - corner1 - side1 - corner2 - side2 - corner3 - side3 - corner0
~~~

Side and corner ports have different colors, but the numeric port indices do not.
The color-preserving automorphism group of that alternating cycle is exactly the
intended square `D4` feature relabelings, so no additional square-object anchor
vertex is required. The squares are recovered as the connected components of the
ports' induced subgraph.

The container is a four-cycle of equally colored wall vertices. Its color-preserving
automorphism group is exactly the container `D4`, so it likewise needs no separate
container-object vertex.

A contact is a factor/event vertex, colored by contact kind, connected to the participating
feature ports. A wall contact connects a square feature port to a container-wall vertex.

Packed squares remain interchangeable: nauty may permute eight-cycle components that
are not anchored by distinct contacts, so square IDs are quotiented out.

### Why the centerless gadget is equivalent

The exact-key relation is color-preserving isomorphism of the incidence graph, so the
gadget is faithful exactly when its color-preserving automorphism group quotients the
intended square-permutation x local-`D4` x container-`D4` relation.

- The induced subgraph on the corner-port and side-port colors is a disjoint union of
  the per-square alternating eight-cycles. Contacts connect ports only to event vertices,
  never port-to-port, so no automorphism can splice ports from different squares; it
  permutes whole cycles, which is exactly a square permutation.
- Within one eight-cycle the color-preserving automorphisms are the rotations by an even
  offset and the reflections through an even axis. Those eight maps form a group
  isomorphic to `D4`, which is exactly the local feature relabeling group.
- The induced subgraph on the container-wall color is the four-cycle, whose
  color-preserving automorphism group is the container `D4`.
- Wall vertices and the four contact-event colors are disjoint from the port colors, so no
  automorphism mixes ports, walls, and events. Two same-colored events with equal
  endpoints would be a duplicate contact, which validation rejects, so an automorphism
  that fixes the ports and walls fixes every event.

Color-preserving graph isomorphism therefore induces precisely the intended relation. The
historical gadget adds a square-object vertex adjacent to all eight ports of its cycle and a
container-object vertex adjacent to all four walls; those anchors are determined by their
neighborhoods and add no constraint, so both gadgets induce the same equivalence classes.
`tests/test_sqtopology.cpp` checks that differential as a bijection between the two induced
partitions -- not merely equal class counts -- over a large deterministic corpus that includes
square permutations, local `D4`, and container `D4` images, on all three backends.

The human-facing canonical form is the full versioned textual encoding (`SQT2|...`). Its
`SQTn` marker versions the encoding itself: it is bumped whenever the canonical vertex set,
vertex colors, or edge semantics change, so forms with different markers are not comparable.
It is a per-build inspection and export artifact, not a cross-version byte-stable interchange
format; no consumer parses the marker or assumes byte stability across versions.
Search uses a separate exact binary key (`SQK5`) containing the canonical color sequence
and an exact sorted canonical edge list. Its cached standard-library string fingerprint is only the
unordered-set bucket hash: equality is always decided by the complete binary bytes.

### Deliberate coarse choices

For phase 1, two positive-length side-side contacts with different geometric overlap
lengths are the same semantic contact type. No continuous quantity is retained.

Pairwise contact-event nodes also do not yet say that several pairwise contacts occur at
the same physical point. For example, a grid vertex where four squares meet is represented
through pairwise relations. A future refinement can add multi-way event identity and
ordering along a side without changing the basic factor-graph architecture.

## Symmetry contract

Canonicalization is intended to identify topologies differing only by:

1. permutation of indistinguishable packed squares;
2. any of the eight local `D4` relabelings of each square independently;
3. any of the eight `D4` relabelings of the square container.

Tests apply these relabelings and compare the **full canonical encoding**.

## Dependencies

Ubuntu packages used by the current implementation:

~~~bash
sudo apt install build-essential cmake ninja-build pkg-config libnauty-dev nauty
~~~

Graphviz is optional and used only to render exported DOT:

~~~bash
sudo apt install graphviz
~~~

The implementation uses nauty in-process through `libnauty`; `geng`/`labelg` are useful
diagnostic tools but are not invoked by the search hot path.

## Build and tests

From `packing/sqtopology`:

~~~bash
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build --output-on-failure
~~~

The tests cover semantic validation, free-square representation, square permutation,
local square `D4`, container `D4`, distinct coarse contact types, deterministic rewrite
generation, shard reproducibility, and inspection export.

### Profile-guided optimization

The default build is portable and uses no profile. The retained throughput
measurement uses PGO, produced by a self-contained two-phase build:

~~~bash
tools/pgo_train.sh build   # configure generate, build, train, rebuild with profile
~~~

The script compiles an instrumented binary, runs a short deterministic training
search across several shards, then rebuilds the same build tree with
`-fprofile-use`. It deletes any previous `.gcda`/`.gcno` before the generate phase,
so a repeated invocation is deterministic and stale counts cannot contaminate the
profile, and it fails loudly if the instrumented library or vendored Traces object
recorded no profile. The `.gcda` data stays in the build directory and is never
committed; re-run the script after changing the hot path. PGO only changes
inlining and block layout: it does not introduce a host-specific ISA beyond the
compiler and toolchain's normal target configuration, though the trained
optimization is still tuned to the training workload. On the target host it removes
about 10% of retired instructions and about 6% of the per-candidate wall time.

## Inspect fixtures

~~~bash
./build/sqtopology list-fixtures

./build/sqtopology inspect grid-3x3 \
  --json /tmp/grid-3x3.json \
  --dot /tmp/grid-3x3.dot \
  --canonical

dot -Tsvg /tmp/grid-3x3.dot -o /tmp/grid-3x3.svg
~~~

Fixtures include isolated and disjoint squares (`isolated-1`, `disjoint-2`,
`disjoint-4`), a `1x4` row (`line-4`), each elementary contact kind
(`corner-corner-2`, `corner-side-2`, `side-side-2`), `2x2`, `3x3`, `4x4`, and a
`4x4` grid with one square removed.

The `3x3` fixture deliberately records the central square's four side contacts and four
diagonal corner-point contacts.

## Rewrites

The first rewrite surface is intentionally mechanical and geometry-agnostic:

~~~bash
./build/sqtopology neighbors grid-2x2 --max-additions 64
~~~

It can remove an existing contact or add a semantically valid pairwise/wall contact. It
does not assert that the resulting topology is realizable.

This is a substrate for later graph-search experiments, not a mathematical completeness
claim.

## Bounded search and sharding

A worker owns a coarse deterministic shard:

~~~bash
./build/sqtopology search grid-4x4-minus-one \
  --seconds 30 \
  --max-candidates 0 \
  --max-unique 200000 \
  --max-depth 3 \
  --max-additions 256 \
  --shard 5/16 \
  --json
~~~

The root's deterministic rewrite sequence is partitioned by `index mod shard_count`.
After that first-level assignment, each process generates, canonicalizes, and
deduplicates its descendants locally.

This has two consequences:

- there is no per-candidate coordinator or IPC bottleneck;
- different shards can rediscover the same deeper canonical state.

The second point is deliberate in phase 1. Shard outputs can be merged offline, and a
future canonical-augmentation search can remove cross-shard overlap if measurements show
that it matters. Therefore current shard runs are **not** an exhaustive partition proof.

`--emit-keys FILE` writes sorted exact search keys as `SQK5HEX:<hex>` text for offline
comparison or merge. The hexadecimal rendering is generated only when explicitly requested;
it is not built per candidate in the search hot path.

## Research mode

`research` is a single-process instrumentation traversal for the topology-space
study. It runs the exact production rewrite and canonicalization semantics and only
adds per-depth and per-state aggregation, so it never changes the discovered
canonical key set:

~~~bash
./build/sqtopology research grid-4x4-minus-one \
  --max-depth 2 \
  --additions uncapped \
  --json /tmp/research.json
~~~

Options:

- `--max-depth N` sets the traversal depth;
- `--additions N | uncapped` selects the production 256-addition cap or the full
  event neighborhood `E(n) = 64*C(n,2) + 32*n` (uncapped is the default);
- `--canonical-backend B` selects the canonical backend;
- `--json FILE` writes the machine-readable report;
- `--emit-keys FILE` also writes sorted `SQK5HEX` keys for the same-`n` overlap study;
- `--no-symmetry` disables the residual-symmetry aggregation.

Every run is a single process, so counts are global-unique for the whole reachable
set; the JSON records this explicitly as `counts_scope`. Multi-worker `search` runs
re-expand states shared across shards and are exploratory only.

The campaign driver `tools/research_campaign.sh` runs a fixed seed/depth list and
writes one JSON per run, and `tools/research_analyze.py` (stdlib-only, no plotting
stack) renders tables, SVG plots, and exact key-set overlap. See
`docs/topology-space-research-2026-10-17.md`.

## Process scaling

The Python harness is orchestration only. It launches long-running native shards and waits
for one summary from each process; it never handles candidates.

~~~bash
python3 tools/bench_scaling.py \
  --binary ./build/sqtopology \
  --fixture grid-4x4-minus-one \
  --workers 1,2,4,8,16 \
  --seconds 10 \
  --json-report /tmp/sqtopology-scaling.json
~~~

Each worker performs all candidate work inside the C++ process. The report includes raw
candidate throughput, speedup, efficiency, duplicates, and the sum of per-shard local
unique counts.

Longer runs should use tens of seconds per width so startup cost is negligible.
For controlled comparisons on a fixed CPU set, add `--pin-workers`, or specify
an ordered CPU list with `--cpus 0,1,2,3`. The report records each shard's CPU
affinity, aggregate CPU/wall ratio, and the largest worker CPU/wall gap.

### Two distinct benchmark purposes

Run A and B below as separate measurements; they answer different questions and must not be
compared as if they were one series.

**A. Fixed-work completion / semantic regression.** `grid-4x4-minus-one`, Traces, depth 3,
unlimited candidates and unique states, a generous per-width time cap. Every width exhausts
the whole depth-3 space, so the total candidate and unique counts are a deterministic
semantic fingerprint: any refactor of the equivalence classes, the local dedup, or the shard
partition changes them. The reference is the 16-worker result, `26,689,273` raw candidates
and `12,972,556` local unique states. Raw counts grow with the worker count because states
shared across shard boundaries are re-expanded once per shard; the width-1 result
(`12,120,816` raw, `4,392,083` unique) is the sharding-independent fingerprint and its unique
count is the true global count. Completion wall time here is a makespan, not a
sustained-throughput number.

~~~bash
python3 tools/bench_scaling.py --binary ./build/sqtopology \
  --fixture grid-4x4-minus-one --workers 1,2,4,8,16 --seconds 400 \
  --max-candidates 0 --max-unique 0 --max-depth 3 --max-additions 256 \
  --pin-workers --json-report /tmp/sqtopology-fixedwork.json
~~~

**B. Sustained 30-second throughput.** The same fixture and backend at depth 4 with
unlimited candidates and unique states. The depth-4 space is large enough that every width
keeps all workers busy for the full 30 s, so `candidates_per_second` is a genuine sustained
throughput and the efficiency column measures parallel efficiency rather than makespan
behaviour.

~~~bash
python3 tools/bench_scaling.py --binary ./build/sqtopology \
  --fixture grid-4x4-minus-one --workers 1,2,4,8,16 --seconds 30 \
  --max-candidates 0 --max-unique 0 --max-depth 4 --max-additions 256 \
  --pin-workers --json-report /tmp/sqtopology-sustained.json
~~~

## Hot-path baseline cleanup

The first measured 16-process run showed that rewrite generation and incidence-graph
construction together cost more than nauty itself. The phase-1.1 hot path therefore keeps
the semantic representation unchanged while removing avoidable work:

- search rewrite labels are disabled unless a human-facing neighbor listing needs them;
- generated children are moved into the frontier rather than normalized/copied again;
- the search path validates a topology once and then uses a validated incidence builder;
- incidence edges are preallocated and are not sorted merely for nauty input;
- a bounded per-thread cache reuses the fixed square/container gadget prefix;
  contacts are appended fresh, with arithmetic port IDs;
- canonicalization consumes the incidence graph directly instead of copying/sorting it;
- contact normalization uses structural tuples rather than temporary string keys.

The checked public incidence builder remains available for external callers. The native
tests assert that the checked and validated fast paths produce the same canonical encoding.

### Trusted rewrite validation

Search fully validates its external seed. `generate_rewrites_validated()` then
preserves validity by construction: removing a contact cannot introduce an error;
new contacts use in-range features on distinct squares (or a valid wall), infer
their kind, and exclude existing normalized events. This contract holds inductively
for every search descendant. Release search therefore skips repeated full semantic
validation of generated children.

Use `search ... --validate-generated` to run full validation on every generated
candidate and fail immediately if the construction invariant is violated. Tests
exercise this diagnostic against the trusted path, including exact retained keys
and deterministic shards. The public `generate_rewrites()`, `run_search()`, and
`to_incidence_graph()` entry points still validate external input.

## Exact binary search key

Phase 1.3 removes human-readable canonical serialization from the search hot path.

After the selected canonical-labeling backend returns, search builds an exact `SQK5`
binary key directly from:

- a version marker and backend tag;
- canonical vertex count and encoded endpoint width;
- exact canonical edge count;
- the canonical vertex-color sequence;
- the sorted canonical undirected edge list.

Endpoint indices use one byte while the canonical graph has at most 256 vertices, two
bytes up to 65,536 vertices, and four bytes above that. With `S` squares and `C`
contacts the seed incidence graph has exactly `8S + 4 + C` vertices and
`8S + 4 + 2C` edges, so the `grid-4x4-minus-one` fixture (15 squares, 50 contacts) is
174 vertices and 224 edges. Candidates that add or remove contacts are larger or
smaller: averaged over the complete depth-3 `grid-4x4-minus-one` space the candidate
graph is about 176.0 vertices and 228.0 edges with an average exact key of about 646
bytes. That is far below about 2.2 KiB for the earlier packed-triangle SQK3 and roughly
4.6 KiB of dense nauty words.

Sparse nauty extracts the canonical edge list from its sparse output. Traces returns
only its canonical labeling; the wrapper applies it to the input CSR, avoiding a
second sparse graph. For graphs up to 256 vertices, four-word row bitsets order
forward neighbors; larger graphs sort each forward-neighbor list. They no longer convert the canonical
result to a dense matrix or scan O(V^2) possible adjacency positions. Dense nauty remains
available as a comparison backend and extracts its edge list from the dense canonical
matrix.

The key is stored in an exact hash set together with a cached string fingerprint
used for bucket selection. Search uses Boost's `unordered_flat_set` when its headers
are available, with `std::unordered_set` as a fallback. Set
`-DSQTOPOLOGY_BOOST_FLAT_SET=OFF` for the standard-container comparison. Hash collisions do not affect correctness because the full
binary key bytes remain the equality oracle.

The old `CanonicalForm` / `SQT2|...` representation is retained for inspection, JSON,
debugging, and semantic regression tests. Search does not build the human-facing `CanonicalForm` or run `ostringstream`
for every candidate.

Tests compare binary-key equality against textual canonical-form equality across symmetry
transforms and distinct contact types. Retained search keys are rendered as `SQK5HEX:...`
only at the end of a run when `--emit-keys` is requested.

### nauty/Traces integration

CMake prefers the installed static nauty archive when available, avoiding shared
library TLS lookup overhead. Set `-DSQTOPOLOGY_STATIC_NAUTY=OFF` to compare shared
linking.

With nauty 2.9.3, the default build uses a private Traces copy with bounded scratch
reuse. The labeling algorithm is unchanged: only the end-of-call scratch-array
cleanup is deferred. Arrays are retained for graphs up to 4096 vertices and freed
at thread exit; larger graphs use stock cleanup. Other per-call Traces allocations
are still released normally. Set `-DSQTOPOLOGY_CACHED_TRACES=OFF` to use the stock
engine. Other nauty versions automatically use the installed engine.

See [the dependency notes](third_party/nauty/README.md) for provenance and the
small source change, and [the session measurements](docs/performance-2026-10-16.md)
for comparisons. Dense nauty and sparse nauty remain stock implementations.

## Canonical backend comparison

Search defaults to `traces`. The target-host 15-second benchmark on
`grid-4x4-minus-one` at 16 workers measured 1,813,688 candidates/s for Traces,
versus 1,323,391 for sparse nauty and 267,486 for dense nauty (PGO build). Dense and
sparse backends remain selectable for regression testing and workload-specific comparisons.

Search can now use any of three in-process canonical-labeling backends:

- `dense-nauty`: the original dense `densenauty()` baseline;
- `sparse-nauty`: nauty's sparse-graph interface;
- `traces`: Traces on the same colored incidence graph.

Override the default in the native CLI with:

~~~bash
./build/sqtopology search grid-4x4-minus-one \
  --canonical-backend sparse-nauty \
  --seconds 30 \
  --max-unique 0 \
  --json
~~~

Or benchmark all three through the existing coarse-process harness:

~~~bash
python3 tools/bench_scaling.py \
  --binary ./build/sqtopology \
  --fixture grid-4x4-minus-one \
  --backends dense-nauty,sparse-nauty,traces \
  --workers 1,2,4,8,16 \
  --seconds 30 \
  --max-candidates 0 \
  --max-unique 0 \
  --max-depth 3 \
  --max-additions 256 \
  --profile-canonical \
  --json-report /tmp/sqtopology-backends.json
~~~

All backends consume the same `ColoredGraph` and the same initial color partition.
Sparse nauty and Traces keep their canonical output sparse through exact-key construction.
The canonical adjacency is normalized to a sorted undirected edge list before serialization.
Dense nauty uses the same SQK5 logical format after extracting edges from its dense output.

The exact search key format is now `SQK5` and includes a backend tag. This is deliberate:
different canonical-labeling engines are required to identify the same isomorphism classes,
but they are not required to choose byte-identical canonical labels. Therefore emitted
keys from different backends must not be merged as if they belonged to one key namespace.

Native tests verify that all three backends induce the same equivalence relation on
symmetry-transformed fixtures and agree on duplicate/unique counts in a bounded search.

## Exact-key payload accounting

The first SQK3 packed-triangle implementation reduced retained key memory but scanned
the full O(V^2) canonical adjacency triangle. On the target host that raised Traces
key-build cost to about 12 us/candidate and reduced 16-worker throughput from about
396k to 348k candidates/s. SQK4 replaced that scan with the sparse canonical edge-list
path above, and SQK5 kept that layout while changing the payload after the
square/container object vertices were dropped from the incidence gadget.

Search summaries report both total candidate-key bytes and the exact payload bytes retained
for unique states. The scaling harness prints an `exact canonical-key footprint` table
with average key bytes and stored payload MiB. This is the payload of the equality keys
themselves, not process RSS; allocator, hash-table, frontier, and topology overhead remain
outside that number.

## Canonicalization microprofiling

The phase-1.2 instrumentation can split the canonicalization block without changing the
search semantics. The same instrumentation now applies to dense nauty, sparse nauty, and Traces. It is opt-in so ordinary search throughput is not charged for several
extra high-resolution clock reads per candidate.

Use:

~~~bash
python3 tools/bench_scaling.py \
  --binary ./build/sqtopology \
  --fixture grid-4x4-minus-one \
  --workers 1,2,4,8,16 \
  --seconds 30 \
  --max-candidates 0 \
  --max-unique 200000 \
  --max-depth 3 \
  --max-additions 256 \
  --profile-canonical \
  --json-report /tmp/sqtopology-canonical-profile.json
~~~

The harness prints a second table in microseconds per profiled search canonicalization.
The search hot path is split into:

- backend input graph construction;
- initial colored partition/labelling setup;
- canonical engine call (`densenauty`, `sparsenauty`, or `Traces`);
- sparse canonical-output preparation;
- exact binary-key construction;
- cached standard-library bucket hash;
- residual canonical-block time not covered by those regions.

The human-facing `CanonicalForm` path still has extraction and textual-encoding timers,
but ordinary search no longer executes those stages.

The unprofiled command remains the correct throughput benchmark. A run with
`--profile-canonical` is diagnostic and should not be compared directly with the
unprofiled throughput baseline.

## Measurement fields

Native search summaries separately report:

- raw candidates;
- valid candidates;
- canonicalizations;
- duplicates;
- local unique states;
- root rewrites selected by the shard;
- wall time and process user/system CPU time;
- peak process RSS and peak expandable-frontier states;
- page faults and voluntary/involuntary context switches;
- rewrite-generation time;
- semantic-validation time;
- incidence-graph conversion time;
- nauty canonicalization time;
- deduplication time;
- unattributed wall time;
- total candidate-contact count;
- total incidence vertices and edges;
- total candidate exact-key bytes and stored unique-key payload bytes;
- number of profiled canonicalizations;
- backend input-build, partition, engine, output-preparation, binary-key build, hash,
  and residual search canonicalization times when profiling is enabled;
- extraction and textual-encoding timers for callers that explicitly use `CanonicalForm`.

The purpose is to locate the actual bottleneck before optimizing it.

## Next phase

Phase 2 should attach a geometric realization layer to a canonical topology and ask
whether `R(Sigma)` is nonempty. Only then should the project introduce continuous
variables, non-overlap branches, Jacobians, shrink-direction tests, LP/NLP, or exact
algebra.

The discrete representation should remain independently testable even after geometry is
added.
