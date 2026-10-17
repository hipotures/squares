#include "sqtopology/orbit.hpp"

#include <algorithm>
#include <bit>
#include <chrono>
#include <cmath>
#include <cstdint>
#include <deque>
#include <functional>
#include <iomanip>
#include <limits>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

#include <sys/resource.h>

namespace sqtopology {
namespace {

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

D4Element d4_from_digit(std::uint8_t digit) {
    return D4Element{
        .rotation = static_cast<std::uint8_t>(digit / 2),
        .reflected = (digit % 2) != 0,
    };
}

std::uint8_t d4_to_digit(const D4Element& element) {
    return static_cast<std::uint8_t>(2 * (element.rotation % 4) + (element.reflected ? 1 : 0));
}

// ---------------------------------------------------------------------------
// Minimal exact unsigned big integer, base 10^9 limbs, little-endian.
// Only the operations needed by exact Burnside counting are provided.
// ---------------------------------------------------------------------------

class BigUint {
  public:
    BigUint() = default;

    explicit BigUint(std::uint64_t value) {
        while (value > 0) {
            limbs_.push_back(static_cast<std::uint32_t>(value % kBase));
            value /= kBase;
        }
    }

    [[nodiscard]] bool is_zero() const noexcept { return limbs_.empty(); }

    [[nodiscard]] static BigUint power_of_two(unsigned exponent) {
        BigUint result(1);
        for (unsigned step = 0; step < exponent; ++step) {
            result.mul_small(2);
        }
        return result;
    }

    void add_into(const BigUint& other) {
        const std::size_t size = std::max(limbs_.size(), other.limbs_.size());
        limbs_.resize(size, 0);
        std::uint64_t carry = 0;
        for (std::size_t i = 0; i < size; ++i) {
            std::uint64_t sum = carry + limbs_[i];
            if (i < other.limbs_.size()) {
                sum += other.limbs_[i];
            }
            if (sum >= kBase) {
                limbs_[i] = static_cast<std::uint32_t>(sum - kBase);
                carry = 1;
            } else {
                limbs_[i] = static_cast<std::uint32_t>(sum);
                carry = 0;
            }
        }
        if (carry != 0) {
            limbs_.push_back(static_cast<std::uint32_t>(carry));
        }
    }

    void mul_small(std::uint64_t factor) {
        if (factor == 0) {
            limbs_.clear();
            return;
        }
        std::uint64_t carry = 0;
        for (auto& limb : limbs_) {
            const std::uint64_t product =
                static_cast<std::uint64_t>(limb) * factor + carry;
            limb = static_cast<std::uint32_t>(product % kBase);
            carry = product / kBase;
        }
        while (carry > 0) {
            limbs_.push_back(static_cast<std::uint32_t>(carry % kBase));
            carry /= kBase;
        }
    }

    // In-place exact division by a small positive divisor; returns the
    // remainder. The caller checks that the remainder is zero where the
    // mathematical value is known to be divisible.
    [[nodiscard]] std::uint64_t div_small(std::uint64_t divisor) {
        if (divisor == 0) {
            throw std::invalid_argument("big integer division by zero");
        }
        std::uint64_t remainder = 0;
        for (std::size_t i = limbs_.size(); i-- > 0;) {
            const std::uint64_t current =
                remainder * kBase + static_cast<std::uint64_t>(limbs_[i]);
            limbs_[i] = static_cast<std::uint32_t>(current / divisor);
            remainder = current % divisor;
        }
        trim();
        return remainder;
    }

    [[nodiscard]] std::string to_decimal() const {
        if (limbs_.empty()) {
            return "0";
        }
        std::ostringstream out;
        out << limbs_.back();
        for (std::size_t i = limbs_.size() - 1; i-- > 0;) {
            out << std::setw(9) << std::setfill('0') << limbs_[i];
        }
        return out.str();
    }

    [[nodiscard]] std::uint64_t to_uint64() const {
        std::uint64_t value = 0;
        for (std::size_t i = limbs_.size(); i-- > 0;) {
            value = value * kBase + limbs_[i];
        }
        return value;
    }

  private:
    static constexpr std::uint64_t kBase = 1000000000ULL;

    void trim() {
        while (!limbs_.empty() && limbs_.back() == 0) {
            limbs_.pop_back();
        }
    }

