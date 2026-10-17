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
//       one square, which forces a point onto two parallel lines;
//   R4: a wall-side contact and a wall-corner contact of one of its own
//       endpoints on the same wall cannot both be exact, because the side
//       absorbs the corner;
//   R5: two adjacent corners of one square on the same wall put the connecting
//       side on that wall, which absorbs both corner contacts;
//   R6: two opposite corners of one square on the same wall force the other
//       two corners to distance 1/sqrt(2) on either side of the wall line, so
//       one is outside the container;
//   R7: one corner feature required on two distinct walls (disjoint opposite
//       segments, or an adjacent-wall wedge whose absorbing side lies on the
//       wall);
//   R8: a corner and a non-incident side of the same square on one wall
//       (corner-to-side-line distance is exactly 1);
//   R9: two distinct sides of one square on the same wall (adjacent sides are
//       perpendicular; opposite sides are parallel at distance 1);
//   R10: an orientation/parallelism cycle in Z_2 (SS parallel, wall-side
//       parallel to the wall, adjacent sides perpendicular);
//   R11: a CC class containing two distinct corners of one square;
//   R12: two corners of one square on the interior of the same side feature
//       (open side length 1 - 2e-6, corner distance at least 1);
//   R13: a CC class containing a non-endpoint corner of a square and a corner
//       required on one of that square's sides (distance 1).
//
// All predicates depend only on incidences and fixed unit-square feature
// distances, so they are invariant under the full G_n action (endpoint,
// adjacency, opposition, parallelism and coincidence are D4 relations). A
// proof therefore lifts from the class representative to every gauge branch
// and to the whole canonical orbit. R7-R13 are tolerance-safe because their
// contradictions are separated by a fixed distance (1, sqrt(2) or the 2e-6
// strict-interior margin) or by 90 degrees, far above the 1e-7 contact
// tolerance. Forced-event rules whose conclusion would accumulate several
// contact tolerances (R14/R15 candidates) are deliberately not included; see
// docs/geometric-realizability-phase2b-2026-10-17.md.
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
    // Deterministic solve budget per gauge branch. A full class search may use
    // up to 2^n times this value (see realize_topology).
    std::uint64_t max_solves{400};
    // Heuristic bisection for the smallest container side with a witness.
    bool minimize_container{true};
    std::uint32_t minimization_steps{8};
    std::uint64_t seed{0x9e3779b97f4a7c15ULL};
    // Corpus worker count. Each canonical class is an independent work item and
    // is solved on one thread; the per-class solver is single-threaded, so
    // N workers mean N concurrent single-threaded solvers (no nested
    // oversubscription). Must be at least 1. Workers only affect scheduling:
    // class order, seeds and results are independent of the worker count.
    std::uint32_t workers{1};
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
    // Bit i is set when the witness uses the reflected feature frame of square
    // i. Branch 0 is the standard-frame representative; other branches are the
    // 2^n cosets of H_n inside the G_n orbit (see realize.cpp). The witness is
    // always stated for the input Sigma, so it verifies against Sigma directly.
    std::uint32_t frame_branch{0};
    std::uint32_t weak_frame_branch{0};
    std::uint32_t branches_tried{0};
    std::uint64_t solves{0};
};

// Solves the realizability problem for Sigma. Requires a normalized topology
// with no duplicate contacts; square counts of 1..4 keep the enumeration-free
// solver paths fast.
//
// The search enumerates the 2^n gauge branches of Sigma: the cosets of the
// standard-frame subgroup H_n inside its full G_n orbit. Realizability is
// G_n-invariant (see the symmetry-contract notes in the Phase-2 document), so
// the class is feasible iff some branch is; a witness found for branch b is
// transported back to Sigma with psi_{tau_b} and re-verified against Sigma.
// The returned witness therefore verifies against the input topology, with
// per-square frame parity when a mixed-parity branch was used.
[[nodiscard]] SolveResult realize_topology(const Topology& sigma, const SolveConfig& config = {});

// Scene action psi_g for EVERY element of G_n. The semantic feature frame of a
// square carries a discrete parity, and psi_g updates it together with the
// center and orientation:
//
//   F'_sigma(i) = Q_g F_i L_i^{-1},   Q_g = R(-90k) M^b,
//
// where F_i = R(theta_i) M^{b_i} is the pose frame, L_i is the ring-direction
// map of the local D4 element, and Q_g is the container isometry (wall
// w -> transform_wall(w, container)). The resulting pose has
// theta' = atan2(-F'[0][1], F'[1][1]) and frame_reflected = det(F') < 0.
// Then extraction(psi_g(P)) == g . extraction(P) holds for both the exact and
// weak strata; the test suite checks this against the production
// relabel_square / relabel_container / permute_squares transformations for all
// of G_1, G_2 and G_3.
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
