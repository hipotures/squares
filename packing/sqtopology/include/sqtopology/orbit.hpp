#pragma once

#include "sqtopology/topology.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace sqtopology {

// ---------------------------------------------------------------------------
// Independent event-set / group-action oracle for the uncapped rewrite system.
//
// For a fixed square count n the semantic contact events form a finite set
// Omega_n with
//
//   E(n) = |Omega_n| = 64*C(n,2) + 32*n,
//
// and an uncapped labeled topology is exactly a subset of Omega_n: one rewrite
// toggles one event, so the labeled rewrite graph is the Boolean hypercube Q_E.
//
// This module represents Omega_n, the induced action of
//
//   G_n = (D4^n semidirect S_n) x D4_container
//
// on it, event cycle decomposition, exact Burnside/Pólya orbit counting, and
// exact orbit-Hamming distances. It is written from the semantic specification
// and deliberately never calls canonicalization, so it can act as an
// independent mathematical oracle for the canonicalizing engine.
// ---------------------------------------------------------------------------

using EventId = std::uint32_t;

// Largest square count representable by the fixed-size group element below.
// n = 4 only needs 4; the margin keeps small experiments convenient.
inline constexpr std::uint32_t kMaxOrbitSquares = 8;

enum class EventKind : std::uint8_t {
    SquareSquare = 0,
    Wall = 1,
};

// Fully decoded event. For wall events first_square == second_square and only
// first_ring/wall are meaningful; for square-square events the two squares are
// distinct and the rings are ordered by square id.
struct EventRef {
    EventKind kind{EventKind::Wall};
    SquareId first_square{0};
    SquareId second_square{0};
    std::uint8_t first_ring{0};
    std::uint8_t second_ring{0};
    std::uint8_t wall{0};

    bool operator==(const EventRef&) const = default;
};

// Deterministic integer event IDs:
//   square-square: 64*pair_index(i, j) + 8*first_ring + second_ring   (i < j)
//   wall:          64*C(n,2) + 32*square + 4*ring + wall
// pair_index enumerates (0,1), (0,2), ..., (n-2,n-1) in lexicographic order.
struct EventSetLayout {
    std::uint32_t square_count{0};
    std::uint64_t square_square_count{0};
    std::uint64_t wall_count{0};
    std::uint64_t event_count{0};

    [[nodiscard]] static EventSetLayout for_square_count(std::uint32_t n);
    [[nodiscard]] std::uint64_t pair_index(SquareId first, SquareId second) const;
    [[nodiscard]] std::pair<SquareId, SquareId> pair_squares(std::uint64_t index) const;
    [[nodiscard]] EventId square_square_event(
        SquareId first,
        SquareId second,
        std::uint8_t first_ring,
        std::uint8_t second_ring
    ) const;
    [[nodiscard]] EventId wall_event(
        SquareId square,
        std::uint8_t ring,
        std::uint8_t wall
    ) const;
    [[nodiscard]] EventRef describe(EventId id) const;
    [[nodiscard]] EventKind kind_of(EventId id) const;
};

[[nodiscard]] std::uint64_t event_count_for_squares(std::uint32_t n) noexcept;

// D4 element in the engine's (rotation, reflected) representation. The engine
// convention is: reflect first with r -> (8-r) mod 8, then rotate by
// +2*rotation mod 8 on the eight-ring, and r -> (4-r) mod 4 then
// +rotation mod 4 on the four container walls.
struct D4Element {
    std::uint8_t rotation{0};
    bool reflected{false};

    bool operator==(const D4Element&) const = default;
};

// Composition: result acts as `outer` after `inner`.
[[nodiscard]] D4Element compose_d4(const D4Element& outer, const D4Element& inner);
[[nodiscard]] D4Element inverse_d4(const D4Element& element);
[[nodiscard]] std::uint8_t transform_ring(std::uint8_t ring, const D4Element& element);
[[nodiscard]] std::uint8_t transform_wall(std::uint8_t wall, const D4Element& element);

// Conjugacy class of a D4 element: identity, rotation180, rotation90,
// reflection through the corner axis, reflection through the side axis.
[[nodiscard]] std::string d4_conjugacy_class_name(const D4Element& element);

// One element of G_n. `square_map` is the old -> new square permutation, `local`
// carries the D4 transform applied at each *old* square, and `container` is the
// container D4 transform. A single square feature (s, r) therefore maps to
// (square_map[s], transform_ring(r, local[s])).
struct GroupElement {
    std::uint32_t square_count{0};
    std::array<SquareId, kMaxOrbitSquares> square_map{};
    std::array<D4Element, kMaxOrbitSquares> local{};
    D4Element container{};
};

