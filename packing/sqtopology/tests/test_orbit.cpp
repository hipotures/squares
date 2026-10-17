// Tests for the independent event-set / group-action oracle in orbit.hpp.
//
// These tests pin down the mathematical model (Omega_n, G_n, Q_E / G_n) with
// exact reference values, structural identities, and agreement with the
// production symmetry transforms. The oracle itself never derives its action
// from canonicalization; canonicalization appears here only as a cross-check.

#include "sqtopology/canonical.hpp"
#include "sqtopology/fixtures.hpp"
#include "sqtopology/orbit.hpp"
#include "sqtopology/research.hpp"
#include "sqtopology/topology.hpp"

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <map>
#include <random>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

using namespace sqtopology;

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

// ---------------------------------------------------------------------------
// Small helpers: reference-file reading, decimal string arithmetic, and
// minimal parsers for the tool's exact JSON output.
// ---------------------------------------------------------------------------

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
        throw std::runtime_error("missing integer field: " + name);
    }
    std::size_t index = position + key.size();
    std::uint64_t value = 0;
    bool any = false;
    while (index < json.size() && json[index] >= '0' && json[index] <= '9') {
        value = value * 10 + static_cast<std::uint64_t>(json[index] - '0');
        ++index;
        any = true;
    }
    if (!any) {
        throw std::runtime_error("malformed integer field: " + name);
    }
    return value;
}

std::string extract_string(const std::string& json, const std::string& name) {
    const std::string key = "\"" + name + "\":\"";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing string field: " + name);
    }
    const auto start = position + key.size();
    const auto end = json.find('"', start);
    if (end == std::string::npos) {
        throw std::runtime_error("unterminated string field: " + name);
    }
    return json.substr(start, end - start);
}

std::vector<std::string> extract_string_array(const std::string& json, const std::string& name) {
    const std::string key = "\"" + name + "\":[";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing string array field: " + name);
    }
    std::vector<std::string> values;
    std::size_t index = position + key.size();
    while (index < json.size()) {
        if (json[index] == ']') {
            break;
        }
        if (json[index] == '"') {
            const auto end = json.find('"', index + 1);
            if (end == std::string::npos) {
                throw std::runtime_error("unterminated string array: " + name);
            }
            values.push_back(json.substr(index + 1, end - index - 1));
            index = end + 1;
            continue;
        }
        ++index;
    }
    return values;
}

std::vector<std::uint64_t> extract_uint_array(const std::string& json, const std::string& name) {
    const std::string key = "\"" + name + "\":[";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing uint array field: " + name);
    }
    std::vector<std::uint64_t> values;
    std::size_t index = position + key.size();
    while (index < json.size()) {
        if (json[index] == ']') {
            break;
        }
        if (json[index] == ',') {
            ++index;
            continue;
        }
        expect(json[index] >= '0' && json[index] <= '9', "uint array digit");
        std::uint64_t value = 0;
        while (index < json.size() && json[index] >= '0' && json[index] <= '9') {
            value = value * 10 + static_cast<std::uint64_t>(json[index] - '0');
            ++index;
        }
        values.push_back(value);
    }
    return values;
}

std::vector<std::vector<std::uint64_t>> extract_uint_matrix(
    const std::string& json,
    const std::string& name
) {
    const std::string key = "\"" + name + "\":";
    const auto position = json.find(key);
    if (position == std::string::npos) {
        throw std::runtime_error("missing matrix field: " + name);
    }
    std::size_t index = position + key.size();
    expect(index < json.size() && json[index] == '[', "matrix outer bracket");
    ++index;
    std::vector<std::vector<std::uint64_t>> matrix;
    while (index < json.size()) {
        if (json[index] == ']') {
            break;
        }
        if (json[index] == ',') {
            ++index;
            continue;
        }
        expect(json[index] == '[', "matrix row bracket");
        ++index;
        std::vector<std::uint64_t> row;
        while (index < json.size() && json[index] != ']') {
            if (json[index] == ',') {
                ++index;
                continue;
            }
            expect(json[index] >= '0' && json[index] <= '9', "matrix digit");
            std::uint64_t value = 0;
            while (index < json.size() && json[index] >= '0' && json[index] <= '9') {
                value = value * 10 + static_cast<std::uint64_t>(json[index] - '0');
                ++index;
            }
            row.push_back(value);
        }
        expect(index < json.size() && json[index] == ']', "matrix row close");
        ++index;
        matrix.push_back(std::move(row));
    }
    return matrix;
}

std::string add_decimal(const std::string& left, const std::string& right) {
    std::string result;
    std::size_t i = left.size();
    std::size_t j = right.size();
    int carry = 0;
    while (i > 0 || j > 0 || carry != 0) {
        const int left_digit = i > 0 ? left[--i] - '0' : 0;
        const int right_digit = j > 0 ? right[--j] - '0' : 0;
        const int sum = left_digit + right_digit + carry;
        result.push_back(static_cast<char>('0' + sum % 10));
        carry = sum / 10;
    }
    std::reverse(result.begin(), result.end());
    return result.empty() ? std::string("0") : result;
}

std::string mul_small_decimal(const std::string& value, std::uint32_t factor) {
    std::string result;
    std::uint64_t carry = 0;
    for (std::size_t index = value.size(); index > 0; --index) {
        const std::uint64_t product =
            static_cast<std::uint64_t>(value[index - 1] - '0') * factor + carry;
        result.push_back(static_cast<char>('0' + product % 10));
        carry = product / 10;
    }
    while (carry != 0) {
        result.push_back(static_cast<char>('0' + carry % 10));
        carry /= 10;
    }
    std::reverse(result.begin(), result.end());
    return result;
}

bool same_group_element(const GroupElement& left, const GroupElement& right) {
    if (left.square_count != right.square_count || !(left.container == right.container)) {
        return false;
    }
    for (SquareId square = 0; square < left.square_count; ++square) {
        if (left.square_map[square] != right.square_map[square]
            || !(left.local[square] == right.local[square])) {
            return false;
        }
    }
    return true;
}

std::string contacts_fingerprint(const Topology& topology) {
    std::vector<std::string> keys;
    keys.reserve(topology.contacts().size());
    for (const auto& contact : topology.contacts()) {
        keys.push_back(contact_key(contact));
    }
    std::sort(keys.begin(), keys.end());
    std::string result;
    for (const auto& key : keys) {
        result += key;
        result.push_back('\n');
    }
    return result;
}

