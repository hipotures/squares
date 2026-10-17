// Tests for the Phase-2 realizability layer in realize.hpp.
//
// Three independent kinds of check:
//  1. the verifier's extraction of the fixture scenes equals the committed
//     fixture contact sets (the geometry ground truth);
//  2. the solver's statuses agree with the static filters / negative fixtures,
//     and every VERIFIED_FEASIBLE witness is re-verified from scratch;
//  3. the scene action psi_g commutes with the production relabel/permute
//     transformations for every element of G_n (exact and weak strata, with
//     the per-square feature-frame parity), and the n = 2/3 corpus
//     enumeration reproduces the Burnside coefficients.
//
// The corpus solve tests deliberately use a small budget; the full corpus run
// is a separate CTest target (`sqtopology_realize_corpus_w2`).

#include "sqtopology/fixtures.hpp"
#include "sqtopology/geometry.hpp"
#include "sqtopology/orbit.hpp"
#include "sqtopology/realize.hpp"
#include "sqtopology/topology.hpp"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <random>
#include <set>
#include <sstream>
#include <string>
#include <vector>

namespace {

using namespace sqtopology;

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

std::string read_source_file(const std::string& relative) {
    const std::string path = std::string(SQTOPOLOGY_SOURCE_DIR) + "/" + relative;
    std::ifstream input(path, std::ios::binary);
    if (!input) {
        throw std::runtime_error("cannot open reference file: " + path);
    }
    std::ostringstream buffer;
    buffer << input.rdbuf();
    return buffer.str();
}

std::uint64_t extract_uint(const std::string& json, const std::string& name) {
    const std::string key = "\"" + name + "\":";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing JSON field: " + name);
    }
    return std::stoull(json.substr(position + key.size()));
}

std::string extract_string(const std::string& json, const std::string& name) {
    const std::string key = "\"" + name + "\":\"";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing JSON string field: " + name);
    }
    const auto start = position + key.size();
    const auto end = json.find('"', start);
    return json.substr(start, end - start);
}

std::size_t count_occurrences(const std::string& haystack, const std::string& needle) {
    std::size_t count = 0;
    for (auto position = haystack.find(needle); position != std::string::npos;
         position = haystack.find(needle, position + needle.size())) {
        ++count;
    }
    return count;
}

std::vector<std::string> keys_of(const Topology& topology) {
    return sorted_contact_keys(topology.contacts());
}

Topology topology_of(const std::vector<Contact>& contacts, std::uint32_t square_count) {
    Topology topology(square_count);
    for (const auto& contact : contacts) {
        topology.add_contact(contact);
    }
    return topology.normalized();
}

// ---------------------------------------------------------------------------
// Fixtures and verifier
// ---------------------------------------------------------------------------

void test_fixture_extraction() {
    const auto fixtures = scene_fixtures();
    expect(!fixtures.empty(), "fixture list must not be empty");
    for (const auto& fixture : fixtures) {
        const std::uint32_t square_count =
            static_cast<std::uint32_t>(fixture.scene.squares.size());
        const Topology expected =
            expected_fixture_topology(fixture.expected_fixture, square_count);
        const ExtractionResult extraction = extract_contacts(fixture.scene);
        expect(
            sorted_contact_keys(extraction.exact) == keys_of(expected),
            "exact extraction differs from the fixture for " + fixture.name
        );
        const WitnessReport report = verify_witness(fixture.scene, expected);
        expect(report.contained, "fixture scene must be contained: " + fixture.name);
        expect(report.separated, "fixture scene must be separated: " + fixture.name);
        expect(report.exact_accepted, "fixture witness must verify: " + fixture.name);
        expect(report.missing_exact.empty(), "fixture witness has missing contacts");
        expect(report.extra_exact.empty(), "fixture witness has extra contacts");

        // Weak closure: every exact contact is a weak contact, and every weak
        // contact either is required or is a genuine extra at the closure.
        const auto exact = sorted_contact_keys(extraction.exact);
        const auto weak = sorted_contact_keys(extraction.weak);
        for (const auto& key : exact) {
            expect(
                std::binary_search(weak.begin(), weak.end(), key),
                "exact contacts must be weak contacts: " + fixture.name
            );
        }
    }
}

void test_weak_stratum_semantics() {
    // Diagonal corner-corner scene: exact = one CC, weak = that CC plus the
    // four corner-side closures and the two zero-overlap side-side closures.
    const auto fixtures = scene_fixtures();
    const auto found = std::find_if(
        fixtures.begin(), fixtures.end(),
        [](const SceneFixture& fixture) { return fixture.name == "corner-corner-2"; }
    );
    expect(found != fixtures.end(), "corner-corner fixture present");
    const ExtractionResult extraction = extract_contacts(found->scene);
    expect(extraction.exact.size() == 1, "diagonal scene has one exact contact");
    expect(extraction.weak.size() == 7, "diagonal scene has seven weak contacts");
    expect(
        extraction.weak.size() > extraction.exact.size(),
        "weak stratum strictly dominates on the diagonal scene"
    );
    // Absorption: the side-side fixture's endpoint corner coincidences are
    // absorbed by the positive-overlap side contact.
    const auto side_side = std::find_if(
        fixtures.begin(), fixtures.end(),
        [](const SceneFixture& fixture) { return fixture.name == "side-side-2"; }
    );
    expect(side_side != fixtures.end(), "side-side fixture present");
    const ExtractionResult side_extraction = extract_contacts(side_side->scene);
    expect(side_extraction.exact.size() == 1, "side-side scene absorbs endpoint CCs");
    expect(
        side_extraction.exact.front().kind == ContactKind::SideSide,
        "side-side scene reports the side contact"
    );
}

