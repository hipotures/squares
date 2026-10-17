#pragma once

#include "sqtopology/bigint.hpp"
#include "sqtopology/orbit.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace sqtopology {

// ---------------------------------------------------------------------------
// Class-aggregated exact Burnside counting for
//
//   G_n = (D4 wr S_n) x D4_container,  |G_n| = n! * 8^n * 8,
//
// replacing direct enumeration of all |G_n| elements with a sum over
// conjugacy classes of the wreath product. The classification used is the
// standard one for B wr S_n: a class is a multiset of cycles of the square
// permutation, each cycle decorated with the conjugacy class of its cycle
// product in B = D4; conjugate classes of equal cycle length may be permuted.
//
// The induced action on Omega_n is a class function (conjugate group elements
// induce conjugate event permutations, hence equal cycle type), so one
// canonical representative per class is enough to obtain the exact induced
// event cycle type; the class size supplies the Burnside multiplicity.
// ---------------------------------------------------------------------------

// Largest square count supported by the class-aggregated counter. Class sizes,
// Burnside weights, and the group order |G_12| ~ 2.6e20 are accumulated in
// 128-bit integers; every consumer of the 64-bit wrappers below keeps its own
// range check. n = 12 closes the low-weight d = 6 stabilization row.
inline constexpr std::uint32_t kMaxWreathSquares = 12;

enum class D4Class : std::uint8_t {
    Identity = 0,
    Rotation180 = 1,
    Rotation90 = 2,
    ReflectionCornerAxis = 3,
    ReflectionSideAxis = 4,
};

inline constexpr std::uint32_t kD4ClassCount = 5;

[[nodiscard]] std::uint32_t d4_class_size(D4Class element_class) noexcept;
[[nodiscard]] const char* d4_class_name(D4Class element_class) noexcept;
[[nodiscard]] D4Class d4_class_of(const D4Element& element);
[[nodiscard]] D4Element d4_class_representative(D4Class element_class) noexcept;

// Wreath-product conjugacy type of one element of D4 wr S_n, together with the
// independent container D4 class. counts[l][c] is the number of l-cycles of
// the square permutation whose cycle product has D4 conjugacy class c.
struct GroupConjugacyType {
    std::uint32_t square_count{0};
    std::array<std::array<std::uint8_t, kD4ClassCount>, kMaxWreathSquares + 1> counts{};
    D4Class container{D4Class::Identity};

    [[nodiscard]] std::uint32_t square_cycle_count() const noexcept;
    [[nodiscard]] std::string label() const;
    bool operator==(const GroupConjugacyType&) const = default;
};

// All wreath-product conjugacy types of D4 wr S_n, in a deterministic order
// (cycle lengths ascending, class multiplicities colexicographic). The
// container field is always Identity here; the full G_n class list is the
// product of this list with the five container classes.
[[nodiscard]] std::vector<GroupConjugacyType> enumerate_group_conjugacy_types(
    std::uint32_t n
);

// Conjugacy type of an explicitly constructed group element.
[[nodiscard]] GroupConjugacyType wreath_type_of_element(const GroupElement& element);

// Exact class size in G_n (including the container factor), from the class
// formula validated against direct element enumeration for n <= 4. The wide
// form is the primary implementation (128-bit, exact for every supported n);
// the uint64 form is the historical interface and throws when a class size
// exceeds 64 bits. Every class size fits 64 bits through n = 12 (the maximum,
// reached at n = 12, is 1.37e18), so the guard is future-proofing for
// extensions past the current square-count cap.
[[nodiscard]] BigWide group_class_size_wide(const GroupConjugacyType& type);
[[nodiscard]] std::uint64_t group_class_size(const GroupConjugacyType& type);

// Canonical representative of the class: square permutation built from
// consecutive increasing cycles, cycle product classes realized by one D4
// label at the cycle start, container D4 class representative.
[[nodiscard]] GroupElement representative_group_element(const GroupConjugacyType& type);

// Number of conjugacy classes of G_n via the classification: 5 * types.
[[nodiscard]] std::uint64_t group_conjugacy_class_count_wreath(std::uint32_t n);