std::string canonical_hex(const Topology& topology) {
    return canonical_key_hex(canonical_key_colored_graph(
        to_incidence_graph(topology.normalized()),
        CanonicalBackend::DenseNauty
    ));
}

// Exact quotient ball around a seed: every labeled topology whose toggle set
// relative to the seed has at most `radius` events, collapsed to canonical
// hex keys. Used to test the ball criterion delta <= r + s.
std::set<std::string> quotient_ball_keys(const Topology& seed, std::size_t radius) {
    const std::uint64_t event_count = event_count_for_squares(seed.square_count());
    const EventBitset seed_bits = topology_to_event_bitset(seed);
    std::set<std::string> keys;
    std::vector<EventId> toggles;

    const auto record_current = [&]() {
        EventBitset bits = seed_bits;
        for (const EventId id : toggles) {
            bits[id / 64U] ^= std::uint64_t{1} << (id % 64U);
        }
        keys.insert(canonical_hex(
            event_bitset_to_topology(seed.square_count(), bits)
        ));
    };

    const auto enumerate = [&](auto&& self, std::uint64_t start, std::size_t remaining) -> void {
        record_current();
        if (remaining == 0) {
            return;
        }
        for (std::uint64_t id = start; id < event_count; ++id) {
            toggles.push_back(static_cast<EventId>(id));
            self(self, id + 1, remaining - 1);
            toggles.pop_back();
        }
    };
    enumerate(enumerate, 0, radius);
    return keys;
}

// ---------------------------------------------------------------------------
// Event set layout
// ---------------------------------------------------------------------------

void test_event_layout() {
    constexpr std::array<std::uint64_t, 5> expected_event_counts{0, 32, 128, 288, 512};
    for (std::uint32_t n = 1; n <= 4; ++n) {
        const auto layout = EventSetLayout::for_square_count(n);
        const std::uint64_t pairs = static_cast<std::uint64_t>(n) * (n - 1U) / 2U;
        expect(layout.square_square_count == 64U * pairs, "square-square count is 64*C(n,2)");
        expect(layout.wall_count == 32U * n, "wall count is 32*n");
        expect(
            layout.event_count == 64U * pairs + 32U * n,
            "E(n) = 64*C(n,2) + 32*n"
        );
        expect(layout.event_count == expected_event_counts[n], "E(n) reference value");
        expect(
            layout.event_count == event_count_for_squares(n),
            "event_count_for_squares agrees with EventSetLayout"
        );

        std::uint64_t square_square_seen = 0;
        std::uint64_t wall_seen = 0;
        for (EventId id = 0; id < layout.event_count; ++id) {
            const EventRef ref = layout.describe(id);
            if (ref.kind == EventKind::SquareSquare) {
                ++square_square_seen;
                expect(ref.first_square < ref.second_square, "square pair is ordered");
                expect(ref.first_ring < 8 && ref.second_ring < 8, "ring indices are in range");
                expect(
                    layout.kind_of(id) == EventKind::SquareSquare,
                    "kind_of agrees with describe for square-square events"
                );
                expect(
                    layout.square_square_event(
                        ref.first_square,
                        ref.second_square,
                        ref.first_ring,
                        ref.second_ring
                    ) == id,
                    "square-square event id reconstructs from its fields"
                );
            } else {
                ++wall_seen;
                expect(ref.first_square == ref.second_square, "wall events use one square id");
                expect(ref.first_ring < 8 && ref.wall < 4, "wall domains are in range");
                expect(
                    layout.kind_of(id) == EventKind::Wall,
                    "kind_of agrees with describe for wall events"
                );
                expect(
                    layout.wall_event(ref.first_square, ref.first_ring, ref.wall) == id,
                    "wall event id reconstructs from its fields"
                );
            }
        }
        expect(square_square_seen == layout.square_square_count, "every square-square id appears once");
        expect(wall_seen == layout.wall_count, "every wall id appears once");
        expect(
            layout.kind_of(static_cast<EventId>(layout.square_square_count)) == EventKind::Wall,
            "wall ids start at 64*C(n,2)"
        );

        for (std::uint64_t index = 0; index < layout.square_square_count / 64U; ++index) {
            const auto [first, second] = layout.pair_squares(index);
            expect(first < second, "pair_squares returns an ordered pair");
            expect(layout.pair_index(first, second) == index, "pair_index inverts pair_squares");
        }
    }
}

// ---------------------------------------------------------------------------
// D4 and group law
// ---------------------------------------------------------------------------

std::vector<D4Element> all_d4_elements() {
    std::vector<D4Element> elements;
    for (int reflected = 0; reflected < 2; ++reflected) {
        for (int rotation = 0; rotation < 4; ++rotation) {
            elements.push_back(D4Element{
                .rotation = static_cast<std::uint8_t>(rotation),
                .reflected = reflected != 0,
            });
        }
    }
    return elements;
}