    std::vector<std::uint32_t> limbs_;
};

std::string pack_cycle_type(const EventCycleType& type) {
    std::string key;
    key.reserve(type.lengths.size() * 2);
    for (const auto length : type.lengths) {
        key.push_back(static_cast<char>(length & 0xFFU));
        key.push_back(static_cast<char>((length >> 8) & 0xFFU));
    }
    return key;
}

}  // namespace

// ---------------------------------------------------------------------------
// Event set layout
// ---------------------------------------------------------------------------

std::uint64_t event_count_for_squares(std::uint32_t n) noexcept {
    const std::uint64_t squares = n;
    const std::uint64_t pairs = squares * (squares - 1U) / 2U;
    return 64U * pairs + 32U * squares;
}

EventSetLayout EventSetLayout::for_square_count(std::uint32_t n) {
    if (n == 0 || n > kMaxOrbitSquares) {
        throw std::invalid_argument("event set requires 1 <= square_count <= kMaxOrbitSquares");
    }
    EventSetLayout layout;
    layout.square_count = n;
    layout.square_square_count = 64U * static_cast<std::uint64_t>(n) * (n - 1U) / 2U;
    layout.wall_count = 32U * static_cast<std::uint64_t>(n);
    layout.event_count = layout.square_square_count + layout.wall_count;
    return layout;
}

std::uint64_t EventSetLayout::pair_index(SquareId first, SquareId second) const {
    if (first >= second || second >= square_count) {
        throw std::invalid_argument("pair_index requires 0 <= first < second < square_count");
    }
    return static_cast<std::uint64_t>(first) * (2U * square_count - first - 1U) / 2U
        + (second - first - 1U);
}

std::pair<SquareId, SquareId> EventSetLayout::pair_squares(std::uint64_t index) const {
    const std::uint64_t pair_total =
        static_cast<std::uint64_t>(square_count) * (square_count - 1U) / 2U;
    if (index >= pair_total) {
        throw std::invalid_argument("pair_squares index outside the pair range");
    }
    for (SquareId first = 0; first < square_count; ++first) {
        const std::uint64_t remaining = square_count - first - 1U;
        if (index < remaining) {
            return {first, static_cast<SquareId>(first + 1U + index)};
        }
        index -= remaining;
    }
    throw std::logic_error("unreachable pair enumeration");
}

EventId EventSetLayout::square_square_event(
    SquareId first,
    SquareId second,
    std::uint8_t first_ring,
    std::uint8_t second_ring
) const {
    if (first_ring >= 8 || second_ring >= 8) {
        throw std::invalid_argument("ring index must be in 0..7");
    }
    return static_cast<EventId>(
        64U * pair_index(first, second) + 8U * first_ring + second_ring
    );
}

EventId EventSetLayout::wall_event(
    SquareId square,
    std::uint8_t ring,
    std::uint8_t wall
) const {
    if (square >= square_count || ring >= 8 || wall >= 4) {
        throw std::invalid_argument("wall event coordinates outside range");
    }
    return static_cast<EventId>(
        square_square_count + 32U * square + 4U * ring + wall
    );
}

EventRef EventSetLayout::describe(EventId id) const {
    if (id >= event_count) {
        throw std::invalid_argument("event id outside Omega_n");
    }
    EventRef ref;
    if (static_cast<std::uint64_t>(id) < square_square_count) {
        ref.kind = EventKind::SquareSquare;
        const std::uint64_t pair = static_cast<std::uint64_t>(id) / 64U;
        const std::uint64_t remainder = static_cast<std::uint64_t>(id) % 64U;
        const auto [first, second] = pair_squares(pair);
        ref.first_square = first;
        ref.second_square = second;
        ref.first_ring = static_cast<std::uint8_t>(remainder / 8U);
        ref.second_ring = static_cast<std::uint8_t>(remainder % 8U);
        return ref;
    }
    ref.kind = EventKind::Wall;
    const std::uint64_t offset = static_cast<std::uint64_t>(id) - square_square_count;
    ref.first_square = static_cast<SquareId>(offset / 32U);
    ref.second_square = ref.first_square;
    const std::uint64_t remainder = offset % 32U;
    ref.first_ring = static_cast<std::uint8_t>(remainder / 4U);
    ref.wall = static_cast<std::uint8_t>(remainder % 4U);
    return ref;
}

EventKind EventSetLayout::kind_of(EventId id) const {
    return describe(id).kind;
}

// ---------------------------------------------------------------------------
// D4
// ---------------------------------------------------------------------------

D4Element compose_d4(const D4Element& outer, const D4Element& inner) {
    const std::uint8_t outer_rotation = outer.rotation % 4;
    const std::uint8_t inner_rotation = inner.rotation % 4;
    const std::uint8_t rotation = static_cast<std::uint8_t>(
        (outer_rotation
         + (outer.reflected ? (4U - inner_rotation) % 4U : inner_rotation))
        % 4U
    );
    return D4Element{
        .rotation = rotation,
        .reflected = outer.reflected != inner.reflected,
    };
}

D4Element inverse_d4(const D4Element& element) {
    const std::uint8_t rotation = element.rotation % 4;
    const std::uint8_t inverse_rotation = element.reflected
        ? static_cast<std::uint8_t>((4U - rotation) % 4U)
        : rotation;
    return D4Element{
        .rotation = static_cast<std::uint8_t>((4U - inverse_rotation) % 4U),
        .reflected = element.reflected,
    };
}

std::uint8_t transform_ring(std::uint8_t ring, const D4Element& element) {
    if (ring >= 8 || element.rotation >= 4) {
        throw std::invalid_argument("ring/rotation index outside D4 domain");
    }
    int value = static_cast<int>(ring);
    if (element.reflected) {
        value = (8 - value) % 8;
    }
    value = (value + 2 * static_cast<int>(element.rotation)) % 8;
    return static_cast<std::uint8_t>(value);
}

std::uint8_t transform_wall(std::uint8_t wall, const D4Element& element) {
    if (wall >= 4 || element.rotation >= 4) {
        throw std::invalid_argument("wall/rotation index outside D4 domain");
    }
    int value = static_cast<int>(wall);
    if (element.reflected) {
        value = (4 - value) % 4;
    }
    value = (value + static_cast<int>(element.rotation)) % 4;
    return static_cast<std::uint8_t>(value);
}

std::string d4_conjugacy_class_name(const D4Element& element) {
    if (element.rotation >= 4) {
        throw std::invalid_argument("rotation index outside D4 domain");
    }
    if (!element.reflected) {
        if (element.rotation == 0) {
            return "identity";
        }
        if (element.rotation == 2) {
            return "rotation180";
        }
        return "rotation90";
    }
    // Reflections whose axis passes through two corners fix rings 0/4 or 2/6;
    // reflections whose axis passes through two sides fix rings 1/5 or 3/7.
    return (element.rotation % 2 == 0) ? "reflection_corner_axis"
                                       : "reflection_side_axis";
}

// ---------------------------------------------------------------------------
// Group elements
// ---------------------------------------------------------------------------

std::uint64_t group_element_count(std::uint32_t n) {
    if (n == 0 || n > kMaxOrbitSquares) {
        throw std::invalid_argument("group requires 1 <= square_count <= kMaxOrbitSquares");
    }
    std::uint64_t size = 8;  // container D4
    for (std::uint32_t square = 0; square < n; ++square) {
        size *= 8;  // local D4 per square
    }
    return size * factorial(n);
}

GroupElement identity_group_element(std::uint32_t n) {
    if (n == 0 || n > kMaxOrbitSquares) {
        throw std::invalid_argument("group requires 1 <= square_count <= kMaxOrbitSquares");
    }
    GroupElement element;
    element.square_count = n;
    for (SquareId square = 0; square < n; ++square) {
        element.square_map[square] = square;
    }
    return element;
}

GroupElement decode_group_element(std::uint32_t n, std::uint64_t index) {
    const std::uint64_t total = group_element_count(n);
    if (index >= total) {
        throw std::invalid_argument("group element index outside G_n");
    }
    GroupElement element;
    element.square_count = n;

    std::uint64_t remaining = index;
    element.container = d4_from_digit(static_cast<std::uint8_t>(remaining % 8U));
    remaining /= 8U;
    for (SquareId square = 0; square < n; ++square) {
        element.local[square] = d4_from_digit(static_cast<std::uint8_t>(remaining % 8U));
        remaining /= 8U;
    }

    // Factorial-number-system unranking: remaining is the Lehmer rank.
    std::array<SquareId, kMaxOrbitSquares> pool{};
    for (SquareId square = 0; square < n; ++square) {
        pool[square] = square;
    }
    std::uint32_t pool_size = n;
    for (SquareId position = 0; position < n; ++position) {
        const std::uint64_t block = factorial(n - position - 1U);
        const std::uint64_t digit = remaining / block;
        remaining %= block;
        element.square_map[position] = pool[digit];
        for (std::uint32_t move = static_cast<std::uint32_t>(digit);
             move + 1U < pool_size;
             ++move) {
            pool[move] = pool[move + 1U];
        }
        --pool_size;
    }
    return element;
}

std::uint64_t encode_group_element(const GroupElement& element) {
    const std::uint32_t n = element.square_count;
    if (n == 0 || n > kMaxOrbitSquares) {
        throw std::invalid_argument("group element has unsupported square count");
    }

    std::array<bool, kMaxOrbitSquares> used{};
    for (SquareId square = 0; square < n; ++square) {
        if (element.square_map[square] >= n || used[element.square_map[square]]) {
            throw std::invalid_argument("group element is not a square permutation");
        }
        used[element.square_map[square]] = true;
    }

    std::uint64_t rank = 0;
    std::array<SquareId, kMaxOrbitSquares> pool{};
    for (SquareId square = 0; square < n; ++square) {
        pool[square] = square;
    }
    std::uint32_t pool_size = n;
    for (SquareId position = 0; position < n; ++position) {
        std::uint64_t digit = 0;
        while (pool[digit] != element.square_map[position]) {
            ++digit;
        }
        rank += digit * factorial(n - position - 1U);
        for (std::uint32_t move = static_cast<std::uint32_t>(digit);
             move + 1U < pool_size;
             ++move) {
            pool[move] = pool[move + 1U];
        }
        --pool_size;
    }

    std::uint64_t encoded = rank;
    for (std::uint32_t step = n; step-- > 0;) {
        encoded = encoded * 8U + d4_to_digit(element.local[step]);
    }
    encoded = encoded * 8U + d4_to_digit(element.container);
    return encoded;
}

GroupElement compose_group_elements(
    const GroupElement& outer,
    const GroupElement& inner
) {
    if (outer.square_count != inner.square_count) {
        throw std::invalid_argument("cannot compose group elements of different square counts");
    }
    GroupElement result;
    result.square_count = outer.square_count;
    for (SquareId square = 0; square < outer.square_count; ++square) {
        result.square_map[square] = outer.square_map[inner.square_map[square]];
        result.local[square] = compose_d4(
            outer.local[inner.square_map[square]],
            inner.local[square]
        );
    }
    result.container = compose_d4(outer.container, inner.container);
    return result;
}

GroupElement inverse_group_element(const GroupElement& element) {
    GroupElement result;
    result.square_count = element.square_count;
    for (SquareId square = 0; square < element.square_count; ++square) {
        const SquareId image = element.square_map[square];
        result.square_map[image] = square;
        result.local[image] = inverse_d4(element.local[square]);
    }
    result.container = inverse_d4(element.container);
    return result;
}

GroupElement conjugate_group_element(
    const GroupElement& element,
    const GroupElement& conjugator
) {
    return compose_group_elements(
        compose_group_elements(conjugator, element),
        inverse_group_element(conjugator)
    );
}

bool is_permutation(const GroupElement& element) {
    const std::uint32_t n = element.square_count;
    if (n == 0 || n > kMaxOrbitSquares) {
        return false;
    }
    std::array<bool, kMaxOrbitSquares> used{};
    for (SquareId square = 0; square < n; ++square) {
        const SquareId image = element.square_map[square];
        if (image >= n || used[image]) {
            return false;
        }
        used[image] = true;
        if (element.local[square].rotation >= 4 || element.container.rotation >= 4) {
            return false;
        }
    }
    return true;
}

// ---------------------------------------------------------------------------
// Action on Omega_n
// ---------------------------------------------------------------------------

EventId apply_group_element_to_event(const GroupElement& element, EventId id) {
    const EventSetLayout layout = EventSetLayout::for_square_count(element.square_count);
    const EventRef ref = layout.describe(id);
    if (ref.kind == EventKind::Wall) {
        const SquareId square = element.square_map[ref.first_square];
        const std::uint8_t ring =
            transform_ring(ref.first_ring, element.local[ref.first_square]);
        const std::uint8_t wall = transform_wall(ref.wall, element.container);
        return layout.wall_event(square, ring, wall);
    }
    const SquareId first = element.square_map[ref.first_square];
    const SquareId second = element.square_map[ref.second_square];
    const std::uint8_t first_ring =
        transform_ring(ref.first_ring, element.local[ref.first_square]);
    const std::uint8_t second_ring =
        transform_ring(ref.second_ring, element.local[ref.second_square]);
    if (first < second) {
        return layout.square_square_event(first, second, first_ring, second_ring);
    }
    return layout.square_square_event(second, first, second_ring, first_ring);
}

std::vector<EventId> event_permutation(const GroupElement& element) {
    const EventSetLayout layout = EventSetLayout::for_square_count(element.square_count);
    std::vector<EventId> permutation(static_cast<std::size_t>(layout.event_count), 0);
    for (EventId id = 0; id < layout.event_count; ++id) {
        permutation[id] = apply_group_element_to_event(element, id);
    }
    return permutation;
}

namespace {

// Per-element action tables used by the bitset permutation and by the distance
// scan. The square-permutation tables only change when the square permutation
// changes; the transform tables change for every element.
struct ElementAction {
    EventSetLayout layout{};
    std::vector<std::uint64_t> pair_target;
    std::vector<std::uint8_t> pair_swap;
    std::vector<std::uint64_t> wall_base;
    std::vector<std::array<std::uint8_t, 8>> ring_to;
    std::array<std::uint8_t, 4> container_to{};