[[nodiscard]] std::uint64_t group_element_count(std::uint32_t n);
[[nodiscard]] GroupElement identity_group_element(std::uint32_t n);
[[nodiscard]] GroupElement decode_group_element(std::uint32_t n, std::uint64_t index);
[[nodiscard]] std::uint64_t encode_group_element(const GroupElement& element);
// Composition: result acts as `outer` after `inner`.
[[nodiscard]] GroupElement compose_group_elements(
    const GroupElement& outer,
    const GroupElement& inner
);
[[nodiscard]] GroupElement inverse_group_element(const GroupElement& element);
[[nodiscard]] GroupElement conjugate_group_element(
    const GroupElement& element,
    const GroupElement& conjugator
);
[[nodiscard]] bool is_permutation(const GroupElement& element);

[[nodiscard]] EventId apply_group_element_to_event(const GroupElement& element, EventId id);
[[nodiscard]] std::vector<EventId> event_permutation(const GroupElement& element);

// Event subsets as a dense bitset of E(n) bits.
using EventBitset = std::vector<std::uint64_t>;

[[nodiscard]] EventBitset topology_to_event_bitset(const Topology& topology);
[[nodiscard]] Topology event_bitset_to_topology(std::uint32_t square_count, const EventBitset& bitset);
[[nodiscard]] std::uint64_t event_bitset_popcount(const EventBitset& bitset);
[[nodiscard]] std::uint64_t event_bitset_symmetric_difference_size(
    const EventBitset& first,
    const EventBitset& second
);
[[nodiscard]] EventBitset permute_event_bitset(
    const std::vector<EventId>& permutation,
    const EventBitset& bitset
);

// Applies a group element through the production relabel_square /
// relabel_container / permute_squares transformations. Used by tests and by the
// distance tool to verify the oracle against the engine's own symmetry
// contract. It does not canonicalize.
[[nodiscard]] Topology apply_group_element_to_topology(
    const Topology& topology,
    const GroupElement& element
);

struct OrbitDistanceResult {
    std::uint64_t distance{0};
    std::uint64_t first_weight{0};
    std::uint64_t second_weight{0};
    GroupElement witness{};
    // |first symmetric_difference witness(second)| recomputed through the
    // production transformations; must equal distance.
    std::uint64_t witness_symmetric_difference{0};
};

[[nodiscard]] OrbitDistanceResult orbit_hamming_distance(
    const Topology& first,
    const Topology& second
);

struct EventCycleType {
    std::vector<std::uint16_t> lengths;  // ascending

    [[nodiscard]] std::uint32_t cycle_count() const noexcept {
        return static_cast<std::uint32_t>(lengths.size());
    }
    [[nodiscard]] std::string to_compact_string() const;
};

[[nodiscard]] EventCycleType event_cycle_type(const GroupElement& element);

// One (ring D4 class, wall D4 class) contributor to a cycle type. Only
// meaningful for n = 1, where G_1 = D4_ring x D4_wall and every group element
// belongs to exactly one D4 class pair.
struct D4ClassPairCount {
    std::string ring_class;
    std::string wall_class;
    std::uint64_t group_elements{0};
};

struct CycleTypeRecord {
    EventCycleType cycle_type;
    std::uint64_t group_elements{0};
    // Exact contribution m * product(1 + x^|C|), as decimal strings a_0..a_E,
    // before division by |G|. Empty unless requested.
    std::vector<std::string> contribution_decimal;
    // n = 1 only: D4 class-pair breakdown of the group elements with this
    // induced cycle type. Empty otherwise.
    std::vector<D4ClassPairCount> d4_class_pairs;
};

struct OrbitCountOptions {
    bool emit_contributions{false};
    bool count_conjugacy_classes{true};
};

struct OrbitCountResult {
    std::uint32_t square_count{0};
    std::uint64_t event_count{0};
    std::uint64_t square_square_events{0};
    std::uint64_t wall_events{0};
    std::uint64_t group_size{0};
    std::uint64_t distinct_cycle_types{0};
    std::uint64_t conjugacy_classes{0};  // 0 when not computed
    // Sorted by (cycle count, lengths), therefore deterministic.
    std::vector<CycleTypeRecord> cycle_types;
    // Exact decimal strings. coefficient_sum_decimal holds the un-divided
    // Burnside numerator; coefficient_decimal holds a_d after exact division.
    std::vector<std::string> coefficient_sum_decimal;
    std::vector<std::string> coefficient_decimal;
    std::string total_orbit_count_decimal;
    std::string total_from_cycle_counts_decimal;
    bool checks_divisible{true};
    bool checks_complement_symmetric{true};
    bool checks_total_matches{true};
    bool checks_endpoints_unit{true};
    bool checks_positive{true};
    double enumeration_seconds{0.0};
    double polynomial_seconds{0.0};
    double total_seconds{0.0};
    std::uint64_t peak_rss_kib{0};
};

[[nodiscard]] OrbitCountResult burnside_orbit_count(
    std::uint32_t square_count,
    const OrbitCountOptions& options = {}
);

[[nodiscard]] std::string orbit_count_to_json(const OrbitCountResult& result);

// Number of conjugacy classes of G_n, computed by explicit conjugation-BFS on
// the enumerated group. Feasible for n <= 4 on this host.
[[nodiscard]] std::uint64_t group_conjugacy_class_count(std::uint32_t n);

}  // namespace sqtopology