void test_d4_elements() {
    const auto elements = all_d4_elements();
    expect(elements.size() == 8, "D4 has eight elements");
    const D4Element identity{};

    for (const auto& element : elements) {
        expect(compose_d4(identity, element) == element, "left identity");
        expect(compose_d4(element, identity) == element, "right identity");
        expect(compose_d4(element, inverse_d4(element)) == identity, "right inverse");
        expect(compose_d4(inverse_d4(element), element) == identity, "left inverse");

        std::array<int, 8> ring_images{};
        std::array<int, 4> wall_images{};
        for (std::uint8_t ring = 0; ring < 8; ++ring) {
            ++ring_images[transform_ring(ring, element)];
        }
        for (std::uint8_t wall = 0; wall < 4; ++wall) {
            ++wall_images[transform_wall(wall, element)];
        }
        for (const int count : ring_images) {
            expect(count == 1, "every D4 element permutes the eight rings");
        }
        for (const int count : wall_images) {
            expect(count == 1, "every D4 element permutes the four walls");
        }
    }

    for (const auto& a : elements) {
        for (const auto& b : elements) {
            for (const auto& c : elements) {
                expect(
                    compose_d4(compose_d4(a, b), c) == compose_d4(a, compose_d4(b, c)),
                    "D4 composition is associative"
                );
            }
        }
    }

    // The composition law must agree with how the transforms are applied.
    for (const auto& inner : elements) {
        for (const auto& outer : elements) {
            const auto composed = compose_d4(outer, inner);
            for (std::uint8_t ring = 0; ring < 8; ++ring) {
                expect(
                    transform_ring(transform_ring(ring, inner), outer)
                        == transform_ring(ring, composed),
                    "ring transform is a composition action"
                );
            }
            for (std::uint8_t wall = 0; wall < 4; ++wall) {
                expect(
                    transform_wall(transform_wall(wall, inner), outer)
                        == transform_wall(wall, composed),
                    "wall transform is a composition action"
                );
            }
        }
    }

    std::map<std::string, int> class_counts;
    for (const auto& element : elements) {
        ++class_counts[d4_conjugacy_class_name(element)];
    }
    expect(class_counts.size() == 5, "D4 has five conjugacy classes");
    expect(class_counts["identity"] == 1, "identity class size");
    expect(class_counts["rotation90"] == 2, "rotation90 class size");
    expect(class_counts["rotation180"] == 1, "rotation180 class size");
    expect(class_counts["reflection_corner_axis"] == 2, "corner-axis reflection class size");
    expect(class_counts["reflection_side_axis"] == 2, "side-axis reflection class size");
}

void test_group_element_law() {
    constexpr std::array<std::uint64_t, 5> expected_sizes{0, 64, 1024, 24576, 786432};
    for (std::uint32_t n = 1; n <= 4; ++n) {
        expect(group_element_count(n) == expected_sizes[n], "|G_n| = n! * 8^n * 8");
    }
    // Recheck the formula independently: n! * 8^n * 8.
    for (std::uint32_t n = 1; n <= 4; ++n) {
        std::uint64_t formula = 8;  // container D4
        for (std::uint32_t square = 0; square < n; ++square) {
            formula *= 8;
        }
        for (std::uint32_t factor = 2; factor <= n; ++factor) {
            formula *= factor;
        }
        expect(group_element_count(n) == formula, "group order formula n! * 8^n * 8");
    }

    const auto identity = identity_group_element(1);
    expect(encode_group_element(identity) == 0, "identity encodes as zero");
    expect(is_permutation(identity), "identity is a permutation");

    // Full round-trip for n = 1..3, sampled for n = 4.
    for (std::uint32_t n = 1; n <= 4; ++n) {
        const std::uint64_t stride = n <= 3 ? 1 : 1021;
        for (std::uint64_t index = 0; index < group_element_count(n); index += stride) {
            const auto element = decode_group_element(n, index);
            expect(encode_group_element(element) == index, "encode inverts decode");
            expect(is_permutation(element), "decoded elements are permutations");
            expect(element.square_count == n, "decoded square count");
        }
    }

    // Group laws, exhaustive for n = 1 and n = 2.
    for (std::uint32_t n = 1; n <= 2; ++n) {
        const auto unit = identity_group_element(n);
        for (std::uint64_t index = 0; index < group_element_count(n); ++index) {
            const auto element = decode_group_element(n, index);
            expect(same_group_element(compose_group_elements(unit, element), element), "left identity");
            expect(same_group_element(compose_group_elements(element, unit), element), "right identity");
            const auto inverse = inverse_group_element(element);
            expect(
                same_group_element(compose_group_elements(element, inverse), unit),
                "right inverse"
            );
            expect(
                same_group_element(compose_group_elements(inverse, element), unit),
                "left inverse"
            );
        }
    }

    // Associativity and conjugacy, deterministically sampled.
    std::mt19937_64 generator(0x5eed1234ULL);
    for (const std::uint32_t n : {1U, 2U, 4U}) {
        const std::uint64_t size = group_element_count(n);
        std::uniform_int_distribution<std::uint64_t> distribution(0, size - 1);
        for (int trial = 0; trial < 512; ++trial) {
            const auto a = decode_group_element(n, distribution(generator));
            const auto b = decode_group_element(n, distribution(generator));
            const auto c = decode_group_element(n, distribution(generator));
            const auto left = compose_group_elements(compose_group_elements(a, b), c);
            const auto right = compose_group_elements(a, compose_group_elements(b, c));
            expect(same_group_element(left, right), "group composition is associative");
        }
        for (int trial = 0; trial < 256; ++trial) {
            const auto a = decode_group_element(n, distribution(generator));
            const auto b = decode_group_element(n, distribution(generator));
            const auto conjugated = conjugate_group_element(a, b);
            const auto recheck = compose_group_elements(
                compose_group_elements(b, a),
                inverse_group_element(b)
            );
            expect(
                same_group_element(conjugated, recheck),
                "b * a * b^-1 conjugation"
            );
        }
    }

    // Conjugacy class counts (wreath-product values, checkable by hand for n=1).
    expect(group_conjugacy_class_count(1) == 25, "G_1 has 25 conjugacy classes");
    expect(group_conjugacy_class_count(2) == 100, "G_2 has 100 conjugacy classes");
}

// ---------------------------------------------------------------------------
// Event action: valid ids, kind preservation, agreement with production
// ---------------------------------------------------------------------------

void test_event_action_semantics() {
    for (std::uint32_t n = 1; n <= 4; ++n) {
        const auto layout = EventSetLayout::for_square_count(n);
        const std::uint64_t stride = n <= 2 ? 1 : (n == 3 ? 173 : 1021);
        for (std::uint64_t index = 0; index < group_element_count(n); index += stride) {
            const auto element = decode_group_element(n, index);
            const auto permutation = event_permutation(element);
            expect(permutation.size() == layout.event_count, "permutation covers Omega_n");
            std::vector<std::uint8_t> image_seen(layout.event_count, 0);
            for (EventId id = 0; id < layout.event_count; ++id) {
                const EventId image = permutation[id];
                expect(image < layout.event_count, "E(n) is invariant under the action");
                expect(image_seen[image] == 0, "event action is injective");
                image_seen[image] = 1;
                expect(
                    layout.kind_of(image) == layout.kind_of(id),
                    "contact kind is preserved: SS stays SS, wall stays wall"
                );
                expect(
                    apply_group_element_to_event(element, id) == image,
                    "scalar action agrees with the event permutation"
                );
            }
            // Scalar action keeps every event decodable.
            for (EventId id = 0; id < layout.event_count; id += 7) {
                const EventRef ref = layout.describe(apply_group_element_to_event(element, id));
                if (ref.kind == EventKind::SquareSquare) {
                    expect(ref.first_square < ref.second_square, "mapped SS event is ordered");
                } else {
                    expect(ref.first_square == ref.second_square, "mapped wall event is single-square");
                }
            }
        }
    }
}

