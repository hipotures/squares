#pragma once

#include "sqtopology/topology.hpp"

#include <cstddef>
#include <string>
#include <vector>

namespace sqtopology {

enum class RewriteKind {
    RemoveContact,
    AddSquareContact,
    AddWallContact,
};

struct Rewrite {
    RewriteKind kind{};
    std::string label;
    Topology topology;
};

struct RewriteOptions {
    bool include_removals{true};
    bool include_additions{true};
    std::size_t max_additions{256};
    bool include_labels{true};
};

// Checked entry point for external topologies. Rejects invalid input.
[[nodiscard]] std::vector<Rewrite> generate_rewrites(
    const Topology& topology,
    const RewriteOptions& options = {}
);

// Requires a valid topology. Normalizes contact ordering before enumeration.
// Removal preserves validity; additions use in-range, distinct-square features,
// infer their contact kind, and exclude existing events. Thus every returned
// topology is valid by construction. Search may trust this inductive invariant.
[[nodiscard]] std::vector<Rewrite> generate_rewrites_validated(
    const Topology& topology,
    const RewriteOptions& options = {}
);

}  // namespace sqtopology
