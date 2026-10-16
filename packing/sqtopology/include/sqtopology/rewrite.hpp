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
};

[[nodiscard]] std::vector<Rewrite> generate_rewrites(
    const Topology& topology,
    const RewriteOptions& options = {}
);

}  // namespace sqtopology