struct WreathCountOptions {
    // When true, only coefficients a_0..a_low_weight_max are accumulated; the
    // full polynomial and the total are then not evaluated.
    bool low_weight_only{false};
    std::uint32_t low_weight_max{0};
    // Include the induced-cycle-type accumulation table in the result.
    bool emit_cycle_type_table{false};
};

struct InducedTypeRecord {
    EventCycleType cycle_type;
    // Summed class size for this induced type. The 64-bit mirror is zero when
    // the sum exceeds 64 bits (class sizes are positive, so a zero mirror
    // always means "did not fit"), in which case class_elements_decimal is
    // authoritative. No induced-type sum exceeds 64 bits through n = 12 (the
    // maximum is 1.10e19); the split keeps the interface ready for larger n.
    std::uint64_t class_elements{0};
    std::string class_elements_decimal;
    std::uint64_t classes{0};  // number of conjugacy classes
};

struct WreathCountResult {
    std::uint32_t square_count{0};
    std::uint64_t event_count{0};
    // 64-bit mirror of |G_n|; zero when the order exceeds 64 bits (n = 12),
    // in which case group_size_decimal is the authoritative value.
    std::uint64_t group_size{0};
    std::string group_size_decimal;
    std::uint64_t wreath_conjugacy_types{0};
    std::uint64_t total_conjugacy_classes{0};
    std::uint64_t distinct_induced_cycle_types{0};
    // 64-bit mirror of the class-size sum; zero when it exceeds 64 bits
    // (n = 12), in which case class_size_sum_decimal is authoritative.
    std::uint64_t class_size_sum{0};
    std::string class_size_sum_decimal;
    std::uint64_t low_weight_max{0};
    bool low_weight_only{false};
    std::vector<InducedTypeRecord> induced_types;
    // Exact decimal strings. In low-weight mode these cover a_0..a_low_weight_max.
    std::vector<std::string> coefficient_decimal;
    std::vector<std::string> coefficient_sum_decimal;
    std::string total_orbit_count_decimal;
    std::string total_from_cycle_counts_decimal;
    bool checks_class_size_sum{true};
    bool checks_divisible{true};
    bool checks_complement_symmetric{true};
    bool checks_total_matches{true};
    bool checks_endpoints_unit{true};
    bool checks_positive{true};
    double class_generation_seconds{0.0};
    double event_cycle_seconds{0.0};
    double polynomial_seconds{0.0};
    double total_seconds{0.0};
    std::uint64_t peak_rss_kib{0};
};

[[nodiscard]] WreathCountResult wreath_burnside_count(
    std::uint32_t n,
    const WreathCountOptions& options = {}
);

[[nodiscard]] std::string wreath_count_to_json(const WreathCountResult& result);

// Direct cross-check for n <= 4: enumerate every group element, derive its
// conjugacy type, and verify that (a) the number of elements with each type
// equals the class-size formula, and (b) every element of a type induces the
// cycle type computed at the canonical representative of that class.
struct WreathCrossCheckResult {
    std::uint32_t square_count{0};
    std::uint64_t elements{0};
    std::uint64_t classes{0};
    std::uint64_t classes_seen{0};
    bool counts_match{true};
    bool induced_types_match{true};
};

[[nodiscard]] WreathCrossCheckResult cross_check_wreath_against_elements(
    std::uint32_t n
);

// Staged symmetry compression for small n: exact orbit counts a_d of weight-d
// event subsets under the sub-groups of G_n, d = 0..weight_max.
struct StagedQuotientRow {
    std::uint32_t square_count{0};
    std::uint32_t weight_max{0};
    std::vector<std::string> local_only;         // D4^n
    std::vector<std::string> squares_only;       // S_n x D4_container
    std::vector<std::string> local_and_squares;  // D4 wr S_n
    std::vector<std::string> full;               // G_n
};

[[nodiscard]] StagedQuotientRow staged_quotient_counts(
    std::uint32_t n,
    std::uint32_t weight_max
);

}  // namespace sqtopology
