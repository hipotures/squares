#pragma once

#include "sqtopology/canonical.hpp"
#include "sqtopology/topology.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <map>
#include <string>
#include <vector>

namespace sqtopology {

// Research-only breadth-first instrumentation over the exact production rewrite
// and canonicalization semantics. It never changes the discovered canonical key
// set; it only adds per-depth and per-state aggregation. Counts produced here
// are global-unique single-process counts: there is no sharding and no
// cross-shard double counting.
struct ResearchOptions {
    std::size_t max_depth{4};
    // When true, the addition neighborhood is the complete event set
    // E(n) = 64*C(n,2) + 32*n, i.e. every semantic contact not already present.
    // When false, max_additions_per_parent is used verbatim, so the production
    // 256 cap can be reproduced for comparison. 0 disables additions entirely.
    bool additions_uncapped{true};
    std::size_t max_additions_per_parent{256};
    CanonicalBackend canonical_backend{CanonicalBackend::Traces};
    bool collect_symmetry{true};
    bool retain_keys{false};
};

// Exact value -> count histogram with streaming min/max/mean/quantiles.
struct ValueHistogram {
    std::uint64_t count{0};
    long double sum{0.0L};
    std::uint64_t min_value{0};
    std::uint64_t max_value{0};
    std::map<std::uint64_t, std::uint64_t> exact;

    void add(std::uint64_t value);
    [[nodiscard]] double mean() const;
    [[nodiscard]] std::uint64_t quantile(double q) const;
};

// Bit-length histogram for heavy-tailed quantities: bucket 0 is value 0,
// bucket k >= 1 covers [2^(k-1), 2^k).
struct LogHistogram {
    std::uint64_t count{0};
    std::uint64_t sum{0};
    std::uint64_t max_value{0};
    std::map<unsigned, std::uint64_t> buckets;

    void add(std::uint64_t value);
};

struct SymmetryStats {
    std::uint64_t states{0};
    std::uint64_t trivial_group{0};      // automorphism group of the class is trivial
    std::uint64_t nontrivial_group{0};
    double max_group_size_log10{0.0};
    ValueHistogram log2_group_size;      // floor(log2(group size))
    ValueHistogram orbit_count;
    ValueHistogram generator_count;
};

struct DepthRecord {
    std::size_t depth{0};
    // States at depth-1 that were expanded to produce the depth-d candidates.
    std::uint64_t parents_expanded{0};
    std::uint64_t raw_candidates{0};
    std::uint64_t duplicate_candidates{0};
    std::uint64_t duplicate_same_level{0};
    std::uint64_t duplicate_cross_level{0};
    std::uint64_t new_unique{0};
    std::uint64_t cumulative_unique{0};
    // Distinct canonical children per expanded parent (deduplicated within a parent).
    ValueHistogram children_per_parent;
    // Raw rewrite count per expanded parent.
    ValueHistogram rewrites_per_parent;
    // Contact count of the states first discovered at this depth.
    ValueHistogram state_contacts;
    // Contact count of every candidate generated at this depth.
    ValueHistogram candidate_contacts;
    std::uint64_t candidate_contact_total{0};
    // contact kind totals over newly discovered states: cc, cs, ss, wall.
    std::array<std::uint64_t, 4> state_type_totals{0, 0, 0, 0};
    SymmetryStats symmetry;
    // Depth-resolved edge accounting for the states first discovered at this
    // depth. geodesic_predecessors counts distinct canonical parents at depth
    // d-1, one entry per new state: for an unquotiented Hamming cube a state at
    // exact distance d has exactly d of them. same_level_edges must stay zero by
    // the weight-parity argument; backward_edges are children already known at
    // depth <= d-2.
    ValueHistogram geodesic_predecessors;
    std::uint64_t states_with_full_predecessors{0};
    std::uint64_t states_with_merged_predecessors{0};
    std::uint64_t same_level_edges{0};
    std::uint64_t backward_edges{0};
    double wall_seconds{0.0};
};

struct ConvergenceStats {
    std::uint64_t total_candidates{0};
    std::uint64_t total_new_unique{0};
    std::uint64_t total_duplicates{0};
    std::uint64_t total_distinct_parent_edges{0};
    ValueHistogram distinct_parents_per_child;
    LogHistogram incoming_events_per_child;
    LogHistogram same_parent_multiplicity;  // incoming events - distinct parents
    std::uint64_t zero_parent_states{0};
    std::uint64_t single_parent_states{0};
    std::uint64_t multi_parent_states{0};
    std::uint64_t max_distinct_parents{0};
    std::uint64_t max_incoming_events{0};
    // Depth-resolved predecessor accounting over all states at depth >= 1:
    // p(s) = distinct canonical neighbors first discovered at depth-1.
    // The labeled hypercube baseline is p = d for an empty seed.
    ValueHistogram geodesic_predecessors_per_state;
    std::uint64_t geodesic_predecessor_total{0};
    std::uint64_t depth_total{0};
    std::uint64_t full_predecessor_states{0};
    std::uint64_t merged_predecessor_states{0};
    std::uint64_t total_same_level_edges{0};
    std::uint64_t total_backward_edges{0};
    // Exact mean of p(s)/d(s): geodesic_predecessor_total / depth_total.
    double mean_geodesic_predecessor_ratio{0.0};
};

struct ResearchResult {
    std::string fixture;
    std::uint32_t square_count{0};
    std::uint64_t event_space_size{0};       // E(n)
    std::uint64_t seed_contacts{0};
    std::size_t max_depth{0};
    std::size_t max_additions_per_parent{0};
    bool additions_uncapped{true};
    CanonicalBackend canonical_backend{CanonicalBackend::Traces};
    std::string seed_key_hex;
    std::vector<DepthRecord> depths;
    ConvergenceStats convergence;
    std::uint64_t total_unique{0};
    double wall_seconds{0.0};
    std::uint64_t peak_rss_kib{0};
    // Sorted exact SQK5HEX keys, only when ResearchOptions::retain_keys is set.
    std::vector<std::string> unique_keys;
};

// E(n) = 64*C(n,2) + 32*n: every square-square feature pair plus every
// square-feature/wall pair. Each rewrite toggles exactly one event, so the full
// depth-d reachable labeled set is a Hamming ball of that radius in {0,1}^E.
[[nodiscard]] std::uint64_t full_event_space_size(std::uint32_t square_count) noexcept;

[[nodiscard]] ResearchResult run_research_search(
    const Topology& seed,
    const ResearchOptions& options
);

[[nodiscard]] std::string research_result_to_json(const ResearchResult& result);

}  // namespace sqtopology