void test_topology_bitset_roundtrip() {
    std::mt19937_64 generator(0xabcdef01ULL);
    for (const std::uint32_t n : {1U, 2U, 4U}) {
        const auto layout = EventSetLayout::for_square_count(n);
        const std::uint64_t words = (layout.event_count + 63U) / 64U;
        for (int trial = 0; trial < 24; ++trial) {
            EventBitset bits(words, 0);
            const std::uint64_t target = 1U + generator() % std::min<std::uint64_t>(layout.event_count, 40U);
            for (std::uint64_t count = 0; count < target; ++count) {
                const EventId id = static_cast<EventId>(generator() % layout.event_count);
                bits[id / 64U] ^= std::uint64_t{1} << (id % 64U);
            }
            const Topology topology = event_bitset_to_topology(n, bits);
            expect(topology.validate().ok(), "every event subset is a valid topology");
            expect(
                topology.contacts().size() == event_bitset_popcount(bits),
                "contact count equals event weight"
            );
            expect(topology_to_event_bitset(topology) == bits, "bitset round-trips");
        }
    }
}

void test_group_action_matches_production_transforms() {
    struct NamedFixture {
        std::string name;
        std::uint32_t n;
    };
    const std::vector<NamedFixture> fixtures{
        {"isolated-1", 1},
        {"disjoint-2", 2},
        {"corner-side-2", 2},
        {"side-side-2", 2},
        {"disjoint-4", 4},
        {"line-4", 4},
        {"grid-2x2", 4},
    };
    const auto all_d4 = all_d4_elements();

    for (const auto& fixture : fixtures) {
        const auto topology = make_fixture(fixture.name);
        const auto unit = identity_group_element(fixture.n);

        // Container factor against relabel_container.
        for (const auto& container : all_d4) {
            auto element = unit;
            element.container = container;
            const auto direct = relabel_container(
                topology,
                D4Transform{.rotation = container.rotation, .reflected = container.reflected}
            );
            expect(
                contacts_fingerprint(apply_group_element_to_topology(topology, element))
                    == contacts_fingerprint(direct),
                "container action agrees with relabel_container for " + fixture.name
            );
        }

        // Local factor against relabel_square.
        for (SquareId square = 0; square < fixture.n; ++square) {
            for (const auto& local : all_d4) {
                auto element = unit;
                element.local[square] = local;
                const auto direct = relabel_square(
                    topology,
                    square,
                    D4Transform{.rotation = local.rotation, .reflected = local.reflected}
                );
                expect(
                    contacts_fingerprint(apply_group_element_to_topology(topology, element))
                        == contacts_fingerprint(direct),
                    "local D4 action agrees with relabel_square for " + fixture.name
                );
            }
        }

        // Square permutation factor against permute_squares. The production
        // transform takes old -> new, exactly like GroupElement::square_map.
        if (fixture.n >= 2) {
            std::vector<SquareId> swap(fixture.n);
            for (SquareId square = 0; square < fixture.n; ++square) {
                swap[square] = square;
            }
            std::swap(swap[0], swap[1]);
            auto element = unit;
            for (SquareId square = 0; square < fixture.n; ++square) {
                element.square_map[square] = swap[square];
            }
            expect(
                contacts_fingerprint(apply_group_element_to_topology(topology, element))
                    == contacts_fingerprint(permute_squares(topology, swap)),
                "square permutation agrees with permute_squares for " + fixture.name
            );
        }

        // Full elements: event-bitset permutation must agree with the
        // production relabel path, and canonical keys must be preserved.
        const std::uint64_t stride = fixture.n <= 2 ? 37 : 5003;
        for (std::uint64_t index = 0; index < group_element_count(fixture.n); index += stride) {
            const auto element = decode_group_element(fixture.n, index);
            const auto via_bitset = permute_event_bitset(
                event_permutation(element),
                topology_to_event_bitset(topology)
            );
            const auto via_production = topology_to_event_bitset(
                apply_group_element_to_topology(topology, element)
            );
            expect(via_bitset == via_production, "bitset action agrees with production transforms");
        }

        // Canonicalization cross-check: sampled elements must preserve keys.
        const std::string seed_key = canonical_hex(topology);
        const std::uint64_t key_stride = fixture.n <= 2 ? 61 : 2039;
        for (std::uint64_t index = 0; index < group_element_count(fixture.n); index += key_stride) {
            const auto element = decode_group_element(fixture.n, index);
            expect(
                canonical_hex(apply_group_element_to_topology(topology, element)) == seed_key,
                "canonical key is preserved by the audited symmetry for " + fixture.name
            );
        }
    }
}

// ---------------------------------------------------------------------------
// Exact Burnside counts
// ---------------------------------------------------------------------------

const std::vector<std::string>& n1_coefficients() {
    static const std::vector<std::string> values{
        "1", "2", "22", "116", "744", "3568", "15454", "55170", "170302", "448254",
        "1026402", "2042344", "3568192", "5476980", "7429674", "8906430", "9465762",
        "8906430", "7429674", "5476980", "3568192", "2042344", "1026402", "448254",
        "170302", "55170", "15454", "3568", "744", "116", "22", "2", "1",
    };
    return values;
}

const std::string& n1_total() {
    static const std::string value = "67753072";
    return value;
}

const std::vector<std::pair<std::string, std::uint64_t>>& n1_cycle_types() {
    static const std::vector<std::pair<std::string, std::uint64_t>> values{
        {"4^8", 28},
        {"2^16", 21},
        {"1^4 2^14", 8},
        {"1^8 2^12", 4},
        {"1^16 2^8", 2},
        {"1^32", 1},
    };
    return values;
}

