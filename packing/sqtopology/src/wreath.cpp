#include "sqtopology/wreath.hpp"

#include "sqtopology/bigint.hpp"

#include <algorithm>
#include <chrono>
#include <cstdint>
#include <iomanip>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include <sys/resource.h>

namespace sqtopology {
namespace {

// Wide exact arithmetic for the class size product. The module is built with
// -Wpedantic, so the 128-bit type is introduced through the GCC/Clang
// __extension__ mechanism instead of a bare WideUint use.
__extension__ using WideUint = unsigned __int128;

using Clock = std::chrono::steady_clock;

double seconds_between(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double>(end - start).count();
}

std::uint64_t factorial(std::uint32_t n) {
    std::uint64_t result = 1;
    for (std::uint32_t value = 2; value <= n; ++value) {
        result *= value;
    }
    return result;
}

std::uint64_t small_power(std::uint64_t base, std::uint32_t exponent) {
    std::uint64_t result = 1;
    for (std::uint32_t step = 0; step < exponent; ++step) {
        result *= base;
    }
    return result;
}

std::uint64_t small_binomial(std::uint32_t total, std::uint32_t chosen) {
    if (chosen > total) {
        return 0;
    }
    chosen = std::min(chosen, total - chosen);
    std::uint64_t result = 1;
    for (std::uint32_t step = 1; step <= chosen; ++step) {
        result = result * (total - chosen + step) / step;
    }
    return result;
}

// Deterministic packed key of an event cycle type (2 bytes per length).
std::string pack_cycle_type(const EventCycleType& type) {
    std::string key;
    key.reserve(type.lengths.size() * 2);
    for (const auto length : type.lengths) {
        key.push_back(static_cast<char>(length & 0xFFU));
        key.push_back(static_cast<char>((length >> 8) & 0xFFU));
    }
    return key;
}

// Exact class size of a wreath-product conjugacy type without the container
// factor, computed as
//   n! / (prod_l l^{m_l} prod_{l,c} m[l][c]!) * 8^{n-r} * prod_{l,c} |c|^{m[l][c]}
// where m_l = sum_c m[l][c] and r = sum_l m_l is the square-cycle count.
// Every intermediate division below is exact by construction: the cycle-type
// count n!/(prod_l l^{m_l} m_l!) is an integer, the class multinomial
// prod_l m_l!/prod_c m[l][c]! is an integer, and 8^{n-r} and the D4 class
// sizes are integers.
WideUint wreath_class_size_numerator(const GroupConjugacyType& type) {
    const std::uint32_t n = type.square_count;
    std::array<std::uint32_t, kMaxWreathSquares + 1> multiplicity{};
    std::uint32_t cycle_total = 0;
    std::uint32_t weight = 0;
    for (std::uint32_t length = 1; length <= n; ++length) {
        std::uint32_t count = 0;
        for (std::uint32_t element_class = 0; element_class < kD4ClassCount; ++element_class) {
            count += type.counts[length][element_class];
        }
        multiplicity[length] = count;
        cycle_total += count;
        weight += length * count;
    }
    if (weight != n) {
        throw std::invalid_argument("conjugacy type does not weigh n");
    }

    WideUint value = factorial(n);
    for (std::uint32_t length = 1; length <= n; ++length) {
        if (multiplicity[length] > 0) {
            value /= small_power(length, multiplicity[length]);
        }
    }
    // N_sigma = n! / (prod_l l^{m_l} m_l!); the divisions below are exact
    // because n! / (prod_l l^{m_l}) = N_sigma * prod_l m_l!.
    for (std::uint32_t length = 1; length <= n; ++length) {
        if (multiplicity[length] > 0) {
            value /= factorial(multiplicity[length]);
        }
    }
    // Multinomial factors prod_l m_l! / prod_c m[l][c]!.
    for (std::uint32_t length = 1; length <= n; ++length) {
        if (multiplicity[length] == 0) {
            continue;
        }
        std::uint32_t remaining = multiplicity[length];
        for (std::uint32_t element_class = 0;
             element_class < kD4ClassCount;
             ++element_class) {
            const std::uint32_t count = type.counts[length][element_class];
            if (count == 0) {
                continue;
            }
            value *= small_binomial(remaining, count);
            remaining -= count;
        }
    }
    value *= small_power(8, n - cycle_total);
    for (std::uint32_t length = 1; length <= n; ++length) {
        for (std::uint32_t element_class = 0;
             element_class < kD4ClassCount;
             ++element_class) {
            const std::uint32_t count = type.counts[length][element_class];
            if (count > 0) {
                value *= small_power(
                    d4_class_size(static_cast<D4Class>(element_class)),
                    count
                );
            }
        }
    }
    return value;
}

// Enumerate the integer partitions of the remaining weight together with the
// distribution of every cycle multiplicity over the five D4 classes.
void enumerate_types_recursive(
    std::uint32_t square_count,
    std::uint32_t remaining,
    std::uint32_t length,
    GroupConjugacyType& current,
    std::vector<GroupConjugacyType>& out
) {
    if (remaining == 0) {
        current.square_count = square_count;
        current.container = D4Class::Identity;
        out.push_back(current);
        return;
    }
    if (length > remaining) {
        return;
    }
    const std::uint32_t max_multiplicity = remaining / length;
    for (std::uint32_t count = 0; count <= max_multiplicity; ++count) {
        // Distribute `count` cycles over the five classes; for count = 0 there
        // is exactly one distribution, the empty one.
        std::array<std::uint32_t, kD4ClassCount> distribution{};
        const auto distribute = [&](auto&& self, std::uint32_t slot, std::uint32_t left) {
            if (slot + 1 == kD4ClassCount) {
                distribution[slot] = left;
                for (std::uint32_t element_class = 0;
                     element_class < kD4ClassCount;
                     ++element_class) {
                    current.counts[length][element_class] =
                        static_cast<std::uint8_t>(distribution[element_class]);
                }
                enumerate_types_recursive(
                    square_count,
                    remaining - count * length,
                    length + 1,
                    current,
                    out
                );
                return;
            }
            for (std::uint32_t take = 0; take <= left; ++take) {
                distribution[slot] = take;
                self(self, slot + 1, left - take);
            }
        };
        distribute(distribute, 0, count);
    }
    for (std::uint32_t element_class = 0; element_class < kD4ClassCount; ++element_class) {
        current.counts[length][element_class] = 0;
    }
}

// Low-weight coefficient accumulator: [x^d] prod_cycles (1 + x^{|cycle|}) for
// d <= max_degree depends only on the cycle lengths <= max_degree.
class LowWeightAccumulator {
  public:
    explicit LowWeightAccumulator(std::uint32_t max_degree)
        : max_degree_(max_degree), sums_(max_degree + 1) {}