    void initialize(std::uint32_t square_count) {
        layout = EventSetLayout::for_square_count(square_count);
        const std::uint64_t pair_count = layout.square_square_count / 64U;
        pair_target.assign(static_cast<std::size_t>(pair_count), 0);
        pair_swap.assign(static_cast<std::size_t>(pair_count), 0);
        wall_base.assign(square_count, 0);
        ring_to.assign(square_count, {});
    }

    void set_square_map(const GroupElement& element) {
        const std::uint64_t pair_count = layout.square_square_count / 64U;
        for (std::uint64_t pair = 0; pair < pair_count; ++pair) {
            const auto [first, second] = layout.pair_squares(pair);
            const SquareId target_first = element.square_map[first];
            const SquareId target_second = element.square_map[second];
            if (target_first < target_second) {
                pair_target[pair] = layout.pair_index(target_first, target_second);
                pair_swap[pair] = 0;
            } else {
                pair_target[pair] = layout.pair_index(target_second, target_first);
                pair_swap[pair] = 1;
            }
        }
        for (SquareId square = 0; square < element.square_count; ++square) {
            wall_base[square] =
                layout.square_square_count + 32U * element.square_map[square];
        }
    }

    void set_transforms(const GroupElement& element) {
        for (SquareId square = 0; square < element.square_count; ++square) {
            for (std::uint8_t ring = 0; ring < 8; ++ring) {
                ring_to[square][ring] = transform_ring(ring, element.local[square]);
            }
        }
        for (std::uint8_t wall = 0; wall < 4; ++wall) {
            container_to[wall] = transform_wall(wall, element.container);
        }
    }

