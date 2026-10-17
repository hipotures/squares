#pragma once

#include "sqtopology/canonical.hpp"
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
    CanonicalBackend canonical_backend{CanonicalBackend::Traces};
    // Diagnostic: check the construction-by-invariant contract on every child.
    bool validate_generated{false};
};

struct SearchStats {
    CanonicalBackend canonical_backend{CanonicalBackend::Traces};
    std::uint64_t raw_candidates{};
    std::uint64_t valid_candidates{};
    std::uint64_t canonicalizations{};
    std::uint64_t duplicates{};
    std::uint64_t unique_states{};
    std::uint64_t first_level_selected{};
    std::uint64_t total_candidate_contacts{};
    std::uint64_t total_incidence_vertices{};
    std::uint64_t total_incidence_edges{};
    std::uint64_t total_canonical_key_bytes{};
    std::uint64_t stored_canonical_key_bytes{};
    std::uint64_t canonical_profiled_calls{};
    std::uint64_t peak_frontier_states{};
    std::uint64_t peak_rss_kib{};
    double wall_seconds{};
    double generation_seconds{};
    double validation_seconds{};
    double graph_conversion_seconds{};
    double canonicalization_seconds{};
    double dedup_seconds{};
    double canonical_input_build_seconds{};
    double canonical_partition_seconds{};
    double canonical_engine_seconds{};
    double canonical_output_prepare_seconds{};
    double canonical_key_build_seconds{};
    double canonical_extraction_seconds{};
    double canonical_encoding_seconds{};
    double canonical_hash_seconds{};
    double user_cpu_seconds{};
    double system_cpu_seconds{};
    std::uint64_t minor_page_faults{};
    std::uint64_t major_page_faults{};
    std::uint64_t voluntary_context_switches{};
    std::uint64_t involuntary_context_switches{};
};

struct SearchResult {
    SearchStats stats;
    // When retained, exact binary search keys are rendered as versioned hexadecimal text.
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
