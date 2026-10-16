#include "sqtopology/search.hpp"

#include "sqtopology/canonical.hpp"

#include <algorithm>
#include <chrono>
#include <deque>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <unordered_set>
#include <utility>

namespace sqtopology {
namespace {

using Clock = std::chrono::steady_clock;

double seconds_between(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double>(end - start).count();
}

void accumulate_canonical_profile(
    SearchStats& stats,
    const CanonicalProfile& profile
) {
    stats.canonical_profiled_calls += profile.calls;
    stats.canonical_input_build_seconds += profile.input_build_seconds;
    stats.canonical_partition_seconds += profile.partition_seconds;
    stats.canonical_engine_seconds += profile.engine_seconds;
    stats.canonical_output_conversion_seconds += profile.output_conversion_seconds;
    stats.canonical_key_build_seconds += profile.key_build_seconds;
    stats.canonical_extraction_seconds += profile.extraction_seconds;
    stats.canonical_encoding_seconds += profile.encoding_seconds;
    stats.canonical_hash_seconds += profile.hash_seconds;
}

struct QueueItem {
    Topology topology;
    std::size_t depth{};
};

bool limit_reached(const SearchStats& stats, const SearchOptions& options) {
    if (options.max_candidates != 0
        && stats.raw_candidates >= options.max_candidates) {
        return true;
    }
    if (options.max_unique != 0
        && stats.unique_states >= options.max_unique) {
        return true;
    }
    return false;
}

bool deadline_reached(
    Clock::time_point started,
    const SearchOptions& options
) {
    return options.wall_seconds > 0.0
        && seconds_between(started, Clock::now()) >= options.wall_seconds;
}

}  // namespace

SearchResult run_search(
    const Topology& seed,
    const SearchOptions& options
) {
    if (options.shard.count == 0 || options.shard.index >= options.shard.count) {
        throw std::invalid_argument("invalid shard: expected 0 <= index < count");
    }

    const auto seed_validation = seed.validate();
    if (!seed_validation.ok()) {
        throw std::invalid_argument("search seed topology is invalid");
    }

    SearchResult result;
    result.stats.canonical_backend = options.canonical_backend;
    const auto started = Clock::now();

    std::unordered_set<CanonicalKey, CanonicalKeyHash> seen;
    if (options.max_unique != 0) {
        seen.reserve(options.max_unique);
    }

    const auto seed_incidence = to_incidence_graph_validated(seed.normalized());
    auto seed_key = canonical_key_colored_graph(
        seed_incidence,
        options.canonical_backend
    );
    result.stats.stored_canonical_key_bytes = seed_key.bytes.size();
    seen.insert(std::move(seed_key));
    result.stats.canonicalizations = 1;
    result.stats.unique_states = 1;

    std::deque<QueueItem> frontier;

    const auto consider = [&](Topology candidate, std::size_t depth) -> bool {
        if (limit_reached(result.stats, options)
            || deadline_reached(started, options)) {
            return false;
        }

        ++result.stats.raw_candidates;
        result.stats.total_candidate_contacts += candidate.contacts().size();

        auto t0 = Clock::now();
        const auto validation = candidate.validate();
        auto t1 = Clock::now();
        result.stats.validation_seconds += seconds_between(t0, t1);
        if (!validation.ok()) {
            return true;
        }
        ++result.stats.valid_candidates;

        t0 = Clock::now();
        const auto incidence = to_incidence_graph_validated(candidate);
        t1 = Clock::now();
        result.stats.graph_conversion_seconds += seconds_between(t0, t1);
        result.stats.total_incidence_vertices += incidence.vertex_count();
        result.stats.total_incidence_edges += incidence.edges.size();

        CanonicalProfile canonical_profile;
        t0 = Clock::now();
        auto key = canonical_key_colored_graph(
            incidence,
            options.canonical_backend,
            options.profile_canonical ? &canonical_profile : nullptr
        );
        t1 = Clock::now();
        result.stats.canonicalization_seconds += seconds_between(t0, t1);
        ++result.stats.canonicalizations;
        result.stats.total_canonical_key_bytes += key.bytes.size();
        const auto key_bytes = key.bytes.size();
        if (options.profile_canonical) {
            accumulate_canonical_profile(result.stats, canonical_profile);
        }

        t0 = Clock::now();
        const bool inserted = seen.insert(std::move(key)).second;
        t1 = Clock::now();
        result.stats.dedup_seconds += seconds_between(t0, t1);

        if (!inserted) {
            ++result.stats.duplicates;
            return true;
        }

        result.stats.stored_canonical_key_bytes += key_bytes;
        result.stats.unique_states = seen.size();
        frontier.push_back(
            QueueItem{
                .topology = std::move(candidate),
                .depth = depth,
            }
        );
        return !limit_reached(result.stats, options);
    };

    if (options.max_depth > 0
        && !limit_reached(result.stats, options)
        && !deadline_reached(started, options)) {
        RewriteOptions rewrite_options{
            .include_removals = true,
            .include_additions = true,
            .max_additions = options.max_additions_per_parent,
            .include_labels = false,
        };

        auto t0 = Clock::now();
        auto root_rewrites = generate_rewrites(seed, rewrite_options);
        auto t1 = Clock::now();
        result.stats.generation_seconds += seconds_between(t0, t1);

        for (std::size_t i = 0; i < root_rewrites.size(); ++i) {
            if ((i % options.shard.count) != options.shard.index) {
                continue;
            }
            ++result.stats.first_level_selected;
            if (!consider(std::move(root_rewrites[i].topology), 1)) {
                break;
            }
        }

        while (!frontier.empty()
               && !limit_reached(result.stats, options)
               && !deadline_reached(started, options)) {
            QueueItem parent = std::move(frontier.front());
            frontier.pop_front();

            if (parent.depth >= options.max_depth) {
                continue;
            }

            t0 = Clock::now();
            auto rewrites = generate_rewrites(parent.topology, rewrite_options);
            t1 = Clock::now();
            result.stats.generation_seconds += seconds_between(t0, t1);

            for (auto& rewrite : rewrites) {
                if (!consider(std::move(rewrite.topology), parent.depth + 1)) {
                    break;
                }
            }
        }
    }

    result.stats.unique_states = seen.size();
    result.stats.wall_seconds = seconds_between(started, Clock::now());

    if (options.retain_keys) {
        result.unique_encodings.reserve(seen.size());
        for (const auto& key : seen) {
            result.unique_encodings.push_back(canonical_key_hex(key));
        }
        std::sort(result.unique_encodings.begin(), result.unique_encodings.end());
    }
    return result;
}

std::string search_stats_to_json(
    const SearchStats& stats,
    Shard shard
) {
    const double attributed_seconds =
        stats.generation_seconds
        + stats.validation_seconds
        + stats.graph_conversion_seconds
        + stats.canonicalization_seconds
        + stats.dedup_seconds;
    const double unattributed_seconds =
        std::max(0.0, stats.wall_seconds - attributed_seconds);

    const double canonical_profile_sum =
        stats.canonical_input_build_seconds
        + stats.canonical_partition_seconds
        + stats.canonical_engine_seconds
        + stats.canonical_output_conversion_seconds
        + stats.canonical_key_build_seconds
        + stats.canonical_extraction_seconds
        + stats.canonical_encoding_seconds
        + stats.canonical_hash_seconds;
    const double canonical_profile_other_seconds =
        stats.canonical_profiled_calls > 0
            ? std::max(0.0, stats.canonicalization_seconds - canonical_profile_sum)
            : 0.0;

    std::ostringstream out;
    out << std::setprecision(17)
        << '{'
        << "\"schema\":\"sqtopology.search-summary.v6\","
        << "\"canonical_backend\":\"" << to_string(stats.canonical_backend) << "\","
        << "\"shard\":{\"index\":" << shard.index
        << ",\"count\":" << shard.count << "},"
        << "\"raw_candidates\":" << stats.raw_candidates << ','
        << "\"valid_candidates\":" << stats.valid_candidates << ','
        << "\"canonicalizations\":" << stats.canonicalizations << ','
        << "\"duplicates\":" << stats.duplicates << ','
        << "\"unique_states\":" << stats.unique_states << ','
        << "\"first_level_selected\":" << stats.first_level_selected << ','
        << "\"total_candidate_contacts\":" << stats.total_candidate_contacts << ','
        << "\"total_incidence_vertices\":" << stats.total_incidence_vertices << ','
        << "\"total_incidence_edges\":" << stats.total_incidence_edges << ','
        << "\"total_canonical_key_bytes\":" << stats.total_canonical_key_bytes << ','
        << "\"stored_canonical_key_bytes\":" << stats.stored_canonical_key_bytes << ','
        << "\"canonical_profile_enabled\":"
        << (stats.canonical_profiled_calls > 0 ? "true" : "false") << ','
        << "\"canonical_profiled_calls\":" << stats.canonical_profiled_calls << ','
        << "\"wall_seconds\":" << stats.wall_seconds << ','
        << "\"generation_seconds\":" << stats.generation_seconds << ','
        << "\"validation_seconds\":" << stats.validation_seconds << ','
        << "\"graph_conversion_seconds\":" << stats.graph_conversion_seconds << ','
        << "\"canonicalization_seconds\":" << stats.canonicalization_seconds << ','
        << "\"dedup_seconds\":" << stats.dedup_seconds << ','
        << "\"unattributed_seconds\":" << unattributed_seconds << ','
        << "\"canonical_input_build_seconds\":"
        << stats.canonical_input_build_seconds << ','
        << "\"canonical_partition_seconds\":"
        << stats.canonical_partition_seconds << ','
        << "\"canonical_engine_seconds\":"
        << stats.canonical_engine_seconds << ','
        << "\"canonical_output_conversion_seconds\":"
        << stats.canonical_output_conversion_seconds << ','
        << "\"canonical_key_build_seconds\":"
        << stats.canonical_key_build_seconds << ','
        << "\"canonical_extraction_seconds\":"
        << stats.canonical_extraction_seconds << ','
        << "\"canonical_encoding_seconds\":"
        << stats.canonical_encoding_seconds << ','
        << "\"canonical_hash_seconds\":"
        << stats.canonical_hash_seconds << ','
        << "\"canonical_profile_other_seconds\":"
        << canonical_profile_other_seconds
        << "}\n";
    return out.str();
}

}  // namespace sqtopology