    void add(const EventCycleType& cycle_type, std::uint64_t weight) {
        std::vector<BigUint> polynomial(static_cast<std::size_t>(max_degree_) + 1);
        polynomial[0] = BigUint(1);
        for (const auto length : cycle_type.lengths) {
            if (length > max_degree_) {
                continue;
            }
            for (std::uint32_t degree = max_degree_; degree >= length; --degree) {
                polynomial[degree].add_into(polynomial[degree - length]);
            }
        }
        for (std::uint32_t degree = 0; degree <= max_degree_; ++degree) {
            BigUint term = polynomial[degree];
            term.mul_small(weight);
            sums_[degree].add_into(term);
        }
    }

    std::vector<std::string> divide_exact(std::uint64_t order, bool& ok) const {
        std::vector<std::string> result;
        result.reserve(sums_.size());
        for (const auto& sum : sums_) {
            BigUint value = sum;
            const std::uint64_t remainder = value.div_small(order);
            if (remainder != 0) {
                ok = false;
            }
            result.push_back(value.to_decimal());
        }
        return result;
    }

    [[nodiscard]] const BigUint& sum(std::uint32_t degree) const {
        return sums_[degree];
    }

  private:
    std::uint32_t max_degree_{0};
    std::vector<BigUint> sums_;
};

}  // namespace

// ---------------------------------------------------------------------------
// D4 conjugacy classes
// ---------------------------------------------------------------------------

std::uint32_t d4_class_size(D4Class element_class) noexcept {
    switch (element_class) {
        case D4Class::Identity:
        case D4Class::Rotation180:
            return 1;
        case D4Class::Rotation90:
        case D4Class::ReflectionCornerAxis:
        case D4Class::ReflectionSideAxis:
            return 2;
    }
    return 0;
}

const char* d4_class_name(D4Class element_class) noexcept {
    switch (element_class) {
        case D4Class::Identity:
            return "identity";
        case D4Class::Rotation180:
            return "rotation180";
        case D4Class::Rotation90:
            return "rotation90";
        case D4Class::ReflectionCornerAxis:
            return "reflection_corner_axis";
        case D4Class::ReflectionSideAxis:
            return "reflection_side_axis";
    }
    return "unknown";
}

D4Class d4_class_of(const D4Element& element) {
    if (element.rotation >= 4) {
        throw std::invalid_argument("rotation index outside D4 domain");
    }
    if (!element.reflected) {
        if (element.rotation == 0) {
            return D4Class::Identity;
        }
        if (element.rotation == 2) {
            return D4Class::Rotation180;
        }
        return D4Class::Rotation90;
    }
    return (element.rotation % 2 == 0) ? D4Class::ReflectionCornerAxis
                                       : D4Class::ReflectionSideAxis;
}

D4Element d4_class_representative(D4Class element_class) noexcept {
    switch (element_class) {
        case D4Class::Identity:
            return D4Element{.rotation = 0, .reflected = false};
        case D4Class::Rotation180:
            return D4Element{.rotation = 2, .reflected = false};
        case D4Class::Rotation90:
            return D4Element{.rotation = 1, .reflected = false};
        case D4Class::ReflectionCornerAxis:
            return D4Element{.rotation = 0, .reflected = true};
        case D4Class::ReflectionSideAxis:
            return D4Element{.rotation = 1, .reflected = true};
    }
    return D4Element{};
}

// ---------------------------------------------------------------------------
// Conjugacy types
// ---------------------------------------------------------------------------

std::uint32_t GroupConjugacyType::square_cycle_count() const noexcept {
    std::uint32_t total = 0;
    for (std::uint32_t length = 1; length <= square_count; ++length) {
        for (std::uint32_t element_class = 0; element_class < kD4ClassCount; ++element_class) {
            total += counts[length][element_class];
        }
    }
    return total;
}

std::string GroupConjugacyType::label() const {
    std::ostringstream out;
    for (std::uint32_t length = 1; length <= square_count; ++length) {
        std::uint32_t total = 0;
        for (const auto count : counts[length]) {
            total += count;
        }
        if (total == 0) {
            continue;
        }
        out << length << ":(";
        for (std::uint32_t element_class = 0; element_class < kD4ClassCount; ++element_class) {
            if (element_class != 0) {
                out << ',';
            }
            out << static_cast<int>(counts[length][element_class]);
        }
        out << ");";
    }
    out << "c=" << d4_class_name(container);
    return out.str();
}

std::vector<GroupConjugacyType> enumerate_group_conjugacy_types(std::uint32_t n) {
    if (n == 0 || n > kMaxWreathSquares) {
        throw std::invalid_argument("conjugacy types require 1 <= n <= kMaxWreathSquares");
    }
    std::vector<GroupConjugacyType> types;
    GroupConjugacyType current;
    enumerate_types_recursive(n, n, 1, current, types);
    return types;
}

GroupConjugacyType wreath_type_of_element(const GroupElement& element) {
    const std::uint32_t n = element.square_count;
    if (n == 0 || n > kMaxWreathSquares) {
        throw std::invalid_argument("element square count outside the supported range");
    }
    GroupConjugacyType type;
    type.square_count = n;
    std::vector<std::uint8_t> visited(n, 0);
    for (SquareId start = 0; start < n; ++start) {
        if (visited[start] != 0) {
            continue;
        }
        std::vector<SquareId> cycle;
        SquareId current = start;
        do {
            visited[current] = 1;
            cycle.push_back(current);
            current = element.square_map[current];
        } while (current != start);
        // Invariant cycle product in the order fixed by the class
        // classification: product of the labels along the cycle, applied in
        // the order of the cycle itself, i.e. label(i_{l-1}) o ... o label(i_0).
        D4Element product{};
        for (const SquareId square : cycle) {
            product = compose_d4(element.local[square], product);
        }
        const auto element_class = static_cast<std::uint32_t>(d4_class_of(product));
        ++type.counts[cycle.size()][element_class];
    }
    type.container = d4_class_of(element.container);
    return type;
}

std::uint64_t group_class_size(const GroupConjugacyType& type) {
    const WideUint value = wreath_class_size_numerator(type);
    if (type.container != D4Class::Identity) {
        // The container factor multiplies the wreath class size; recompute the
        // full expression to keep the arithmetic exact.
        const WideUint container_factor = d4_class_size(type.container);
        const WideUint scaled = value * container_factor;
        if (scaled > static_cast<WideUint>(~std::uint64_t{0})) {
            throw std::overflow_error("class size does not fit in 64 bits");
        }
        return static_cast<std::uint64_t>(scaled);
    }
    if (value > static_cast<WideUint>(~std::uint64_t{0})) {
        throw std::overflow_error("class size does not fit in 64 bits");
    }
    return static_cast<std::uint64_t>(value);
}

GroupElement representative_group_element(const GroupConjugacyType& type) {
    const std::uint32_t n = type.square_count;
    if (n == 0 || n > kMaxWreathSquares) {
        throw std::invalid_argument("representative requires 1 <= n <= kMaxWreathSquares");
    }
    GroupElement element = identity_group_element(n);
    SquareId next = 0;
    for (std::uint32_t length = 1; length <= n; ++length) {
        for (std::uint32_t element_class = 0; element_class < kD4ClassCount; ++element_class) {
            const std::uint32_t count = type.counts[length][element_class];
            for (std::uint32_t index = 0; index < count; ++index) {
                if (next + length > n) {
                    throw std::invalid_argument("conjugacy type overflows the square count");
                }
                for (std::uint32_t step = 0; step < length; ++step) {
                    const SquareId square = static_cast<SquareId>(next + step);
                    element.square_map[square] = static_cast<SquareId>(
                        step + 1 < length ? next + step + 1 : next
                    );
                }
                element.local[next] = d4_class_representative(
                    static_cast<D4Class>(element_class)
                );
                next = static_cast<SquareId>(next + length);
            }
        }
    }
    if (next != n) {
        throw std::invalid_argument("conjugacy type does not cover all squares");
    }
    element.container = d4_class_representative(type.container);
    return element;
}

std::uint64_t group_conjugacy_class_count_wreath(std::uint32_t n) {
    return kD4ClassCount * static_cast<std::uint64_t>(enumerate_group_conjugacy_types(n).size());
}

// ---------------------------------------------------------------------------
// Exact class-aggregated Burnside counting
// ---------------------------------------------------------------------------

WreathCountResult wreath_burnside_count(
    std::uint32_t n,
    const WreathCountOptions& options
) {
    if (n == 0 || n > kMaxWreathSquares) {
        throw std::invalid_argument("wreath counting requires 1 <= n <= kMaxWreathSquares");
    }
    if (options.low_weight_only && options.low_weight_max > event_count_for_squares(n)) {
        throw std::invalid_argument("low-weight bound exceeds the event count");
    }
    const auto total_started = Clock::now();
    const EventSetLayout layout = EventSetLayout::for_square_count(n);
    const std::uint64_t event_count = layout.event_count;
    const std::uint64_t group_size = group_element_count(n);
    if (options.low_weight_only && options.low_weight_max == 0) {
        throw std::invalid_argument("low-weight mode needs a positive bound");
    }

    WreathCountResult result;
    result.square_count = n;
    result.event_count = event_count;
    result.group_size = group_size;
    result.low_weight_only = options.low_weight_only;
    result.low_weight_max = options.low_weight_max;

    // --- Class generation: wreath classes with exact sizes. ----------------
    const auto generation_started = Clock::now();
    const std::vector<GroupConjugacyType> wreath_types = enumerate_group_conjugacy_types(n);
    std::vector<std::uint64_t> wreath_sizes(wreath_types.size(), 0);
    std::uint64_t wreath_size_sum = 0;
    for (std::size_t index = 0; index < wreath_types.size(); ++index) {
        wreath_sizes[index] = group_class_size(wreath_types[index]);
        wreath_size_sum += wreath_sizes[index];
    }
    result.wreath_conjugacy_types = wreath_types.size();
    result.total_conjugacy_classes = kD4ClassCount * wreath_types.size();
    const std::uint64_t wreath_group_size = factorial(n) * small_power(8, n);
    if (wreath_size_sum != wreath_group_size) {
        result.checks_class_size_sum = false;
    }
    result.class_generation_seconds = seconds_between(generation_started, Clock::now());

    // --- Induced event cycle types, one representative per class. -----------
    const auto event_cycles_started = Clock::now();
    struct Aggregate {
        EventCycleType cycle_type;
        std::uint64_t weight{0};
        std::uint64_t classes{0};
    };
    std::map<std::string, Aggregate> aggregates;
    std::uint64_t class_size_sum = 0;
    for (const auto& wreath_type : wreath_types) {
        const std::uint64_t wreath_size = group_class_size(wreath_type);
        for (std::uint32_t container_index = 0; container_index < kD4ClassCount;
             ++container_index) {
            GroupConjugacyType full = wreath_type;
            full.container = static_cast<D4Class>(container_index);
            const std::uint64_t class_size =
                wreath_size * d4_class_size(full.container);
            class_size_sum += class_size;
            const GroupElement element = representative_group_element(full);
            const EventCycleType cycle_type = event_cycle_type(element);
            const std::string key = pack_cycle_type(cycle_type);
            auto [position, inserted] = aggregates.try_emplace(key);
            if (inserted) {
                position->second.cycle_type = cycle_type;
            }
            position->second.weight += class_size;
            position->second.classes += 1;
        }
    }
    result.class_size_sum = class_size_sum;
    if (class_size_sum != group_size) {
        result.checks_class_size_sum = false;
    }
    result.distinct_induced_cycle_types = aggregates.size();
    result.event_cycle_seconds = seconds_between(event_cycles_started, Clock::now());

    // --- Exact orbit polynomial ---------------------------------------------
    const auto polynomial_started = Clock::now();
    const std::uint32_t max_degree = options.low_weight_only
        ? options.low_weight_max
        : static_cast<std::uint32_t>(event_count);
    std::vector<BigUint> coefficient_sums(static_cast<std::size_t>(max_degree) + 1);
    BigUint total_from_cycle_counts(0);
    for (const auto& [key, aggregate] : aggregates) {
        std::vector<BigUint> polynomial(static_cast<std::size_t>(max_degree) + 1);
        polynomial[0] = BigUint(1);
        std::uint32_t degree = 0;
        for (const auto length : aggregate.cycle_type.lengths) {
            if (length > max_degree) {
                continue;
            }
            degree += length;
            const std::uint32_t top = std::min(degree, max_degree);
            for (std::uint32_t index = top; index >= length; --index) {
                polynomial[index].add_into(polynomial[index - length]);
            }
        }
        for (std::uint32_t index = 0; index <= max_degree; ++index) {
            BigUint term = polynomial[index];
            term.mul_small(aggregate.weight);
            coefficient_sums[index].add_into(term);
        }
        if (!options.low_weight_only) {
            BigUint element_count = BigUint::power_of_two(aggregate.cycle_type.cycle_count());
            element_count.mul_small(aggregate.weight);
            total_from_cycle_counts.add_into(element_count);
        }
    }
    result.polynomial_seconds = seconds_between(polynomial_started, Clock::now());

    // --- Exact division by |G| and internal checks. -------------------------
    BigUint numerator_total(0);
    for (const auto& coefficient : coefficient_sums) {
        numerator_total.add_into(coefficient);
    }
    if (!options.low_weight_only) {
        const std::uint64_t remainder = numerator_total.div_small(group_size);
        if (remainder != 0) {
            result.checks_divisible = false;
        }
        result.total_orbit_count_decimal = numerator_total.to_decimal();
    }

    result.coefficient_sum_decimal.reserve(coefficient_sums.size());
    result.coefficient_decimal.reserve(coefficient_sums.size());
    for (auto& coefficient : coefficient_sums) {
        BigUint value = coefficient;
        const std::uint64_t remainder = value.div_small(group_size);
        if (remainder != 0) {
            result.checks_divisible = false;
        }
        result.coefficient_sum_decimal.push_back(coefficient.to_decimal());
        result.coefficient_decimal.push_back(value.to_decimal());
    }

    if (!options.low_weight_only) {
        const std::uint64_t remainder = total_from_cycle_counts.div_small(group_size);
        if (remainder != 0) {
            result.checks_divisible = false;
        }
        result.total_from_cycle_counts_decimal = total_from_cycle_counts.to_decimal();
        if (result.total_orbit_count_decimal != result.total_from_cycle_counts_decimal) {
            result.checks_total_matches = false;
        }
        for (std::size_t index = 0; index < result.coefficient_decimal.size(); ++index) {
            if (result.coefficient_decimal[index]
                != result.coefficient_decimal[result.coefficient_decimal.size() - 1 - index]) {
                result.checks_complement_symmetric = false;
            }
            if (result.coefficient_decimal[index] == "0") {
                result.checks_positive = false;
            }
        }
        if (result.coefficient_decimal.front() != "1"
            || result.coefficient_decimal.back() != "1") {
            result.checks_endpoints_unit = false;
        }
    } else {
        if (result.coefficient_decimal.front() != "1") {
            result.checks_endpoints_unit = false;
        }
        for (const auto& coefficient : result.coefficient_decimal) {
            if (coefficient == "0") {
                result.checks_positive = false;
            }
        }
    }

    if (options.emit_cycle_type_table) {
        result.induced_types.reserve(aggregates.size());
        for (const auto& [key, aggregate] : aggregates) {
            result.induced_types.push_back(InducedTypeRecord{
                .cycle_type = aggregate.cycle_type,
                .class_elements = aggregate.weight,
                .classes = aggregate.classes,
            });
        }
        std::sort(
            result.induced_types.begin(),
            result.induced_types.end(),
            [](const InducedTypeRecord& lhs, const InducedTypeRecord& rhs) {
                if (lhs.cycle_type.cycle_count() != rhs.cycle_type.cycle_count()) {
                    return lhs.cycle_type.cycle_count() < rhs.cycle_type.cycle_count();
                }
                return lhs.cycle_type.lengths < rhs.cycle_type.lengths;
            }
        );
    }

    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        result.peak_rss_kib = static_cast<std::uint64_t>(usage.ru_maxrss);
    }
    result.total_seconds = seconds_between(total_started, Clock::now());
    return result;
}

