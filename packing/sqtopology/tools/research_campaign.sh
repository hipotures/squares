#!/usr/bin/env bash
#
# First topology-space research campaign driver.
#
#   tools/research_campaign.sh [BINARY] [OUTPUT_DIR]
#
# Every run is single-process, so the reported counts are global unique counts
# for the whole reachable set. The script writes one JSON file per run, plus
# exact-key files for the same-n seed-overlap study, plus a manifest.
#
# The campaign has two regimes:
#   * uncapped  - additions enumerate the full event neighborhood E(n); the
#                 reachable labeled set is the Hamming ball of radius d.
#   * capped    - the production --max-additions limit is reproduced so the
#                 effect of the truncation can be measured against the audit.
#
set -euo pipefail

binary="${1:-build-pgo/sqtopology}"
out="${2:-/tmp/sqresearch/campaign}"
mkdir -p "$out"

echo "binary=$binary" > "$out/manifest.txt"
"$binary" 2>&1 | head -1 >> "$out/manifest.txt" || true
git -C "$(dirname "$0")/.." rev-parse HEAD >> "$out/manifest.txt"
date -u +"%Y-%m-%dT%H:%M:%SZ" >> "$out/manifest.txt"

uncapped() {
    local fixture="$1" depth="$2"
    local json="$out/uncapped-${fixture}-d${depth}.json"
    echo "uncapped $fixture depth $depth"
    "$binary" research "$fixture" --max-depth "$depth" --json "$json" >/dev/null
}

capped() {
    local fixture="$1" depth="$2" cap="$3"
    local json="$out/capped${cap}-${fixture}-d${depth}.json"
    echo "capped $fixture depth $depth additions $cap"
    "$binary" research "$fixture" --max-depth "$depth" \
        --additions "$cap" --json "$json" >/dev/null
}

emit_keys() {
    local fixture="$1" depth="$2"
    local json="$out/keys-${fixture}-d${depth}.json"
    local keys="$out/keys-${fixture}-d${depth}.txt"
    echo "keys $fixture depth $depth"
    "$binary" research "$fixture" --max-depth "$depth" \
        --json "$json" --emit-keys "$keys" >/dev/null
}

# --- Uncapped: full event neighborhood -------------------------------- #
uncapped isolated-1 10
uncapped disjoint-2 5
uncapped corner-corner-2 4
uncapped corner-side-2 5
uncapped side-side-2 4
uncapped disjoint-4 3
uncapped line-4 3
uncapped grid-2x2 3
uncapped grid-3x3 2
uncapped grid-4x4-minus-one 2

# --- Capped: production 256-addition neighborhood --------------------- #
capped grid-2x2 3 256
capped grid-3x3 3 256
capped grid-4x4-minus-one 3 256

# --- Same-n seed overlap --------------------------------------------- #
for fixture in disjoint-2 corner-corner-2 corner-side-2 side-side-2; do
    emit_keys "$fixture" 4
done
for fixture in disjoint-4 line-4 grid-2x2; do
    emit_keys "$fixture" 3
done

echo "campaign complete: $out"
