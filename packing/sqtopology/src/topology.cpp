#include "sqtopology/topology.hpp"

#include <algorithm>
#include <array>
#include <sstream>
#include <stdexcept>
#include <tuple>
#include <utility>

namespace sqtopology {
namespace {

auto feature_tuple(const FeatureRef& feature) {
    return std::tuple{
        feature.square,
        static_cast<int>(feature.kind),
        static_cast<int>(feature.index),
    };
}

Contact normalized_contact(Contact contact) {
    if (contact.kind != ContactKind::Wall && contact.b.has_value()) {
        if (feature_tuple(*contact.b) < feature_tuple(contact.a)) {
            std::swap(contact.a, *contact.b);
        }
    }
    return contact;
}

ContactKind inferred_kind(FeatureKind a, FeatureKind b) {
    if (a == FeatureKind::Corner && b == FeatureKind::Corner) {
        return ContactKind::CornerCorner;
    }
    if (a == FeatureKind::Side && b == FeatureKind::Side) {
        return ContactKind::SideSide;
    }
    return ContactKind::CornerSide;
}

bool valid_feature(const FeatureRef& feature, std::uint32_t square_count) {
    return feature.square < square_count && feature.index < 4;
}

}  // namespace

Topology::Topology(std::uint32_t square_count) : square_count_(square_count) {}

std::uint32_t Topology::square_count() const noexcept {
    return square_count_;
}

const std::vector<Contact>& Topology::contacts() const noexcept {
    return contacts_;
}

std::vector<Contact>& Topology::contacts() noexcept {
    return contacts_;
}

void Topology::add_contact(Contact contact) {
    contacts_.push_back(normalized_contact(std::move(contact)));
}

ValidationResult Topology::validate() const {
    ValidationResult result;
    if (square_count_ == 0) {
        result.errors.emplace_back("topology must contain at least one square");
    }

    for (std::size_t i = 0; i < contacts_.size(); ++i) {
        const auto& contact = contacts_[i];
        const std::string prefix = "contact " + std::to_string(i) + ": ";

        if (!valid_feature(contact.a, square_count_)) {
            result.errors.push_back(prefix + "invalid first feature");
            continue;
        }

        if (contact.kind == ContactKind::Wall) {
            if (contact.b.has_value()) {
                result.errors.push_back(prefix + "wall contact must not have a second square feature");
            }
            if (!contact.wall.has_value() || *contact.wall >= 4) {
                result.errors.push_back(prefix + "wall contact must reference wall 0..3");
            }
        } else {
            if (!contact.b.has_value()) {
                result.errors.push_back(prefix + "square-square contact is missing second feature");
                continue;
            }
            if (contact.wall.has_value()) {
                result.errors.push_back(prefix + "square-square contact must not reference a wall");
            }
            if (!valid_feature(*contact.b, square_count_)) {
                result.errors.push_back(prefix + "invalid second feature");
                continue;
            }
            if (contact.a.square == contact.b->square) {
                result.errors.push_back(prefix + "a square cannot contact itself");
            }
            if (contact.kind != inferred_kind(contact.a.kind, contact.b->kind)) {
                result.errors.push_back(prefix + "contact kind does not match endpoint feature kinds");
            }
        }

        const auto normalized = normalized_contact(contact);
        for (std::size_t previous = 0; previous < i; ++previous) {
            if (normalized_contact(contacts_[previous]) == normalized) {
                result.errors.push_back(prefix + "duplicate contact event");
                break;
            }
        }
    }

    return result;
}

Topology Topology::normalized() const {
    Topology result(square_count_);
    result.contacts_.reserve(contacts_.size());
    for (const auto& contact : contacts_) {
        result.contacts_.push_back(normalized_contact(contact));
    }
    std::sort(
        result.contacts_.begin(),
        result.contacts_.end(),
        [](const Contact& lhs, const Contact& rhs) {
            return contact_key(lhs) < contact_key(rhs);
        }
    );
    return result;
}

Contact make_square_contact(FeatureRef a, FeatureRef b) {
    Contact contact{
        .kind = inferred_kind(a.kind, b.kind),
        .a = a,
        .b = b,
        .wall = std::nullopt,
    };
    return normalized_contact(std::move(contact));
}

Contact make_wall_contact(FeatureRef feature, std::uint8_t wall) {
    return Contact{
        .kind = ContactKind::Wall,
        .a = feature,
        .b = std::nullopt,
        .wall = wall,
    };
}

std::string to_string(FeatureKind kind) {
    switch (kind) {
        case FeatureKind::Corner:
            return "corner";
        case FeatureKind::Side:
            return "side";
    }
    throw std::logic_error("unknown FeatureKind");
}

std::string to_string(ContactKind kind) {
    switch (kind) {
        case ContactKind::CornerCorner:
            return "corner-corner";
        case ContactKind::CornerSide:
            return "corner-side";
        case ContactKind::SideSide:
            return "side-side";
        case ContactKind::Wall:
            return "wall";
    }
    throw std::logic_error("unknown ContactKind");
}

std::string contact_key(const Contact& raw_contact) {
    const Contact contact = normalized_contact(raw_contact);
    std::ostringstream out;
    out << static_cast<int>(contact.kind) << ':'
        << contact.a.square << ':'
        << static_cast<int>(contact.a.kind) << ':'
        << static_cast<int>(contact.a.index);

    if (contact.kind == ContactKind::Wall) {
        out << "|w:" << (contact.wall.has_value() ? static_cast<int>(*contact.wall) : -1);
    } else if (contact.b.has_value()) {
        out << '|'
            << contact.b->square << ':'
            << static_cast<int>(contact.b->kind) << ':'
            << static_cast<int>(contact.b->index);
    } else {
        out << "|missing";
    }
    return out.str();
}

std::vector<D4Transform> all_d4_transforms() {
    std::vector<D4Transform> result;
    result.reserve(8);
    for (std::uint8_t rotation = 0; rotation < 4; ++rotation) {
        result.push_back(D4Transform{.rotation = rotation, .reflected = false});
        result.push_back(D4Transform{.rotation = rotation, .reflected = true});
    }
    return result;
}

std::uint8_t feature_ring_index(FeatureRef feature) {
    if (feature.index >= 4) {
        throw std::invalid_argument("feature index must be in 0..3");
    }
    return static_cast<std::uint8_t>(
        2 * feature.index + (feature.kind == FeatureKind::Side ? 1 : 0)
    );
}

FeatureRef feature_from_ring_index(SquareId square, std::uint8_t ring_index) {
    if (ring_index >= 8) {
        throw std::invalid_argument("ring index must be in 0..7");
    }
    const bool side = (ring_index & 1U) != 0;
    return FeatureRef{
        .square = square,
        .kind = side ? FeatureKind::Side : FeatureKind::Corner,
        .index = static_cast<std::uint8_t>(ring_index / 2),
    };
}

FeatureRef transform_feature(FeatureRef feature, D4Transform transform) {
    if (transform.rotation >= 4) {
        throw std::invalid_argument("D4 rotation must be in 0..3");
    }
    int ring = static_cast<int>(feature_ring_index(feature));
    if (transform.reflected) {
        ring = (8 - ring) % 8;
    }
    ring = (ring + 2 * static_cast<int>(transform.rotation)) % 8;
    return feature_from_ring_index(feature.square, static_cast<std::uint8_t>(ring));
}

std::uint8_t transform_wall(std::uint8_t wall, D4Transform transform) {
    if (wall >= 4 || transform.rotation >= 4) {
        throw std::invalid_argument("wall/rotation index outside D4 domain");
    }
    int mapped = static_cast<int>(wall);
    if (transform.reflected) {
        mapped = (4 - mapped) % 4;
    }
    mapped = (mapped + static_cast<int>(transform.rotation)) % 4;
    return static_cast<std::uint8_t>(mapped);
}

Topology relabel_square(
    const Topology& topology,
    SquareId square,
    D4Transform transform
) {
    if (square >= topology.square_count()) {
        throw std::invalid_argument("square index outside topology");
    }
    Topology result = topology;
    for (auto& contact : result.contacts()) {
        if (contact.a.square == square) {
            contact.a = transform_feature(contact.a, transform);
        }
        if (contact.b.has_value() && contact.b->square == square) {
            *contact.b = transform_feature(*contact.b, transform);
        }
        contact = normalized_contact(std::move(contact));
    }
    return result.normalized();
}

Topology relabel_container(
    const Topology& topology,
    D4Transform transform
) {
    Topology result = topology;
    for (auto& contact : result.contacts()) {
        if (contact.kind == ContactKind::Wall && contact.wall.has_value()) {
            contact.wall = transform_wall(*contact.wall, transform);
        }
    }
    return result.normalized();
}

Topology permute_squares(
    const Topology& topology,
    const std::vector<SquareId>& old_to_new
) {
    if (old_to_new.size() != topology.square_count()) {
        throw std::invalid_argument("square permutation has wrong size");
    }

    std::vector<bool> seen(topology.square_count(), false);
    for (const auto value : old_to_new) {
        if (value >= topology.square_count() || seen[value]) {
            throw std::invalid_argument("square permutation is not a bijection");
        }
        seen[value] = true;
    }

    Topology result(topology.square_count());
    for (auto contact : topology.contacts()) {
        contact.a.square = old_to_new[contact.a.square];
        if (contact.b.has_value()) {
            contact.b->square = old_to_new[contact.b->square];
        }
        result.add_contact(std::move(contact));
    }
    return result.normalized();
}

}  // namespace sqtopology