std::string wreath_count_to_json(const WreathCountResult& result) {
    std::ostringstream out;
    out << std::setprecision(17);
    out << '{'
        << "\"schema\":\"sqtopology.wreath-count.v1\","
        << "\"n\":" << result.square_count << ','
        << "\"event_count\":" << result.event_count << ','
        << "\"group_size\":" << result.group_size << ','
        << "\"group_order_formula\":\"n! * 8^n * 8\","
        << "\"wreath_conjugacy_types\":" << result.wreath_conjugacy_types << ','
        << "\"total_conjugacy_classes\":" << result.total_conjugacy_classes << ','
        << "\"distinct_induced_cycle_types\":" << result.distinct_induced_cycle_types << ','
        << "\"class_size_sum\":" << result.class_size_sum << ','
        << "\"mode\":\"" << (result.low_weight_only ? "low_weight" : "full") << "\","
        << "\"low_weight_max\":" << result.low_weight_max << ','
        << "\"coefficients\":[";
    for (std::size_t index = 0; index < result.coefficient_decimal.size(); ++index) {
        if (index != 0) {
            out << ',';
        }
        out << '"' << result.coefficient_decimal[index] << '"';
    }
    out << "],\"total_orbit_count\":\"" << result.total_orbit_count_decimal << '"'
        << ",\"total_from_cycle_counts\":\"" << result.total_from_cycle_counts_decimal << '"'
        << ",\"checks\":{"
        << "\"class_size_sum_equals_group\":" << (result.checks_class_size_sum ? "true" : "false")
        << ",\"all_coefficients_divisible\":" << (result.checks_divisible ? "true" : "false")
        << ",\"complement_symmetric\":" << (result.checks_complement_symmetric ? "true" : "false")
        << ",\"total_matches_burnside_sum\":" << (result.checks_total_matches ? "true" : "false")
        << ",\"endpoints_unit\":" << (result.checks_endpoints_unit ? "true" : "false")
        << ",\"all_coefficients_positive\":" << (result.checks_positive ? "true" : "false")
        << "},";
    if (!result.induced_types.empty()) {
        out << "\"induced_cycle_types\":[";
        for (std::size_t index = 0; index < result.induced_types.size(); ++index) {
            const auto& record = result.induced_types[index];
            if (index != 0) {
                out << ',';
            }
            out << "{\"cycle_type\":\"" << record.cycle_type.to_compact_string() << '"'
                << ",\"cycles\":" << record.cycle_type.cycle_count()
                << ",\"classes\":" << record.classes
                << ",\"class_elements\":" << record.class_elements
                << '}';
        }
        out << "],";
    }
    out << "\"timings\":{\"class_generation_seconds\":" << result.class_generation_seconds
        << ",\"event_cycle_seconds\":" << result.event_cycle_seconds
        << ",\"polynomial_seconds\":" << result.polynomial_seconds
        << ",\"total_seconds\":" << result.total_seconds << "},"
        << "\"peak_rss_kib\":" << result.peak_rss_kib
        << "}\n";
    return out.str();
}