const std::map<std::pair<std::string, std::string>, std::string>& n1_d4_class_table() {
    // (ring class, wall class) -> induced cycle type on the 32 wall events.
    static const std::map<std::pair<std::string, std::string>, std::string> table{
        {{"identity", "identity"}, "1^32"},
        {{"identity", "reflection_corner_axis"}, "1^16 2^8"},
        {{"identity", "reflection_side_axis"}, "2^16"},
        {{"identity", "rotation180"}, "2^16"},
        {{"identity", "rotation90"}, "4^8"},
        {{"reflection_corner_axis", "identity"}, "1^8 2^12"},
        {{"reflection_corner_axis", "reflection_corner_axis"}, "1^4 2^14"},
        {{"reflection_corner_axis", "reflection_side_axis"}, "2^16"},
        {{"reflection_corner_axis", "rotation180"}, "2^16"},
        {{"reflection_corner_axis", "rotation90"}, "4^8"},
        {{"reflection_side_axis", "identity"}, "1^8 2^12"},
        {{"reflection_side_axis", "reflection_corner_axis"}, "1^4 2^14"},
        {{"reflection_side_axis", "reflection_side_axis"}, "2^16"},
        {{"reflection_side_axis", "rotation180"}, "2^16"},
        {{"reflection_side_axis", "rotation90"}, "4^8"},
        {{"rotation180", "identity"}, "2^16"},
        {{"rotation180", "reflection_corner_axis"}, "2^16"},
        {{"rotation180", "reflection_side_axis"}, "2^16"},
        {{"rotation180", "rotation180"}, "2^16"},
        {{"rotation180", "rotation90"}, "4^8"},
        {{"rotation90", "identity"}, "4^8"},
        {{"rotation90", "reflection_corner_axis"}, "4^8"},
        {{"rotation90", "reflection_side_axis"}, "4^8"},
        {{"rotation90", "rotation180"}, "4^8"},
        {{"rotation90", "rotation90"}, "4^8"},
    };
    return table;
}

std::uint64_t d4_class_size(const std::string& name) {
    if (name == "identity" || name == "rotation180") {
        return 1;
    }
    return 2;
}

void test_burnside_n1_exact() {
    OrbitCountOptions options;
    options.emit_contributions = true;
    options.count_conjugacy_classes = true;
    const auto result = burnside_orbit_count(1, options);

    expect(result.square_count == 1, "n=1");
    expect(result.event_count == 32, "E(1) = 32");
    expect(result.group_size == 64, "|G_1| = 64");
    expect(result.distinct_cycle_types == 6, "six distinct induced cycle types");
    expect(result.conjugacy_classes == 25, "25 conjugacy classes");
    expect(result.checks_divisible, "all Burnside coefficients divide by |G|");
    expect(result.checks_complement_symmetric, "complement symmetry");
    expect(result.checks_total_matches, "both orbit totals agree");
    expect(result.checks_endpoints_unit, "a_0 = a_E = 1");
    expect(result.checks_positive, "all coefficients are positive");

    expect(result.coefficient_decimal == n1_coefficients(), "exact n=1 coefficients");
    expect(result.total_orbit_count_decimal == n1_total(), "N_1 = 67,753,072");
    expect(result.total_from_cycle_counts_decimal == n1_total(), "cycle-type total agrees");
    expect(result.coefficient_sum_decimal.size() == 33, "numerator array is a_0..a_32");

    // The full cycle-type table with multiplicities.
    std::map<std::string, std::uint64_t> observed;
    for (const auto& record : result.cycle_types) {
        observed[record.cycle_type.to_compact_string()] = record.group_elements;
        expect(record.contribution_decimal.size() == 33, "each contribution has 33 coefficients");
        expect(
            record.contribution_decimal.front() == std::to_string(record.group_elements),
            "contribution degree zero equals the multiplicity"
        );
        // D4 class pairs of this cycle type: every (ring, wall) pair appears
        // exactly once across the whole table.
    }
    std::map<std::string, std::uint64_t> expected;
    for (const auto& [type, count] : n1_cycle_types()) {
        expected[type] = count;
    }
    expect(observed == expected, "n=1 cycle-type multiplicity table");

    // The 25 (ring, wall) D4 class pairs must partition the 64 elements, and
    // each pair must induce the tabulated cycle type.
    std::map<std::pair<std::string, std::string>, std::pair<std::string, std::uint64_t>> pairs;
    for (const auto& record : result.cycle_types) {
        for (const auto& pair : record.d4_class_pairs) {
            const auto key = std::make_pair(pair.ring_class, pair.wall_class);
            expect(pairs.count(key) == 0, "each D4 class pair appears once");
            pairs[key] = {record.cycle_type.to_compact_string(), pair.group_elements};
        }
    }
    expect(pairs.size() == 25, "25 D4 class pairs");
    for (const auto& [key, expected_type] : n1_d4_class_table()) {
        const auto found = pairs.find(key);
        expect(found != pairs.end(), "D4 class pair present");
        expect(found->second.first == expected_type, "D4 class pair cycle type");
        expect(
            found->second.second == d4_class_size(key.first) * d4_class_size(key.second),
            "D4 class pair element count"
        );
    }
    std::uint64_t element_total = 0;
    for (const auto& [type, count] : observed) {
        element_total += count;
    }
    expect(element_total == 64, "cycle types partition the group");

    // Contribution arrays must sum, degree by degree, to the numerators, and
    // the numerators must sum to |G| * N_1.
    std::vector<std::string> sums(33, "0");
    for (const auto& record : result.cycle_types) {
        for (std::size_t degree = 0; degree < 33; ++degree) {
            sums[degree] = add_decimal(sums[degree], record.contribution_decimal[degree]);
        }
    }
    for (std::size_t degree = 0; degree < 33; ++degree) {
        expect(sums[degree] == result.coefficient_sum_decimal[degree], "contribution sum per degree");
    }
    std::string numerator_total = "0";
    std::string coefficient_total = "0";
    for (std::size_t degree = 0; degree < 33; ++degree) {
        numerator_total = add_decimal(numerator_total, result.coefficient_sum_decimal[degree]);
        coefficient_total = add_decimal(coefficient_total, result.coefficient_decimal[degree]);
    }
    expect(coefficient_total == n1_total(), "coefficient sum equals N_1");
    expect(numerator_total == mul_small_decimal(n1_total(), 64), "numerator sum equals |G| * N_1");
}

