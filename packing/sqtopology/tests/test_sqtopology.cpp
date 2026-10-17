#include "sqtopology/canonical.hpp"
#include "sqtopology/export.hpp"
#include "sqtopology/fixtures.hpp"
#include "sqtopology/rewrite.hpp"
#include "sqtopology/search.hpp"
#include "sqtopology/topology.hpp"

#include <algorithm>
#include <cstdint>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <unordered_set>
#ifdef SQTOPOLOGY_BOOST_FLAT_SET
#include <boost/unordered/unordered_flat_set.hpp>
#endif
#include <vector>

namespace {

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_valid(
    const sqtopology::Topology& topology,
    const std::string& message
) {
    const auto validation = topology.validate();
    if (validation.ok()) {
        return;
    }

    std::string detail = message;
    for (const auto& error : validation.errors) {
        detail += "; " + error;
    }
    throw std::runtime_error(detail);
}

std::string canonical_encoding(const sqtopology::Topology& topology) {
    return sqtopology::canonicalize(topology).encoding;
}

sqtopology::CanonicalKey canonical_key(
    const sqtopology::Topology& topology,
    sqtopology::CanonicalBackend backend = sqtopology::CanonicalBackend::DenseNauty
) {
    return sqtopology::canonical_key_colored_graph(
        sqtopology::to_incidence_graph(topology),
        backend
    );
}

void test_validation() {
    using namespace sqtopology;

    expect_valid(make_fixture("grid-3x3"), "grid fixture must validate");
    expect_valid(make_fixture("disjoint-2"), "free squares must be representable");

    Topology self_contact(2);
    self_contact.add_contact(
        make_square_contact(
            FeatureRef{0, FeatureKind::Corner, 0},
            FeatureRef{0, FeatureKind::Corner, 1}
        )
    );
    expect(!self_contact.validate().ok(), "self-contact must be rejected");

    Topology duplicate(2);
    const auto contact = make_square_contact(
        FeatureRef{0, FeatureKind::Side, 1},
        FeatureRef{1, FeatureKind::Side, 3}
    );
    duplicate.add_contact(contact);
    duplicate.add_contact(contact);
    expect(!duplicate.validate().ok(), "duplicate contact events must be rejected");
}

void test_square_permutation_invariance() {
    using namespace sqtopology;

    const auto base = make_fixture("grid-3x3");
    std::vector<SquareId> permutation(base.square_count());
    for (SquareId old = 0; old < base.square_count(); ++old) {
        permutation[old] = base.square_count() - 1U - old;
    }

    const auto transformed = permute_squares(base, permutation);
    expect(
        canonical_encoding(base) == canonical_encoding(transformed),
        "canonical form must quotient packed-square permutation"
    );
}

void test_local_d4_invariance() {
    using namespace sqtopology;

    const auto base = make_fixture("grid-3x3");
    const auto expected = canonical_encoding(base);

    for (SquareId square = 0; square < base.square_count(); ++square) {
        for (const auto transform : all_d4_transforms()) {
            const auto transformed = relabel_square(base, square, transform);
            expect(
                canonical_encoding(transformed) == expected,
                "canonical form must quotient every square's local D4 relabeling"
            );
        }
    }
}

void test_container_d4_invariance() {
    using namespace sqtopology;

    const auto base = make_fixture("grid-4x4-minus-one");
    const auto expected = canonical_encoding(base);

    for (const auto transform : all_d4_transforms()) {
        const auto transformed = relabel_container(base, transform);
        expect(
            canonical_encoding(transformed) == expected,
            "canonical form must quotient container D4 relabeling"
        );
    }
}

void test_distinct_topologies_remain_distinct() {
    using namespace sqtopology;

    const auto isolated = canonical_encoding(make_fixture("isolated-1"));
    const auto disjoint = canonical_encoding(make_fixture("disjoint-2"));
    const auto cc = canonical_encoding(make_fixture("corner-corner-2"));
    const auto cs = canonical_encoding(make_fixture("corner-side-2"));
    const auto ss = canonical_encoding(make_fixture("side-side-2"));

    expect(isolated != disjoint, "one and two free squares must differ");
    expect(cc != cs, "corner-corner and corner-side contacts must differ");
    expect(cc != ss, "corner-corner and side-side contacts must differ");
    expect(cs != ss, "corner-side and side-side contacts must differ");
}

void test_grid_3x3_central_square_has_eight_square_contacts() {
    using namespace sqtopology;

    const auto topology = make_fixture("grid-3x3");
    std::size_t incident = 0;
    for (const auto& contact : topology.contacts()) {
        if (contact.kind == ContactKind::Wall) {
            continue;
        }
        if (contact.a.square == 4
            || (contact.b.has_value() && contact.b->square == 4)) {
            ++incident;
        }
    }
    expect(
        incident == 8,
        "3x3 central square must have four side and four diagonal point contacts"
    );
}

void test_rewrites_are_deterministic() {
    using namespace sqtopology;

    const auto base = make_fixture("grid-2x2");
    const RewriteOptions options{
        .include_removals = true,
        .include_additions = true,
        .max_additions = 32,
    };
    const auto first = generate_rewrites(base, options);
    const auto second = generate_rewrites(base, options);

    expect(first.size() == second.size(), "rewrite count must be deterministic");
    for (std::size_t i = 0; i < first.size(); ++i) {
        expect(first[i].label == second[i].label, "rewrite labels must be deterministic");
        expect(
            canonical_encoding(first[i].topology)
                == canonical_encoding(second[i].topology),
            "rewrite topology sequence must be deterministic"
        );
    }
}

void test_rewrite_validity_contract() {
    using namespace sqtopology;
    for (const auto& name : fixture_names()) {
        auto parent = make_fixture(name);
        // Descend through several generated states, checking removals and both
        // square/wall additions. Small fixtures exhaust the square-pair domain.
        for (std::size_t depth = 0; depth < 4; ++depth) {
            const RewriteOptions options{.max_additions = 256, .include_labels = false};
            const auto checked = generate_rewrites(parent, options);
            const auto trusted = generate_rewrites_validated(parent, options);
            expect(checked.size() == trusted.size(), "trusted rewrite count must match");
            for (std::size_t i = 0; i < trusted.size(); ++i) {
                expect_valid(trusted[i].topology, "every generated state must be valid");
                expect(trusted[i].topology.contacts() == checked[i].topology.contacts(),
                       "trusted rewrites must preserve deterministic contact ordering");
                expect(trusted[i].topology.contacts()
                           == trusted[i].topology.normalized().contacts(),
                       "generated contacts must remain normalized");
            }
            if (trusted.empty()) break;
            parent = trusted[(depth * 71 + 13) % trusted.size()].topology;
        }
    }

    SearchOptions options{
        .max_candidates = 1500, .max_unique = 0, .max_depth = 3,
        .max_additions_per_parent = 32, .retain_keys = true,
    };
    const auto seed = make_fixture("grid-3x3");
    for (std::size_t shard = 0; shard < 3; ++shard) {
        options.shard = Shard{.index = shard, .count = 3};
        options.validate_generated = false;
        const auto trusted = run_search(seed, options);
        options.validate_generated = true;
        const auto checked = run_search(seed, options);
        expect(trusted.unique_encodings == checked.unique_encodings,
               "diagnostic validation must preserve exact search keys and sharding");
        expect(trusted.stats.raw_candidates == checked.stats.raw_candidates
                   && trusted.stats.duplicates == checked.stats.duplicates,
               "diagnostic validation must preserve the rewrite sequence");
    }

    Topology invalid(0);
    bool rewrite_rejected = false;
    bool search_rejected = false;
    bool incidence_rejected = false;
    try { (void)generate_rewrites(invalid); }
    catch (const std::invalid_argument&) { rewrite_rejected = true; }
    try { (void)run_search(invalid, options); }
    catch (const std::invalid_argument&) { search_rejected = true; }
    try { (void)to_incidence_graph(invalid); }
    catch (const std::invalid_argument&) { incidence_rejected = true; }
    expect(rewrite_rejected && search_rejected && incidence_rejected,
           "external topology entry points must keep full validation");
}

void test_shard_reproducibility() {
    using namespace sqtopology;

    const SearchOptions options{
        .max_candidates = 120,
        .max_unique = 100,
        .max_depth = 2,
        .max_additions_per_parent = 32,
        .wall_seconds = 0.0,
        .shard = Shard{.index = 1, .count = 3},
        .retain_keys = true,
    };

    const auto seed = make_fixture("grid-3x3");
    const auto first = run_search(seed, options);
    const auto second = run_search(seed, options);

    expect(
        first.unique_encodings == second.unique_encodings,
        "same seed/config/shard must produce the same canonical state set"
    );
    expect(
        first.stats.raw_candidates == second.stats.raw_candidates,
        "same shard must process the same candidate count"
    );
    expect(
        first.stats.duplicates == second.stats.duplicates,
        "same shard must have the same duplicate count"
    );
}

void test_sorted_contact_insertion() {
    using namespace sqtopology;
    const auto contacts_fixture = make_fixture("grid-2x2");
    for (const auto& name : fixture_names()) {
        const auto base = make_fixture(name).normalized();
        for (const auto& contact : contacts_fixture.contacts()) {
            // Ordering equivalence is independent of semantic endpoint bounds.
            auto appended = base;
            appended.add_contact(contact);
            const auto inserted = base.with_added_contact_normalized(contact);
            expect(inserted.contacts() == appended.normalized().contacts(),
                   "sorted insertion must exactly match append-and-normalize ordering");
            if (contact.b) {
                auto reversed = contact;
                std::swap(reversed.a, *reversed.b);
                expect(base.with_added_contact_normalized(reversed).contacts()
                           == inserted.contacts(),
                       "insertion must normalize reversed contact endpoints");
            }
        }
    }
}

void test_depth_bound_frontier() {
    using namespace sqtopology;
    const SearchOptions options{
        .max_candidates = 0, .max_unique = 0, .max_depth = 1,
        .max_additions_per_parent = 32, .retain_keys = true,
    };
    const auto seed = make_fixture("grid-2x2");
    const auto result = run_search(seed, options);
    expect(result.stats.peak_frontier_states == 0,
           "depth-bound states must be deduplicated without retaining topologies");
    std::vector<std::string> expected{canonical_key_hex(canonical_key(seed, CanonicalBackend::Traces))};
    for (const auto& child : generate_rewrites(seed, RewriteOptions{.max_additions = 32})) {
        expected.push_back(canonical_key_hex(canonical_key(child.topology, CanonicalBackend::Traces)));
    }
    std::sort(expected.begin(), expected.end());
    expected.erase(std::unique(expected.begin(), expected.end()), expected.end());
    expect(result.unique_encodings == expected,
           "depth-bound states must still participate in exact canonical deduplication");
}

void test_export_smoke() {
    using namespace sqtopology;

    const auto topology = make_fixture("corner-side-2");
    const auto canonical = canonicalize(topology);
    const auto json = topology_to_json(topology, canonical);
    const auto dot = topology_to_dot(topology);

    expect(
        json.find("\"schema\":\"sqtopology.semantic.v1\"") != std::string::npos,
        "JSON export must identify its schema"
    );
    expect(
        json.find("corner-side") != std::string::npos,
        "JSON export must include contact type"
    );
    expect(
        dot.find("graph sqtopology") != std::string::npos,
        "DOT export must be a graph"
    );
    expect(
        dot.find("shape=diamond") != std::string::npos,
        "DOT export must expose contact-event nodes"
    );
}

void test_validated_incidence_fast_path_matches_checked_path() {
    using namespace sqtopology;

    const auto topology = make_fixture("grid-4x4-minus-one").normalized();
    const auto checked = canonicalize_colored_graph(to_incidence_graph(topology));
    const auto fast = canonicalize_colored_graph(to_incidence_graph_validated(topology));

    expect(
        checked.encoding == fast.encoding,
        "validated incidence fast path must preserve canonical semantics"
    );
}

void test_incidence_prefix_cache_transitions() {
    using namespace sqtopology;
    for (const std::uint32_t squares : {1U, 15U, 4U, 257U, 15U, 4U, 1U}) {
        const auto graph = to_incidence_graph(Topology(squares));
        expect(graph.vertex_count() == 9U * squares + 5U,
               "fixed incidence prefix must preserve every square and container vertex");
        expect(graph.edges.size() == 16U * squares + 8U,
               "fixed incidence prefix must preserve all gadget edges across size changes");
        std::vector<unsigned> degrees(graph.vertex_count());
        for (const auto& [a, b] : graph.edges) { ++degrees[a]; ++degrees[b]; }
        for (std::uint32_t square = 0; square < squares; ++square) {
            expect(degrees[9U * square] == 8, "square centers must retain all eight ports");
            for (unsigned port = 1; port <= 8; ++port)
                expect(degrees[9U * square + port] == 3, "free ports must retain their center and cycle neighbors");
        }
        expect(degrees[9U * squares] == 4, "container center must retain all four walls");
    }
    const auto first = to_incidence_graph(make_fixture("corner-corner-2"));
    (void)to_incidence_graph(make_fixture("side-side-2"));
    const auto again = to_incidence_graph(make_fixture("corner-corner-2"));
    expect(first.colors == again.colors && first.edges == again.edges,
           "cached prefixes must never retain contact factors from prior topologies");
}

void test_backend_names() {
    using namespace sqtopology;

    expect(
        canonical_backend_from_string("dense-nauty") == CanonicalBackend::DenseNauty,
        "dense-nauty backend name must parse"
    );
    expect(
        canonical_backend_from_string("sparse-nauty") == CanonicalBackend::SparseNauty,
        "sparse-nauty backend name must parse"
    );
    expect(
        canonical_backend_from_string("traces") == CanonicalBackend::Traces,
        "traces backend name must parse"
    );
    expect(
        to_string(CanonicalBackend::DenseNauty) == "dense-nauty",
        "dense backend must have a stable name"
    );
}

void test_binary_key_matches_textual_equivalence() {
    using namespace sqtopology;

    const auto base = make_fixture("grid-3x3");
    std::vector<SquareId> permutation(base.square_count());
    for (SquareId old = 0; old < base.square_count(); ++old) {
        permutation[old] = base.square_count() - 1U - old;
    }

    const std::vector<Topology> samples{
        base,
        permute_squares(base, permutation),
        relabel_square(base, 4, D4Transform{.rotation = 1, .reflected = true}),
        relabel_container(base, D4Transform{.rotation = 3, .reflected = true}),
        make_fixture("corner-corner-2"),
        make_fixture("corner-side-2"),
        make_fixture("side-side-2"),
        make_fixture("disjoint-2"),
    };

    std::vector<std::string> text_keys;
    for (const auto& topology : samples) {
        text_keys.push_back(canonical_encoding(topology));
    }

    const std::vector<CanonicalBackend> backends{
        CanonicalBackend::DenseNauty,
        CanonicalBackend::SparseNauty,
        CanonicalBackend::Traces,
    };

    for (const auto backend : backends) {
        std::vector<CanonicalKey> binary_keys;
        for (const auto& topology : samples) {
            binary_keys.push_back(canonical_key(topology, backend));
        }

        for (std::size_t i = 0; i < samples.size(); ++i) {
            for (std::size_t j = 0; j < samples.size(); ++j) {
                expect(
                    (text_keys[i] == text_keys[j]) == (binary_keys[i] == binary_keys[j]),
                    "every backend binary key must induce the textual equivalence relation"
                );
            }
        }

        expect(
            canonical_key_hex(binary_keys.front()).starts_with("SQK4HEX:"),
            "retained binary key text must carry the SQK2HEX version marker"
        );
    }
}

void test_compact_binary_key_layout() {
    using namespace sqtopology;

    const auto topology = make_fixture("grid-4x4-minus-one").normalized();
    const auto incidence = to_incidence_graph_validated(topology);
    const auto key = canonical_key_colored_graph(
        incidence,
        CanonicalBackend::Traces
    );

    const auto n = incidence.vertex_count();
    const std::size_t endpoint_width =
        n <= 256U ? 1U : (n <= 65536U ? 2U : 4U);
    const auto expected_bytes =
        4U
        + 1U
        + 4U
        + 1U
        + 4U
        + n
        + incidence.edges.size() * 2U * endpoint_width;

    expect(
        key.bytes.size() == expected_bytes,
        "SQK4 must store colors plus one exact canonical edge list"
    );

    const auto triangle_bits = n * (n - 1U) / 2U;
    const auto triangle_bytes = (triangle_bits + 7U) / 8U;
    expect(
        incidence.edges.size() * 2U * endpoint_width < triangle_bytes,
        "sparse edge-list payload must beat the packed triangle for this fixture"
    );
}

void test_key_endpoint_width_boundary() {
    using namespace sqtopology;
    for (const std::size_t n : {255U, 256U, 257U}) {
        ColoredGraph graph;
        graph.colors.assign(n, 1);
        graph.colors[0] = 2;
        graph.colors[n / 3] = 3;
        for (std::uint32_t i = 1; i < n; ++i) graph.edges.emplace_back(i - 1, i);
        const auto text = canonicalize_colored_graph(graph).encoding;
        for (const auto backend : {CanonicalBackend::DenseNauty,
                                   CanonicalBackend::SparseNauty, CanonicalBackend::Traces}) {
            const auto key = canonical_key_colored_graph(graph, backend);
            const auto width = static_cast<unsigned char>(key.bytes[9]);
            expect(width == (n <= 256 ? 1 : 2), "SQK4 endpoint width must handle vertex 255 exactly");
            expect(key.bytes.size() == 14 + n + graph.edges.size() * 2 * width,
                   "SQK4 boundary payload must have the expected length");
            ColoredGraph decoded;
            for (std::size_t i = 0; i < n; ++i)
                decoded.colors.push_back(static_cast<unsigned char>(key.bytes[14 + i]));
            std::size_t cursor = 14 + n;
            const auto read_index = [&]() {
                std::uint32_t value = 0;
                for (unsigned byte = 0; byte < width; ++byte)
                    value = (value << 8) | static_cast<unsigned char>(key.bytes[cursor++]);
                return value;
            };
            while (cursor < key.bytes.size()) {
                const auto a = read_index();
                const auto b = read_index();
                expect(a < b && b < n, "decoded canonical edges must be normalized and in range");
                decoded.edges.emplace_back(a, b);
            }
            expect(canonicalize_colored_graph(decoded).encoding == text,
                   "SQK4 must encode the complete graph across the byte-width boundary");
            expect(canonical_key_colored_graph(decoded, backend) == key,
                   "canonical binary keys must be idempotent across endpoint widths");
        }
    }
}

void test_canonical_microprofile_preserves_semantics() {
    using namespace sqtopology;

    const auto topology = make_fixture("grid-4x4-minus-one").normalized();
    const auto incidence = to_incidence_graph_validated(topology);
    const auto baseline = canonicalize_colored_graph(incidence);

    CanonicalProfile profile;
    const auto profiled = canonicalize_colored_graph(incidence, &profile);

    expect(
        baseline.encoding == profiled.encoding,
        "canonical microprofiling must not change the canonical encoding"
    );
    expect(
        baseline.fingerprint == profiled.fingerprint,
        "canonical microprofiling must not change the canonical fingerprint"
    );
    expect(profile.calls == 1, "canonical profile must count the profiled call");
    expect(profile.input_build_seconds >= 0.0, "input-build timing must be non-negative");
    expect(profile.partition_seconds >= 0.0, "partition timing must be non-negative");
    expect(profile.engine_seconds >= 0.0, "engine timing must be non-negative");
    expect(
        profile.output_prepare_seconds >= 0.0,
        "output-conversion timing must be non-negative"
    );
    expect(profile.key_build_seconds >= 0.0, "key-build timing must be non-negative");
    expect(profile.extraction_seconds >= 0.0, "extraction timing must be non-negative");
    expect(profile.encoding_seconds >= 0.0, "encoding timing must be non-negative");
    expect(profile.hash_seconds >= 0.0, "hash timing must be non-negative");
}

void test_search_canonical_microprofile() {
    using namespace sqtopology;

    const SearchOptions options{
        .max_candidates = 24,
        .max_unique = 24,
        .max_depth = 1,
        .max_additions_per_parent = 16,
        .wall_seconds = 0.0,
        .shard = Shard{.index = 0, .count = 1},
        .retain_keys = false,
        .profile_canonical = true,
    };

    const auto result = run_search(make_fixture("grid-3x3"), options);
    expect(result.stats.valid_candidates > 0, "profiled search must process candidates");
    expect(
        result.stats.canonical_profiled_calls == result.stats.valid_candidates,
        "every valid search candidate must receive one canonical microprofile"
    );

    const auto json = search_stats_to_json(result.stats, options.shard);
    expect(
        json.find("\"canonical_profile_enabled\":true") != std::string::npos,
        "search JSON must report enabled canonical profiling"
    );
    expect(
        json.find("\"canonical_engine_seconds\":") != std::string::npos,
        "search JSON must expose backend engine timing"
    );
    expect(
        json.find("\"canonical_backend\":\"traces\"") != std::string::npos,
        "default search JSON must expose Traces as the canonical backend"
    );
    expect(
        json.find("\"canonical_key_build_seconds\":") != std::string::npos,
        "search JSON must expose binary-key construction timing"
    );
    expect(
        json.find("\"stored_canonical_key_bytes\":") != std::string::npos,
        "search JSON must expose exact stored key payload"
    );
    expect(
        result.stats.canonical_extraction_seconds == 0.0,
        "search binary-key path must not extract canonical edge vectors"
    );
    expect(
        result.stats.canonical_encoding_seconds == 0.0,
        "search binary-key path must not build textual SQT1 encodings"
    );
}

void test_search_backends_agree() {
    using namespace sqtopology;

    SearchOptions options{
        .max_candidates = 240,
        .max_unique = 0,
        .max_depth = 2,
        .max_additions_per_parent = 32,
        .wall_seconds = 0.0,
        .shard = Shard{.index = 0, .count = 1},
        .retain_keys = false,
        .profile_canonical = false,
    };

    const auto seed = make_fixture("grid-3x3");

    options.canonical_backend = CanonicalBackend::DenseNauty;
    const auto dense = run_search(seed, options);

    options.canonical_backend = CanonicalBackend::SparseNauty;
    const auto sparse = run_search(seed, options);

    options.canonical_backend = CanonicalBackend::Traces;
    const auto traces = run_search(seed, options);

    expect(
        dense.stats.raw_candidates == sparse.stats.raw_candidates
            && dense.stats.raw_candidates == traces.stats.raw_candidates,
        "all canonical backends must process the same bounded candidate count"
    );
    expect(
        dense.stats.valid_candidates == sparse.stats.valid_candidates
            && dense.stats.valid_candidates == traces.stats.valid_candidates,
        "all canonical backends must agree on valid candidate count"
    );
    expect(
        dense.stats.duplicates == sparse.stats.duplicates
            && dense.stats.duplicates == traces.stats.duplicates,
        "all canonical backends must agree on duplicate classification"
    );
    expect(
        dense.stats.unique_states == sparse.stats.unique_states
            && dense.stats.unique_states == traces.stats.unique_states,
        "all canonical backends must agree on unique-state count"
    );
}

void test_traces_workspace_size_changes() {
    using namespace sqtopology;
    std::mt19937 random(0x437a1);
    for (const std::size_t n : {31U, 4095U, 7U, 4097U, 1024U, 4096U, 13U}) {
        ColoredGraph graph;
        for (std::size_t i = 0; i < n; ++i) graph.colors.push_back(random() % 17);
        for (std::uint32_t i = 1; i < n; ++i) {
            graph.edges.emplace_back(i - 1, i);
            const auto neighbor = random() % n;
            if (neighbor != i) graph.edges.emplace_back(i, neighbor);
        }
        graph.normalize_edges();
        const auto key = canonical_key_colored_graph(graph, CanonicalBackend::Traces);
        auto transformed = graph;
        for (std::size_t i = 0; i < n; ++i) transformed.colors[n - 1 - i] = graph.colors[i];
        for (auto& [a, b] : transformed.edges) {
            a = static_cast<std::uint32_t>(n - 1 - a);
            b = static_cast<std::uint32_t>(n - 1 - b);
        }
        std::shuffle(transformed.edges.begin(), transformed.edges.end(), random);
        expect(canonical_key_colored_graph(transformed, CanonicalBackend::Traces) == key,
               "Traces scratch growth, bounded-cache cleanup, and input permutation must preserve exact keys");
    }
}

void test_search_key_hash_collisions() {
    using namespace sqtopology;
    auto first = canonical_key(make_fixture("corner-corner-2"), CanonicalBackend::Traces);
    auto second = canonical_key(make_fixture("side-side-2"), CanonicalBackend::Traces);
    // Deliberately force the same bucket hash for different complete keys.
    second.fingerprint = first.fingerprint;
#ifdef SQTOPOLOGY_BOOST_FLAT_SET
    boost::unordered_flat_set<CanonicalKey, CanonicalKeyHash> seen;
#else
    std::unordered_set<CanonicalKey, CanonicalKeyHash> seen;
#endif
    expect(seen.insert(first).second, "first exact key must insert");
    expect(seen.insert(second).second, "hash collisions must retain distinct exact keys");
    expect(!seen.insert(first).second, "identical full bytes must deduplicate");
    expect(seen.size() == 2, "hash values must never decide canonical equality");
}

void test_canonical_equality_uses_encoding() {
    using namespace sqtopology;

    const auto base = make_fixture("side-side-2");
    const auto transformed = relabel_square(
        base,
        1,
        D4Transform{.rotation = 2, .reflected = true}
    );
    const auto lhs = canonicalize(base);
    const auto rhs = canonicalize(transformed);

    expect(lhs.encoding == rhs.encoding, "canonical equality must use full encoding");
    expect(lhs.fingerprint == rhs.fingerprint, "equal encodings must have equal fingerprints");
}

}  // namespace

int main() {
    try {
        test_validation();
        test_square_permutation_invariance();
        test_local_d4_invariance();
        test_container_d4_invariance();
        test_distinct_topologies_remain_distinct();
        test_grid_3x3_central_square_has_eight_square_contacts();
        test_rewrites_are_deterministic();
        test_rewrite_validity_contract();
        test_shard_reproducibility();
        test_sorted_contact_insertion();
        test_depth_bound_frontier();
        test_export_smoke();
        test_validated_incidence_fast_path_matches_checked_path();
        test_incidence_prefix_cache_transitions();
        test_backend_names();
        test_binary_key_matches_textual_equivalence();
        test_compact_binary_key_layout();
        test_key_endpoint_width_boundary();
        test_canonical_microprofile_preserves_semantics();
        test_search_canonical_microprofile();
        test_search_backends_agree();
        test_traces_workspace_size_changes();
        test_search_key_hash_collisions();
        test_canonical_equality_uses_encoding();
        std::cout << "sqtopology_tests: all tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_tests: FAIL: " << error.what() << '\n';
        return 1;
    }
}
