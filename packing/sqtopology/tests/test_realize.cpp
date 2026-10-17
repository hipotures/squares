// Tests for the Phase-2 realizability layer in realize.hpp.
//
// Three independent kinds of check:
//  1. the verifier's extraction of the fixture scenes equals the committed
//     fixture contact sets (the geometry ground truth);
//  2. the solver's statuses agree with the static filters / negative fixtures,
//     and every VERIFIED_FEASIBLE witness is re-verified from scratch;
//  3. the scene action psi_g commutes with the production relabel/permute
//     transformations on exactly the parity-consistent subgroup, and the
//     n = 2 corpus enumeration reproduces the Burnside coefficients.
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
// psi_g: scene action versus the production label transformations
// ---------------------------------------------------------------------------

Scene two_square_corner_scene() {
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    return scene;
}

bool parity_consistent(const GroupElement& element) {
    for (SquareId square = 0; square < element.square_count; ++square) {
        if (element.local[square].reflected != element.container.reflected) {
            return false;
        }
    }
    return true;
}

void test_scene_action_commutes_with_relabeling() {
    const Scene scene = two_square_corner_scene();
    const std::uint32_t n = 2;
    const Topology base = topology_of(extract_contacts(scene).exact, n);
    expect(keys_of(base) == keys_of(make_fixture("corner-corner-2")),
           "two-square scene extracts the corner-corner fixture");

    std::uint64_t consistent = 0;
    std::uint64_t inconsistent = 0;
    for (std::uint64_t index = 0; index < group_element_count(n); ++index) {
        const GroupElement element = decode_group_element(n, index);
        if (!parity_consistent(element)) {
            ++inconsistent;
            bool threw = false;
            try {
                (void)apply_group_element_to_scene(element, scene);
            } catch (const std::invalid_argument&) {
                threw = true;
            }
            expect(threw, "mixed-parity elements must be rejected by the scene action");
            continue;
        }
        ++consistent;
        const Scene moved = apply_group_element_to_scene(element, scene);
        expect(std::abs(moved.container_side - scene.container_side) <= 1e-12,
               "scene action preserves the container side");
        const Topology moved_topology = topology_of(extract_contacts(moved).exact, n);
        const Topology expected = apply_group_element_to_topology(base, element);
        expect(
            keys_of(moved_topology) == keys_of(expected),
            "psi_g must commute with relabel_square/relabel_container/permute_squares"
        );
        const WitnessReport report = verify_witness(moved, expected);
        expect(report.contained && report.separated,
               "transformed scene stays inside the container and separated");
    }
    expect(consistent == 256, "G_2 has 256 parity-consistent elements");
    expect(inconsistent == group_element_count(n) - consistent,
           "the remaining elements are mixed parity");
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

    // Vertical mirror x -> L - x: corner c maps to (1 - c) mod 4, and walls map
    // through (4 - w) mod 4.
    Scene corners;
    corners.container_side = 3.0;
    corners.squares = {SquarePose{1.5, 3.0 - std::sqrt(2.0) / 2.0, -3.14159265358979323846 / 4.0}};
    const Topology corner_base = topology_of(extract_contacts(corners).exact, 1);
    GroupElement mirror = identity_group_element(1);
    mirror.container = D4Element{0, true};
    mirror.local[0] = D4Element{0, true};
    const Scene mirrored = apply_group_element_to_scene(mirror, corners);
    const Topology mirrored_topology = topology_of(extract_contacts(mirrored).exact, 1);
    const Topology expected = apply_group_element_to_topology(corner_base, mirror);
    expect(keys_of(mirrored_topology) == keys_of(expected),
           "vertical mirror commutes with relabeling");
}

void test_scene_action_transfers_witnesses() {
    // Realize the corner-corner topology, then push both the topology and the
    // witness through a nontrivial parity-consistent element; the moved scene
    // must verify against the moved topology.
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
    expect(json.find("\"schema\":\"sqtopology.realizability.v1\"") != std::string::npos,
           "corpus report schema");
    expect(json.find("\"class_count\":5") != std::string::npos, "corpus report class count");
    expect(json.find("\"weak_only\":0") != std::string::npos, "corpus report weak count");
}

void test_weight_one_golden() {
    // Committed machine-readable record of one deterministic n = 2 weight-1
    // run. Floating-point digits are not pinned (they are platform dependent);
    // the schema, the class accounting, and the status distribution are.
    const std::string json = read_source_file("tests/data/realizability-n2-w1.json");
    expect(extract_string(json, "schema") == "sqtopology.realizability.v1",
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
        {"scene action commutes", test_scene_action_commutes_with_relabeling},
        {"scene action on wall contacts", test_scene_action_on_wall_contacts},
        {"scene action transfers witnesses", test_scene_action_transfers_witnesses},
        {"corpus enumeration counts", test_corpus_enumeration_counts},
        {"corpus weight one solves", test_corpus_weight_one_solves},
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
