#!/usr/bin/env bash
#
# Two-phase profile-guided optimization for the native engine.
#
#   tools/pgo_train.sh [build-dir] [seconds-per-shard]
#
# The first phase compiles an instrumented binary, the training workload below
# exercises the generation, canonicalization, exact-key, and dedup paths across
# several deterministic first-level shards, and the second phase rebuilds the
# same build tree with the collected profile.  The .gcda files stay in the build
# directory, so nothing generated is committed.  Re-run after a hot-path change.
set -euo pipefail

build_dir="${1:-build}"
seconds="${2:-6}"
jobs="$(nproc)"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

common=(
    --seconds "$seconds"
    --max-candidates 0
    --max-unique 0
    --max-depth 3
    --max-additions 256
    --canonical-backend traces
)

cmake -S . -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DSQTOPOLOGY_PGO=generate
cmake --build "$build_dir" -j "$jobs"

# Cover the widest fixture at several shards, then a smaller fixture, so the
# hot loops are all observed.  Traces is the retained backend.
for shard in 0 1 2 3; do
    "$build_dir/sqtopology" search grid-4x4-minus-one "${common[@]}" \
        --shard "$shard/4" >/dev/null
done
"$build_dir/sqtopology" search grid-3x3 "${common[@]}" --shard 0/1 >/dev/null

cmake -S . -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DSQTOPOLOGY_PGO=use
cmake --build "$build_dir" -j "$jobs"

echo "PGO build ready in $build_dir"