void test_negative_fixtures() {
    const auto fixtures = negative_fixtures();
    expect(fixtures.size() == 4, "four negative fixtures");
    SolveConfig config;
    config.starts_per_rung = 8;
    config.ladder = {1.0, 2.0, 3.0};
    config.minimize_container = false;
    for (const auto& fixture : fixtures) {
        const SolveResult result = realize_topology(fixture.topology, config);
        expect(
            result.status == fixture.expected_status,
            "negative fixture status mismatch: " + fixture.name
                + " (got " + to_string(result.status) + ")"
        );
        expect(
            !result.exact_witness,
            "no exact witness may be accepted for " + fixture.name
        );
        if (fixture.expected_status == RealizabilityStatus::ProvedInfeasible) {
            expect(!result.filter_reason.empty(), "filter reason recorded: " + fixture.name);
        }
    }
}

// ---------------------------------------------------------------------------
// Solver on the fixture topologies; every accepted witness is re-verified.
// ---------------------------------------------------------------------------

void test_solver_on_fixture_topologies() {
    const std::vector<std::string> names{
        "isolated-1", "corner-corner-2", "corner-side-2", "side-side-2",
    };
    for (const auto& name : names) {
        const Topology topology = make_fixture(name);
        const SolveResult result = realize_topology(topology);
        expect(
            result.status == RealizabilityStatus::VerifiedFeasible,
            "solver must realize fixture topology " + name
        );
        expect(result.exact_witness, "fixture solve must be exact: " + name);
        const WitnessReport recheck = verify_witness(result.witness, topology);
        expect(recheck.exact_accepted, "returned witness must re-verify: " + name);
        expect(
            result.container_side >= 2.0 - 1e-9 || name == "isolated-1",
            "container side below the n = 2 lower bound: " + name
        );
        expect(
            result.bisection_lower <= result.container_side,
            "bisection bracket must contain the reported side"
        );
    }

    for (const auto& [name, expected] : std::vector<std::pair<std::string, std::string>>{
             {"wall-corner", "@wall-corner-single"},
             {"wall-side", "@wall-side-single"},
         }) {
        const Topology topology = expected_fixture_topology(expected, 1);
        const SolveResult result = realize_topology(topology);
        expect(
            result.status == RealizabilityStatus::VerifiedFeasible,
            "solver must realize wall fixture " + name
        );
        const WitnessReport recheck = verify_witness(result.witness, topology);
        expect(recheck.exact_accepted, "wall fixture witness must re-verify: " + name);
    }
}

void test_grid_topology_is_tight() {
    // The 2x2 grid topology forces the container to exactly 2: the four unit
    // squares tile it, so the reported side must be the ladder minimum.
    const Topology topology = make_fixture("grid-2x2");
    SolveConfig config;
    config.ladder = {2.0, 3.0};
    const SolveResult result = realize_topology(topology);
    expect(
        result.status == RealizabilityStatus::VerifiedFeasible,
        "grid-2x2 topology must be realizable"
    );
    expect(
        std::abs(result.container_side - 2.0) <= 1e-9,
        "grid-2x2 must be realized at the tight side length"
    );
    expect(
        verify_witness(result.witness, topology).exact_accepted,
        "grid-2x2 witness re-verifies"
    );
    expect(!config.ladder.empty(), "config unused warning guard");
}

// ---------------------------------------------------------------------------
// psi_g: full G_n scene action versus the production label transformations
// ---------------------------------------------------------------------------

Scene two_square_corner_scene() {
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    return scene;
}

Scene two_square_corner_side_scene() {
    const double radius = std::sqrt(2.0) / 2.0;
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {
        SquarePose{1.5 - radius, 2.0, -3.14159265358979323846 / 4.0},
        SquarePose{2.0, 2.0, 0.0},
    };
    return scene;
}

Scene two_square_side_side_scene() {
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 2.0, 0.0}};
    return scene;
}

// Multi-contact scene: SS along the bottom wall plus two wall-side contacts.
Scene two_square_wall_scene() {
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 0.5, 0.0}, SquarePose{2.0, 0.5, 0.0}};
    return scene;
}

