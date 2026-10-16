#include "sqtopology/canonical.hpp"
#include "sqtopology/export.hpp"
#include "sqtopology/fixtures.hpp"
#include "sqtopology/rewrite.hpp"
#include "sqtopology/search.hpp"
#include "sqtopology/topology.hpp"

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
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
        test_shard_reproducibility();
        test_export_smoke();
        test_validated_incidence_fast_path_matches_checked_path();
        test_canonical_equality_uses_encoding();
        std::cout << "sqtopology_tests: all tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_tests: FAIL: " << error.what() << '\n';
        return 1;
    }
}