// ---------------------------------------------------------------------------
// Direct element cross-check (n <= 4)
// ---------------------------------------------------------------------------

WreathCrossCheckResult cross_check_wreath_against_elements(std::uint32_t n) {
    if (n == 0 || n > 4) {
        throw std::invalid_argument("element cross-check supports 1 <= n <= 4");
    }
    WreathCrossCheckResult result;
    result.square_count = n;

    std::map<std::string, std::uint64_t> expected_counts;
    std::map<std::string, std::string> expected_induced;
    for (const auto& wreath_type : enumerate_group_conjugacy_types(n)) {
        for (std::uint32_t container_index = 0; container_index < kD4ClassCount;
             ++container_index) {
            GroupConjugacyType full = wreath_type;
            full.container = static_cast<D4Class>(container_index);
            const std::string label = full.label();
            expected_counts[label] += group_class_size(full);
            expected_induced[label] = pack_cycle_type(
                event_cycle_type(representative_group_element(full))
            );
        }
    }

    std::map<std::string, std::uint64_t> seen_counts;
    std::map<std::string, std::string> seen_induced;
    const std::uint64_t total = group_element_count(n);
    for (std::uint64_t index = 0; index < total; ++index) {
        const GroupElement element = decode_group_element(n, index);
        const GroupConjugacyType type = wreath_type_of_element(element);
        const std::string label = type.label();
        ++seen_counts[label];
        const std::string induced = pack_cycle_type(event_cycle_type(element));
        const auto [position, inserted] = seen_induced.try_emplace(label, induced);
        if (!inserted && position->second != induced) {
            result.induced_types_match = false;
        }
    }

    result.elements = total;
    result.classes = expected_counts.size();
    result.classes_seen = seen_counts.size();
    result.counts_match = (seen_counts == expected_counts);
    for (const auto& [label, induced] : seen_induced) {
        const auto found = expected_induced.find(label);
        if (found == expected_induced.end() || found->second != induced) {
            result.induced_types_match = false;
        }
    }
    return result;
}