// Check extraction(psi_g(P)) == g . extraction(P) for every element of G_n,
// on both the exact and the weak stratum, and that the moved scene stays
// contained and interior-disjoint. This is the central symmetry invariant.
void expect_full_group_covariance(const Scene& scene, const std::string& name) {
    const std::uint32_t n = static_cast<std::uint32_t>(scene.squares.size());
    const ExtractionResult base = extract_contacts(scene);
    const Topology base_exact = topology_of(base.exact, n);
    const Topology base_weak = topology_of(base.weak, n);
    for (std::uint64_t index = 0; index < group_element_count(n); ++index) {
        const GroupElement element = decode_group_element(n, index);
        const Scene moved = apply_group_element_to_scene(element, scene);
        expect(
            std::abs(moved.container_side - scene.container_side) <= 1e-12,
            "psi_g preserves the container side: " + name
        );
        const ExtractionResult got = extract_contacts(moved);
        const Topology expected_exact = apply_group_element_to_topology(base_exact, element);
        const Topology expected_weak = apply_group_element_to_topology(base_weak, element);
        expect(
            keys_of(topology_of(got.exact, n)) == keys_of(expected_exact),
            "exact extraction covariance under full G_n: " + name
        );
        expect(
            keys_of(topology_of(got.weak, n)) == keys_of(expected_weak),
            "weak extraction covariance under full G_n: " + name
        );
        const WitnessReport report = verify_witness(moved, expected_exact);
        expect(
            report.contained && report.separated,
            "psi_g preserves containment and separation: " + name
        );
    }
}

void test_full_group_covariance_n1() {
    Scene wall_side;
    wall_side.container_side = 3.0;
    wall_side.squares = {SquarePose{1.5, 2.5, 0.0}};
    expect_full_group_covariance(wall_side, "wall-side-1");

    Scene wall_corner;
    wall_corner.container_side = 3.0;
    wall_corner.squares = {
        SquarePose{1.5, 3.0 - std::sqrt(2.0) / 2.0, -3.14159265358979323846 / 4.0}};
    expect_full_group_covariance(wall_corner, "wall-corner-1");

    Scene mirrored;
    mirrored.container_side = 2.0;
    mirrored.squares = {SquarePose{1.0, 1.0, 0.0, true}};
    expect_full_group_covariance(mirrored, "single-mirrored-1");
    expect(extract_contacts(mirrored).exact.size() == 0, "free mirrored square has no contacts");
}

void test_full_group_covariance_n2() {
    expect_full_group_covariance(two_square_corner_scene(), "corner-corner-2");
    expect_full_group_covariance(two_square_corner_side_scene(), "corner-side-2");
    expect_full_group_covariance(two_square_side_side_scene(), "side-side-2");
    expect_full_group_covariance(two_square_wall_scene(), "wall-ss-2");

    // Mixed frame parity: the same physical squares with one frame reflected.
    Scene mixed = two_square_side_side_scene();
    mixed.squares[0].frame_reflected = true;
    expect_full_group_covariance(mixed, "side-side-2-mixed-frame");
}

void test_full_group_covariance_n3() {
    Scene scene;
    scene.container_side = 2.0;
    scene.squares = {
        SquarePose{0.5, 1.5, 0.0},
        SquarePose{1.5, 1.5, 0.0},
        SquarePose{0.5, 0.5, 0.0},
    };
    expect_full_group_covariance(scene, "grid-3squares");
}

void test_frame_parity_is_gauge() {
    // Changing only frame_reflected keeps the occupied point set identical and
    // relabels corner c as corner (-c) mod 4, the engine's local reflection
    // (rotation 0, reflected): corners 0 and 2 are fixed, 1 and 3 swap.
    Scene plain = two_square_corner_scene();
    Scene reflected = plain;
    reflected.squares[0].frame_reflected = true;

    const auto plain_corners = square_corners(plain.squares[0]);
    const auto reflected_corners = square_corners(reflected.squares[0]);
    for (std::uint8_t corner = 0; corner < 4; ++corner) {
        const Vec2 a = plain_corners[corner];
        const Vec2 b = reflected_corners[static_cast<std::uint8_t>((4U - corner) % 4U)];
        expect(norm(a - b) <= 1e-12, "frame parity maps corner c to -c");
    }
    // The extracted sets differ exactly by the local reflection element.
    GroupElement tau = identity_group_element(2);
    tau.local[0] = D4Element{0, true};
    const Topology plain_topology = topology_of(extract_contacts(plain).exact, 2);
    const Topology reflected_topology = topology_of(extract_contacts(reflected).exact, 2);
    expect(
        keys_of(reflected_topology) == keys_of(apply_group_element_to_topology(plain_topology, tau)),
        "frame parity acts as the local reflection on extracted contacts"
    );
    expect(
        keys_of(topology_of(extract_contacts(reflected).weak, 2))
            == keys_of(apply_group_element_to_topology(
                   topology_of(extract_contacts(plain).weak, 2), tau)),
        "frame parity acts as the local reflection on weak contacts"
    );
}

