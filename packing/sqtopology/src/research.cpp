#include "sqtopology/research.hpp"

#include "sqtopology/rewrite.hpp"

#include <algorithm>
#include <chrono>
#include <cmath>
#include <deque>
#include <iomanip>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>

#ifdef SQTOPOLOGY_BOOST_FLAT_SET
#include <boost/unordered/unordered_flat_map.hpp>
#endif

#include <sys/resource.h>

namespace sqtopology {
namespace {

using Clock = std::chrono::steady_clock;

double seconds_between(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double>(end - start).count();
}

constexpr std::uint32_t kNoParent = std::numeric_limits<std::uint32_t>::max();

struct ContactCounts {
    std::uint64_t total{0};
    std::array<std::uint64_t, 4> by_kind{0, 0, 0, 0};
};

ContactCounts count_contacts(const Topology& topology) {
    ContactCounts counts;
    for (const auto& contact : topology.contacts()) {
        ++counts.total;
        ++counts.by_kind[static_cast<std::size_t>(contact.kind)];
    }
    return counts;
}

unsigned log2_bucket(std::uint64_t value) {
    if (value == 0) {
        return 0;
    }
    unsigned bucket = 0;
    while ((std::uint64_t{1} << bucket) <= value) {
        ++bucket;
    }
    return bucket;  // value in [2^(bucket-1), 2^bucket)
}

}  // namespace

void ValueHistogram::add(std::uint64_t value) {
    if (count == 0) {
        min_value = value;
        max_value = value;
    } else {
        min_value = std::min(min_value, value);
        max_value = std::max(max_value, value);
    }
    ++count;
    sum += static_cast<long double>(value);
    ++exact[value];
}

double ValueHistogram::mean() const {
    if (count == 0) {
        return 0.0;
    }
    return static_cast<double>(sum / static_cast<long double>(count));
}

std::uint64_t ValueHistogram::quantile(double q) const {
    if (count == 0) {
        return 0;
    }
    if (q <= 0.0) {
        return min_value;
    }
    if (q >= 1.0) {
        return max_value;
    }
    const auto target = static_cast<std::uint64_t>(
        std::ceil(q * static_cast<double>(count))
    );
    std::uint64_t cumulative = 0;
    for (const auto& [value, occurrences] : exact) {
        cumulative += occurrences;
        if (cumulative >= std::max<std::uint64_t>(1, target)) {
            return value;
        }
    }
    return max_value;
}

void LogHistogram::add(std::uint64_t value) {
    ++count;
    sum += value;
    max_value = std::max(max_value, value);
    ++buckets[log2_bucket(value)];
}

namespace {

void write_histogram(std::ostringstream& out, const ValueHistogram& histogram) {
    out << "{\"count\":" << histogram.count
        << ",\"min\":" << histogram.min_value
        << ",\"max\":" << histogram.max_value
        << ",\"mean\":" << std::setprecision(12) << histogram.mean()
        << ",\"p50\":" << histogram.quantile(0.50)
        << ",\"p90\":" << histogram.quantile(0.90)
        << ",\"p99\":" << histogram.quantile(0.99)
        << ",\"exact\":[";
    bool first = true;
    for (const auto& [value, occurrences] : histogram.exact) {
        if (!first) {
            out << ',';
        }
        first = false;
        out << '[' << value << ',' << occurrences << ']';
    }
    out << "]}";
}

void write_log_histogram(std::ostringstream& out, const LogHistogram& histogram) {
    out << "{\"count\":" << histogram.count
        << ",\"sum\":" << histogram.sum
        << ",\"max\":" << histogram.max_value
        << ",\"buckets\":{";
    bool first = true;
    for (const auto& [bucket, occurrences] : histogram.buckets) {
        if (!first) {
            out << ',';
        }
        first = false;
        out << '"' << bucket << "\":" << occurrences;
    }
    out << "}}";
}

void write_symmetry(std::ostringstream& out, const SymmetryStats& symmetry) {
    out << "{\"states\":" << symmetry.states
        << ",\"trivial_group\":" << symmetry.trivial_group
        << ",\"nontrivial_group\":" << symmetry.nontrivial_group
        << ",\"max_group_size_log10\":" << std::setprecision(12)
        << symmetry.max_group_size_log10
        << ",\"log2_group_size\":";
    write_histogram(out, symmetry.log2_group_size);
    out << ",\"orbit_count\":";
    write_histogram(out, symmetry.orbit_count);
    out << ",\"generator_count\":";
    write_histogram(out, symmetry.generator_count);
    out << '}';
}

}  // namespace

std::uint64_t full_event_space_size(std::uint32_t square_count) noexcept {
    const std::uint64_t n = square_count;
    const std::uint64_t pairs = n * (n - 1U) / 2U;
    return 64U * pairs + 32U * n;
}

ResearchResult run_research_search(
    const Topology& seed,
    const ResearchOptions& options
) {
    const auto seed_validation = seed.validate();
    if (!seed_validation.ok()) {
        throw std::invalid_argument("research seed topology is invalid");
    }

    ResearchResult result;
    result.square_count = seed.square_count();
    result.event_space_size = full_event_space_size(result.square_count);
    result.max_depth = options.max_depth;
    result.canonical_backend = options.canonical_backend;
    result.additions_uncapped = options.additions_uncapped;
    const std::size_t max_additions = options.additions_uncapped
        ? static_cast<std::size_t>(result.event_space_size)
        : options.max_additions_per_parent;
    result.max_additions_per_parent = max_additions;

    const Topology normalized_seed = seed.normalized();
    result.seed_contacts = normalized_seed.contacts().size();

    const RewriteOptions rewrite_options{
        .include_removals = true,
        .include_additions = max_additions > 0,
        .max_additions = max_additions,
        .include_labels = false,
    };

    const auto started = Clock::now();

#ifdef SQTOPOLOGY_BOOST_FLAT_SET
    boost::unordered_flat_map<CanonicalKey, std::uint32_t, CanonicalKeyHash> seen;
#else
    std::unordered_map<CanonicalKey, std::uint32_t, CanonicalKeyHash> seen;
#endif

    // Compact per-state aggregates indexed by canonical id. No full Topology or
    // variable-length metadata is retained per state.
    std::vector<std::uint32_t> depth_of;
    std::vector<std::uint64_t> incoming_events;
    std::vector<std::uint32_t> distinct_parents;
    std::vector<std::uint32_t> last_parent;

    const auto ensure_capacity = [&](std::size_t size) {
        depth_of.resize(size, 0);
        incoming_events.resize(size, 0);
        distinct_parents.resize(size, 0);
        last_parent.resize(size, kNoParent);
    };

    const bool collect_symmetry = options.collect_symmetry;

    const auto canonicalize = [&](const Topology& topology, CanonicalSymmetry& symmetry) {
        const auto incidence = to_incidence_graph_validated(topology);
        return canonical_key_colored_graph(
            incidence,
            options.canonical_backend,
            nullptr,
            collect_symmetry ? &symmetry : nullptr
        );
    };

    // Seed.
    result.depths.emplace_back();
    DepthRecord& seed_record = result.depths.back();
    seed_record.depth = 0;
    seed_record.new_unique = 1;
    seed_record.cumulative_unique = 1;

    CanonicalSymmetry seed_symmetry;
    const auto seed_key = canonicalize(normalized_seed, seed_symmetry);
    result.seed_key_hex = canonical_key_hex(seed_key);
    ensure_capacity(1);
    {
        const auto counts = count_contacts(normalized_seed);
        for (std::size_t kind = 0; kind < 4; ++kind) {
            seed_record.state_type_totals[kind] = counts.by_kind[kind];
        }
    }
    seed_record.state_contacts.add(result.seed_contacts);
    if (collect_symmetry && seed_symmetry.available) {
        const double log10_size = std::log10(std::max(seed_symmetry.group_size1, 1.0))
            + static_cast<double>(seed_symmetry.group_size2);
        if (log10_size <= 0.0) {
            ++seed_record.symmetry.trivial_group;
        } else {
            ++seed_record.symmetry.nontrivial_group;
        }
        ++seed_record.symmetry.states;
        seed_record.symmetry.max_group_size_log10 = std::max(0.0, log10_size);
        const auto log2_size = static_cast<std::uint64_t>(
            std::max(0.0, std::floor(log10_size * 3.321928094887362))
        );
        seed_record.symmetry.log2_group_size.add(log2_size);
        seed_record.symmetry.orbit_count.add(
            static_cast<std::uint64_t>(seed_symmetry.orbit_count)
        );
        seed_record.symmetry.generator_count.add(
            static_cast<std::uint64_t>(seed_symmetry.generator_count)
        );
    } else if (collect_symmetry) {
        ++seed_record.symmetry.states;
    }

    std::uint32_t next_id = 1;
    seen.emplace(seed_key, 0);

    // Frontier entries carry the global canonical id, so distinct-parent
    // accounting is exact across levels.
    struct FrontierEntry {
        Topology topology;
        std::uint32_t id{0};
    };

    std::vector<FrontierEntry> frontier;
    if (options.max_depth > 0) {
        frontier.push_back(FrontierEntry{normalized_seed, 0});
    }

    for (std::size_t depth = 1; depth <= options.max_depth && !frontier.empty(); ++depth) {
        const auto level_started = Clock::now();
        DepthRecord record;
        record.depth = depth;
        record.parents_expanded = frontier.size();

        std::vector<FrontierEntry> next_frontier;

        for (std::size_t parent_index = 0; parent_index < frontier.size(); ++parent_index) {
            const std::uint32_t parent_id = frontier[parent_index].id;
            auto rewrites = generate_rewrites_validated(
                frontier[parent_index].topology,
                rewrite_options
            );
            record.rewrites_per_parent.add(rewrites.size());

            std::uint64_t distinct_children = 0;
            for (auto& rewrite : rewrites) {
                Topology& candidate = rewrite.topology;
                ++record.raw_candidates;

                const auto counts = count_contacts(candidate);
                record.candidate_contacts.add(counts.total);
                record.candidate_contact_total += counts.total;

                CanonicalSymmetry symmetry;
                const auto key = canonicalize(candidate, symmetry);

                std::uint32_t child_id = 0;
#ifdef SQTOPOLOGY_BOOST_FLAT_SET
                auto map_result = seen.try_emplace(std::move(key), next_id);
#else
                auto map_result = seen.emplace(std::move(key), next_id);
#endif
                if (map_result.second) {
                    child_id = next_id;
                    ++next_id;
                    ensure_capacity(next_id);
                    depth_of[child_id] = static_cast<std::uint32_t>(depth);
                    for (std::size_t kind = 0; kind < 4; ++kind) {
                        record.state_type_totals[kind] += counts.by_kind[kind];
                    }
                    record.state_contacts.add(counts.total);
                    ++record.new_unique;

                    if (collect_symmetry) {
                        ++record.symmetry.states;
                        if (symmetry.available) {
                            const double log10_size =
                                std::log10(std::max(symmetry.group_size1, 1.0))
                                + static_cast<double>(symmetry.group_size2);
                            if (log10_size <= 0.0) {
                                ++record.symmetry.trivial_group;
                            } else {
                                ++record.symmetry.nontrivial_group;
                            }
                            record.symmetry.max_group_size_log10 =
                                std::max(record.symmetry.max_group_size_log10, log10_size);
                            record.symmetry.log2_group_size.add(static_cast<std::uint64_t>(
                                std::max(0.0, std::floor(log10_size * 3.321928094887362))
                            ));
                            record.symmetry.orbit_count.add(
                                static_cast<std::uint64_t>(symmetry.orbit_count)
                            );
                            record.symmetry.generator_count.add(
                                static_cast<std::uint64_t>(symmetry.generator_count)
                            );
                        }
                    }

                    if (depth < options.max_depth) {
                        next_frontier.push_back(FrontierEntry{std::move(candidate), child_id});
                    }
                } else {
                    child_id = map_result.first->second;
                    ++record.duplicate_candidates;
                    if (depth_of[child_id] == static_cast<std::uint32_t>(depth)) {
                        ++record.duplicate_same_level;
                    } else {
                        ++record.duplicate_cross_level;
                    }
                }

                ++incoming_events[child_id];
                if (last_parent[child_id] != parent_id) {
                    last_parent[child_id] = parent_id;
                    ++distinct_parents[child_id];
                    ++distinct_children;
                }
            }

            record.children_per_parent.add(distinct_children);
        }

        record.cumulative_unique = seen.size();
        record.wall_seconds = seconds_between(level_started, Clock::now());
        result.depths.push_back(std::move(record));
        frontier = std::move(next_frontier);
    }

    result.total_unique = seen.size();
    result.wall_seconds = seconds_between(started, Clock::now());

    result.convergence.total_candidates = 0;
    result.convergence.total_duplicates = 0;
    for (const auto& record : result.depths) {
        result.convergence.total_candidates += record.raw_candidates;
        result.convergence.total_duplicates += record.duplicate_candidates;
    }
    result.convergence.total_new_unique = result.total_unique;

    std::uint64_t distinct_edges = 0;
    for (std::size_t id = 0; id < seen.size(); ++id) {
        result.convergence.distinct_parents_per_child.add(distinct_parents[id]);
        result.convergence.incoming_events_per_child.add(incoming_events[id]);
        const auto extra = incoming_events[id] >= distinct_parents[id]
            ? incoming_events[id] - distinct_parents[id]
            : 0;
        result.convergence.same_parent_multiplicity.add(extra);
        if (distinct_parents[id] == 0) {
            ++result.convergence.zero_parent_states;
        } else if (distinct_parents[id] > 1) {
            ++result.convergence.multi_parent_states;
        } else {
            ++result.convergence.single_parent_states;
        }
        result.convergence.max_distinct_parents =
            std::max<std::uint64_t>(result.convergence.max_distinct_parents, distinct_parents[id]);
        result.convergence.max_incoming_events =
            std::max<std::uint64_t>(result.convergence.max_incoming_events, incoming_events[id]);
        distinct_edges += distinct_parents[id];
    }
    result.convergence.total_distinct_parent_edges = distinct_edges;

    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        result.peak_rss_kib = static_cast<std::uint64_t>(usage.ru_maxrss);
    }