// ---------------------------------------------------------------------------
// Staged symmetry compression (small n)
// ---------------------------------------------------------------------------

StagedQuotientRow staged_quotient_counts(std::uint32_t n, std::uint32_t weight_max) {
    if (n == 0 || n > 6) {
        throw std::invalid_argument("staged quotient tables support 1 <= n <= 6");
    }
    if (weight_max == 0 || weight_max > event_count_for_squares(n)) {
        throw std::invalid_argument("staged quotient tables need a valid weight bound");
    }
    StagedQuotientRow row;
    row.square_count = n;
    row.weight_max = weight_max;
    bool ok = true;

    // Stage 1: local D4^n only. Classes are ordered tuples of D4 classes with
    // class size prod |c_i|; the representative applies each class
    // representative at its own square.
    {
        LowWeightAccumulator accumulator(weight_max);
        std::vector<D4Class> tuple(n, D4Class::Identity);
        const auto visit = [&](auto&& self, std::uint32_t position) -> void {
            if (position == n) {
                GroupElement element = identity_group_element(n);
                std::uint64_t class_size = 1;
                for (std::uint32_t square = 0; square < n; ++square) {
                    element.local[square] = d4_class_representative(tuple[square]);
                    class_size *= d4_class_size(tuple[square]);
                }
                accumulator.add(event_cycle_type(element), class_size);
                return;
            }
            for (std::uint32_t element_class = 0; element_class < kD4ClassCount;
                 ++element_class) {
                tuple[position] = static_cast<D4Class>(element_class);
                self(self, position + 1);
            }
        };
        visit(visit, 0);
        row.local_only = accumulator.divide_exact(small_power(8, n), ok);
    }

    // Stage 2: S_n x D4_container. Classes are (S_n cycle type, container
    // class); the representative fixes all local D4 labels.
    {
        LowWeightAccumulator accumulator(weight_max);
        // Recursive cycle-type enumeration: at cycle length `length`, either
        // stop adding cycles of this length (advance to length + 1) or add one
        // more cycle of the same length and recurse with the same length so
        // that every multiplicity is reached exactly once. cycles_of_length is
        // the number of cycles of this length already placed.
        const auto visit = [&](auto&& self, std::uint32_t remaining, std::uint32_t length,
                               GroupElement& element, std::uint64_t sigma_class_size,
                               std::uint32_t cycles_of_length) -> void {
            if (remaining == 0) {
                for (std::uint32_t container_index = 0;
                     container_index < kD4ClassCount;
                     ++container_index) {
                    const auto container_class = static_cast<D4Class>(container_index);
                    GroupElement full = element;
                    full.container = d4_class_representative(container_class);
                    accumulator.add(
                        event_cycle_type(full),
                        sigma_class_size * d4_class_size(container_class)
                    );
                }
                return;
            }
            if (length > remaining) {
                return;
            }
            // Multiplicity reached: move on to the next cycle length.
            self(self, remaining, length + 1, element, sigma_class_size, 0);
            // One more cycle of this length, placed at the first free square.
            SquareId next = 0;
            while (next < n && element.square_map[next] != next) {
                ++next;
            }
            for (std::uint32_t step = 0; step < length; ++step) {
                const SquareId square = static_cast<SquareId>(next + step);
                element.square_map[square] = static_cast<SquareId>(
                    step + 1 < length ? next + step + 1 : next
                );
            }
            // The number of sigma with this partial cycle type is
            // n!/(prod l^{m_l} m_l!); the incremental division by
            // length * m is exact (see the class-size formula).
            const std::uint32_t multiplicity = cycles_of_length + 1;
            self(
                self,
                remaining - length,
                length,
                element,
                sigma_class_size / (length * multiplicity),
                multiplicity
            );
            for (std::uint32_t step = 0; step < length; ++step) {
                const SquareId square = static_cast<SquareId>(next + step);
                element.square_map[square] = square;
            }
        };
        GroupElement element = identity_group_element(n);
        visit(visit, n, 1, element, factorial(n), 0);
        row.squares_only = accumulator.divide_exact(factorial(n) * 8, ok);
    }

    // Stage 3: D4 wr S_n (local D4 and square permutations, no container).
    {
        LowWeightAccumulator accumulator(weight_max);
        for (const auto& wreath_type : enumerate_group_conjugacy_types(n)) {
            accumulator.add(
                event_cycle_type(representative_group_element(wreath_type)),
                group_class_size(wreath_type)
            );
        }
        row.local_and_squares =
            accumulator.divide_exact(factorial(n) * small_power(8, n), ok);
    }

    // Stage 4: full G_n.
    {
        LowWeightAccumulator accumulator(weight_max);
        for (const auto& wreath_type : enumerate_group_conjugacy_types(n)) {
            const std::uint64_t wreath_size = group_class_size(wreath_type);
            for (std::uint32_t container_index = 0; container_index < kD4ClassCount;
                 ++container_index) {
                GroupConjugacyType full = wreath_type;
                full.container = static_cast<D4Class>(container_index);
                accumulator.add(
                    event_cycle_type(representative_group_element(full)),
                    wreath_size * d4_class_size(full.container)
                );
            }
        }
        row.full = accumulator.divide_exact(
            factorial(n) * small_power(8, n) * 8,
            ok
        );
    }

    if (!ok) {
        throw std::logic_error("staged quotient numerator was not divisible by the group order");
    }
    return row;
}

}  // namespace sqtopology