void test_scene_action_on_wall_contacts() {
    // A single square flush with the top wall: a pure container rotation by one
    // quarter turn must move the wall contact from wall 0 to wall 1 while the
    // square's own labels stay put.
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.5, 2.5, 0.0}};
    const Topology base = topology_of(extract_contacts(scene).exact, 1);
    expect(keys_of(base) == keys_of(expected_fixture_topology("@wall-side-single", 1)),
           "wall-side scene extracts the wall-side fixture");

    for (std::uint8_t rotation = 0; rotation < 4; ++rotation) {
        GroupElement element = identity_group_element(1);
        element.container = D4Element{rotation, false};
        const Scene moved = apply_group_element_to_scene(element, scene);
        const Topology moved_topology = topology_of(extract_contacts(moved).exact, 1);
        const Topology expected = apply_group_element_to_topology(base, element);
        expect(keys_of(moved_topology) == keys_of(expected),
               "container rotation moves the wall contact as relabel_container does");
        expect(moved_topology.contacts().front().wall.has_value(), "wall contact survives");
    }

    // Vertical mirror x -> L - x: corner c maps to (1 - c) mod 4 and wall w to
    // (4 - w) mod 4. Test both the parity-consistent and the mixed-parity
    // case; the latter is only representable with the frame gauge.
    Scene corners;
    corners.container_side = 3.0;
    corners.squares = {
        SquarePose{1.5, 3.0 - std::sqrt(2.0) / 2.0, -3.14159265358979323846 / 4.0}};
    const Topology corner_base = topology_of(extract_contacts(corners).exact, 1);
    for (const bool local_reflected : {true, false}) {
        GroupElement mirror = identity_group_element(1);
        mirror.container = D4Element{0, true};
        mirror.local[0] = D4Element{0, local_reflected};
        const Scene mirrored = apply_group_element_to_scene(mirror, corners);
        const Topology moved = topology_of(extract_contacts(mirrored).exact, 1);
        const Topology expected = apply_group_element_to_topology(corner_base, mirror);
        expect(keys_of(moved) == keys_of(expected),
               "vertical mirror commutes with relabeling for either frame parity");
    }
}

void test_scene_action_transfers_witnesses() {
    // Realize the corner-corner topology, then push both the topology and the
    // witness through mixed-parity elements; the moved scene must verify
    // against the moved topology. This is what makes psi_g total.
    const Topology sigma = make_fixture("corner-corner-2");
    const SolveResult result = realize_topology(sigma);
    expect(result.status == RealizabilityStatus::VerifiedFeasible, "corner-corner realized");

    const GroupElement elements[] = {
        GroupElement{
            2,
            {1, 0},
            {D4Element{1, false}, D4Element{3, false}},
            D4Element{2, false},
        },
        GroupElement{
            2,
            {0, 1},
            {D4Element{0, true}, D4Element{2, true}},
            D4Element{0, true},
        },
        GroupElement{
            2,
            {1, 0},
            {D4Element{0, true}, D4Element{0, false}},
            D4Element{0, false},
        },
    };
    for (const auto& element : elements) {
        expect(is_permutation(element), "test element is a valid group element");
        const Topology moved_sigma = apply_group_element_to_topology(sigma, element);
        const Scene moved_scene = apply_group_element_to_scene(element, result.witness);
        const WitnessReport report = verify_witness(moved_scene, moved_sigma);
        expect(report.exact_accepted,
               "psi_g transfers the exact witness to the relabeled topology");
    }
}

// ---------------------------------------------------------------------------
// Filters: full-group invariance and the absorption-aware rules
// ---------------------------------------------------------------------------

void expect_filter_invariance(const Topology& sigma, const std::string& name, bool proved) {
    const std::uint32_t n = sigma.square_count();
    for (std::uint64_t index = 0; index < group_element_count(n); ++index) {
        const GroupElement element = decode_group_element(n, index);
        const Topology moved = apply_group_element_to_topology(sigma, element);
        const InfeasibilityFilter filter = static_infeasibility_filters(moved);
        expect(
            filter.proved == proved,
            "filter invariance under full G_n for " + name
        );
    }
}

void test_filter_group_invariance() {
    for (const auto& fixture : negative_fixtures()) {
        if (fixture.expected_status == RealizabilityStatus::ProvedInfeasible) {
            expect_filter_invariance(fixture.topology, fixture.name, true);
        }
    }
    // Positive controls: feasible single-contact topologies.
    Topology corner_wall(1);
    corner_wall.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
    expect_filter_invariance(corner_wall.normalized(), "corner-wall", false);

    Topology wall_side(1);
    wall_side.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
    expect_filter_invariance(wall_side.normalized(), "wall-side", false);

    Topology adjacent_walls(1);
    adjacent_walls.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
    adjacent_walls.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 1));
    expect_filter_invariance(adjacent_walls.normalized(), "adjacent-walls", false);
}

