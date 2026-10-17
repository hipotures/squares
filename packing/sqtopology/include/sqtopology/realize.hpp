#pragma once

#include "sqtopology/geometry.hpp"
#include "sqtopology/orbit.hpp"
#include "sqtopology/topology.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace sqtopology {

// ---------------------------------------------------------------------------
// Phase-2 geometric realizability layer.
//
// For a contact topology Sigma (a set of semantic contact events at a fixed
// square count n) the realizability question is:
//
//   exact: does there exist a scene whose exact contact extraction (with the
//          canonical absorption rules of geometry.hpp) equals Sigma exactly?
//   weak:  does there exist a scene whose weak extraction contains Sigma?
//          The weak stratum closes the side segments and admits zero-length
//          side overlaps, so a weak witness is a containment certificate in a
//          relaxed relation, not a proof that Sigma is a limit of exact
//          contact sets. It is reported separately and never as an exact
//          realization.
//
// The solver in realize.cpp minimizes a residual/penalty formulation of the
// required contacts. The verifier below is written directly from the geometric
// predicates in geometry.hpp and shares no code with the solver, so solver
// failure is never reported as impossibility. Only the static filters may
// return PROVED_INFEASIBLE.
// ---------------------------------------------------------------------------

enum class RealizabilityStatus : std::uint8_t {
    VerifiedFeasible = 0,
    NotFound = 1,
    ProvedInfeasible = 2,
};

[[nodiscard]] std::string to_string(RealizabilityStatus status);

// Structural impossibility filters, independent of any continuous search:
//   R1: one side feature is required to lie on two distinct wall lines;
//   R2: coincident corners (via corner-corner chains) are required on opposite
//       walls (w and w+2), which forces a point onto two parallel lines;
//   R3: one corner is required on both members of a pair of opposite sides of
//       one square, which forces a point onto two parallel lines.
struct InfeasibilityFilter {
    bool proved{false};
    std::string reason;
};

[[nodiscard]] InfeasibilityFilter static_infeasibility_filters(const Topology& sigma);

// Independent witness verification. A witness must keep every square inside
// the container and every pair of interiors disjoint (SAT) before any contact
// bookkeeping is interpreted.
struct WitnessReport {
    bool contained{true};
    bool separated{true};
    bool exact_accepted{false};
    bool weak_accepted{false};
    std::vector<std::string> missing_exact;
    std::vector<std::string> extra_exact;
    std::vector<std::string> missing_weak;
    double min_separation_slack{0.0};
    // Smallest margin over exact relations that are not required contacts
    // (absorption already discounted); absent when the scene has none.
    bool has_extra_margin{false};
    double min_extra_margin{0.0};
};

[[nodiscard]] WitnessReport verify_witness(
    const Scene& scene,
    const Topology& sigma,
    const ContactTolerances& tolerances = {}
);

struct SolveConfig {
    // Container sides tried in order. Two disjoint unit squares need L >= 2,
    // so the ladder starts at 1 to exercise the failure path explicitly.
    std::vector<double> ladder{1.0, 2.0, 2.2, 2.5, 3.0, 4.0};
    std::uint32_t starts_per_rung{32};
    std::uint32_t lm_max_iterations{120};
    std::uint64_t max_solves{400};
    // Heuristic bisection for the smallest container side with a witness.
    bool minimize_container{true};
    std::uint32_t minimization_steps{8};
    std::uint64_t seed{0x9e3779b97f4a7c15ULL};
};

struct SolveResult {
    RealizabilityStatus status{RealizabilityStatus::NotFound};
    std::string filter_reason;
    bool exact_witness{false};
    bool weak_witness{false};
    double container_side{0.0};
    Scene witness;
    WitnessReport report;
    // Weak (closure-only) witness, recorded even when no exact witness is
    // found. Never reported as an accepted realization by itself.
    double weak_container_side{0.0};
    Scene weak_scene;
    // Largest rung below container_side whose solve attempt failed; the exact
    // bracketed interval for the heuristic container minimization.
    double bisection_lower{0.0};
    std::uint64_t solves{0};
};

// Solves the realizability problem for Sigma. Requires a normalized topology
// with no duplicate contacts; square counts of 1..4 keep the enumeration-free
// solver paths fast. The returned witness is the last verified-accepted scene
// for feasible statuses (or the best rejected candidate otherwise).
[[nodiscard]] SolveResult realize_topology(const Topology& sigma, const SolveConfig& config = {});

// Scene action psi_g for the subgroup of G_n whose per-square local D4
// elements have the same reflection parity as the container element. For those
// elements extraction(psi_g(P)) == g . extraction(P) holds exactly, which the
// test suite checks against the production relabel_square / relabel_container /
// permute_squares transformations. Elements outside the subgroup throw
// std::invalid_argument: no standard-labeled scene can carry a mixed-parity
// feature relabeling.
[[nodiscard]] Scene apply_group_element_to_scene(const GroupElement& element, const Scene& scene);

// ---------------------------------------------------------------------------
// n = 2 corpus of canonical event-subset classes and the CLI fixtures.
// ---------------------------------------------------------------------------

struct CorpusClass {
    std::uint32_t square_count{0};
    std::uint32_t weight{0};
    std::vector<EventId> events;  // sorted
    Topology topology;
};

[[nodiscard]] std::vector<CorpusClass> corpus_classes(
    std::uint32_t square_count,
    std::uint32_t weight
);

struct SceneFixture {
    std::string name;
    // Expected exact contact set: an engine fixture name from make_fixture(),
    // one of the local "@wall-corner-single"/"@wall-side-single" topologies,
    // or "" for an empty contact set.
    std::string expected_fixture;
    Scene scene;
    std::string note;
};

[[nodiscard]] std::vector<SceneFixture> scene_fixtures();

// Resolves a SceneFixture::expected_fixture name into a topology; "" yields an
// empty topology over `square_count` squares.
[[nodiscard]] Topology expected_fixture_topology(std::string_view name, std::uint32_t square_count);

struct NegativeFixture {
    std::string name;
    Topology topology;
    RealizabilityStatus expected_status{RealizabilityStatus::NotFound};
    std::string note;
};

[[nodiscard]] std::vector<NegativeFixture> negative_fixtures();

// Full n = 2 corpus pipeline: enumerate the canonical weight-w classes, solve
// each one, and package the results for the machine-readable report. The
// enumeration is exact (canonical-minimal event bitset over all of G_2), so
// class_count must equal the Burnside coefficient a_w.
struct CorpusClassResult {
    CorpusClass corpus;
    SolveResult solve;
};

struct CorpusReport {
    std::uint32_t square_count{0};
    std::uint32_t weight{0};
    SolveConfig config;
    std::vector<CorpusClassResult> classes;
};

[[nodiscard]] CorpusReport run_corpus(
    std::uint32_t square_count,
    std::uint32_t weight,
    const SolveConfig& config = {}
);

// Schema: sqtopology.realizability.v1.
[[nodiscard]] std::string corpus_report_to_json(const CorpusReport& report);

[[nodiscard]] std::string scene_to_json(const Scene& scene);
[[nodiscard]] std::string topology_contact_keys_json(const Topology& topology);

}  // namespace sqtopology