    if (options.retain_keys) {
        result.unique_keys.reserve(seen.size());
        for (const auto& entry : seen) {
            result.unique_keys.push_back(canonical_key_hex(entry.first));
        }
        std::sort(result.unique_keys.begin(), result.unique_keys.end());
    }

    return result;
}

std::string research_result_to_json(const ResearchResult& result) {
    std::ostringstream out;
    out << std::setprecision(17);
    out << '{'
        << "\"schema\":\"sqtopology.research.v1\","
        << "\"fixture\":\"" << result.fixture << "\","
        << "\"square_count\":" << result.square_count << ','
        << "\"event_space_size\":" << result.event_space_size << ','
        << "\"seed_contacts\":" << result.seed_contacts << ','
        << "\"max_depth\":" << result.max_depth << ','
        << "\"max_additions_per_parent\":" << result.max_additions_per_parent << ','
        << "\"additions_uncapped\":" << (result.additions_uncapped ? "true" : "false") << ','
        << "\"canonical_backend\":\"" << to_string(result.canonical_backend) << "\","
        << "\"seed_key_hex\":\"" << result.seed_key_hex << "\","
        << "\"counts_scope\":\"global-unique-single-process\","
        << "\"total_unique\":" << result.total_unique << ','
        << "\"wall_seconds\":" << result.wall_seconds << ','
        << "\"peak_rss_kib\":" << result.peak_rss_kib << ','
        << "\"depths\":[";

    for (std::size_t i = 0; i < result.depths.size(); ++i) {
        const auto& record = result.depths[i];
        if (i != 0) {
            out << ',';
        }
        out << "{\"depth\":" << record.depth
            << ",\"parents_expanded\":" << record.parents_expanded
            << ",\"raw_candidates\":" << record.raw_candidates
            << ",\"duplicate_candidates\":" << record.duplicate_candidates
            << ",\"duplicate_same_level\":" << record.duplicate_same_level
            << ",\"duplicate_cross_level\":" << record.duplicate_cross_level
            << ",\"new_unique\":" << record.new_unique
            << ",\"cumulative_unique\":" << record.cumulative_unique
            << ",\"children_per_parent\":";
        write_histogram(out, record.children_per_parent);
        out << ",\"rewrites_per_parent\":";
        write_histogram(out, record.rewrites_per_parent);
        out << ",\"state_contacts\":";
        write_histogram(out, record.state_contacts);
        out << ",\"candidate_contacts\":";
        write_histogram(out, record.candidate_contacts);
        out << ",\"candidate_contact_total\":" << record.candidate_contact_total
            << ",\"state_type_totals\":{\"corner_corner\":"
            << record.state_type_totals[0]
            << ",\"corner_side\":" << record.state_type_totals[1]
            << ",\"side_side\":" << record.state_type_totals[2]
            << ",\"wall\":" << record.state_type_totals[3] << '}'
            << ",\"symmetry\":";
        write_symmetry(out, record.symmetry);
        out << ",\"wall_seconds\":" << record.wall_seconds
            << '}';
    }

    out << "],\"convergence\":{\"total_candidates\":"
        << result.convergence.total_candidates
        << ",\"total_new_unique\":" << result.convergence.total_new_unique
        << ",\"total_duplicates\":" << result.convergence.total_duplicates
        << ",\"total_distinct_parent_edges\":"
        << result.convergence.total_distinct_parent_edges
        << ",\"single_parent_states\":" << result.convergence.single_parent_states
        << ",\"multi_parent_states\":" << result.convergence.multi_parent_states
        << ",\"zero_parent_states\":" << result.convergence.zero_parent_states
        << ",\"max_distinct_parents\":" << result.convergence.max_distinct_parents
        << ",\"max_incoming_events\":" << result.convergence.max_incoming_events
        << ",\"distinct_parents_per_child\":";
    write_histogram(out, result.convergence.distinct_parents_per_child);
    out << ",\"incoming_events_per_child\":";
    write_log_histogram(out, result.convergence.incoming_events_per_child);
    out << ",\"same_parent_multiplicity\":";
    write_log_histogram(out, result.convergence.same_parent_multiplicity);
    out << "},\"retained_keys\":" << (result.unique_keys.empty() ? "false" : "true")
        << "}\n";

    return out.str();
}

}  // namespace sqtopology