void test_absorption_filters() {
    const auto filter_of = [](const Topology& topology) {
        return static_infeasibility_filters(topology);
    };
    const auto expect_rule = [&](const Topology& topology, const std::string& rule,
                                 const std::string& name) {
        const InfeasibilityFilter filter = filter_of(topology);
        expect(filter.proved, "rule must fire for " + name);
        expect(filter.reason.rfind(rule, 0) == 0, "expected " + rule + " for " + name);
        const SolveResult result = realize_topology(topology);
        expect(
            result.status == RealizabilityStatus::ProvedInfeasible,
            "filtered topology is proved infeasible: " + name
        );
        expect_filter_invariance(topology, name, true);
    };

    {
        // R4: side 0 on wall 0 plus its endpoint corner 0 on wall 0.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        expect_rule(topology.normalized(), "R4", "R4-side-endpoint");
    }
    {
        // R4 also covers the other endpoint (corner 1 of side 0).
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 0));
        expect_rule(topology.normalized(), "R4", "R4-side-endpoint-2");
    }
    {
        // R5: adjacent corners 0 and 1 on wall 0 force side 0 onto the wall.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 0));
        expect_rule(topology.normalized(), "R5", "R5-adjacent-corners");
    }
    {
        // R6: opposite corners 0 and 2 on wall 0 put a third corner outside.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 2}, 0));
        expect_rule(topology.normalized(), "R6", "R6-opposite-corners");
    }

    // Positive controls that are close to the rules but not covered by them.
    const auto expect_feasible = [](const Topology& topology, const std::string& name) {
        const InfeasibilityFilter filter = static_infeasibility_filters(topology);
        expect(!filter.proved, "positive control must not be filtered: " + name);
        const SolveResult result = realize_topology(topology);
        expect(
            result.status == RealizabilityStatus::VerifiedFeasible,
            "positive control must be realizable: " + name
        );
        expect(
            verify_witness(result.witness, topology).exact_accepted,
            "positive control witness re-verifies: " + name
        );
    };
    {
        // Side of square 0 on wall 0, corner of *another* square on wall 0.
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{1, FeatureKind::Corner, 0}, 0));
        expect_feasible(topology.normalized(), "R4-positive-other-square");
    }
    {
        // Adjacent corners of two different squares on the same wall.
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{1, FeatureKind::Corner, 1}, 0));
        expect_feasible(topology.normalized(), "R5-positive-other-square");
    }
    {
        // Opposite corners of two different squares on the same wall.
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{1, FeatureKind::Corner, 2}, 0));
        expect_feasible(topology.normalized(), "R6-positive-other-square");
    }
    {
        // Adjacent corners of one square on adjacent walls: realizable, and
        // the old standard-frame "wrong order" is also realizable through the
        // frame gauge (the class appears in the weight-2 corpus).
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 1));
        expect_feasible(topology.normalized(), "adjacent-walls-positive");
    }
}

// ---------------------------------------------------------------------------
// Gauge-branch lifting: the two weight-2 classes that the standard frame
// cannot realize but a reflected local frame can.
// ---------------------------------------------------------------------------

void test_branch_lifting() {
    struct Case {
        Topology topology;
        std::uint8_t reflected_square;
    };
    std::vector<Case> cases;
    {
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 1));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 0));
        cases.push_back(Case{topology.normalized(), 0});
    }
    {
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 1));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 1}, 0));
        cases.push_back(Case{topology.normalized(), 0});
    }
    for (const auto& item : cases) {
        const SolveResult result = realize_topology(item.topology);
        expect(
            result.status == RealizabilityStatus::VerifiedFeasible,
            "mixed-frame branch class is feasible: "
                + topology_contact_keys_json(item.topology)
        );
        expect(result.frame_branch != 0U, "witness uses a reflected frame branch");
        expect(
            (result.frame_branch & (1U << item.reflected_square)) != 0U,
            "expected square carries the reflected frame"
        );
        expect(
            result.witness.squares[item.reflected_square].frame_reflected,
            "witness scene records the reflected frame"
        );
        expect(
            verify_witness(result.witness, item.topology).exact_accepted,
            "branch-lifted witness verifies against the canonical topology"
        );

        // The lifted witness is psi_tau of the branch witness, so applying the
        // same tau to the topology must give the branch that was solved.
        GroupElement tau = identity_group_element(2);
        tau.local[item.reflected_square] = D4Element{0, true};
        const Scene branch_scene = apply_group_element_to_scene(tau, result.witness);
        const Topology branch_topology = apply_group_element_to_topology(item.topology, tau);
        expect(
            verify_witness(branch_scene, branch_topology).exact_accepted,
            "applying tau maps the lifted witness to a standard-frame witness"
        );
    }
}

// ---------------------------------------------------------------------------
// Deterministic corpus parallelism
// ---------------------------------------------------------------------------

void expect_same_semantics(const CorpusReport& first, const CorpusReport& second) {
    expect(first.classes.size() == second.classes.size(), "worker class counts match");
    for (std::size_t index = 0; index < first.classes.size(); ++index) {
        const auto& a = first.classes[index];
        const auto& b = second.classes[index];
        expect(
            keys_of(a.corpus.topology) == keys_of(b.corpus.topology),
            "worker class representative order"
        );
        expect(a.solve.status == b.solve.status, "worker status");
        expect(a.solve.exact_witness == b.solve.exact_witness, "worker exact flag");
        expect(a.solve.weak_witness == b.solve.weak_witness, "worker weak flag");
        expect(a.solve.filter_reason == b.solve.filter_reason, "worker filter reason");
        expect(a.solve.frame_branch == b.solve.frame_branch, "worker branch");
        expect(a.solve.branches_tried == b.solve.branches_tried, "worker branch count");
        expect(a.solve.solves == b.solve.solves, "worker solve count");
        expect(
            std::abs(a.solve.container_side - b.solve.container_side) <= 1e-12,
            "worker container side"
        );
        if (a.solve.exact_witness) {
            expect(
                scene_to_json(a.solve.witness) == scene_to_json(b.solve.witness),
                "worker witness coordinates"
            );
        }
    }
}

