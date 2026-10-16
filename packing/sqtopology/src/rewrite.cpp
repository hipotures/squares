#include "sqtopology/rewrite.hpp"

#include <sstream>
#include <unordered_set>

namespace sqtopology {

std::vector<Rewrite> generate_rewrites(
    const Topology& input,
    const RewriteOptions& options
) {
    const Topology topology = input.normalized();
    std::vector<Rewrite> result;

    if (options.include_removals) {
        for (std::size_t i = 0; i < topology.contacts().size(); ++i) {
            Topology child = topology;
            const auto removed = child.contacts()[i];
            child.contacts().erase(child.contacts().begin() + static_cast<std::ptrdiff_t>(i));
            result.push_back(
                Rewrite{
                    .kind = RewriteKind::RemoveContact,
                    .label = "remove " + contact_key(removed),
                    .topology = child.normalized(),
                }
            );
        }
    }

    if (!options.include_additions || options.max_additions == 0) {
        return result;
    }

    std::unordered_set<std::string> existing;
    existing.reserve(topology.contacts().size() * 2U + 1U);
    for (const auto& contact : topology.contacts()) {
        existing.insert(contact_key(contact));
    }

    std::size_t additions = 0;
    const auto append = [&](Contact contact, RewriteKind kind, std::string label) {
        const auto key = contact_key(contact);
        if (existing.contains(key) || additions >= options.max_additions) {
            return;
        }
        Topology child = topology;
        child.add_contact(std::move(contact));
        const auto validation = child.validate();
        if (!validation.ok()) {
            return;
        }
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
                    std::ostringstream label;
                    label << "add " << to_string(contact.kind)
                          << " s" << a << "/p" << static_cast<int>(a_ring)
                          << " s" << b << "/p" << static_cast<int>(b_ring);
                    append(
                        std::move(contact),
                        RewriteKind::AddSquareContact,
                        label.str()
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
                std::ostringstream label;
                label << "add wall s" << square
                      << "/p" << static_cast<int>(ring)
                      << " w" << static_cast<int>(wall);
                append(
                    std::move(contact),
                    RewriteKind::AddWallContact,
                    label.str()
                );
            }
        }
    }

    return result;
}

}  // namespace sqtopology
