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

Each square is converted to a colored graph gadget with one square-object vertex and an
alternating eight-cycle of ports:

~~~text
corner0 - side0 - corner1 - side1 - corner2 - side2 - corner3 - side3 - corner0
~~~

The center is connected to all eight ports. Side and corner ports have different colors,
but the numeric port indices do not. The color-preserving automorphism group of this gadget
contains exactly the intended square `D4` feature relabelings.

The container has one container-object vertex and a four-cycle of equally colored wall
vertices. This exposes the container's `D4` symmetry to canonical labeling.

A contact is a factor/event vertex, colored by contact kind, connected to the participating
feature ports. A wall contact connects a square feature port to a container-wall vertex.

Packed-square object vertices all share one color. nauty may therefore permute them, so
square IDs are also quotiented out.

The canonical equality key is the full versioned encoding (`SQT1|...`), not its 64-bit
fingerprint. The FNV-1a fingerprint is only a compact display/index aid.

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

## Inspect fixtures

~~~bash
./build/sqtopology list-fixtures

./build/sqtopology inspect grid-3x3 \
  --json /tmp/grid-3x3.json \
  --dot /tmp/grid-3x3.dot \
  --canonical

dot -Tsvg /tmp/grid-3x3.dot -o /tmp/grid-3x3.svg
~~~

Fixtures include isolated and disjoint squares, each elementary contact kind, `2x2`,
`3x3`, `4x4`, and a `4x4` grid with one square removed.

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
After that first-level assignment, each process generates, validates, canonicalizes, and
deduplicates its descendants locally.

This has two consequences:

- there is no per-candidate coordinator or IPC bottleneck;
- different shards can rediscover the same deeper canonical state.

The second point is deliberate in phase 1. Shard outputs can be merged offline, and a
future canonical-augmentation search can remove cross-shard overlap if measurements show
that it matters. Therefore current shard runs are **not** an exhaustive partition proof.

`--emit-keys FILE` writes sorted full canonical encodings for offline comparison or merge.

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

## Measurement fields

Native search summaries separately report:

- raw candidates;
- valid candidates;
- canonicalizations;
- duplicates;
- local unique states;
- root rewrites selected by the shard;
- wall time;
- rewrite-generation time;
- semantic-validation time;
- incidence-graph conversion time;
- nauty canonicalization time;
- deduplication time.

The purpose is to locate the actual bottleneck before optimizing it.

## Next phase

Phase 2 should attach a geometric realization layer to a canonical topology and ask
whether `R(Sigma)` is nonempty. Only then should the project introduce continuous
variables, non-overlap branches, Jacobians, shrink-direction tests, LP/NLP, or exact
algebra.

The discrete representation should remain independently testable even after geometry is
added.