const std::vector<std::string>& n2_head_coefficients() {
    static const std::vector<std::string> values{"1", "5", "87", "1411", "26620", "481126"};
    return values;
}

const std::string& n2_total() {
    static const std::string value = "332317140421910940456278459867471872";
    return value;
}

void test_burnside_n2_exact_and_golden() {
    OrbitCountOptions options;
    options.count_conjugacy_classes = true;
    const auto result = burnside_orbit_count(2, options);

    expect(result.event_count == 128, "E(2) = 128");
    expect(result.group_size == 1024, "|G_2| = 1024");
    expect(result.distinct_cycle_types == 26, "26 distinct induced cycle types");
    expect(result.conjugacy_classes == 100, "100 conjugacy classes");
    expect(result.coefficient_decimal.size() == 129, "a_0..a_128");
    expect(result.checks_divisible && result.checks_total_matches && result.checks_complement_symmetric,
           "n=2 Burnside checks");
    expect(
        std::vector<std::string>(result.coefficient_decimal.begin(), result.coefficient_decimal.begin() + 6)
            == n2_head_coefficients(),
        "n=2 head coefficients"
    );
    expect(result.total_orbit_count_decimal == n2_total(), "N_2 exact value");
    expect(result.total_from_cycle_counts_decimal == n2_total(), "n=2 cycle-type total");

    std::uint64_t element_total = 0;
    for (const auto& record : result.cycle_types) {
        element_total += record.group_elements;
    }
    expect(element_total == 1024, "n=2 cycle types partition the group");

    // Golden file committed as an exact machine-readable reference.
    const std::string golden = read_source_file("tests/data/orbit-count-n2.json");
    expect(extract_string(golden, "schema") == "sqtopology.orbit-count.v1", "golden schema");
    expect(extract_uint(golden, "n") == 2, "golden n");
    expect(extract_uint(golden, "event_count") == 128, "golden E(2)");
    expect(extract_uint(golden, "group_size") == 1024, "golden |G_2|");
    expect(extract_uint(golden, "distinct_cycle_types") == 26, "golden cycle types");
    expect(extract_uint(golden, "conjugacy_classes") == 100, "golden conjugacy classes");
    expect(extract_string_array(golden, "coefficients") == result.coefficient_decimal, "golden coefficients");
    expect(extract_string(golden, "total_orbit_count") == n2_total(), "golden total");
    expect(golden.find("\"all_coefficients_divisible\":true") != std::string::npos, "golden checks");
    expect(golden.find("\"total_matches_burnside_sum\":true") != std::string::npos, "golden checks");

    // The depth-4 research diagonal for the empty disjoint-2 seed must equal
    // the cumulative Burnside sum through a_4; this is the campaign's own
    // cross-validation of the model.
    std::string cumulative = "0";
    for (int degree = 0; degree <= 4; ++degree) {
        cumulative = add_decimal(cumulative, result.coefficient_decimal[static_cast<std::size_t>(degree)]);
    }
    expect(cumulative == "28124", "research depth-4 diagonal for disjoint-2 equals sum a_0..a_4");
}

void test_golden_count_files() {
    // n = 1 golden file carries the full contribution breakdown.
    const std::string n1_json = read_source_file("tests/data/orbit-count-n1.json");
    expect(extract_string(n1_json, "schema") == "sqtopology.orbit-count.v1", "n=1 golden schema");
    expect(extract_uint(n1_json, "n") == 1, "n=1 golden n");
    expect(extract_uint(n1_json, "event_count") == 32, "n=1 golden E");
    expect(extract_uint(n1_json, "group_size") == 64, "n=1 golden group");
    expect(extract_uint(n1_json, "distinct_cycle_types") == 6, "n=1 golden cycle types");
    expect(extract_uint(n1_json, "conjugacy_classes") == 25, "n=1 golden conjugacy");
    expect(extract_string_array(n1_json, "coefficients") == n1_coefficients(), "n=1 golden coefficients");
    expect(extract_string_array(n1_json, "coefficient_sums").size() == 33, "n=1 golden numerators");
    expect(extract_string(n1_json, "total_orbit_count") == n1_total(), "n=1 golden total");
    expect(n1_json.find("\"all_coefficients_positive\":true") != std::string::npos, "n=1 golden checks");
    expect(n1_json.find("\"complement_symmetric\":true") != std::string::npos, "n=1 golden checks");

    // n = 3 and n = 4 records pin the larger-n scaling facts.
    const std::string n3_json = read_source_file("tests/data/orbit-count-n3.json");
    expect(extract_uint(n3_json, "n") == 3, "n=3 golden n");
    expect(extract_uint(n3_json, "event_count") == 288, "n=3 golden E");
    expect(extract_uint(n3_json, "group_size") == 24576, "n=3 golden group");
    expect(extract_uint(n3_json, "distinct_cycle_types") == 78, "n=3 golden cycle types");
    expect(extract_uint(n3_json, "conjugacy_classes") == 325, "n=3 golden conjugacy");
    expect(extract_string_array(n3_json, "coefficients").size() == 289, "n=3 golden coefficient count");
    expect(n3_json.find("\"all_coefficients_divisible\":true") != std::string::npos, "n=3 golden checks");
    const auto n3_coefficients = extract_string_array(n3_json, "coefficients");
    expect(
        std::vector<std::string>(n3_coefficients.begin(), n3_coefficients.begin() + 7)
            == std::vector<std::string>{"1", "5", "119", "2979", "92770", "2985882", "94975858"},
        "n=3 head coefficients"
    );

    const std::string n4_json = read_source_file("tests/data/orbit-count-n4.json");
    expect(extract_uint(n4_json, "n") == 4, "n=4 golden n");
    expect(extract_uint(n4_json, "event_count") == 512, "n=4 golden E");
    expect(extract_uint(n4_json, "group_size") == 786432, "n=4 golden group");
    expect(extract_uint(n4_json, "distinct_cycle_types") == 203, "n=4 golden cycle types");
    expect(extract_uint(n4_json, "conjugacy_classes") == 950, "n=4 golden conjugacy");
    expect(extract_string_array(n4_json, "coefficients").size() == 513, "n=4 golden coefficient count");
    expect(n4_json.find("\"all_coefficients_divisible\":true") != std::string::npos, "n=4 golden checks");
    const auto n4_coefficients = extract_string_array(n4_json, "coefficients");
    expect(
        std::vector<std::string>(n4_coefficients.begin(), n4_coefficients.begin() + 9)
            == std::vector<std::string>{"1", "5", "125", "3560", "137549", "5938772",
                                        "268405879", "12147272864", "537727714799"},
        "n=4 head coefficients"
    );
}