    void set_all(const GroupElement& element) {
        set_square_map(element);
        set_transforms(element);
    }

    [[nodiscard]] EventId map_event(EventId id) const {
        if (static_cast<std::uint64_t>(id) < layout.square_square_count) {
            const std::uint64_t pair = static_cast<std::uint64_t>(id) / 64U;
            const std::uint64_t remainder = static_cast<std::uint64_t>(id) % 64U;
            const std::uint8_t first_ring = static_cast<std::uint8_t>(remainder / 8U);
            const std::uint8_t second_ring = static_cast<std::uint8_t>(remainder % 8U);
            const auto [first, second] = layout.pair_squares(pair);
            EventId result = static_cast<EventId>(64U * pair_target[pair]);
            if (pair_swap[pair] == 0) {
                result = static_cast<EventId>(
                    result + 8U * ring_to[first][first_ring] + ring_to[second][second_ring]
                );
            } else {
                result = static_cast<EventId>(
                    result + 8U * ring_to[second][second_ring] + ring_to[first][first_ring]
                );
            }
            return result;
        }
        const std::uint64_t offset =
            static_cast<std::uint64_t>(id) - layout.square_square_count;
        const SquareId square = static_cast<SquareId>(offset / 32U);
        const std::uint64_t remainder = offset % 32U;
        const std::uint8_t ring = static_cast<std::uint8_t>(remainder / 4U);
        const std::uint8_t wall = static_cast<std::uint8_t>(remainder % 4U);
        return static_cast<EventId>(
            wall_base[square] + 4U * ring_to[square][ring] + container_to[wall]
        );
    }
};

void permute_bitset_with_element(
    const ElementAction& action,
    const EventBitset& source,
    EventBitset& destination
) {
    std::fill(destination.begin(), destination.end(), 0);
    for (std::size_t word = 0; word < source.size(); ++word) {
        std::uint64_t bits = source[word];
        while (bits != 0) {
            const unsigned bit = std::countr_zero(bits);
            bits &= bits - 1U;
            const EventId id = static_cast<EventId>(word * 64U + bit);
            const EventId target = action.map_event(id);
            destination[target / 64U] |= std::uint64_t{1} << (target % 64U);
        }
    }
}

}  // namespace

// ---------------------------------------------------------------------------
// Event subsets
// ---------------------------------------------------------------------------

EventBitset topology_to_event_bitset(const Topology& input) {
    const auto validation = input.validate();
    if (!validation.ok()) {
        throw std::invalid_argument("cannot encode an invalid topology as an event subset");
    }
    const Topology topology = input.normalized();
    const EventSetLayout layout = EventSetLayout::for_square_count(topology.square_count());
    EventBitset bitset(static_cast<std::size_t>((layout.event_count + 63U) / 64U), 0);
    std::uint64_t encoded = 0;
    for (const auto& contact : topology.contacts()) {
        EventId id = 0;
        if (contact.kind == ContactKind::Wall) {
            id = layout.wall_event(
                contact.a.square,
                feature_ring_index(contact.a),
                *contact.wall
            );
        } else {
            id = layout.square_square_event(
                contact.a.square,
                contact.b->square,
                feature_ring_index(contact.a),
                feature_ring_index(*contact.b)
            );
        }
        if ((bitset[id / 64U] & (std::uint64_t{1} << (id % 64U))) != 0) {
            throw std::logic_error("duplicate semantic contact in normalized topology");
        }
        bitset[id / 64U] |= std::uint64_t{1} << (id % 64U);
        ++encoded;
    }
    if (encoded != topology.contacts().size()) {
        throw std::logic_error("event encoding lost a contact");
    }
    return bitset;
}

Topology event_bitset_to_topology(std::uint32_t square_count, const EventBitset& bitset) {
    const EventSetLayout layout = EventSetLayout::for_square_count(square_count);
    if (bitset.size() != static_cast<std::size_t>((layout.event_count + 63U) / 64U)) {
        throw std::invalid_argument("event bitset has the wrong size for this square count");
    }
    Topology topology(square_count);
    for (EventId id = 0; id < layout.event_count; ++id) {
        if ((bitset[id / 64U] & (std::uint64_t{1} << (id % 64U))) == 0) {
            continue;
        }
        const EventRef ref = layout.describe(id);
        if (ref.kind == EventKind::Wall) {
            topology.add_contact(
                make_wall_contact(feature_from_ring_index(ref.first_square, ref.first_ring), ref.wall)
            );
        } else {
            topology.add_contact(
                make_square_contact(
                    feature_from_ring_index(ref.first_square, ref.first_ring),
                    feature_from_ring_index(ref.second_square, ref.second_ring)
                )
            );
        }
    }
    return topology.normalized();
}

std::uint64_t event_bitset_popcount(const EventBitset& bitset) {
    std::uint64_t total = 0;
    for (const auto word : bitset) {
        total += std::popcount(word);
    }
    return total;
}

std::uint64_t event_bitset_symmetric_difference_size(
    const EventBitset& first,
    const EventBitset& second
) {
    if (first.size() != second.size()) {
        throw std::invalid_argument("event bitsets have different sizes");
    }
    std::uint64_t total = 0;
    for (std::size_t word = 0; word < first.size(); ++word) {
        total += std::popcount(first[word] ^ second[word]);
    }
    return total;
}

EventBitset permute_event_bitset(
    const std::vector<EventId>& permutation,
    const EventBitset& bitset
) {
    EventBitset result(bitset.size(), 0);
    for (EventId id = 0; id < permutation.size(); ++id) {
        if ((bitset[id / 64U] & (std::uint64_t{1} << (id % 64U))) == 0) {
            continue;
        }
        const EventId target = permutation[id];
        result[target / 64U] |= std::uint64_t{1} << (target % 64U);
    }
    return result;
}

Topology apply_group_element_to_topology(
    const Topology& input,
    const GroupElement& element
) {
    if (input.square_count() != element.square_count) {
        throw std::invalid_argument("group element square count does not match topology");
    }
    const auto validation = input.validate();
    if (!validation.ok()) {
        throw std::invalid_argument("cannot transform an invalid topology");
    }
    Topology result = input.normalized();
    for (SquareId square = 0; square < element.square_count; ++square) {
        result = relabel_square(
            result,
            square,
            D4Transform{
                .rotation = element.local[square].rotation,
                .reflected = element.local[square].reflected,
            }
        );
    }
    result = relabel_container(
        result,
        D4Transform{
            .rotation = element.container.rotation,
            .reflected = element.container.reflected,
        }
    );
    result = permute_squares(result, std::vector<SquareId>(
        element.square_map.begin(),
        element.square_map.begin() + element.square_count
    ));
    return result.normalized();
}

// ---------------------------------------------------------------------------
// Orbit-Hamming distance
// ---------------------------------------------------------------------------

OrbitDistanceResult orbit_hamming_distance(
    const Topology& first,
    const Topology& second
) {
    if (first.square_count() != second.square_count()) {
        throw std::invalid_argument("orbit distance requires equal square counts");
    }
    const std::uint32_t n = first.square_count();
    const Topology normalized_first = first.normalized();
    const Topology normalized_second = second.normalized();

    const EventBitset first_bits = topology_to_event_bitset(normalized_first);
    const EventBitset second_bits = topology_to_event_bitset(normalized_second);

    OrbitDistanceResult result;
    result.first_weight = event_bitset_popcount(first_bits);
    result.second_weight = event_bitset_popcount(second_bits);

    const std::uint64_t group_size = group_element_count(n);
    EventBitset scratch(first_bits.size(), 0);
    ElementAction action;
    action.initialize(n);
    // decode_group_element orders the square permutation as the slowest index:
    // the permutation changes exactly once per 8^(n+1) consecutive elements.
    std::uint64_t sigma_period = 1;
    for (std::uint32_t step = 0; step <= n; ++step) {
        sigma_period *= 8U;
    }
    std::uint64_t best = std::numeric_limits<std::uint64_t>::max();
    GroupElement best_element = identity_group_element(n);
    for (std::uint64_t index = 0; index < group_size; ++index) {
        const GroupElement element = decode_group_element(n, index);
        if (index % sigma_period == 0) {
            action.set_square_map(element);
        }
        action.set_transforms(element);
        permute_bitset_with_element(action, second_bits, scratch);
        std::uint64_t partial = 0;
        for (std::size_t word = 0; word < first_bits.size(); ++word) {
            partial += std::popcount(first_bits[word] ^ scratch[word]);
            if (partial > best) {
                break;
            }
        }
        if (partial < best) {
            best = partial;
            best_element = element;
        }
    }

    result.distance = best;
    result.witness = best_element;

    // Independent recheck through the production transformation functions.
    const Topology transformed = apply_group_element_to_topology(
        normalized_second,
        best_element
    );
    std::vector<std::string> first_keys;
    std::vector<std::string> transformed_keys;
    first_keys.reserve(normalized_first.contacts().size());
    transformed_keys.reserve(transformed.contacts().size());
    for (const auto& contact : normalized_first.contacts()) {
        first_keys.push_back(contact_key(contact));
    }
    for (const auto& contact : transformed.contacts()) {
        transformed_keys.push_back(contact_key(contact));
    }
    std::sort(first_keys.begin(), first_keys.end());
    std::sort(transformed_keys.begin(), transformed_keys.end());
    std::vector<std::string> difference;
    std::set_symmetric_difference(
        first_keys.begin(),
        first_keys.end(),
        transformed_keys.begin(),
        transformed_keys.end(),
        std::back_inserter(difference)
    );
    result.witness_symmetric_difference = difference.size();
    if (result.witness_symmetric_difference != result.distance) {
        throw std::logic_error(
            "distance witness disagrees with the production transformation path"
        );
    }
    return result;
}

// ---------------------------------------------------------------------------
// Cycle decomposition
// ---------------------------------------------------------------------------

std::string EventCycleType::to_compact_string() const {
    std::ostringstream out;
    std::uint32_t index = 0;
    while (index < lengths.size()) {
        std::uint32_t run = 1;
        while (index + run < lengths.size() && lengths[index + run] == lengths[index]) {
            ++run;
        }
        if (run > 1) {
            out << lengths[index] << '^' << run;
        } else {
            out << lengths[index];
        }
        if (index + run < lengths.size()) {
            out << ' ';
        }
        index += run;
    }
    return out.str();
}

EventCycleType event_cycle_type(const GroupElement& element) {
    const std::vector<EventId> permutation = event_permutation(element);
    EventCycleType type;
    std::vector<std::uint8_t> visited(permutation.size(), 0);
    for (EventId start = 0; start < permutation.size(); ++start) {
        if (visited[start] != 0) {
            continue;
        }
        std::uint32_t length = 0;
        EventId current = start;
        do {
            visited[current] = 1;
            current = permutation[current];
            ++length;
        } while (current != start);
        type.lengths.push_back(static_cast<std::uint16_t>(length));
    }
    std::sort(type.lengths.begin(), type.lengths.end());
    return type;
}

// ---------------------------------------------------------------------------
// Exact Burnside/Pólya orbit counting
// ---------------------------------------------------------------------------

namespace {

struct TypeAccumulator {
    EventCycleType type;
    std::uint64_t group_elements{0};
    std::map<std::pair<std::string, std::string>, std::uint64_t> d4_pairs;
};

}  // namespace

OrbitCountResult burnside_orbit_count(
    std::uint32_t square_count,
    const OrbitCountOptions& options
) {
    const auto started = Clock::now();
    const EventSetLayout layout = EventSetLayout::for_square_count(square_count);
    const std::uint64_t event_count = layout.event_count;
    const std::uint64_t group_size = group_element_count(square_count);

    OrbitCountResult result;
    result.square_count = square_count;
    result.event_count = event_count;
    result.square_square_events = layout.square_square_count;
    result.wall_events = layout.wall_count;
    result.group_size = group_size;

    // --- Induced event cycle types, aggregated over identical types. ---------
    const auto enumeration_started = Clock::now();
    std::unordered_map<std::string, std::size_t> type_index;
    std::vector<TypeAccumulator> accumulators;
    for (std::uint64_t index = 0; index < group_size; ++index) {
        const GroupElement element = decode_group_element(square_count, index);
        const EventCycleType type = event_cycle_type(element);
        const std::string key = pack_cycle_type(type);
        const auto [position, inserted] =
            type_index.emplace(key, accumulators.size());
        if (inserted) {
            TypeAccumulator accumulator;
            accumulator.type = type;
            accumulators.push_back(std::move(accumulator));
        }
        TypeAccumulator& accumulator = accumulators[position->second];
        ++accumulator.group_elements;
        if (square_count == 1) {
            ++accumulator.d4_pairs[
                {d4_conjugacy_class_name(element.local[0]),
                 d4_conjugacy_class_name(element.container)}
            ];
        }
    }
    result.enumeration_seconds = seconds_between(enumeration_started, Clock::now());
    result.distinct_cycle_types = accumulators.size();

    std::sort(
        accumulators.begin(),
        accumulators.end(),
        [](const TypeAccumulator& lhs, const TypeAccumulator& rhs) {
            if (lhs.type.cycle_count() != rhs.type.cycle_count()) {
                return lhs.type.cycle_count() < rhs.type.cycle_count();
            }
            return lhs.type.lengths < rhs.type.lengths;
        }
    );

    // --- Exact orbit polynomial. --------------------------------------------
    // For a group element whose action on Omega_n has cycles C,
    //   [x^d] product_C (1 + x^|C|)
    // counts the d-event subsets fixed by the element. Summing over all group
    // elements and dividing by |G_n| is Burnside's lemma.
    const auto polynomial_started = Clock::now();
    std::vector<BigUint> coefficient_sums(static_cast<std::size_t>(event_count + 1U));
    BigUint total_from_cycle_counts(0);
    std::vector<BigUint> polynomial(static_cast<std::size_t>(event_count + 1U));
    for (TypeAccumulator& accumulator : accumulators) {
        for (auto& coefficient : polynomial) {
            coefficient = BigUint();
        }
        polynomial[0] = BigUint(1);
        std::uint32_t degree = 0;
        for (const auto length : accumulator.type.lengths) {
            const std::uint32_t step = length;
            degree += step;
            // Multiply the current polynomial by (1 + x^step) in place. The
            // descending loop reads the old P[d-step] before it is overwritten.
            for (std::uint32_t index = degree; index >= step; --index) {
                polynomial[index].add_into(polynomial[index - step]);
            }
        }
        if (degree != event_count) {
            throw std::logic_error("event cycle lengths do not sum to |Omega_n|");
        }
        for (std::uint32_t index = 0; index <= degree; ++index) {
            polynomial[index].mul_small(accumulator.group_elements);
            coefficient_sums[index].add_into(polynomial[index]);
        }
        BigUint element_count = BigUint::power_of_two(accumulator.type.cycle_count());
        element_count.mul_small(accumulator.group_elements);
        total_from_cycle_counts.add_into(element_count);

        CycleTypeRecord record;
        record.cycle_type = accumulator.type;
        record.group_elements = accumulator.group_elements;
        if (options.emit_contributions) {
            record.contribution_decimal.reserve(degree + 1U);
            for (std::uint32_t index = 0; index <= degree; ++index) {
                record.contribution_decimal.push_back(polynomial[index].to_decimal());
            }
        }
        if (square_count == 1) {
            for (const auto& [classes, count] : accumulator.d4_pairs) {
                record.d4_class_pairs.push_back(
                    D4ClassPairCount{
                        .ring_class = classes.first,
                        .wall_class = classes.second,
                        .group_elements = count,
                    }
                );
            }
        }
        result.cycle_types.push_back(std::move(record));
    }
    result.polynomial_seconds = seconds_between(polynomial_started, Clock::now());

    // --- Exact division by |G| and internal checks. -------------------------
    // Accumulate the un-divided numerator total first, so the second total path
    // really is independent of the per-coefficient division below.
    BigUint coefficient_numerator_total(0);
    for (std::uint32_t index = 0; index <= event_count; ++index) {
        coefficient_numerator_total.add_into(coefficient_sums[index]);
    }
    const std::uint64_t divided_remainder = coefficient_numerator_total.div_small(group_size);
    if (divided_remainder != 0) {
        result.checks_divisible = false;
    }
    result.total_orbit_count_decimal = coefficient_numerator_total.to_decimal();

    result.coefficient_sum_decimal.reserve(coefficient_sums.size());
    result.coefficient_decimal.reserve(coefficient_sums.size());
    for (std::uint32_t index = 0; index <= event_count; ++index) {
        result.coefficient_sum_decimal.push_back(coefficient_sums[index].to_decimal());
        const std::uint64_t remainder = coefficient_sums[index].div_small(group_size);
        if (remainder != 0) {
            result.checks_divisible = false;
        }
        result.coefficient_decimal.push_back(coefficient_sums[index].to_decimal());
    }

    const std::uint64_t total_remainder = total_from_cycle_counts.div_small(group_size);
    if (total_remainder != 0) {
        result.checks_divisible = false;
    }
    result.total_from_cycle_counts_decimal = total_from_cycle_counts.to_decimal();
    if (result.total_orbit_count_decimal != result.total_from_cycle_counts_decimal) {
        result.checks_total_matches = false;
    }

    for (std::uint32_t index = 0; index <= event_count; ++index) {
        if (result.coefficient_decimal[index]
            != result.coefficient_decimal[event_count - index]) {
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

    if (options.count_conjugacy_classes) {
        result.conjugacy_classes = group_conjugacy_class_count(square_count);
    }

    rusage usage{};
    if (getrusage(RUSAGE_SELF, &usage) == 0) {
        result.peak_rss_kib = static_cast<std::uint64_t>(usage.ru_maxrss);
    }
    result.total_seconds = seconds_between(started, Clock::now());
    return result;
}

std::string orbit_count_to_json(const OrbitCountResult& result) {
    std::ostringstream out;
    out << std::setprecision(17);
    out << '{'
        << "\"schema\":\"sqtopology.orbit-count.v1\","
        << "\"n\":" << result.square_count << ','
        << "\"event_count\":" << result.event_count << ','
        << "\"event_breakdown\":{\"square_square\":" << result.square_square_events
        << ",\"wall\":" << result.wall_events << "},"
        << "\"group_size\":" << result.group_size << ','
        << "\"group_order_formula\":\"n! * 8^n * 8\","
        << "\"distinct_cycle_types\":" << result.distinct_cycle_types << ','
        << "\"conjugacy_classes\":" << result.conjugacy_classes << ','
        << "\"cycle_types\":[";
    for (std::size_t index = 0; index < result.cycle_types.size(); ++index) {
        const auto& record = result.cycle_types[index];
        if (index != 0) {
            out << ',';
        }
        out << "{\"cycle_type\":\"" << record.cycle_type.to_compact_string() << "\""
            << ",\"cycles\":" << record.cycle_type.cycle_count()
            << ",\"group_elements\":" << record.group_elements;
        if (!record.d4_class_pairs.empty()) {
            out << ",\"d4_class_pairs\":[";
            for (std::size_t pair = 0; pair < record.d4_class_pairs.size(); ++pair) {
                if (pair != 0) {
                    out << ',';
                }
                out << "{\"ring\":\"" << record.d4_class_pairs[pair].ring_class
                    << "\",\"wall\":\"" << record.d4_class_pairs[pair].wall_class
                    << "\",\"elements\":" << record.d4_class_pairs[pair].group_elements
                    << '}';
            }
            out << ']';
        }
        if (!record.contribution_decimal.empty()) {
            out << ",\"contribution\":[";
            for (std::size_t degree = 0; degree < record.contribution_decimal.size(); ++degree) {
                if (degree != 0) {
                    out << ',';
                }
                out << '"' << record.contribution_decimal[degree] << '"';
            }
            out << ']';
        }
        out << '}';
    }
    out << "],\"coefficient_sums\":[";
    for (std::size_t index = 0; index < result.coefficient_sum_decimal.size(); ++index) {
        if (index != 0) {
            out << ',';
        }
        out << '"' << result.coefficient_sum_decimal[index] << '"';
    }
    out << "],\"coefficients\":[";
    for (std::size_t index = 0; index < result.coefficient_decimal.size(); ++index) {
        if (index != 0) {
            out << ',';
        }
        out << '"' << result.coefficient_decimal[index] << '"';
    }
    out << "],\"total_orbit_count\":\"" << result.total_orbit_count_decimal << '"'
        << ",\"total_from_cycle_counts\":\"" << result.total_from_cycle_counts_decimal << '"'
        << ",\"checks\":{"
        << "\"all_coefficients_divisible\":" << (result.checks_divisible ? "true" : "false")
        << ",\"complement_symmetric\":" << (result.checks_complement_symmetric ? "true" : "false")
        << ",\"total_matches_burnside_sum\":" << (result.checks_total_matches ? "true" : "false")
        << ",\"endpoints_unit\":" << (result.checks_endpoints_unit ? "true" : "false")
        << ",\"all_coefficients_positive\":" << (result.checks_positive ? "true" : "false")
        << "},"
        << "\"timings\":{\"group_enumeration_seconds\":" << result.enumeration_seconds
        << ",\"polynomial_seconds\":" << result.polynomial_seconds
        << ",\"total_seconds\":" << result.total_seconds << "},"
        << "\"peak_rss_kib\":" << result.peak_rss_kib
        << "}\n";
    return out.str();
}

// ---------------------------------------------------------------------------
// Conjugacy classes of G_n
// ---------------------------------------------------------------------------

std::uint64_t group_conjugacy_class_count(std::uint32_t n) {
    const std::uint64_t group_size = group_element_count(n);
    std::vector<GroupElement> generators;
    if (n >= 2) {
        GroupElement transposition = identity_group_element(n);
        transposition.square_map[0] = 1;
        transposition.square_map[1] = 0;
        generators.push_back(transposition);

        GroupElement cycle = identity_group_element(n);
        for (SquareId square = 0; square < n; ++square) {
            cycle.square_map[square] = (square + 1U) % n;
        }
        generators.push_back(cycle);
    }
    {
        GroupElement local_rotation = identity_group_element(n);
        local_rotation.local[0] = D4Element{.rotation = 1, .reflected = false};
        generators.push_back(local_rotation);

        GroupElement local_reflection = identity_group_element(n);
        local_reflection.local[0] = D4Element{.rotation = 0, .reflected = true};
        generators.push_back(local_reflection);

        GroupElement container_rotation = identity_group_element(n);
        container_rotation.container = D4Element{.rotation = 1, .reflected = false};
        generators.push_back(container_rotation);

        GroupElement container_reflection = identity_group_element(n);
        container_reflection.container = D4Element{.rotation = 0, .reflected = true};
        generators.push_back(container_reflection);
    }
    std::vector<GroupElement> inverses;
    inverses.reserve(generators.size());
    for (const auto& generator : generators) {
        inverses.push_back(inverse_group_element(generator));
    }

    // The conjugation BFS below visits exactly one conjugacy class per start
    // element only if these generators generate all of G_n. Verify that
    // independently before counting, so an insufficient generating set would
    // fail loudly instead of over-counting classes.
    {
        std::vector<std::uint8_t> reachable(static_cast<std::size_t>(group_size), 0);
        std::vector<std::uint64_t> stack;
        const std::uint64_t identity_index = encode_group_element(identity_group_element(n));
        reachable[identity_index] = 1;
        stack.push_back(identity_index);
        std::uint64_t reached = 1;
        while (!stack.empty()) {
            const std::uint64_t current = stack.back();
            stack.pop_back();
            const GroupElement element = decode_group_element(n, current);
            for (const auto& generator : generators) {
                const std::uint64_t next =
                    encode_group_element(compose_group_elements(generator, element));
                if (reachable[next] == 0) {
                    reachable[next] = 1;
                    ++reached;
                    stack.push_back(next);
                }
            }
        }
        if (reached != group_size) {
            throw std::logic_error("conjugacy generators do not generate G_n");
        }
    }

    std::vector<std::uint8_t> visited(static_cast<std::size_t>(group_size), 0);
    std::vector<std::uint64_t> queue;
    std::uint64_t classes = 0;
    for (std::uint64_t start = 0; start < group_size; ++start) {
        if (visited[start] != 0) {
            continue;
        }
        ++classes;
        visited[start] = 1;
        queue.clear();
        queue.push_back(start);
        while (!queue.empty()) {
            const std::uint64_t current = queue.back();
            queue.pop_back();
            const GroupElement element = decode_group_element(n, current);
            for (std::size_t index = 0; index < generators.size(); ++index) {
                const GroupElement conjugated = compose_group_elements(
                    compose_group_elements(generators[index], element),
                    inverses[index]
                );
                const std::uint64_t encoded = encode_group_element(conjugated);
                if (visited[encoded] == 0) {
                    visited[encoded] = 1;
                    queue.push_back(encoded);
                }
            }
        }
    }
    return classes;
}

}  // namespace sqtopology