void test_worker_determinism() {
    SolveConfig one;
    one.workers = 1;
    SolveConfig many = one;
    many.workers = 4;
    const CorpusReport serial = run_corpus(2, 1, one);
    const CorpusReport parallel = run_corpus(2, 1, many);
    expect(serial.classes.size() == 5, "worker test class count");
    expect_same_semantics(serial, parallel);

    // No duplicate or missing class representatives.
    std::set<std::vector<std::string>> keys;
    for (const auto& entry : parallel.classes) {
        expect(keys.insert(keys_of(entry.corpus.topology)).second,
               "parallel run has no duplicate classes");
    }
    expect(keys.size() == 5, "parallel run has every class");

    // Worker count zero is rejected rather than silently redefined.
    SolveConfig zero = one;
    zero.workers = 0;
    bool threw = false;
    try {
        (void)run_corpus(2, 1, zero);
    } catch (const std::invalid_argument&) {
        threw = true;
    }
    expect(threw, "zero workers is rejected");
}

// ---------------------------------------------------------------------------
// R7-R13: orientation, coincidence and feature-metric filters
// ---------------------------------------------------------------------------

void expect_new_rule(const Topology& topology, const std::string& rule,
                     const std::string& name) {
    const InfeasibilityFilter filter = static_infeasibility_filters(topology);
    expect(filter.proved, "new rule must fire: " + name);
    expect(filter.reason.rfind(rule, 0) == 0, "expected " + rule + " for " + name);
    const SolveResult result = realize_topology(topology);
    expect(
        result.status == RealizabilityStatus::ProvedInfeasible,
        "new rule topology is proved infeasible: " + name
    );
    expect_filter_invariance(topology, name, true);
}

void test_new_geometric_filters() {
    {
        // R7: one corner required on two distinct walls.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 1));
        expect_new_rule(topology.normalized(), "R7", "R7-same-corner-two-walls");
    }
    {
        // R8: corner + non-incident side of the same square on one wall.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 1}, 0));
        expect_new_rule(topology.normalized(), "R8", "R8-corner-nonincident-side");
    }
    {
        // R9: two distinct sides of one square on the same wall.
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 1}, 0));
        expect_new_rule(topology.normalized(), "R9", "R9-two-sides-one-wall");
    }
    {
        // R10: square-square parallelism cycle.
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Side, 0},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Side, 1},
                                                  FeatureRef{1, FeatureKind::Side, 2}));
        expect_new_rule(topology.normalized(), "R10", "R10-parallelism-cycle");
    }
    {
        // R11: a CC chain forces two corners of one square to coincide.
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Corner, 0}));
        topology.add_contact(make_square_contact(FeatureRef{1, FeatureKind::Corner, 0},
                                                  FeatureRef{0, FeatureKind::Corner, 1}));
        expect_new_rule(topology.normalized(), "R11", "R11-same-square-coincidence");
    }
    {
        // R12: two corners of one square on the same side feature.
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 1},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        expect_new_rule(topology.normalized(), "R12", "R12-two-corners-one-side");
    }
    {
        // R13: a CC class puts a non-endpoint corner of the side's square on
        // that side, at metric distance 1.
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Corner, 2}));
        expect_new_rule(topology.normalized(), "R13", "R13-cc-on-side");
    }

    // Positive controls: close to the rules but realizable.
    const auto expect_feasible = [](const Topology& topology, const std::string& name) {
        expect(!static_infeasibility_filters(topology).proved,
               "positive control must pass every filter: " + name);
        const SolveResult result = realize_topology(topology);
        expect(result.status == RealizabilityStatus::VerifiedFeasible,
               "positive control must be realizable: " + name);
        expect(verify_witness(result.witness, topology).exact_accepted,
               "positive control witness re-verifies: " + name);
    };
    {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 1}, 1));
        expect_feasible(topology.normalized(), "R7-positive-different-corners");
    }
    {
        // R8 is a same-square rule; the same wall pattern across two squares
        // is realizable.
        Topology topology(2);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{1, FeatureKind::Side, 1}, 0));
        expect_feasible(topology.normalized(), "R8-positive-other-square");
    }
    {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 1}, 1));
        expect_feasible(topology.normalized(), "R9-positive-different-walls");
    }
    {
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Side, 0},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        expect_feasible(topology.normalized(), "R10-positive-single-ss");
    }
    {
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Corner, 0}));
        expect_feasible(topology.normalized(), "R11-positive-single-cc");
    }
    {
        Topology topology(2);
        topology.add_contact(make_square_contact(FeatureRef{0, FeatureKind::Corner, 0},
                                                  FeatureRef{1, FeatureKind::Side, 0}));
        expect_feasible(topology.normalized(), "R12-positive-single-cs");
    }
}