// ---------------------------------------------------------------------------
// Research traversal validation and depth-resolved accounting
// ---------------------------------------------------------------------------

void test_research_matches_burnside_and_accounting() {
    OrbitCountOptions burnside_options;
    burnside_options.count_conjugacy_classes = false;
    const auto n1_burnside = burnside_orbit_count(1, burnside_options);

    ResearchOptions options;
    options.max_depth = 6;
    options.collect_symmetry = false;
    const auto isolated = run_research_search(make_fixture("isolated-1"), options);

    expect(isolated.depths.size() == 7, "isolated-1 depths 0..6");
    std::uint64_t cumulative = 0;
    for (const auto& record : isolated.depths) {
        cumulative += record.new_unique;
        expect(
            std::to_string(record.new_unique) == n1_burnside.coefficient_decimal[record.depth],
            "isolated-1 new_unique(d) equals the Burnside coefficient a_d"
        );
        expect(record.cumulative_unique == cumulative, "isolated-1 cumulative");
    }
    expect(isolated.total_unique == 19907, "isolated-1 depth-6 total equals sum a_0..a_6");

    // Depth-resolved geodesic accounting. On the unquotiented hypercube every
    // state at distance d has exactly d geodesic predecessors, so p <= d and
    // p >= 1 must hold for every depth; merged predecessors below d are the
    // quotient effect the metric is designed to expose.
    for (const auto& record : isolated.depths) {
        if (record.depth == 0) {
            continue;
        }
        expect(record.same_level_edges == 0, "same-level edges must not occur (weight parity)");
        expect(
            record.geodesic_predecessors.count == record.new_unique,
            "every state contributes one predecessor count"
        );
        expect(
            record.states_with_full_predecessors + record.states_with_merged_predecessors
                == record.new_unique,
            "full + merged predecessor states partition the layer"
        );
        expect(record.geodesic_predecessors.min_value >= 1, "every non-seed state has a parent");
        expect(
            record.geodesic_predecessors.max_value <= record.depth,
            "geodesic predecessors never exceed the depth"
        );
        if (record.depth == 1) {
            expect(
                record.states_with_full_predecessors == record.new_unique,
                "depth-1 states have their single geodesic predecessor"
            );
        }
    }
    expect(isolated.convergence.total_same_level_edges == 0, "no same-level edges anywhere");
    expect(
        isolated.convergence.geodesic_predecessors_per_state.count == isolated.total_unique - 1,
        "predecessor histogram covers every non-seed state"
    );
    expect(
        isolated.convergence.geodesic_predecessor_total
            == static_cast<std::uint64_t>(isolated.convergence.geodesic_predecessors_per_state.sum),
        "predecessor totals reconcile"
    );

    // n = 2 empty seed: production traversal vs exact Burnside coefficients.
    const auto n2_burnside = burnside_orbit_count(2, burnside_options);
    ResearchOptions n2_options;
    n2_options.max_depth = 3;
    n2_options.collect_symmetry = false;
    const auto disjoint = run_research_search(make_fixture("disjoint-2"), n2_options);
    expect(disjoint.depths.size() == 4, "disjoint-2 depths 0..3");
    cumulative = 0;
    for (const auto& record : disjoint.depths) {
        cumulative += record.new_unique;
        expect(
            std::to_string(record.new_unique) == n2_burnside.coefficient_decimal[record.depth],
            "disjoint-2 new_unique(d) equals the Burnside coefficient a_d"
        );
        expect(record.cumulative_unique == cumulative, "disjoint-2 cumulative");
        if (record.depth > 0) {
            expect(record.same_level_edges == 0, "disjoint-2 same-level edges must not occur");
        }
    }
    expect(disjoint.total_unique == 1504, "disjoint-2 depth-3 total equals sum a_0..a_3");
}

// ---------------------------------------------------------------------------
// Orbit-Hamming distances and the ball criterion
// ---------------------------------------------------------------------------

std::vector<std::vector<std::uint64_t>> n2_distance_matrix() {
    return {
        {0, 1, 1, 1},
        {1, 0, 2, 2},
        {1, 2, 0, 2},
        {1, 2, 2, 0},
    };
}

void test_seed_distances_n2() {
    const std::vector<std::string> names{
        "disjoint-2", "corner-corner-2", "corner-side-2", "side-side-2"};
    const auto expected = n2_distance_matrix();
    std::vector<std::vector<std::uint64_t>> matrix(4, std::vector<std::uint64_t>(4, 0));
    std::vector<OrbitDistanceResult> results(16);
    for (std::size_t row = 0; row < names.size(); ++row) {
        for (std::size_t column = 0; column < names.size(); ++column) {
            if (row == column) {
                continue;
            }
            const auto result = orbit_hamming_distance(
                make_fixture(names[row]),
                make_fixture(names[column])
            );
            results[row * 4 + column] = result;
            matrix[row][column] = result.distance;
        }
    }
    expect(matrix == expected, "n=2 seed distance matrix");
    for (std::size_t row = 0; row < names.size(); ++row) {
        for (std::size_t column = 0; column < names.size(); ++column) {
            if (row == column) {
                continue;
            }
            const auto& result = results[row * 4 + column];
            const std::uint64_t gap = result.first_weight > result.second_weight
                ? result.first_weight - result.second_weight
                : result.second_weight - result.first_weight;
            expect(result.witness_symmetric_difference == result.distance, "witness recheck");
            expect(result.distance >= gap, "weight lower bound");
            expect(
                (result.distance + result.first_weight + result.second_weight) % 2U == 0U,
                "weight parity"
            );
        }
    }
}

