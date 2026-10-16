#include "sqtopology/rewrite.hpp"

#include <algorithm>
#include <sstream>
#include <stdexcept>

namespace sqtopology {
namespace {

bool contains_contact(const Topology& topology, const Contact& contact) {
    return std::find(topology.contacts().begin(), topology.contacts().end(), contact)
        != topology.contacts().end();
}

std::string square_contact_label(
    const Contact& contact,
    SquareId a,
    std::uint8_t a_ring,
    SquareId b,
    std::uint8_t b_ring
) {
    std::ostringstream label;
    label << "add " << to_string(contact.kind)
          << " s" << a << "/p" << static_cast<int>(a_ring)
          << " s" << b << "/p" << static_cast<int>(b_ring);
    return label.str();
}

std::string wall_contact_label(
    SquareId square,
    std::uint8_t ring,
    std::uint8_t wall
) {
    std::ostringstream label;
    label << "add wall s" << square
          << "/p" << static_cast<int>(ring)
          << " w" << static_cast<int>(wall);
    return label.str();
}

}  // namespace

std::vector<Rewrite> generate_rewrites(
    const Topology& input,
    const RewriteOptions& options
) {
    if (!input.validate().ok()) {
        throw std::invalid_argument("rewrite input topology is invalid");
    }
    return generate_rewrites_validated(input, options);
}

std::vector<Rewrite> generate_rewrites_validated(
    const Topology& input,
    const RewriteOptions& options
) {
    const Topology topology = input.normalized();
    std::vector<Rewrite> result;
    result.reserve(
        (options.include_removals ? topology.contacts().size() : 0U)
        + (options.include_additions ? options.max_additions : 0U)
    );

    if (options.include_removals) {
        for (std::size_t i = 0; i < topology.contacts().size(); ++i) {
            Topology child = topology;
            const auto removed = child.contacts()[i];
            child.contacts().erase(child.contacts().begin() + static_cast<std::ptrdiff_t>(i));
            result.push_back(
                Rewrite{
                    .kind = RewriteKind::RemoveContact,
                    .label = options.include_labels ? "remove " + contact_key(removed) : std::string{},
                    .topology = std::move(child),
                }
            );
        }
    }

    if (!options.include_additions || options.max_additions == 0) {
        return result;
    }

    std::size_t additions = 0;
    const auto append = [&](Contact contact, RewriteKind kind, std::string label) {
        if (additions >= options.max_additions || contains_contact(topology, contact)) {
            return;
        }

        Topology child = topology;
        child.add_contact(std::move(contact));

        result.push_back(
            Rewrite{
                .kind = kind,
                .label = std::move(label),
                .topology = child.normalized(),
            }
        );
        ++additions;
    };

    for (SquareId a = 0;
         a < topology.square_count() && additions < options.max_additions;
         ++a) {
        for (SquareId b = a + 1;
             b < topology.square_count() && additions < options.max_additions;
             ++b) {
            for (std::uint8_t a_ring = 0;
                 a_ring < 8 && additions < options.max_additions;
                 ++a_ring) {
                for (std::uint8_t b_ring = 0;
                     b_ring < 8 && additions < options.max_additions;
                     ++b_ring) {
                    const auto first = feature_from_ring_index(a, a_ring);
                    const auto second = feature_from_ring_index(b, b_ring);
                    auto contact = make_square_contact(first, second);

                    append(
                        contact,
                        RewriteKind::AddSquareContact,
                        options.include_labels
                            ? square_contact_label(contact, a, a_ring, b, b_ring)
                            : std::string{}
                    );
                }
            }
        }
    }

    for (SquareId square = 0;
         square < topology.square_count() && additions < options.max_additions;
         ++square) {
        for (std::uint8_t ring = 0;
             ring < 8 && additions < options.max_additions;
             ++ring) {
            for (std::uint8_t wall = 0;
                 wall < 4 && additions < options.max_additions;
                 ++wall) {
                const auto feature = feature_from_ring_index(square, ring);
                auto contact = make_wall_contact(feature, wall);

                append(
                    contact,
                    RewriteKind::AddWallContact,
                    options.include_labels
                        ? wall_contact_label(square, ring, wall)
                        : std::string{}
                );
            }
        }
    }

    return result;
}

}  // namespace sqtopology