void test_filters_never_reject_verified_scenes() {
    // Generate contained, contact-rich lattice scenes, extract their exact
    // contact sets and require that no filter rejects a set that a scene just
    // produced. This is an independent soundness check of every proof rule.
    std::mt19937_64 rng(987654321ULL);
    std::uint64_t checked = 0;
    for (int trial = 0; trial < 3000; ++trial) {
        const int rows = 1 + static_cast<int>(rng() % 4);
        const int cols = 1 + static_cast<int>(rng() % 4);
        const double side = static_cast<double>(std::max(rows, cols))
            + (rng() % 2 == 0 ? 0.0 : 0.5);
        const double shift = (rng() % 3 == 0) ? 0.5 : 0.0;
        Scene scene;
        scene.container_side = side;
        for (int row = 0; row < rows; ++row) {
            for (int column = 0; column < cols; ++column) {
                if (rng() % 5 == 0) {
                    continue;
                }
                const bool interior = row > 0 && column > 0
                    && row + 1 < rows && column + 1 < cols;
                double theta = 0.5 * 3.14159265358979323846
                    * static_cast<double>(rng() % 4);
                if (interior && rng() % 4 == 0) {
                    theta = 0.25 * 3.14159265358979323846
                        * static_cast<double>(1 + 2 * (rng() % 4));
                }
                scene.squares.push_back(SquarePose{
                    static_cast<double>(column) + 0.5 + shift,
                    side - static_cast<double>(row) - 0.5 + shift,
                    theta,
                    rng() % 2 == 0,
                });
            }
        }
        if (scene.squares.empty()) {
            continue;
        }
        const ExtractionResult extraction = extract_contacts(scene);
        if (extraction.exact.empty()) {
            continue;
        }
        const Topology topology =
            topology_of(extraction.exact, static_cast<std::uint32_t>(scene.squares.size()));
        const InfeasibilityFilter filter = static_infeasibility_filters(topology);
        expect(
            !filter.proved,
            "a filter rejected a contact set extracted from a scene: " + filter.reason
        );
        ++checked;
    }
    expect(checked > 500, "random-scene filter check covered enough scenes");
}

// ---------------------------------------------------------------------------
// Corpus enumeration and a light corpus solve
// ---------------------------------------------------------------------------

void test_corpus_enumeration_counts() {
    const auto weight1 = corpus_classes(2, 1);
    const auto weight2 = corpus_classes(2, 2);
    const auto weight3 = corpus_classes(2, 3);
    expect(weight1.size() == 5, "n = 2 weight 1 has 5 classes");
    expect(weight2.size() == 87, "n = 2 weight 2 has 87 classes");
    expect(weight3.size() == 1411, "n = 2 weight 3 has 1411 classes");
    // n = 1: G_1 = D4_ring x D4_wall, so a single event has two orbits: the
    // four corner features and the four side features (walls are transitive).
    expect(corpus_classes(1, 1).size() == 2, "n = 1 weight 1 has 2 classes");

    // Every representative is a valid topology of the right weight, and its
    // event set is canonical: applying a group element reproduces a class in
    // the same level (checked here by re-canonicalizing through the orbit key).
    for (const auto& entry : weight2) {
        expect(entry.weight == 2, "corpus class weight");
        expect(entry.square_count == 2, "corpus class square count");
        expect(entry.events.size() == 2, "corpus class event count");
        expect(entry.topology.validate().ok(), "corpus class topology is valid");
        const EventBitset bitset = topology_to_event_bitset(entry.topology);
        expect(event_bitset_popcount(bitset) == 2, "corpus class bitset weight");
    }

    // Canonical minimality: no element of G_2 lowers the event bitset below the
    // representative.
    for (const auto& entry : weight1) {
        const EventBitset bitset = topology_to_event_bitset(entry.topology);
        for (std::uint64_t index = 0; index < group_element_count(2); ++index) {
            const GroupElement element = decode_group_element(2, index);
            const EventBitset moved =
                permute_event_bitset(event_permutation(element), bitset);
            expect(!(moved < bitset), "corpus representative is orbit-minimal");
        }
    }
}

void test_corpus_weight_one_solves() {
    SolveConfig config;
    config.starts_per_rung = 24;
    config.max_solves = 400;
    config.ladder = {2.0, 2.5, 3.0};
    const CorpusReport report = run_corpus(2, 1, config);
    expect(report.classes.size() == 5, "weight-1 corpus run covers 5 classes");
    for (const auto& entry : report.classes) {
        expect(
            entry.solve.status == RealizabilityStatus::VerifiedFeasible,
            "every weight-1 class is realizable: " + topology_contact_keys_json(entry.corpus.topology)
        );
        expect(entry.solve.exact_witness, "weight-1 witnesses are exact");
        const WitnessReport recheck =
            verify_witness(entry.solve.witness, entry.corpus.topology);
        expect(recheck.exact_accepted, "weight-1 witness re-verifies");
    }
    const std::string json = corpus_report_to_json(report);
    expect(json.find("\"schema\":\"sqtopology.realizability.v2\"") != std::string::npos,
           "corpus report schema");
    expect(json.find("\"class_count\":5") != std::string::npos, "corpus report class count");
    expect(json.find("\"weak_only\":0") != std::string::npos, "corpus report weak count");
}

