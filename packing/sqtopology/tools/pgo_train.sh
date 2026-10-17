#!/usr/bin/env bash
#
# Two-phase profile-guided optimization for the native engine.
#
#   tools/pgo_train.sh [build-dir] [candidates-per-shard]
#
# The first phase compiles an instrumented binary, the training workload below
# exercises the generation, canonicalization, exact-key, and dedup paths across
# several deterministic first-level shards, and the second phase rebuilds the
# same build tree with the collected profile.  The .gcda files stay in the build
# directory, so nothing generated is committed.  Re-run after a hot-path change.
#
# Determinism: training uses a fixed candidate budget per shard rather than a
# wall-clock limit, so repeated invocations record the same counters.  The script
# also deletes any .gcda/.gcno from an earlier run before the generate phase, so a
# stale profile cannot contaminate the training counts, and it verifies that the
# instrumented library objects and the vendored Traces object actually recorded a
# profile before the use phase, which keeps a use build from silently degrading to
# non-PGO code.
set -euo pipefail

build_dir="${1:-build}"
candidates="${2:-400000}"
jobs="$(nproc)"

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

common=(
    --seconds 0
    --max-candidates "$candidates"
    --max-unique 0
    --max-depth 3
    --max-additions 256
    --canonical-backend traces
)

# Clean profiling state so this training run cannot merge stale counters.
if [ -d "$build_dir" ]; then
    find "$build_dir" -name '*.gcda' -delete
    find "$build_dir" -name '*.gcno' -delete
fi

cmake -S . -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DSQTOPOLOGY_PGO=generate
cmake --build "$build_dir" -j "$jobs"

# Cover the widest fixture at several shards, then a smaller fixture, so the
# hot loops are all observed.  Traces is the retained backend.
for shard in 0 1 2 3; do
    "$build_dir/sqtopology" search grid-4x4-minus-one "${common[@]}" \
        --shard "$shard/4" >/dev/null
done
"$build_dir/sqtopology" search grid-3x3 "${common[@]}" --shard 0/1 >/dev/null

core_profiles="$(find "$build_dir/CMakeFiles/sqtopology_core.dir" -name '*.gcda' 2>/dev/null | wc -l)"
main_profiles="$(find "$build_dir/CMakeFiles/sqtopology.dir" -name '*.gcda' 2>/dev/null | wc -l)"
if [ "$core_profiles" -eq 0 ] || [ "$main_profiles" -eq 0 ]; then
    echo "pgo_train: no profile data was recorded; aborting before the use phase" >&2
    exit 1
fi

if [ -d "$build_dir/CMakeFiles/sqtopology_cached_traces.dir" ]; then
    traces_profiles="$(find "$build_dir/CMakeFiles/sqtopology_cached_traces.dir" \
        -name '*.gcda' 2>/dev/null | wc -l)"
    if [ "$traces_profiles" -eq 0 ]; then
        echo "pgo_train: the vendored Traces object recorded no profile; aborting" >&2
        exit 1
    fi
fi

cmake -S . -B "$build_dir" -DCMAKE_BUILD_TYPE=Release -DSQTOPOLOGY_PGO=use
cmake --build "$build_dir" -j "$jobs"

echo "PGO build ready in $build_dir"