void test_seed_distances_n4() {
    const std::vector<std::string> names{"disjoint-4", "line-4", "grid-2x2"};
    const std::vector<std::vector<std::uint64_t>> expected{
        {0, 13, 14},
        {13, 0, 11},
        {14, 11, 0},
    };
    std::vector<std::vector<std::uint64_t>> matrix(3, std::vector<std::uint64_t>(3, 0));
    for (std::size_t row = 0; row < names.size(); ++row) {
        for (std::size_t column = row + 1; column < names.size(); ++column) {
            const auto forward = orbit_hamming_distance(
                make_fixture(names[row]),
                make_fixture(names[column])
            );
            const auto backward = orbit_hamming_distance(
                make_fixture(names[column]),
                make_fixture(names[row])
            );
            expect(forward.distance == backward.distance, "orbit distance is symmetric");
            expect(forward.witness_symmetric_difference == forward.distance, "witness recheck");
            matrix[row][column] = forward.distance;
            matrix[column][row] = forward.distance;
        }
    }
    expect(matrix == expected, "n=4 seed distance matrix");

    // line-4 vs grid-2x2: weight gap one, structural excess ten. The shallow
    // radius-3 zero overlap is fully explained by delta = 11 > 6; the weight
    // bound alone would only give delta >= 1.
    const auto line = orbit_hamming_distance(make_fixture("line-4"), make_fixture("grid-2x2"));
    const std::uint64_t gap = line.first_weight > line.second_weight
        ? line.first_weight - line.second_weight
        : line.second_weight - line.first_weight;
    expect(gap == 1, "line-4/grid-2x2 weight gap");
    expect(line.distance - gap == 10, "line-4/grid-2x2 structural excess");
}

void test_distance_golden_files() {
    const std::string n2_json = read_source_file("tests/data/seed-distances-n2.json");
    expect(extract_string(n2_json, "schema") == "sqtopology.orbit-distances.v1", "n=2 distance schema");
    expect(extract_uint(n2_json, "n") == 2, "n=2 distance n");
    expect(extract_uint_matrix(n2_json, "matrix") == n2_distance_matrix(), "n=2 golden matrix");
    expect(
        extract_uint_array(n2_json, "contact_counts") == std::vector<std::uint64_t>{0, 1, 1, 1},
        "n=2 golden contact counts"
    );
    expect(n2_json.find("\"symmetric_matrix\":true") != std::string::npos, "n=2 distance checks");
    expect(n2_json.find("\"weight_lower_bound\":true") != std::string::npos, "n=2 distance checks");

    const std::string n4_json = read_source_file("tests/data/seed-distances-n4.json");
    expect(extract_uint(n4_json, "n") == 4, "n=4 distance n");
    expect(extract_uint(n4_json, "event_count") == 512, "n=4 distance E");
    expect(
        extract_uint_matrix(n4_json, "matrix")
            == std::vector<std::vector<std::uint64_t>>{{0, 13, 14}, {13, 0, 11}, {14, 11, 0}},
        "n=4 golden matrix"
    );
    expect(
        extract_uint_array(n4_json, "contact_counts") == std::vector<std::uint64_t>{0, 13, 14},
        "n=4 golden contact counts"
    );
    expect(n4_json.find("\"triangle_inequality\":true") != std::string::npos, "n=4 distance checks");
}

void test_ball_criterion_n2() {
    const std::vector<std::string> names{
        "disjoint-2", "corner-corner-2", "corner-side-2", "side-side-2"};
    std::vector<std::vector<std::uint64_t>> delta(4, std::vector<std::uint64_t>(4, 0));
    for (std::size_t row = 0; row < 4; ++row) {
        for (std::size_t column = row + 1; column < 4; ++column) {
            const auto result = orbit_hamming_distance(
                make_fixture(names[row]),
                make_fixture(names[column])
            );
            delta[row][column] = result.distance;
            delta[column][row] = result.distance;
        }
    }

    std::vector<std::vector<std::set<std::string>>> balls(4);
    for (std::size_t index = 0; index < 4; ++index) {
        for (std::size_t radius = 0; radius <= 2; ++radius) {
            balls[index].push_back(quotient_ball_keys(make_fixture(names[index]), radius));
        }
    }

    // B_r(A) and B_s(B) intersect iff delta(A, B) <= r + s.
    for (std::size_t a = 0; a < 4; ++a) {
        for (std::size_t b = a + 1; b < 4; ++b) {
            for (std::size_t r = 0; r <= 2; ++r) {
                for (std::size_t s = 0; s <= 2; ++s) {
                    std::vector<std::string> common;
                    std::set_intersection(
                        balls[a][r].begin(),
                        balls[a][r].end(),
                        balls[b][s].begin(),
                        balls[b][s].end(),
                        std::back_inserter(common)
                    );
                    const bool expected_nonempty = delta[a][b] <= r + s;
                    expect(
                        !common.empty() == expected_nonempty,
                        "ball intersection criterion for " + names[a] + " vs " + names[b]
                    );
                }
            }
        }
    }

    // Balls are nested, and the empty seed reproduces the Burnside layers.
    for (std::size_t index = 0; index < 4; ++index) {
        expect(
            std::includes(
                balls[index][2].begin(),
                balls[index][2].end(),
                balls[index][1].begin(),
                balls[index][1].end()
            ),
            "radius-2 ball contains the radius-1 ball"
        );
        expect(
            std::includes(
                balls[index][1].begin(),
                balls[index][1].end(),
                balls[index][0].begin(),
                balls[index][0].end()
            ),
            "radius-1 ball contains the radius-0 ball"
        );
    }
    expect(balls[0][0].size() == 1, "B_0 has one element");
    expect(balls[0][1].size() == 6, "disjoint-2 B_1 size equals a_0 + a_1");
    expect(balls[0][2].size() == 93, "disjoint-2 B_2 size equals a_0 + a_1 + a_2");
}

}  // namespace

int main() {
    try {
        test_event_layout();
        test_d4_elements();
        test_group_element_law();
        test_event_action_semantics();
        test_topology_bitset_roundtrip();
        test_group_action_matches_production_transforms();
        test_burnside_n1_exact();
        test_burnside_n2_exact_and_golden();
        test_golden_count_files();
        test_research_matches_burnside_and_accounting();
        test_seed_distances_n2();
        test_seed_distances_n4();
        test_distance_golden_files();
        test_ball_criterion_n2();
        std::cout << "sqtopology_orbit_tests: all tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_orbit_tests: FAIL: " << error.what() << '\n';
        return 1;
    }
}