void test_n3_weight_one() {
    const auto classes = corpus_classes(3, 1);
    expect(classes.size() == 5, "n = 3 weight 1 has 5 Burnside classes");
    SolveConfig config;
    config.starts_per_rung = 24;
    config.max_solves = 600;
    config.ladder = {2.0, 2.5, 3.0};
    const CorpusReport report = run_corpus(3, 1, config);
    expect(report.classes.size() == 5, "n = 3 weight-1 corpus covers 5 classes");
    for (const auto& entry : report.classes) {
        expect(
            entry.solve.status == RealizabilityStatus::VerifiedFeasible,
            "every n = 3 single-contact class is realizable: "
                + topology_contact_keys_json(entry.corpus.topology)
        );
        expect(entry.solve.exact_witness, "n = 3 weight-1 witnesses are exact");
        expect(
            verify_witness(entry.solve.witness, entry.corpus.topology).exact_accepted,
            "n = 3 weight-1 witness re-verifies"
        );
        // The third (free) square cannot make the container tighter than the
        // n = 2 lower bound, and the solver must stay above it.
        expect(entry.solve.container_side > 2.0, "n = 3 container side above 2");
    }
}

void test_weight_one_golden() {
    // Committed machine-readable record of one deterministic n = 2 weight-1
    // run. Floating-point digits are not pinned (they are platform dependent);
    // the schema, the class accounting, and the status distribution are.
    const std::string json = read_source_file("tests/data/realizability-n2-w1.json");
    expect(extract_string(json, "schema") == "sqtopology.realizability.v2",
           "golden schema");
    expect(extract_uint(json, "n") == 2, "golden n");
    expect(extract_uint(json, "weight") == 1, "golden weight");
    expect(extract_uint(json, "class_count") == 5, "golden class count");
    expect(extract_uint(json, "group_size") == 1024, "golden group size");
    expect(extract_uint(json, "event_count") == 128, "golden event count");
    expect(extract_uint(json, "exact_witnesses") == 5, "golden exact witness count");
    expect(extract_uint(json, "weak_only") == 0, "golden weak-only count");
    expect(
        count_occurrences(json, "\"status\":\"VERIFIED_FEASIBLE\"") == 5,
        "golden status distribution"
    );
    expect(
        count_occurrences(json, "\"status\":\"NOT_FOUND\"") == 0,
        "golden has no not-found classes"
    );
    expect(
        count_occurrences(json, "\"frame_branch\":0") == 5,
        "weight-1 golden witnesses use the standard frame"
    );
    expect(
        count_occurrences(json, "\"branches_tried\":1") == 5,
        "weight-1 golden solves one gauge branch per class"
    );
    expect(json.find("\"witness\":{\"container_side\"") != std::string::npos,
           "golden witnesses are embedded");
}

void test_status_and_json_shapes() {
    expect(to_string(RealizabilityStatus::VerifiedFeasible) == "VERIFIED_FEASIBLE",
           "status string");
    expect(to_string(RealizabilityStatus::NotFound) == "NOT_FOUND", "status string");
    expect(to_string(RealizabilityStatus::ProvedInfeasible) == "PROVED_INFEASIBLE",
           "status string");

    Topology topology = make_fixture("corner-side-2");
    const std::string keys = topology_contact_keys_json(topology);
    expect(keys.front() == '[' && keys.back() == ']', "contact key JSON is an array");

    Scene scene = two_square_corner_scene();
    const std::string scene_json = scene_to_json(scene);
    expect(scene_json.find("\"container_side\":3") != std::string::npos,
           "scene JSON carries the container side");
    expect(scene_json.find("\"squares\":[") != std::string::npos, "scene JSON squares");
}

}  // namespace

int main() {
    struct Test {
        const char* name;
        void (*function)();
    };
    const Test tests[] = {
        {"fixture extraction", test_fixture_extraction},
        {"weak stratum semantics", test_weak_stratum_semantics},
        {"negative fixtures", test_negative_fixtures},
        {"solver on fixture topologies", test_solver_on_fixture_topologies},
        {"grid topology is tight", test_grid_topology_is_tight},
        {"full G1 covariance", test_full_group_covariance_n1},
        {"full G2 covariance", test_full_group_covariance_n2},
        {"full G3 covariance", test_full_group_covariance_n3},
        {"frame parity is gauge", test_frame_parity_is_gauge},
        {"scene action on wall contacts", test_scene_action_on_wall_contacts},
        {"scene action transfers witnesses", test_scene_action_transfers_witnesses},
        {"worker determinism", test_worker_determinism},
        {"new geometric filters", test_new_geometric_filters},
        {"filters never reject verified scenes", test_filters_never_reject_verified_scenes},
        {"corpus enumeration counts", test_corpus_enumeration_counts},
        {"filter group invariance", test_filter_group_invariance},
        {"absorption filters", test_absorption_filters},
        {"branch lifting", test_branch_lifting},
        {"corpus weight one solves", test_corpus_weight_one_solves},
        {"n = 3 weight one", test_n3_weight_one},
        {"weight one golden", test_weight_one_golden},
        {"status and JSON shapes", test_status_and_json_shapes},
    };
    int failures = 0;
    for (const auto& test : tests) {
        try {
            test.function();
            std::cout << "ok   " << test.name << '\n';
        } catch (const std::exception& error) {
            ++failures;
            std::cout << "FAIL " << test.name << ": " << error.what() << '\n';
        }
    }
    if (failures != 0) {
        std::cout << failures << " test(s) failed\n";
        return 1;
    }
    std::cout << "all Phase-2 realize tests passed\n";
    return 0;
}
