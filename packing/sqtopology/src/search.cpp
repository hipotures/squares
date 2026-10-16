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
    const auto started = Clock::now();

    std::unordered_set<std::string> seen;
    if (options.max_unique != 0) {
        seen.reserve(options.max_unique);
    }

    const auto seed_form = canonicalize(seed);
    seen.insert(seed_form.encoding);
    result.stats.canonicalizations = 1;
    result.stats.unique_states = 1;

    std::deque<QueueItem> frontier;

    const auto consider = [&](const Topology& candidate, std::size_t depth) -> bool {
        if (limit_reached(result.stats, options)
            || deadline_reached(started, options)) {
            return false;
        }

        ++result.stats.raw_candidates;

        auto t0 = Clock::now();
        const auto validation = candidate.validate();
        auto t1 = Clock::now();
        result.stats.validation_seconds += seconds_between(t0, t1);
        if (!validation.ok()) {
            return true;
        }
        ++result.stats.valid_candidates;

        t0 = Clock::now();
        const auto incidence = to_incidence_graph(candidate);
        t1 = Clock::now();
        result.stats.graph_conversion_seconds += seconds_between(t0, t1);

        t0 = Clock::now();
        const auto form = canonicalize_colored_graph(incidence);
        t1 = Clock::now();
        result.stats.canonicalization_seconds += seconds_between(t0, t1);
        ++result.stats.canonicalizations;

        t0 = Clock::now();
        const bool inserted = seen.insert(form.encoding).second;
        t1 = Clock::now();
        result.stats.dedup_seconds += seconds_between(t0, t1);

        if (!inserted) {
            ++result.stats.duplicates;
            return true;
        }

        result.stats.unique_states = seen.size();
        frontier.push_back(QueueItem{.topology = candidate.normalized(), .depth = depth});
        return !limit_reached(result.stats, options);
    };

    if (options.max_depth > 0
        && !limit_reached(result.stats, options)
        && !deadline_reached(started, options)) {
        RewriteOptions rewrite_options{
            .include_removals = true,
            .include_additions = true,
            .max_additions = options.max_additions_per_parent,
        };

        auto t0 = Clock::now();
        const auto root_rewrites = generate_rewrites(seed, rewrite_options);
        auto t1 = Clock::now();
        result.stats.generation_seconds += seconds_between(t0, t1);

        for (std::size_t i = 0; i < root_rewrites.size(); ++i) {
            if ((i % options.shard.count) != options.shard.index) {
                continue;
            }
            ++result.stats.first_level_selected;
            if (!consider(root_rewrites[i].topology, 1)) {
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
            const auto rewrites = generate_rewrites(parent.topology, rewrite_options);
            t1 = Clock::now();
            result.stats.generation_seconds += seconds_between(t0, t1);

            for (const auto& rewrite : rewrites) {
                if (!consider(rewrite.topology, parent.depth + 1)) {
                    break;
                }
            }
        }
    }

    result.stats.unique_states = seen.size();
    result.stats.wall_seconds = seconds_between(started, Clock::now());

    if (options.retain_keys) {
        result.unique_encodings.assign(seen.begin(), seen.end());
        std::sort(result.unique_encodings.begin(), result.unique_encodings.end());
    }
    return result;
}

std::string search_stats_to_json(
    const SearchStats& stats,
    Shard shard
) {
    std::ostringstream out;
    out << std::setprecision(17)
        << '{'
        << "\"schema\":\"sqtopology.search-summary.v1\","
        << "\"shard\":{\"index\":" << shard.index
        << ",\"count\":" << shard.count << "},"
        << "\"raw_candidates\":" << stats.raw_candidates << ','
        << "\"valid_candidates\":" << stats.valid_candidates << ','
        << "\"canonicalizations\":" << stats.canonicalizations << ','
        << "\"duplicates\":" << stats.duplicates << ','
        << "\"unique_states\":" << stats.unique_states << ','
        << "\"first_level_selected\":" << stats.first_level_selected << ','
        << "\"wall_seconds\":" << stats.wall_seconds << ','
        << "\"generation_seconds\":" << stats.generation_seconds << ','
        << "\"validation_seconds\":" << stats.validation_seconds << ','
        << "\"graph_conversion_seconds\":" << stats.graph_conversion_seconds << ','
        << "\"canonicalization_seconds\":" << stats.canonicalization_seconds << ','
        << "\"dedup_seconds\":" << stats.dedup_seconds
        << "}\n";
    return out.str();
}

}  // namespace sqtopology
