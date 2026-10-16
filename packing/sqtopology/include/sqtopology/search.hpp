#pragma once

#include "sqtopology/rewrite.hpp"
#include "sqtopology/topology.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace sqtopology {

struct Shard {
    std::size_t index{0};
    std::size_t count{1};
};

struct SearchOptions {
    std::size_t max_candidates{100000};
    std::size_t max_unique{50000};
    std::size_t max_depth{3};
    std::size_t max_additions_per_parent{256};
    double wall_seconds{0.0};
    Shard shard{};
    bool retain_keys{false};
    bool profile_canonical{false};
};

struct SearchStats {
    std::uint64_t raw_candidates{};
    std::uint64_t valid_candidates{};
    std::uint64_t canonicalizations{};
    std::uint64_t duplicates{};
    std::uint64_t unique_states{};
    std::uint64_t first_level_selected{};
    std::uint64_t total_candidate_contacts{};
    std::uint64_t total_incidence_vertices{};
    std::uint64_t total_incidence_edges{};
    std::uint64_t canonical_profiled_calls{};
    double wall_seconds{};
    double generation_seconds{};
    double validation_seconds{};
    double graph_conversion_seconds{};
    double canonicalization_seconds{};
    double dedup_seconds{};
    double canonical_dense_build_seconds{};
    double canonical_partition_seconds{};
    double canonical_nauty_seconds{};
    double canonical_extraction_seconds{};
    double canonical_encoding_seconds{};
    double canonical_hash_seconds{};
};

struct SearchResult {
    SearchStats stats;
    std::vector<std::string> unique_encodings;
};

[[nodiscard]] SearchResult run_search(
    const Topology& seed,
    const SearchOptions& options
);
[[nodiscard]] std::string search_stats_to_json(
    const SearchStats& stats,
    Shard shard
);

}  // namespace sqtopology
