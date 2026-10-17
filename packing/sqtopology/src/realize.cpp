#include "sqtopology/realize.hpp"

#include "sqtopology/fixtures.hpp"

#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <functional>
#include <map>
#include <mutex>
#include <optional>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <thread>
#include <utility>
#include <vector>

namespace sqtopology {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kContainmentTolerance = 1e-9;

std::uint64_t corner_node(SquareId square, std::uint8_t corner) {
    return static_cast<std::uint64_t>(square) * 4U + corner;
}

std::uint64_t side_node(SquareId square, std::uint8_t side) {
    return static_cast<std::uint64_t>(square) * 4U + side;
}

bool set_difference_empty(
    const std::vector<std::string>& required,
    const std::vector<std::string>& present,
    std::vector<std::string>& missing
) {
    std::set<std::string> present_set(present.begin(), present.end());
    for (const auto& key : required) {
        if (present_set.count(key) == 0U) {
            missing.push_back(key);
        }
    }
    return missing.empty();
}

std::vector<std::string> keys_not_required(
    const std::vector<std::string>& present,
    const std::vector<std::string>& required
) {
    std::set<std::string> required_set(required.begin(), required.end());
    std::vector<std::string> extras;
    for (const auto& key : present) {
        if (required_set.count(key) == 0U) {
            extras.push_back(key);
        }
    }
    return extras;
}

std::uint64_t sampled_seed(std::uint64_t base, const std::vector<std::string>& keys) {
    std::uint64_t hash = 1469598103934665603ULL;
    for (const auto& key : keys) {
        for (const unsigned char byte : key) {
            hash ^= byte;
            hash *= 1099511628211ULL;
        }
    }
    return base ^ hash;
}

}  // namespace

std::string to_string(RealizabilityStatus status) {
    switch (status) {
        case RealizabilityStatus::VerifiedFeasible:
            return "VERIFIED_FEASIBLE";
        case RealizabilityStatus::NotFound:
            return "NOT_FOUND";
        case RealizabilityStatus::ProvedInfeasible:
            return "PROVED_INFEASIBLE";
    }
    throw std::logic_error("unknown realizability status");
}

InfeasibilityFilter static_infeasibility_filters(const Topology& sigma) {
    InfeasibilityFilter result;

    // R1: one side required on two distinct wall lines.
    std::map<std::uint64_t, std::set<std::uint8_t>> side_walls;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        if (contact.a.kind == FeatureKind::Side) {
            auto& walls = side_walls[side_node(contact.a.square, contact.a.index)];
            walls.insert(*contact.wall);
            if (walls.size() >= 2U) {
                std::ostringstream message;
                message << "R1: side " << static_cast<int>(contact.a.index)
                        << " of square " << contact.a.square
                        << " is required on walls";
                for (const auto wall : walls) {
                    message << ' ' << static_cast<int>(wall);
                }
                result.proved = true;
                result.reason = message.str();
                return result;
            }
        }
    }

    // R2: union-find over corner coincidences and wall memberships.
    std::vector<std::uint64_t> parent;
    std::size_t nodes = static_cast<std::size_t>(sigma.square_count()) * 4U;
    if (nodes > 0) {
        parent.resize(nodes);
        for (std::size_t node = 0; node < nodes; ++node) {
            parent[node] = node;
        }
    }
    const auto find_root = [&parent](std::uint64_t node) {
        while (parent[node] != node) {
            parent[node] = parent[parent[node]];
            node = parent[node];
        }
        return node;
    };
    const auto unite = [&parent, &find_root](std::uint64_t first, std::uint64_t second) {
        const std::uint64_t root_first = find_root(first);
        const std::uint64_t root_second = find_root(second);
        if (root_first != root_second) {
            parent[root_second] = root_first;
        }
    };
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind == ContactKind::CornerCorner && contact.b.has_value()) {
            unite(
                corner_node(contact.a.square, contact.a.index),
                corner_node(contact.b->square, contact.b->index)
            );
        }
    }
    std::map<std::uint64_t, std::set<std::uint8_t>> class_walls;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        const auto add_wall = [&](SquareId square, std::uint8_t corner) {
            class_walls[find_root(corner_node(square, corner))].insert(*contact.wall);
        };
        if (contact.a.kind == FeatureKind::Corner) {
            add_wall(contact.a.square, contact.a.index);
        } else {
            add_wall(contact.a.square, contact.a.index);
            add_wall(contact.a.square, static_cast<std::uint8_t>((contact.a.index + 1U) % 4U));
        }
    }
    for (const auto& [root, walls] : class_walls) {
        for (const auto wall : walls) {
            if (walls.count(static_cast<std::uint8_t>((wall + 2U) % 4U)) != 0U) {
                std::ostringstream message;
                message << "R2: coincident corner class contains opposite walls "
                        << static_cast<int>(wall) << " and "
                        << static_cast<int>((wall + 2U) % 4U);
                result.proved = true;
                result.reason = message.str();
                return result;
            }
        }
    }

    // R3: one corner required on two opposite sides of one square.
    std::map<std::uint64_t, std::map<SquareId, std::set<std::uint8_t>>> corner_sides;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::CornerSide || !contact.b.has_value()) {
            continue;
        }
        const FeatureRef corner = contact.a.kind == FeatureKind::Corner
            ? contact.a
            : *contact.b;
        const FeatureRef side = contact.a.kind == FeatureKind::Side
            ? contact.a
            : *contact.b;
        auto& by_square = corner_sides[corner_node(corner.square, corner.index)];
        auto& sides = by_square[side.square];
        sides.insert(side.index);
        if (sides.count(static_cast<std::uint8_t>((side.index + 2U) % 4U)) != 0U) {
            std::ostringstream message;
            message << "R3: corner " << static_cast<int>(corner.index)
                    << " of square " << corner.square
                    << " is required on opposite sides of square " << side.square;
            result.proved = true;
            result.reason = message.str();
            return result;
        }
    }

    // R4-R6: exact-stratum absorption rules. These use only the required
    // wall events, so they are independent of the solver and invariant under
    // the full G_n action (endpoint adjacency and opposite pairs are D4
    // relations). They are stated for the tolerance-based extraction actually
    // implemented in geometry.cpp, not only for the exact continuum picture.
    std::map<std::uint64_t, std::set<std::uint8_t>> side_walls_required;
    std::map<std::uint64_t, std::set<std::uint8_t>> corner_walls_required;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        if (contact.a.kind == FeatureKind::Side) {
            side_walls_required[side_node(contact.a.square, contact.a.index)]
                .insert(*contact.wall);
        } else {
            corner_walls_required[corner_node(contact.a.square, contact.a.index)]
                .insert(*contact.wall);
        }
    }
    const auto has_corner_wall = [&corner_walls_required](
        SquareId square, std::uint8_t corner, std::uint8_t wall
    ) {
        const auto found = corner_walls_required.find(corner_node(square, corner % 4U));
        return found != corner_walls_required.end()
            && found->second.count(wall) != 0U;
    };

    // R4: a wall-side contact absorbs the wall-corner contacts of its own two
    // endpoints on that wall. Requiring both the side and an endpoint corner
    // as separate exact events is therefore contradictory.
    for (const auto& [node, walls] : side_walls_required) {
        const SquareId square = static_cast<SquareId>(node / 4U);
        const std::uint8_t side = static_cast<std::uint8_t>(node % 4U);
        for (const std::uint8_t wall : walls) {
            for (const std::uint8_t corner : {
                     side, static_cast<std::uint8_t>((side + 1U) % 4U)}) {
                if (has_corner_wall(square, corner, wall)) {
                    std::ostringstream message;
                    message << "R4: corner " << static_cast<int>(corner)
                            << " of square " << square
                            << " is an endpoint of side " << static_cast<int>(side)
                            << " required on wall " << static_cast<int>(wall)
                            << ", so the corner-wall event is absorbed";
                    result.proved = true;
                    result.reason = message.str();
                    return result;
                }
            }
        }
    }

    // R5: two adjacent corners of one square on the same wall put the whole
    // side between them on the wall, and its side-wall event absorbs both
    // corner-wall events.
    for (const auto& [node, walls] : corner_walls_required) {
        const SquareId square = static_cast<SquareId>(node / 4U);
        const std::uint8_t corner = static_cast<std::uint8_t>(node % 4U);
        for (const std::uint8_t wall : walls) {
            if (has_corner_wall(square, static_cast<std::uint8_t>((corner + 1U) % 4U), wall)) {
                std::ostringstream message;
                message << "R5: adjacent corners " << static_cast<int>(corner)
                        << " and " << static_cast<int>((corner + 1U) % 4U)
                        << " of square " << square
                        << " are required on wall " << static_cast<int>(wall)
                        << ", so the connecting side-wall event absorbs both";
                result.proved = true;
                result.reason = message.str();
                return result;
            }
        }
    }

    // R6: two opposite corners of one square on the same wall force the other
    // two corners to distance 1/sqrt(2) on either side of that wall line; one
    // of them is outside [0, L]^2. This is a containment violation far larger
    // than every extraction tolerance (1e-7), so it is tolerance-safe.
    for (const auto& [node, walls] : corner_walls_required) {
        const SquareId square = static_cast<SquareId>(node / 4U);
        const std::uint8_t corner = static_cast<std::uint8_t>(node % 4U);
        for (const std::uint8_t wall : walls) {
            if (has_corner_wall(square, static_cast<std::uint8_t>((corner + 2U) % 4U), wall)) {
                std::ostringstream message;
                message << "R6: opposite corners " << static_cast<int>(corner)
                        << " and " << static_cast<int>((corner + 2U) % 4U)
                        << " of square " << square
                        << " are required on wall " << static_cast<int>(wall)
                        << ", forcing another corner outside the container";
                result.proved = true;
                result.reason = message.str();
                return result;
            }
        }
    }

    // R7-R10: wall and orientation contradictions. These are stated directly in
    // terms of the extracted contact relations and are invariant under the
    // full G_n action (D4 preserves incidence, adjacency, opposition,
    // parallelism and perpendicularity).
    //
    // R7: one corner feature required on two distinct walls. Two opposite wall
    // segments are disjoint, so the point cannot lie on both. Two adjacent
    // walls meet at the container corner; containment forces the square's
    // interior wedge (90 degrees) into the container quadrant (90 degrees), and
    // one of the two incident sides ends up with both endpoints within the
    // contact tolerance of one wall (see the proof in the Phase-2 document).
    // That side-wall event absorbs the corresponding corner-wall event, so the
    // two corner events cannot both be exact.
    std::map<std::uint64_t, std::set<std::uint8_t>> corner_walls_r7;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        if (contact.a.kind == FeatureKind::Corner) {
            corner_walls_r7[corner_node(contact.a.square, contact.a.index)]
                .insert(*contact.wall);
        }
    }
    for (const auto& [node, walls] : corner_walls_r7) {
        if (walls.size() >= 2U) {
            const SquareId square = static_cast<SquareId>(node / 4U);
            const std::uint8_t corner = static_cast<std::uint8_t>(node % 4U);
            std::ostringstream message;
            message << "R7: corner " << static_cast<int>(corner)
                    << " of square " << square << " is required on walls";
            for (const std::uint8_t wall : walls) {
                message << ' ' << static_cast<int>(wall);
            }
            message << " simultaneously";
            result.proved = true;
            result.reason = message.str();
            return result;
        }
    }

    // R8: a corner and a non-incident side of the same square required on the
    // same wall. The corner-to-line distance of a non-incident side is exactly
    // 1, while both features being within the 1e-7 tolerance of the wall line
    // bounds that distance by 2e-7. (Incident sides are R4, where the distance
    // is zero and absorption applies instead.)
    std::map<std::uint64_t, std::set<std::uint8_t>> wall_corners_r8;
    std::map<std::uint64_t, std::set<std::uint8_t>> wall_sides_r8;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        if (contact.a.kind == FeatureKind::Corner) {
            wall_corners_r8[side_node(contact.a.square, *contact.wall)]
                .insert(contact.a.index);
        } else {
            wall_sides_r8[side_node(contact.a.square, *contact.wall)]
                .insert(contact.a.index);
        }
    }
    for (const auto& [node, corners] : wall_corners_r8) {
        const auto found = wall_sides_r8.find(node);
        if (found == wall_sides_r8.end()) {
            continue;
        }
        const SquareId square = static_cast<SquareId>(node / 4U);
        const std::uint8_t wall = static_cast<std::uint8_t>(node % 4U);
        for (const std::uint8_t corner : corners) {
            for (const std::uint8_t side : found->second) {
                const bool incident = corner == side
                    || corner == static_cast<std::uint8_t>((side + 1U) % 4U);
                if (incident) {
                    continue;
                }
                std::ostringstream message;
                message << "R8: corner " << static_cast<int>(corner)
                        << " and non-incident side " << static_cast<int>(side)
                        << " of square " << square
                        << " are required on wall " << static_cast<int>(wall)
                        << ", but their distance is 1";
                result.proved = true;
                result.reason = message.str();
                return result;
            }
        }
    }

    // R9: two distinct sides of one square on the same wall. Adjacent sides are
    // perpendicular, so their supporting lines cannot coincide; opposite sides
    // are parallel at distance 1, so the wall line cannot be within tolerance
    // of both. The contradiction is at distance 1 or 90 degrees, far above the
    // 1e-7 extraction tolerance.
    for (const auto& [node, sides] : wall_sides_r8) {
        if (sides.size() < 2U) {
            continue;
        }
        const SquareId square = static_cast<SquareId>(node / 4U);
        const std::uint8_t wall = static_cast<std::uint8_t>(node % 4U);
        std::ostringstream message;
        message << "R9: sides";
        for (const std::uint8_t side : sides) {
            message << ' ' << static_cast<int>(side);
        }
        message << " of square " << square
                << " are required on wall " << static_cast<int>(wall)
                << ", but distinct sides cannot share one line";
        result.proved = true;
        result.reason = message.str();
        return result;
    }

    // R10: orientation/parallelism cycle. Side-side contacts force two sides to
    // be parallel; wall-side contacts force a side parallel to a wall; inside a
    // square adjacent sides are perpendicular (opposite sides parallel). Assign
    // each side and wall an axis in Z_2 (mod 180 degrees) and reject a
    // contradiction. A conflict means two required directions differ by 90
    // degrees while the extraction tolerances allow at most O(1e-7) radians,
    // so this is tolerance-safe. The rule is invariant because D4 preserves
    // parallelism and perpendicularity.
    {
        const std::uint32_t square_count = sigma.square_count();
        const std::uint32_t wall_base = 4U * square_count;
        const std::uint32_t node_count = wall_base + 4U;
        std::vector<std::uint32_t> parent(node_count);
        std::vector<std::uint8_t> parity(node_count, 0);
        std::vector<std::uint8_t> rank(node_count, 0);
        for (std::uint32_t node = 0; node < node_count; ++node) {
            parent[node] = node;
        }
        const std::function<std::pair<std::uint32_t, std::uint8_t>(std::uint32_t)> find =
            [&](std::uint32_t node) {
                if (parent[node] == node) {
                    return std::make_pair(node, std::uint8_t{0});
                }
                const auto root = find(parent[node]);
                parity[node] ^= root.second;
                parent[node] = root.first;
                return std::make_pair(parent[node], parity[node]);
            };
        // rel=0: parallel (same axis), rel=1: perpendicular.
        const auto unite = [&](std::uint32_t first, std::uint32_t second,
                               std::uint8_t relation) {
            auto root_first = find(first);
            auto root_second = find(second);
            if (root_first.first == root_second.first) {
                return (root_first.second ^ root_second.second) == relation;
            }
            if (rank[root_first.first] < rank[root_second.first]) {
                std::swap(root_first, root_second);
            }
            parent[root_second.first] = root_first.first;
            parity[root_second.first] =
                root_first.second ^ root_second.second ^ relation;
            if (rank[root_first.first] == rank[root_second.first]) {
                ++rank[root_first.first];
            }
            return true;
        };
        bool consistent = true;
        // Wall axes: 0 and 2 horizontal, 1 and 3 vertical.
        consistent = consistent && unite(wall_base + 0U, wall_base + 2U, 0);
        consistent = consistent && unite(wall_base + 1U, wall_base + 3U, 0);
        consistent = consistent && unite(wall_base + 0U, wall_base + 1U, 1);
        for (SquareId square = 0; square < square_count && consistent; ++square) {
            for (std::uint8_t side = 0; side < 3U; ++side) {
                consistent = consistent && unite(
                    side_node(square, side),
                    side_node(square, static_cast<std::uint8_t>(side + 1U)),
                    1
                );
            }
        }
        for (const auto& contact : sigma.contacts()) {
            if (!consistent) {
                break;
            }
            if (contact.kind == ContactKind::SideSide && contact.b.has_value()) {
                consistent = consistent && unite(
                    side_node(contact.a.square, contact.a.index),
                    side_node(contact.b->square, contact.b->index),
                    0
                );
            } else if (contact.kind == ContactKind::Wall && contact.wall.has_value()
                       && contact.a.kind == FeatureKind::Side) {
                consistent = consistent && unite(
                    side_node(contact.a.square, contact.a.index),
                    wall_base + *contact.wall,
                    0
                );
            }
        }
        if (!consistent) {
            result.proved = true;
            result.reason =
                "R10: orientation cycle forces two required directions to be "
                "both parallel and perpendicular";
            return result;
        }
    }

    // R11-R13: coincidence and feature-metric contradictions. A corner-corner
    // chain identifies corner points within O(k * contact) of each other, where
    // k is the chain length (at most 4n). All conclusions below are separated
    // from the tolerance by a fixed distance (1 or sqrt(2)) or by the strict
    // CS interior margin (2e-6), so they are tolerance-safe for the square
    // counts this solver supports.
    //
    // R11: two distinct corners of one square in one CC class would coincide,
    // but their distance is 1 (adjacent) or sqrt(2) (opposite).
    std::map<std::uint64_t, std::vector<std::pair<SquareId, std::uint8_t>>> cc_members;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::CornerCorner || !contact.b.has_value()) {
            continue;
        }
        cc_members[find_root(corner_node(contact.a.square, contact.a.index))]
            .push_back({contact.a.square, contact.a.index});
        cc_members[find_root(corner_node(contact.b->square, contact.b->index))]
            .push_back({contact.b->square, contact.b->index});
    }
    for (auto& [root, members] : cc_members) {
        (void)root;
        std::sort(members.begin(), members.end());
        members.erase(std::unique(members.begin(), members.end()), members.end());
        std::map<SquareId, std::uint8_t> seen_corner;
        for (const auto& [square, corner] : members) {
            if (seen_corner.count(square) != 0U) {
                std::ostringstream message;
                message << "R11: corners " << static_cast<int>(seen_corner[square])
                        << " and " << static_cast<int>(corner) << " of square "
                        << square << " are forced to coincide by CC contacts";
                result.proved = true;
                result.reason = message.str();
                return result;
            }
            seen_corner[square] = corner;
        }
    }

    // R12: two corners of one square cannot both lie in the open interior of
    // the same side (of any square). Their mutual distance is at least 1,
    // while the open side has length at most 1 - 2 * interior = 1 - 2e-6.
    std::map<std::uint64_t, std::vector<std::pair<SquareId, std::uint8_t>>> side_corners;
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::CornerSide || !contact.b.has_value()) {
            continue;
        }
        const FeatureRef corner = contact.a.kind == FeatureKind::Corner
            ? contact.a
            : *contact.b;
        const FeatureRef side = contact.a.kind == FeatureKind::Side
            ? contact.a
            : *contact.b;
        side_corners[side_node(side.square, side.index)]
            .push_back({corner.square, corner.index});
    }
    for (const auto& [node, corners] : side_corners) {
        std::vector<std::pair<SquareId, std::uint8_t>> sorted = corners;
        std::sort(sorted.begin(), sorted.end());
        sorted.erase(std::unique(sorted.begin(), sorted.end()), sorted.end());
        std::map<SquareId, std::uint8_t> seen_corner;
        for (const auto& [square, corner] : sorted) {
            if (seen_corner.count(square) != 0U) {
                std::ostringstream message;
                message << "R12: two corners of square " << square
                        << " are required on the interior of one side feature";
                result.proved = true;
                result.reason = message.str();
                return result;
            }
            seen_corner[square] = corner;
        }
    }

    // R13: if a corner is CS-required on a side, every corner in its CC class
    // lies at that point. A corner of the side's own square that is not an
    // endpoint of the side is at distance 1 from the side line, so it cannot
    // coincide with the CS point.
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::CornerSide || !contact.b.has_value()) {
            continue;
        }
        const FeatureRef corner = contact.a.kind == FeatureKind::Corner
            ? contact.a
            : *contact.b;
        const FeatureRef side = contact.a.kind == FeatureKind::Side
            ? contact.a
            : *contact.b;
        const std::uint64_t root = find_root(corner_node(corner.square, corner.index));
        const auto found = cc_members.find(root);
        if (found == cc_members.end()) {
            continue;
        }
        for (const auto& [square, member_corner] : found->second) {
            if (square != side.square) {
                continue;
            }
            if (member_corner == side.index
                || member_corner == static_cast<std::uint8_t>((side.index + 1U) % 4U)) {
                continue;
            }
            std::ostringstream message;
            message << "R13: corner " << static_cast<int>(member_corner)
                    << " of square " << square
                    << " coincides (via CC) with a corner required on side "
                    << static_cast<int>(side.index)
                    << " of the same square, but its distance to that side is 1";
            result.proved = true;
            result.reason = message.str();
            return result;
        }
    }

    // R14: a corner-side contact on a side that is itself a wall-side contact
    // is impossible. The CS point is in the relative interior of the side, so
    // locally the side's square B occupies the inward half-neighbourhood of the
    // wall. A's 90-degree corner wedge at that point cannot be disjoint from B's
    // interior: inward means overlap, outward means A crosses the container
    // wall (unit sides are far larger than the contact tolerance), and tangent
    // puts both interiors on the same side of the wall with a shared boundary
    // segment, again an interior overlap. This is a local, tolerance-safe
    // argument; no accumulated chain of tolerances is used.
    for (const auto& contact : sigma.contacts()) {
        if (contact.kind != ContactKind::CornerSide || !contact.b.has_value()) {
            continue;
        }
        const FeatureRef side = contact.a.kind == FeatureKind::Side
            ? contact.a
            : *contact.b;
        const auto found = side_walls_required.find(side_node(side.square, side.index));
        if (found == side_walls_required.end() || found->second.empty()) {
            continue;
        }
        const FeatureRef corner = contact.a.kind == FeatureKind::Corner
            ? contact.a
            : *contact.b;
        std::ostringstream message;
        message << "R14: corner " << static_cast<int>(corner.index)
                << " of square " << corner.square
                << " is required on side " << static_cast<int>(side.index)
                << " of square " << side.square
                << ", which is required on wall "
                << static_cast<int>(*found->second.begin())
                << "; the two interiors cannot both stay inside the container";
        result.proved = true;
        result.reason = message.str();
        return result;
    }

    return result;
}

WitnessReport verify_witness(
    const Scene& scene,
    const Topology& sigma,
    const ContactTolerances& tolerances
) {
    WitnessReport report;
    const double container = scene.container_side;

    for (const auto& pose : scene.squares) {
        for (std::uint8_t corner = 0; corner < 4; ++corner) {
            const Vec2 point = corner_position(pose, corner);
            if (point.x < -kContainmentTolerance
                || point.x > container + kContainmentTolerance
                || point.y < -kContainmentTolerance
                || point.y > container + kContainmentTolerance) {
                report.contained = false;
                break;
            }
        }
    }

    bool have_pair = false;
    double minimum_slack = std::numeric_limits<double>::infinity();
    for (SquareId first = 0; first < scene.squares.size(); ++first) {
        for (SquareId second = first + 1U; second < scene.squares.size(); ++second) {
            const SatResult sat = sat_separation(
                scene.squares[first],
                scene.squares[second],
                tolerances.contact
            );
            minimum_slack = std::min(minimum_slack, sat.slack);
            have_pair = true;
            if (!sat.interior_disjoint) {
                report.separated = false;
            }
        }
    }
    report.min_separation_slack = have_pair
        ? minimum_slack
        : std::numeric_limits<double>::infinity();

    const ExtractionResult extraction = extract_contacts(scene, tolerances);
    const std::vector<std::string> required = sorted_contact_keys(sigma.contacts());
    const std::vector<std::string> exact_keys = sorted_contact_keys(extraction.exact);
    const std::vector<std::string> weak_keys = sorted_contact_keys(extraction.weak);

    set_difference_empty(required, exact_keys, report.missing_exact);
    report.extra_exact = keys_not_required(exact_keys, required);
    set_difference_empty(required, weak_keys, report.missing_weak);

    report.exact_accepted = report.contained && report.separated
        && report.missing_exact.empty() && report.extra_exact.empty();
    report.weak_accepted = report.contained && report.separated
        && report.missing_weak.empty();

    // Diagnostic: the smallest margin over exact relations that are present in
    // the scene but not required (absorption already discounted). Large margins
    // mean the witness is unambiguous; a missing value means no candidate at
    // all, which is the ideal case for an exactly verified witness.
    std::set<std::string> required_set(required.begin(), required.end());
    for (const auto& margin : scene_contact_margins(scene, tolerances)) {
        if (!margin.exact_held || margin.absorbed) {
            continue;
        }
        const std::string key = contact_key(margin.contact);
        if (required_set.count(key) != 0U) {
            continue;
        }
        if (!report.has_extra_margin || margin.margin < report.min_extra_margin) {
            report.has_extra_margin = true;
            report.min_extra_margin = margin.margin;
        }
    }

    return report;
}

std::string scene_to_json(const Scene& scene) {
    std::ostringstream out;
    out.precision(17);
    out << "{\"container_side\":" << scene.container_side << ",\"squares\":[";
    for (std::size_t index = 0; index < scene.squares.size(); ++index) {
        if (index != 0U) {
            out << ',';
        }
        const auto& pose = scene.squares[index];
        out << "{\"x\":" << pose.x << ",\"y\":" << pose.y
            << ",\"theta\":" << pose.theta
            << ",\"frame_reflected\":" << (pose.frame_reflected ? "true" : "false")
            << '}';
    }
    out << "]}";
    return out.str();
}

std::string topology_contact_keys_json(const Topology& topology) {
    const auto keys = sorted_contact_keys(topology.contacts());
    std::ostringstream out;
    out << '[';
    for (std::size_t index = 0; index < keys.size(); ++index) {
        if (index != 0U) {
            out << ',';
        }
        out << '"' << keys[index] << '"';
    }
    out << ']';
    return out.str();
}

namespace {

// ---------------------------------------------------------------------------
// Solver internals. The residual/penalty formulation below is deliberately
// separate from the geometric predicates in geometry.cpp: the optimizer only
// proposes, the verifier decides.
// ---------------------------------------------------------------------------

constexpr double kMinSideOverlap = 5e-6;    // target overlap for side-side
constexpr double kWallEndMargin = 1e-3;     // keep corner-wall contacts off wall ends
constexpr double kStraySlack = 2e-3;        // push non-required features off walls
constexpr double kStrayWeight = 0.25;
constexpr double kSatWeight = 1.0;
constexpr double kResidualTarget = 1e-10;

struct SplitMix64 {
    std::uint64_t state{0};

    std::uint64_t next() {
        state += 0x9e3779b97f4a7c15ULL;
        std::uint64_t value = state;
        value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
        value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
        return value ^ (value >> 31);
    }

    double uniform() {
        return static_cast<double>(next() >> 11) * (1.0 / 9007199254740992.0);
    }

    double uniform(double low, double high) {
        return low + (high - low) * uniform();
    }

    std::uint32_t index(std::uint32_t count) {
        return count == 0U ? 0U : static_cast<std::uint32_t>(next() % count);
    }
};

struct SolverModel {
    std::uint32_t square_count{0};
    double container_side{0.0};
    std::vector<Contact> contacts;
    std::vector<std::optional<std::size_t>> tau_of_contact;
    std::size_t tau_count{0};
    // Per square: side/corner requirement masks per wall.
    std::vector<std::array<std::array<bool, 4>, 4>> side_wall_required;
    std::vector<std::array<std::array<bool, 4>, 4>> corner_wall_required;

    [[nodiscard]] std::size_t dimension() const {
        return 3U * square_count + tau_count;
    }
};

std::size_t solver_residual_size(const SolverModel& model) {
    std::size_t count = 0;
    for (const auto& contact : model.contacts) {
        switch (contact.kind) {
            case ContactKind::CornerCorner:
            case ContactKind::CornerSide:
                count += 2;
                break;
            case ContactKind::SideSide:
                count += 3;
                break;
            case ContactKind::Wall:
                count += contact.a.kind == FeatureKind::Side ? 2U : 3U;
                break;
        }
    }
    const std::size_t pairs =
        static_cast<std::size_t>(model.square_count) * (model.square_count - 1U) / 2U;
    count += 4U * pairs;                    // SAT penalties
    count += 16U * model.square_count;      // containment hinges
    count += 32U * model.square_count;      // stray side + corner pressures
    return count;
}

// Maximum absolute value over the contact residuals only, walking the same
// push order as evaluate_residuals. This is the cheap gate that decides when
// an LM outcome is worth handing to the independent verifier: soft terms
// (containment hinges, SAT penalties, stray pressures, wall-end margins) stay
// out of the gate because an exact witness may legitimately carry some of them.
double hard_residual_max(const SolverModel& model, const std::vector<double>& residuals) {
    std::size_t position = 0;
    double maximum = 0.0;
    const auto take = [&maximum, &residuals](std::size_t start, std::size_t count) {
        for (std::size_t index = start; index < start + count; ++index) {
            maximum = std::max(maximum, std::abs(residuals[index]));
        }
    };
    for (const auto& contact : model.contacts) {
        switch (contact.kind) {
            case ContactKind::CornerCorner:
            case ContactKind::CornerSide:
                take(position, 2);
                position += 2;
                break;
            case ContactKind::SideSide:
                take(position, 2);  // collinearity pair; the overlap hinge is soft
                position += 3;
                break;
            case ContactKind::Wall:
                if (contact.a.kind == FeatureKind::Side) {
                    take(position, 2);
                    position += 2;
                } else {
                    take(position, 1);
                    position += 3;
                }
                break;
        }
    }
    return maximum;
}

// Builds the solver-side model of a topology at one container side. The
// required wall masks are used only to switch off the stray pressures for the
// features that are legitimately supposed to touch a wall.
SolverModel build_solver_model(const Topology& sigma, double container_side) {
    SolverModel model;
    model.square_count = sigma.square_count();
    model.container_side = container_side;
    model.contacts = sigma.normalized().contacts();
    model.tau_of_contact.assign(model.contacts.size(), std::nullopt);
    for (std::size_t index = 0; index < model.contacts.size(); ++index) {
        if (model.contacts[index].kind == ContactKind::CornerSide) {
            model.tau_of_contact[index] = model.tau_count++;
        }
    }
    const std::size_t square_count = model.square_count;
    model.side_wall_required.assign(square_count, std::array<std::array<bool, 4>, 4>{});
    model.corner_wall_required.assign(square_count, std::array<std::array<bool, 4>, 4>{});
    for (const auto& contact : model.contacts) {
        if (contact.kind != ContactKind::Wall || !contact.wall.has_value()) {
            continue;
        }
        const std::uint8_t wall = *contact.wall;
        if (contact.a.kind == FeatureKind::Side) {
            model.side_wall_required[contact.a.square][contact.a.index][wall] = true;
        } else {
            model.corner_wall_required[contact.a.square][contact.a.index][wall] = true;
        }
    }
    return model;
}

// The coordinate that runs along a wall segment: x on the horizontal walls
// (0 top, 2 bottom) and y on the vertical walls (1 right, 3 left).
double wall_free_coordinate(Vec2 point, std::uint8_t wall) noexcept {
    return (wall % 4U == 0U || wall % 4U == 2U) ? point.x : point.y;
}

// Side direction (from corner s to corner s+1) and midpoint, both computed
// from parity-aware corner positions so the frame gauge is respected.
Vec2 side_direction(const SquarePose& pose, std::uint8_t side) {
    const auto endpoints = side_endpoints(pose, side);
    const Vec2 direction = endpoints[1] - endpoints[0];
    const double length = norm(direction);
    return length > 0.0 ? (1.0 / length) * direction : Vec2{1.0, 0.0};
}

double side_direction_angle(const SquarePose& pose, std::uint8_t side) {
    const Vec2 direction = side_direction(pose, side);
    return std::atan2(direction.y, direction.x);
}

Vec2 side_midpoint(const SquarePose& pose, std::uint8_t side) {
    return side_midpoint_position(pose, side);
}

void evaluate_residuals(
    const SolverModel& model,
    const std::vector<double>& variables,
    std::vector<double>& residuals
) {
    std::size_t position = 0;
    const auto push = [&residuals, &position](double value) {
        residuals[position++] = value;
    };
    const auto pose = [&variables](SquareId square) {
        return SquarePose{
            variables[3U * square],
            variables[3U * square + 1U],
            variables[3U * square + 2U],
        };
    };

    for (std::size_t index = 0; index < model.contacts.size(); ++index) {
        const Contact& contact = model.contacts[index];
        switch (contact.kind) {
            case ContactKind::CornerCorner: {
                const Vec2 first = corner_position(pose(contact.a.square), contact.a.index);
                const Vec2 second =
                    corner_position(pose(contact.b->square), contact.b->index);
                push(first.x - second.x);
                push(first.y - second.y);
                break;
            }
            case ContactKind::CornerSide: {
                const FeatureRef corner = contact.a.kind == FeatureKind::Corner
                    ? contact.a
                    : *contact.b;
                const FeatureRef side = contact.a.kind == FeatureKind::Side
                    ? contact.a
                    : *contact.b;
                const Vec2 point = corner_position(pose(corner.square), corner.index);
                const auto segment = side_endpoints(pose(side.square), side.index);
                const double tau = variables[3U * model.square_count
                                             + *model.tau_of_contact[index]];
                const Vec2 target = segment[0] + tau * (segment[1] - segment[0]);
                push(point.x - target.x);
                push(point.y - target.y);
                break;
            }
            case ContactKind::SideSide: {
                const SquarePose first_pose = pose(contact.a.square);
                const SquarePose second_pose = pose(contact.b->square);
                const std::uint8_t first_side = contact.a.index;
                const std::uint8_t second_side = contact.b->index;
                const Vec2 first_direction = side_direction(first_pose, first_side);
                const Vec2 second_direction = side_direction(second_pose, second_side);
                const Vec2 first_mid = side_midpoint(first_pose, first_side);
                const Vec2 second_mid = side_midpoint(second_pose, second_side);
                push(cross(first_direction, second_direction));
                push(cross(first_direction, second_mid - first_mid));
                const double shift = dot(second_mid - first_mid, first_direction);
                push(std::max(0.0, std::abs(shift) - (1.0 - kMinSideOverlap)));
                break;
            }
            case ContactKind::Wall: {
                const SquarePose feature_pose = pose(contact.a.square);
                const std::uint8_t wall = *contact.wall;
                const auto push_end_margins = [&](Vec2 point) {
                    const double along = wall_free_coordinate(point, wall);
                    push(std::max(0.0, kWallEndMargin - along));
                    push(std::max(0.0, along - (model.container_side - kWallEndMargin)));
                };
                if (contact.a.kind == FeatureKind::Side) {
                    // Both endpoints on the wall line. No end-margin hinge: a
                    // side-wall contact legitimately spans wall endpoint to
                    // wall endpoint in tight packings (grid fixtures), so an
                    // interior margin would contradict exact solutions.
                    const auto segment = side_endpoints(feature_pose, contact.a.index);
                    for (const Vec2 point : segment) {
                        push(wall_signed_distance(point, wall, model.container_side));
                    }
                } else {
                    const Vec2 point = corner_position(feature_pose, contact.a.index);
                    push(wall_signed_distance(point, wall, model.container_side));
                    push_end_margins(point);
                }
                break;
            }
        }
    }

    for (SquareId square = 0; square < model.square_count; ++square) {
        const SquarePose current = pose(square);
        for (std::uint8_t corner = 0; corner < 4; ++corner) {
            const Vec2 point = corner_position(current, corner);
            push(std::max(0.0, -point.x));
            push(std::max(0.0, point.x - model.container_side));
            push(std::max(0.0, -point.y));
            push(std::max(0.0, point.y - model.container_side));
        }
    }

    for (SquareId first = 0; first < model.square_count; ++first) {
        for (SquareId second = first + 1U; second < model.square_count; ++second) {
            const SquarePose first_pose = pose(first);
            const SquarePose second_pose = pose(second);
            const Vec2 delta{
                second_pose.x - first_pose.x,
                second_pose.y - first_pose.y,
            };
            // Separating-axis test: the squares are interior-disjoint as soon
            // as ONE of the four edge normals separates them, so the overlap
            // measure is minus the largest axis gap. Penalizing every axis
            // separately would create a fictitious force even for squares that
            // only touch along one axis.
            double gaps[4] = {0.0, 0.0, 0.0, 0.0};
            for (std::uint8_t axis = 0; axis < 4; ++axis) {
                const bool use_second = axis >= 2U;
                const double pose_angle = use_second ? second_pose.theta : first_pose.theta;
                const double quarter = (axis % 2U == 0U) ? 0.0 : 0.5 * kPi;
                const double angle = pose_angle + quarter;
                const Vec2 normal{std::cos(angle), std::sin(angle)};
                const double half_first = 0.5
                    * (std::abs(std::cos(angle - first_pose.theta))
                       + std::abs(std::sin(angle - first_pose.theta)));
                const double half_second = 0.5
                    * (std::abs(std::cos(angle - second_pose.theta))
                       + std::abs(std::sin(angle - second_pose.theta)));
                gaps[axis] = std::abs(dot(normal, delta)) - (half_first + half_second);
            }
            std::uint8_t best_axis = 0;
            for (std::uint8_t axis = 1; axis < 4; ++axis) {
                if (gaps[axis] > gaps[best_axis]) {
                    best_axis = axis;
                }
            }
            for (std::uint8_t axis = 0; axis < 4; ++axis) {
                push(axis == best_axis
                    ? kSatWeight * std::max(0.0, -gaps[axis])
                    : 0.0);
            }
        }
    }

    for (SquareId square = 0; square < model.square_count; ++square) {
        const SquarePose current = pose(square);
        for (std::uint8_t side = 0; side < 4; ++side) {
            const Vec2 midpoint = side_midpoint(current, side);
            for (std::uint8_t wall = 0; wall < 4; ++wall) {
                // Required contacts get a zero residual rather than being
                // skipped, so the residual count is exactly 32 per square.
                double pressure = 0.0;
                if (!model.side_wall_required[square][side][wall]) {
                    const double distance = std::abs(
                        wall_signed_distance(midpoint, wall, model.container_side)
                    );
                    pressure = std::max(0.0, kStraySlack - distance);
                }
                push(kStrayWeight * pressure);
            }
        }
        for (std::uint8_t corner = 0; corner < 4; ++corner) {
            const Vec2 point = corner_position(current, corner);
            for (std::uint8_t wall = 0; wall < 4; ++wall) {
                const bool endpoint_of_required_side =
                    model.side_wall_required[square][corner][wall]
                    || model.side_wall_required[square][(corner + 3U) % 4U][wall];
                double pressure = 0.0;
                if (!model.corner_wall_required[square][corner][wall]
                    && !endpoint_of_required_side) {
                    const double distance =
                        wall_segment_distance(point, wall, model.container_side);
                    pressure = std::max(0.0, kStraySlack - distance);
                }
                push(kStrayWeight * pressure);
            }
        }
    }
    if (position != residuals.size()) {
        throw std::logic_error("solver residual accounting mismatch");
    }
}

std::vector<double> flatten_scene(const SolverModel& model, const Scene& scene) {
    std::vector<double> variables(model.dimension(), 0.0);
    for (SquareId square = 0; square < model.square_count; ++square) {
        variables[3U * square] = scene.squares[square].x;
        variables[3U * square + 1U] = scene.squares[square].y;
        variables[3U * square + 2U] = scene.squares[square].theta;
    }
    for (std::size_t tau = 0; tau < model.tau_count; ++tau) {
        variables[3U * model.square_count + tau] = 0.5;
    }
    return variables;
}

Scene scene_from_variables(const SolverModel& model, const std::vector<double>& variables) {
    Scene scene;
    scene.container_side = model.container_side;
    scene.squares.resize(model.square_count);
    for (SquareId square = 0; square < model.square_count; ++square) {
        scene.squares[square] = SquarePose{
            variables[3U * square],
            variables[3U * square + 1U],
            variables[3U * square + 2U],
        };
    }
    return scene;
}

bool solve_linear_system(
    std::vector<double>& matrix,
    std::vector<double>& rhs,
    std::vector<double>& solution
) {
    const std::size_t size = rhs.size();
    for (std::size_t column = 0; column < size; ++column) {
        std::size_t pivot = column;
        for (std::size_t row = column + 1U; row < size; ++row) {
            if (std::abs(matrix[row * size + column])
                > std::abs(matrix[pivot * size + column])) {
                pivot = row;
            }
        }
        if (std::abs(matrix[pivot * size + column]) < 1e-14) {
            return false;
        }
        if (pivot != column) {
            for (std::size_t k = 0; k < size; ++k) {
                std::swap(matrix[pivot * size + k], matrix[column * size + k]);
            }
            std::swap(rhs[pivot], rhs[column]);
        }
        const double diagonal = matrix[column * size + column];
        for (std::size_t row = column + 1U; row < size; ++row) {
            const double factor = matrix[row * size + column] / diagonal;
            if (factor == 0.0) {
                continue;
            }
            for (std::size_t k = column; k < size; ++k) {
                matrix[row * size + k] -= factor * matrix[column * size + k];
            }
            rhs[row] -= factor * rhs[column];
        }
    }
    solution.assign(size, 0.0);
    for (std::size_t row = size; row-- > 0;) {
        double value = rhs[row];
        for (std::size_t k = row + 1U; k < size; ++k) {
            value -= matrix[row * size + k] * solution[k];
        }
        solution[row] = value / matrix[row * size + row];
    }
    return true;
}

struct LmOutcome {
    std::vector<double> variables;
    double max_abs{std::numeric_limits<double>::infinity()};
    double hard_max_abs{std::numeric_limits<double>::infinity()};
    std::uint32_t iterations{0};
};

LmOutcome run_lm(
    const SolverModel& model,
    std::vector<double> variables,
    std::uint32_t max_iterations
) {
    const std::size_t dimension = model.dimension();
    const std::size_t residual_count = solver_residual_size(model);
    std::vector<double> residuals(residual_count, 0.0);
    std::vector<double> perturbed(residual_count, 0.0);
    std::vector<double> jacobian(residual_count * dimension, 0.0);
    std::vector<double> normal(dimension * dimension, 0.0);
    std::vector<double> gradient(dimension, 0.0);
    std::vector<double> step;
    std::vector<double> candidate = variables;

    evaluate_residuals(model, variables, residuals);
    double cost = 0.0;
    for (const double value : residuals) {
        cost += value * value;
    }

    double lambda = 1e-3;
    LmOutcome outcome;
    std::uint32_t stagnant = 0;
    for (std::uint32_t iteration = 0; iteration < max_iterations; ++iteration) {
        outcome.iterations = iteration + 1U;
        double maximum = 0.0;
        for (const double value : residuals) {
            maximum = std::max(maximum, std::abs(value));
        }
        if (maximum < kResidualTarget) {
            break;
        }

        for (std::size_t column = 0; column < dimension; ++column) {
            candidate = variables;
            const double relative = std::max(1.0, std::abs(variables[column]));
            const double perturbation = 1e-7 * relative;
            candidate[column] += perturbation;
            evaluate_residuals(model, candidate, perturbed);
            for (std::size_t row = 0; row < residual_count; ++row) {
                jacobian[row * dimension + column] =
                    (perturbed[row] - residuals[row]) / perturbation;
            }
        }

        normal.assign(dimension * dimension, 0.0);
        gradient.assign(dimension, 0.0);
        for (std::size_t row = 0; row < residual_count; ++row) {
            for (std::size_t first = 0; first < dimension; ++first) {
                const double value = jacobian[row * dimension + first];
                if (value == 0.0) {
                    continue;
                }
                gradient[first] += value * residuals[row];
                for (std::size_t second = first; second < dimension; ++second) {
                    normal[first * dimension + second] +=
                        value * jacobian[row * dimension + second];
                }
            }
        }
        for (std::size_t first = 0; first < dimension; ++first) {
            for (std::size_t second = 0; second < first; ++second) {
                normal[first * dimension + second] =
                    normal[second * dimension + first];
            }
        }
        std::vector<double> damped = normal;
        for (std::size_t diagonal = 0; diagonal < dimension; ++diagonal) {
            damped[diagonal * dimension + diagonal] +=
                lambda * std::max(normal[diagonal * dimension + diagonal], 1e-6);
        }
        std::vector<double> rhs = gradient;
        for (double& value : rhs) {
            value = -value;
        }
        if (!solve_linear_system(damped, rhs, step)) {
            lambda *= 10.0;
            if (lambda > 1e12) {
                break;
            }
            continue;
        }

        candidate = variables;
        for (std::size_t index = 0; index < dimension; ++index) {
            candidate[index] += step[index];
        }
        // Keep corner-side parameters strictly inside their side.
        for (std::size_t tau = 0; tau < model.tau_count; ++tau) {
            candidate[3U * model.square_count + tau] =
                std::clamp(candidate[3U * model.square_count + tau], 0.05, 0.95);
        }
        evaluate_residuals(model, candidate, perturbed);
        double candidate_cost = 0.0;
        for (const double value : perturbed) {
            candidate_cost += value * value;
        }
        if (candidate_cost < cost) {
            variables = candidate;
            residuals = perturbed;
            cost = candidate_cost;
            lambda = std::max(1e-12, lambda * 0.3);
            stagnant = 0;
        } else {
            lambda *= 10.0;
            ++stagnant;
            if (lambda > 1e12 || stagnant >= 12U) {
                break;
            }
        }
    }

    outcome.variables = variables;
    outcome.max_abs = 0.0;
    for (std::size_t index = 0; index < residual_count; ++index) {
        outcome.max_abs = std::max(outcome.max_abs, std::abs(residuals[index]));
    }
    outcome.hard_max_abs = hard_residual_max(model, residuals);
    return outcome;
}

// Angle helpers for the required-driven start builder. The builder only has to
// land in the correct basin: LM refines the exact pose, so snapped 45-degree
// stances with a small jitter are enough and keep the starts deterministic.
double vector_angle(Vec2 v) {
    return std::atan2(v.y, v.x);
}

double snap_to_eighth_turn(double angle) {
    return 0.25 * kPi * std::round(angle / (0.25 * kPi));
}

double corner_offset_angle(std::uint8_t corner) {
    return 0.25 * kPi * (3.0 - 2.0 * static_cast<double>(corner % 4U));
}

// Stance that points corner `corner` toward `direction` (the corner offset
// must be antiparallel to it for a body placed behind the corner).
double corner_stance_toward(std::uint8_t corner, Vec2 direction) {
    const double target = vector_angle(direction);
    return snap_to_eighth_turn(target + kPi - corner_offset_angle(corner));
}

// Stance whose side `side` faces toward `direction` (its midpoint offset is
// parallel to `direction`).
double side_stance_toward(std::uint8_t side, Vec2 direction) {
    const double target = vector_angle(direction);
    return snap_to_eighth_turn(
        target - vector_angle(side_midpoint_offset(side))
    );
}

Scene build_required_driven_start(const SolverModel& model, SplitMix64& rng) {
    const double container = model.container_side;
    const Vec2 container_center{0.5 * container, 0.5 * container};
    Scene scene;
    scene.container_side = container;
    scene.squares.resize(model.square_count);
    for (auto& pose : scene.squares) {
        pose = SquarePose{
            rng.uniform(0.2 * container, 0.8 * container),
            rng.uniform(0.2 * container, 0.8 * container),
            rng.uniform(0.0, 2.0 * kPi),
        };
    }
    std::vector<bool> placed(model.square_count, false);

    const auto wall_outward = [](std::uint8_t wall) -> Vec2 {
        switch (wall) {
            case 0:
                return Vec2{0.0, 1.0};
            case 1:
                return Vec2{1.0, 0.0};
            case 2:
                return Vec2{0.0, -1.0};
            default:
                return Vec2{-1.0, 0.0};
        }
    };

    for (const auto& contact : model.contacts) {
        switch (contact.kind) {
            case ContactKind::Wall: {
                const SquareId square = contact.a.square;
                const std::uint8_t wall = *contact.wall;
                if (placed[square]) {
                    break;
                }
                const Vec2 outward = wall_outward(wall);
                const Vec2 tangent{outward.y, -outward.x};
                const double along = rng.uniform(-0.3, 0.3) * container;
                if (contact.a.kind == FeatureKind::Side) {
                    const double theta =
                        0.5 * kPi * static_cast<double>(contact.a.index - wall);
                    scene.squares[square] = SquarePose{
                        container_center.x + along * tangent.x - 0.5 * outward.x,
                        container_center.y + along * tangent.y - 0.5 * outward.y,
                        theta,
                    };
                } else {
                    // Point the required corner at the wall so the body falls
                    // inside the container; jitter keeps the starts distinct.
                    const double theta = corner_stance_toward(contact.a.index, outward)
                        + rng.uniform(-0.02, 0.02);
                    const Vec2 target{
                        container_center.x + along * tangent.x,
                        container_center.y + along * tangent.y,
                    };
                    const Vec2 offset = rotate(
                        corner_offset(contact.a.index),
                        theta
                    );
                    scene.squares[square] = SquarePose{
                        target.x - offset.x,
                        target.y - offset.y,
                        theta,
                    };
                }
                placed[square] = true;
                break;
            }
            case ContactKind::CornerCorner: {
                const SquareId first = contact.a.square;
                const SquareId second = contact.b->square;
                if (placed[first] == placed[second]) {
                    if (!placed[first]) {
                        const double theta = 0.25 * kPi * static_cast<double>(rng.index(8));
                        const Vec2 offset = rotate(corner_offset(contact.a.index), theta);
                        scene.squares[first] = SquarePose{
                            rng.uniform(0.3, 0.7) * container - offset.x,
                            rng.uniform(0.3, 0.7) * container - offset.y,
                            theta,
                        };
                        placed[first] = true;
                    } else {
                        break;
                    }
                }
                const bool first_placed = placed[first];
                const SquareId anchor = first_placed ? first : second;
                const SquareId other = first_placed ? second : first;
                const std::uint8_t anchor_corner =
                    first_placed ? contact.a.index : contact.b->index;
                const std::uint8_t other_corner =
                    first_placed ? contact.b->index : contact.a.index;
                const Vec2 anchor_point =
                    corner_position(scene.squares[anchor], anchor_corner);
                const Vec2 anchor_centre{
                    scene.squares[anchor].x,
                    scene.squares[anchor].y,
                };
                Vec2 away = anchor_point - anchor_centre;
                if (norm(away) <= 0.0) {
                    away = Vec2{1.0, 0.0};
                }
                const double theta = corner_stance_toward(other_corner, away)
                    + rng.uniform(-0.05, 0.05);
                const Vec2 offset = rotate(corner_offset(other_corner), theta);
                scene.squares[other] = SquarePose{
                    anchor_point.x - offset.x,
                    anchor_point.y - offset.y,
                    theta,
                };
                placed[other] = true;
                break;
            }
            case ContactKind::CornerSide: {
                const FeatureRef corner = contact.a.kind == FeatureKind::Corner
                    ? contact.a
                    : *contact.b;
                const FeatureRef side = contact.a.kind == FeatureKind::Side
                    ? contact.a
                    : *contact.b;
                if (placed[corner.square] && placed[side.square]) {
                    break;
                }
                if (!placed[corner.square] && !placed[side.square]) {
                    scene.squares[side.square].theta =
                        0.25 * kPi * static_cast<double>(rng.index(8));
                    placed[side.square] = true;
                }
                if (placed[corner.square]) {
                    // Side square goes on the far side of the known corner
                    // point, with the required side facing the corner body.
                    const Vec2 point =
                        corner_position(scene.squares[corner.square], corner.index);
                    Vec2 away{
                        point.x - scene.squares[corner.square].x,
                        point.y - scene.squares[corner.square].y,
                    };
                    if (norm(away) <= 0.0) {
                        away = Vec2{1.0, 0.0};
                    }
                    const double theta = side_stance_toward(side.index, away)
                        + rng.uniform(-0.02, 0.02);
                    const Vec2 offset = rotate(side_midpoint_offset(side.index), theta);
                    scene.squares[side.square] = SquarePose{
                        point.x - offset.x,
                        point.y - offset.y,
                        theta,
                    };
                    placed[side.square] = true;
                } else {
                    // Place the corner square outside the side square, with its
                    // required corner touching an interior point of the side.
                    const SquarePose side_pose = scene.squares[side.square];
                    const double side_angle = side_direction_angle(side_pose, side.index);
                    const Vec2 side_direction{std::cos(side_angle), std::sin(side_angle)};
                    const Vec2 outward{-side_direction.y, side_direction.x};
                    const Vec2 midpoint = side_midpoint(side_pose, side.index);
                    const double along = rng.uniform(-0.35, 0.35);
                    const Vec2 target = midpoint + along * side_direction;
                    const double theta = corner_stance_toward(corner.index, outward)
                        + rng.uniform(-0.02, 0.02);
                    const Vec2 offset = rotate(corner_offset(corner.index), theta);
                    scene.squares[corner.square] = SquarePose{
                        target.x - offset.x,
                        target.y - offset.y,
                        theta,
                    };
                    placed[corner.square] = true;
                }
                break;
            }
            case ContactKind::SideSide: {
                const SquareId first = contact.a.square;
                const SquareId second = contact.b->square;
                const std::uint8_t first_side = contact.a.index;
                const std::uint8_t second_side = contact.b->index;
                if (placed[first] && placed[second]) {
                    break;
                }
                if (!placed[first] && !placed[second]) {
                    scene.squares[first].theta = rng.uniform(0.0, 2.0 * kPi);
                    placed[first] = true;
                }
                const SquareId anchor = placed[first] ? first : second;
                const SquareId other = placed[first] ? second : first;
                const std::uint8_t anchor_side = placed[first] ? first_side : second_side;
                const std::uint8_t other_side = placed[first] ? second_side : first_side;
                const SquarePose anchor_pose = scene.squares[anchor];
                const double base_angle = side_direction_angle(anchor_pose, anchor_side);
                // The two sides must share a line and face each other: the
                // other square's side direction is antiparallel to the
                // anchor's, and its centre sits one full side length away
                // along the anchor side's outward normal.
                const double theta = base_angle + kPi
                    + 0.5 * kPi * static_cast<double>(other_side);
                const double shift = rng.uniform(-0.9, 0.9) * (1.0 - 2.0 * kMinSideOverlap);
                const Vec2 tangent{std::cos(base_angle), std::sin(base_angle)};
                const Vec2 outward{-tangent.y, tangent.x};
                scene.squares[other] = SquarePose{
                    anchor_pose.x + outward.x + shift * tangent.x,
                    anchor_pose.y + outward.y + shift * tangent.y,
                    theta,
                };
                placed[other] = true;
                break;
            }
        }
    }

    for (SquareId square = 0; square < model.square_count; ++square) {
        if (!placed[square]) {
            scene.squares[square] = SquarePose{
                rng.uniform(0.25 * container, 0.75 * container),
                rng.uniform(0.25 * container, 0.75 * container),
                rng.uniform(0.0, 2.0 * kPi),
            };
        }
    }
    return scene;
}

// Lattice start: lay the squares out on a rows x columns grid scaled to the
// container. At the tight side length L = ceil(sqrt(n)) this is exactly the
// tiling that realizes grid fixtures, a basin random starts almost never reach.
Scene build_grid_start(const SolverModel& model, SplitMix64& rng) {
    const double container = model.container_side;
    const std::uint32_t squares = model.square_count;
    const auto rows = static_cast<std::uint32_t>(
        std::ceil(std::sqrt(static_cast<double>(squares)))
    );
    const std::uint32_t columns =
        (squares + rows - 1U) / std::max(rows, 1U);
    const double cell_width = container / static_cast<double>(std::max(columns, 1U));
    const double cell_height = container / static_cast<double>(std::max(rows, 1U));
    Scene scene;
    scene.container_side = container;
    scene.squares.resize(squares);
    for (SquareId square = 0; square < squares; ++square) {
        const std::uint32_t row = square / std::max(columns, 1U);
        const std::uint32_t column = square % std::max(columns, 1U);
        const double jitter = 0.01 * container;
        scene.squares[square] = SquarePose{
            (static_cast<double>(column) + 0.5) * cell_width
                + rng.uniform(-jitter, jitter),
            container - (static_cast<double>(row) + 0.5) * cell_height
                + rng.uniform(-jitter, jitter),
            0.5 * kPi * static_cast<double>(rng.index(2)) + rng.uniform(-0.02, 0.02),
        };
    }
    return scene;
}

Scene build_random_start(const SolverModel& model, SplitMix64& rng, int mode) {
    const double container = model.container_side;
    Scene scene;
    scene.container_side = container;
    scene.squares.resize(model.square_count);
    for (SquareId square = 0; square < model.square_count; ++square) {
        double theta = 0.0;
        switch (mode) {
            case 1:  // axis aligned, coarse grid placement
                theta = 0.5 * kPi * static_cast<double>(rng.index(2));
                break;
            case 2:  // diagonal stances
                theta = 0.25 * kPi * static_cast<double>(2 * rng.index(4) + 1);
                break;
            default:  // free random
                theta = rng.uniform(0.0, 2.0 * kPi);
                break;
        }
        const double low = 0.35;
        const double high = std::max(low, container - 0.35);
        scene.squares[square] = SquarePose{
            rng.uniform(low, high),
            rng.uniform(low, high),
            theta + rng.uniform(-0.02, 0.02),
        };
    }
    return scene;
}

}  // namespace

std::vector<SceneFixture> scene_fixtures() {
    const double kCornerRadius = std::sqrt(2.0) / 2.0;
    std::vector<SceneFixture> fixtures;

    Scene isolated;
    isolated.container_side = 2.0;
    isolated.squares = {SquarePose{1.0, 1.0, 0.0}};
    fixtures.push_back(SceneFixture{
        "isolated-1", "", isolated, "single interior square has no contacts",
    });

    Scene disjoint;
    disjoint.container_side = 3.0;
    disjoint.squares = {SquarePose{0.75, 0.75, 0.0}, SquarePose{2.25, 2.25, 0.0}};
    fixtures.push_back(SceneFixture{
        "disjoint-2", "",
        disjoint,
        "two separated squares have no contacts",
    });

    Scene corner_corner;
    corner_corner.container_side = 3.0;
    corner_corner.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    fixtures.push_back(SceneFixture{
        "corner-corner-2", "corner-corner-2", corner_corner,
        "one diagonal corner point contact at (1.5, 1.5)",
    });

    Scene corner_side;
    corner_side.container_side = 3.0;
    corner_side.squares = {
        SquarePose{1.5 - kCornerRadius, 2.0, -kPi / 4.0},
        SquarePose{2.0, 2.0, 0.0},
    };
    fixtures.push_back(SceneFixture{
        "corner-side-2", "corner-side-2", corner_side,
        "corner 1 of square 0 on the interior of side 3 of square 1",
    });

    Scene side_side;
    side_side.container_side = 3.0;
    side_side.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 2.0, 0.0}};
    fixtures.push_back(SceneFixture{
        "side-side-2", "side-side-2", side_side,
        "full side overlap; endpoint corner contacts are absorbed",
    });

    Scene wall_corner;
    wall_corner.container_side = 3.0;
    wall_corner.squares = {SquarePose{1.5, 3.0 - kCornerRadius, -kPi / 4.0}};
    fixtures.push_back(SceneFixture{
        "wall-corner", "@wall-corner-single", wall_corner,
        "corner 0 touches the interior of wall 0",
    });

    Scene wall_side;
    wall_side.container_side = 3.0;
    wall_side.squares = {SquarePose{1.5, 2.5, 0.0}};
    fixtures.push_back(SceneFixture{
        "wall-side", "@wall-side-single", wall_side,
        "side 0 lies on the interior of wall 0",
    });

    for (const auto& name : {"grid-2x2", "grid-3x3", "grid-4x4"}) {
        const int side = name[5] - '0';
        Scene grid;
        grid.container_side = static_cast<double>(side);
        for (int row = 0; row < side; ++row) {
            for (int column = 0; column < side; ++column) {
                grid.squares.push_back(SquarePose{
                    static_cast<double>(column) + 0.5,
                    static_cast<double>(side - row) - 0.5,
                    0.0,
                });
            }
        }
        fixtures.push_back(SceneFixture{
            name, name, grid, "unit-cell grid scene",
        });
    }

    return fixtures;
}

Topology expected_fixture_topology(std::string_view name, std::uint32_t square_count) {
    if (name.empty()) {
        return Topology(square_count);
    }
    if (name == "@wall-corner-single") {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        return topology.normalized();
    }
    if (name == "@wall-side-single") {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        return topology.normalized();
    }
    const Topology fixture = make_fixture(name);
    if (fixture.square_count() != square_count) {
        throw std::invalid_argument(
            "fixture square count does not match the scene for " + std::string(name)
        );
    }
    return fixture;
}

std::vector<NegativeFixture> negative_fixtures() {    std::vector<NegativeFixture> fixtures;

    {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 1));
        fixtures.push_back(NegativeFixture{
            "N1-side-two-walls",
            topology.normalized(),
            RealizabilityStatus::ProvedInfeasible,
            "one side on two distinct walls (R1)",
        });
    }
    {
        Topology topology(2);
        topology.add_contact(make_square_contact(
            FeatureRef{0, FeatureKind::Corner, 0},
            FeatureRef{1, FeatureKind::Corner, 0}
        ));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{1, FeatureKind::Corner, 0}, 2));
        fixtures.push_back(NegativeFixture{
            "N2-cc-opposite-walls",
            topology.normalized(),
            RealizabilityStatus::ProvedInfeasible,
            "coincident corners forced onto opposite walls (R2)",
        });
    }
    {
        Topology topology(2);
        topology.add_contact(make_square_contact(
            FeatureRef{0, FeatureKind::Corner, 0},
            FeatureRef{1, FeatureKind::Side, 1}
        ));
        topology.add_contact(make_square_contact(
            FeatureRef{0, FeatureKind::Corner, 0},
            FeatureRef{1, FeatureKind::Side, 3}
        ));
        fixtures.push_back(NegativeFixture{
            "N3-corner-opposite-sides",
            topology.normalized(),
            RealizabilityStatus::ProvedInfeasible,
            "one corner on both members of an opposite side pair (R3)",
        });
    }
    {
        Topology topology(1);
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 0}, 0));
        topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Corner, 2}, 2));
        fixtures.push_back(NegativeFixture{
            "N4-corner-opposite-walls",
            topology.normalized(),
            RealizabilityStatus::NotFound,
            "corner 0 on the top wall and corner 2 on the bottom wall of one "
            "square: containment forces the square to be centered, which adds "
            "side-wall contacts, so no exact witness exists; the static filters "
            "cannot show it, hence NOT_FOUND",
        });
    }

    return fixtures;
}

namespace {

// One container-side solve attempt: deterministic start families, LM, and
// independent verification of every numerically plausible outcome.
struct ContainerAttempt {
    bool exact{false};
    Scene exact_scene;
    WitnessReport exact_report;
    bool weak{false};
    Scene weak_scene;
    WitnessReport weak_report;
    bool has_best{false};
    double best_hard{std::numeric_limits<double>::infinity()};
    Scene best_scene;
    WitnessReport best_report;
    double container_side{0.0};
};

// An LM outcome is handed to the verifier once its hard (contact) residual is
// at or below this value; anything above cannot pass the 1e-7 extraction
// tolerance anyway, but the best rejected candidate is still verified once at
// the end for diagnostics.
constexpr double kVerifyGate = 1e-6;

ContainerAttempt attempt_container(
    const Topology& sigma,
    double container_side,
    const SolveConfig& config,
    SplitMix64& rng,
    std::uint64_t& solves
) {
    ContainerAttempt attempt;
    attempt.container_side = container_side;
    const SolverModel model = build_solver_model(sigma, container_side);
    std::vector<double> variables;
    bool have_pending = false;
    double pending_hard = std::numeric_limits<double>::infinity();
    std::vector<double> pending_variables;

    for (std::uint32_t start = 0; start < config.starts_per_rung; ++start) {
        if (solves >= config.max_solves) {
            break;
        }
        Scene start_scene;
        switch (start % 5U) {
            case 0U:
                start_scene = build_required_driven_start(model, rng);
                break;
            case 1U:
                start_scene = build_random_start(model, rng, 1);
                break;
            case 2U:
                start_scene = build_random_start(model, rng, 2);
                break;
            case 3U:
                start_scene = build_grid_start(model, rng);
                break;
            default:
                start_scene = build_random_start(model, rng, 0);
                break;
        }
        variables = flatten_scene(model, start_scene);
        const LmOutcome outcome = run_lm(model, variables, config.lm_max_iterations);
        ++solves;
        if (outcome.hard_max_abs > kVerifyGate) {
            if (outcome.hard_max_abs < pending_hard) {
                pending_hard = outcome.hard_max_abs;
                pending_variables = outcome.variables;
                have_pending = true;
            }
            continue;
        }
        const Scene candidate = scene_from_variables(model, outcome.variables);
        const WitnessReport report = verify_witness(candidate, sigma);
        if (report.exact_accepted) {
            attempt.exact = true;
            attempt.exact_scene = candidate;
            attempt.exact_report = report;
            return attempt;
        }
        if (report.weak_accepted && !attempt.weak) {
            attempt.weak = true;
            attempt.weak_scene = candidate;
            attempt.weak_report = report;
        }
        if (!attempt.has_best || outcome.hard_max_abs < attempt.best_hard) {
            attempt.has_best = true;
            attempt.best_hard = outcome.hard_max_abs;
            attempt.best_scene = candidate;
            attempt.best_report = report;
        }
    }

    if (!attempt.has_best && have_pending) {
        attempt.best_scene = scene_from_variables(model, pending_variables);
        attempt.best_report = verify_witness(attempt.best_scene, sigma);
        attempt.best_hard = pending_hard;
        attempt.has_best = true;
    }
    return attempt;
}

}  // namespace

namespace {

// Outcome of solving one G_n-orbit representative in the standard feature
// frame. The 2^n gauge branches of a class are solved independently; a witness
// is transported back to the class representative with psi_g afterwards.
struct RepresentativeOutcome {
    bool exact{false};
    double exact_l{-1.0};
    Scene exact_scene;
    WitnessReport exact_report;
    bool weak{false};
    double weak_l{0.0};
    Scene weak_scene;
    WitnessReport weak_report;
    bool has_best{false};
    double best_hard{std::numeric_limits<double>::infinity()};
    Scene best_scene;
    WitnessReport best_report;
    double best_l{0.0};
    double bisection_lower{0.0};
};

RepresentativeOutcome solve_representative(
    const Topology& sigma,
    const SolveConfig& config,
    const std::vector<double>& ladder,
    SplitMix64& rng,
    std::uint64_t& total_solves
) {
    RepresentativeOutcome outcome;
    std::uint64_t branch_solves = 0;
    ContainerAttempt best;
    for (const double container_side : ladder) {
        if (branch_solves >= config.max_solves) {
            break;
        }
        ContainerAttempt attempt =
            attempt_container(sigma, container_side, config, rng, branch_solves);
        if (attempt.exact) {
            outcome.exact = true;
            outcome.exact_l = container_side;
            outcome.exact_scene = attempt.exact_scene;
            outcome.exact_report = attempt.exact_report;
            break;
        }
        if (attempt.weak && !outcome.weak) {
            outcome.weak = true;
            outcome.weak_l = container_side;
            outcome.weak_scene = attempt.weak_scene;
            outcome.weak_report = attempt.weak_report;
        }
        if (attempt.has_best && (!best.has_best || attempt.best_hard < best.best_hard)) {
            best = attempt;
        }
    }

    if (outcome.exact) {
        double lower = 0.0;
        double upper = outcome.exact_l;
        for (const double container_side : ladder) {
            if (container_side < outcome.exact_l) {
                lower = container_side;
            }
        }
        if (config.minimize_container) {
            for (std::uint32_t step = 0; step < config.minimization_steps; ++step) {
                if (branch_solves >= config.max_solves) {
                    break;
                }
                const double middle = 0.5 * (lower + upper);
                if (!(middle > lower) || !(middle < upper)) {
                    break;
                }
                ContainerAttempt attempt =
                    attempt_container(sigma, middle, config, rng, branch_solves);
                if (attempt.exact) {
                    upper = middle;
                    outcome.exact_scene = attempt.exact_scene;
                    outcome.exact_report = attempt.exact_report;
                    outcome.exact_l = middle;
                } else {
                    lower = middle;
                }
            }
        }
        outcome.bisection_lower = lower;
    } else if (best.has_best) {
        outcome.has_best = true;
        outcome.best_hard = best.best_hard;
        outcome.best_scene = best.best_scene;
        outcome.best_report = best.best_report;
        outcome.best_l = best.container_side;
    }
    total_solves += branch_solves;
    return outcome;
}

// H_n event permutations, cached per square count. H_n is the subgroup of
// parity-consistent elements where the scene action stays in the standard
// feature frame; solving one representative per H_n-orbit of gauge branches is
// exact because standard-frame realizability is H_n-invariant.
const std::vector<std::vector<EventId>>& h_n_event_permutations(std::uint32_t square_count) {
    static std::mutex cache_mutex;
    static std::map<std::uint32_t, std::vector<std::vector<EventId>>> cache;
    std::lock_guard<std::mutex> lock(cache_mutex);
    auto found = cache.find(square_count);
    if (found != cache.end()) {
        return found->second;
    }
    std::vector<std::vector<EventId>> permutations;
    const std::uint64_t elements = group_element_count(square_count);
    for (std::uint64_t index = 0; index < elements; ++index) {
        const GroupElement element = decode_group_element(square_count, index);
        bool consistent = true;
        for (SquareId square = 0; square < square_count; ++square) {
            if (element.local[square].reflected != element.container.reflected) {
                consistent = false;
                break;
            }
        }
        if (consistent) {
            permutations.push_back(event_permutation(element));
        }
    }
    return cache.emplace(square_count, std::move(permutations)).first->second;
}

std::vector<std::uint64_t> canonical_branch_key(const Topology& topology) {
    const EventBitset bitset = topology_to_event_bitset(topology);
    const auto& permutations = h_n_event_permutations(topology.square_count());
    std::vector<std::uint64_t> best;
    for (const auto& permutation : permutations) {
        EventBitset moved = permute_event_bitset(permutation, bitset);
        if (best.empty() || moved < best) {
            best = std::move(moved);
        }
    }
    return best;
}

GroupElement frame_branch_element(std::uint32_t square_count, std::uint32_t mask) {
    GroupElement element = identity_group_element(square_count);
    for (SquareId square = 0; square < square_count; ++square) {
        if ((mask & (1U << square)) != 0U) {
            element.local[square] = D4Element{0, true};
        }
    }
    return element;
}

}  // namespace

SolveResult realize_topology(const Topology& sigma, const SolveConfig& config) {
    SolveResult result;
    const auto validation = sigma.validate();
    if (!validation.ok()) {
        throw std::invalid_argument("realize_topology requires a valid topology");
    }
    const Topology normalized = sigma.normalized();
    if (normalized.square_count() == 0 || normalized.square_count() > kMaxOrbitSquares) {
        throw std::invalid_argument("realize_topology supports 1 <= square_count <= kMaxOrbitSquares");
    }

    // R1-R6 are invariants of the labelled incidence structure, hence of the
    // full G_n orbit (see static_infeasibility_filters). They are applied once
    // to the class representative and lifted to every gauge branch.
    const InfeasibilityFilter filter = static_infeasibility_filters(normalized);
    if (filter.proved) {
        result.status = RealizabilityStatus::ProvedInfeasible;
        result.filter_reason = filter.reason;
        return result;
    }

    std::vector<double> ladder = config.ladder;
    ladder.erase(
        std::remove_if(
            ladder.begin(),
            ladder.end(),
            [](double value) { return !(value > 0.0); }
        ),
        ladder.end()
    );
    std::sort(ladder.begin(), ladder.end());
    ladder.erase(std::unique(ladder.begin(), ladder.end()), ladder.end());
    if (ladder.empty()) {
        throw std::invalid_argument("realize_topology requires a non-empty container ladder");
    }

    const std::uint64_t base_seed =
        sampled_seed(config.seed, sorted_contact_keys(normalized.contacts()));
    SplitMix64 rng{base_seed};

    // Gauge branches: tau_b applies the local frame reflection on the squares
    // selected by b. Every labelling realizable by a physical scene with frame
    // vector b is tau_b applied to a standard-frame labelling, so these 2^n
    // representatives cover exactly the G_n orbit (proof in the Phase-2 doc).
    // Branches in the same H_n orbit are the same standard-frame problem, so
    // only one representative per orbit is solved.
    const std::uint32_t branch_count = 1U << normalized.square_count();
    std::set<std::vector<std::uint64_t>> tried;
    bool weak_found = false;
    double weak_l = 0.0;
    Scene weak_scene;
    std::uint32_t weak_branch = 0;
    bool have_best = false;
    double best_hard = std::numeric_limits<double>::infinity();
    Scene best_scene;
    WitnessReport best_report;
    double best_l = 0.0;
    std::uint32_t best_branch = 0;

    for (std::uint32_t mask = 0; mask < branch_count; ++mask) {
        const GroupElement tau = frame_branch_element(normalized.square_count(), mask);
        const Topology branch = mask == 0U
            ? normalized
            : apply_group_element_to_topology(normalized, tau);
        if (!tried.insert(canonical_branch_key(branch)).second) {
            continue;
        }
        ++result.branches_tried;
        RepresentativeOutcome outcome =
            solve_representative(branch, config, ladder, rng, result.solves);

        if (outcome.exact) {
            const Scene transferred = mask == 0U
                ? outcome.exact_scene
                : apply_group_element_to_scene(tau, outcome.exact_scene);
            const WitnessReport report = verify_witness(transferred, normalized);
            if (report.exact_accepted) {
                result.status = RealizabilityStatus::VerifiedFeasible;
                result.exact_witness = true;
                result.witness = transferred;
                result.report = report;
                result.container_side = outcome.exact_l;
                result.bisection_lower = outcome.bisection_lower;
                result.frame_branch = mask;
                return result;
            }
            if (!have_best || outcome.best_hard < best_hard) {
                have_best = true;
                best_hard = outcome.best_hard;
                best_scene = transferred;
                best_report = report;
                best_l = outcome.exact_l;
                best_branch = mask;
            }
        }

        if (outcome.weak && !weak_found) {
            const Scene transferred = mask == 0U
                ? outcome.weak_scene
                : apply_group_element_to_scene(tau, outcome.weak_scene);
            const WitnessReport report = verify_witness(transferred, normalized);
            if (report.weak_accepted) {
                weak_found = true;
                weak_l = outcome.weak_l;
                weak_scene = transferred;
                weak_branch = mask;
            }
        }
        if (outcome.has_best && (!have_best || outcome.best_hard < best_hard)) {
            const Scene transferred = mask == 0U
                ? outcome.best_scene
                : apply_group_element_to_scene(tau, outcome.best_scene);
            have_best = true;
            best_hard = outcome.best_hard;
            best_scene = transferred;
            best_report = verify_witness(transferred, normalized);
            best_l = outcome.best_l;
            best_branch = mask;
        }
    }

    // No branch produced a verified witness. The best rejected candidate is
    // kept for diagnostics only; NOT_FOUND is never a proof of impossibility.
    result.status = RealizabilityStatus::NotFound;
    result.weak_witness = weak_found;
    result.weak_container_side = weak_l;
    result.weak_scene = weak_scene;
    result.weak_frame_branch = weak_branch;
    if (have_best) {
        result.witness = best_scene;
        result.report = best_report;
        result.container_side = best_l;
        result.frame_branch = best_branch;
    }
    return result;
}

namespace {

// 2x2 matrices for the scene action. Frames are products of a rotation and a
// possible mirror. Two different mirrors occur: the world vertical mirror
// (x -> -x), which is the container reflection, and the body feature-frame
// mirror (x, y) -> (-y, -x), which is the engine's local reflection.
struct Mat2 {
    double m00{1.0};
    double m01{0.0};
    double m10{0.0};
    double m11{1.0};
};

Mat2 mat_mul(const Mat2& a, const Mat2& b) {
    return Mat2{
        a.m00 * b.m00 + a.m01 * b.m10,
        a.m00 * b.m01 + a.m01 * b.m11,
        a.m10 * b.m00 + a.m11 * b.m10,
        a.m10 * b.m01 + a.m11 * b.m11,
    };
}

Mat2 mat_transpose(const Mat2& a) {
    return Mat2{a.m00, a.m10, a.m01, a.m11};
}

Vec2 mat_apply(const Mat2& a, Vec2 v) {
    return Vec2{a.m00 * v.x + a.m01 * v.y, a.m10 * v.x + a.m11 * v.y};
}

Mat2 mat_rotation(double angle) {
    const double c = std::cos(angle);
    const double s = std::sin(angle);
    return Mat2{c, -s, s, c};
}

// World vertical mirror (x -> -x): it maps wall w to 4 - w, so it is the
// container reflection Q_g. It is also the mirror used by the ring-direction
// map of a local reflection.
Mat2 mat_world_mirror() {
    return Mat2{-1.0, 0.0, 0.0, 1.0};
}

// Body feature-frame mirror (x, y) -> (-y, -x): the reflection with ring map
// r -> 8 - r. This is exactly the engine's local D4 element (rotation 0,
// reflected), so flipping the pose parity is the same relabeling.
Mat2 mat_body_mirror() {
    return Mat2{0.0, -1.0, -1.0, 0.0};
}

Mat2 mat_power(const Mat2& matrix, bool reflected) {
    return reflected ? matrix : Mat2{};
}

double mat_determinant(const Mat2& a) {
    return a.m00 * a.m11 - a.m01 * a.m10;
}

// Feature-frame matrix of a pose: world = center + F * body_offset.
Mat2 pose_frame(const SquarePose& pose) {
    return mat_mul(mat_rotation(pose.theta), mat_power(mat_body_mirror(), pose.frame_reflected));
}

// Container isometry Q_g: content rotates by -90k (so wall w maps to w + k)
// and, if requested, is mirrored about the vertical centre line (w -> 4 - w).
Mat2 container_frame(const D4Element& container) {
    return mat_mul(
        mat_rotation(-0.5 * kPi * static_cast<double>(container.rotation)),
        mat_power(mat_world_mirror(), container.reflected)
    );
}

// Direction map induced by a local D4 element on the eight ring directions:
// L v_r = v_{transform_ring(r, local)}. With v_r at angle 135 - 45r this is
// R(-90 k) for a rotation and R(90 - 90 k) * M for a reflection.
Mat2 local_direction_frame(const D4Element& local) {
    const double rotation =
        -0.5 * kPi * static_cast<double>(local.rotation % 4U);
    if (!local.reflected) {
        return mat_rotation(rotation);
    }
    return mat_mul(
        mat_rotation(0.5 * kPi + rotation),
        mat_world_mirror()
    );
}

SquarePose pose_from_frame(const Mat2& frame, Vec2 center) {
    const bool reflected = mat_determinant(frame) < 0.0;
    // F e1 = R(theta) M^b e1 is (cos, sin) for b = 0 and (sin, -cos) for b = 1.
    const double theta = std::atan2(frame.m10, frame.m00)
        + (reflected ? 0.5 * kPi : 0.0);
    return SquarePose{
        center.x,
        center.y,
        theta,
        reflected,
    };
}

}  // namespace

Scene apply_group_element_to_scene(const GroupElement& element, const Scene& scene) {
    if (element.square_count == 0 || scene.squares.size() != element.square_count) {
        throw std::invalid_argument("group element square count does not match the scene");
    }
    if (!is_permutation(element)) {
        throw std::invalid_argument("group element is not a valid permutation/D4 record");
    }

    const double side = scene.container_side;
    const Vec2 centre{0.5 * side, 0.5 * side};
    const Mat2 container = container_frame(element.container);

    Scene result;
    result.container_side = side;
    result.squares.resize(element.square_count);
    for (SquareId square = 0; square < element.square_count; ++square) {
        const SquarePose pose = scene.squares[square];
        const Vec2 centered{pose.x - centre.x, pose.y - centre.y};
        const Vec2 placed = centre + mat_apply(container, centered);

        // The label map must send feature r to transform_ring(r, local).
        // Physical directions transform by the container isometry, so the new
        // feature frame is F' = Q F L^{-1}; the pose parity is det(F').
        const Mat2 frame = mat_mul(
            mat_mul(container, pose_frame(pose)),
            mat_transpose(local_direction_frame(element.local[square]))
        );
        result.squares[element.square_map[square]] = pose_from_frame(frame, placed);
    }
    return result;
}

std::uint32_t support_size(const Topology& topology) {
    std::set<SquareId> squares;
    for (const auto& contact : topology.contacts()) {
        squares.insert(contact.a.square);
        if (contact.b.has_value()) {
            squares.insert(contact.b->square);
        }
    }
    return static_cast<std::uint32_t>(squares.size());
}

std::vector<CorpusClass> corpus_classes(std::uint32_t square_count, std::uint32_t weight) {
    if (square_count == 0 || square_count > 3) {
        throw std::invalid_argument("corpus enumeration currently supports n <= 3");
    }
    if (weight == 0) {
        throw std::invalid_argument("corpus weight must be positive");
    }
    const EventSetLayout layout = EventSetLayout::for_square_count(square_count);
    const EventId event_count = static_cast<EventId>(layout.event_count);
    if (weight > event_count) {
        return {};
    }
    const std::uint64_t group_size = group_element_count(square_count);
    const std::size_t word_count =
        static_cast<std::size_t>((layout.event_count + 63U) / 64U);

    std::vector<std::vector<EventId>> permutations;
    permutations.reserve(group_size);
    for (std::uint64_t index = 0; index < group_size; ++index) {
        permutations.push_back(event_permutation(decode_group_element(square_count, index)));
    }

    using Bitset = std::vector<std::uint64_t>;
    const auto canonicalize = [&](const Bitset& input) {
        Bitset best;
        Bitset candidate(word_count, 0);
        for (const auto& permutation : permutations) {
            std::fill(candidate.begin(), candidate.end(), 0);
            for (std::size_t word = 0; word < word_count; ++word) {
                std::uint64_t bits = input[word];
                while (bits != 0U) {
                    const EventId id = static_cast<EventId>(
                        word * 64U + static_cast<std::size_t>(std::countr_zero(bits))
                    );
                    bits &= bits - 1U;
                    const EventId target = permutation[id];
                    candidate[target / 64U] |= std::uint64_t{1} << (target % 64U);
                }
            }
            if (best.empty() || candidate < best) {
                best = candidate;
            }
        }
        return best;
    };

    // Exact level-by-level enumeration of the canonical classes: every class
    // at weight w contains a class at weight w-1, so expanding the previous
    // level by one event and canonicalizing is complete.
    std::vector<Bitset> level{canonicalize(Bitset(word_count, 0))};
    for (std::uint32_t depth = 1; depth <= weight; ++depth) {
        std::set<Bitset> next;
        for (const Bitset& representative : level) {
            for (EventId id = 0; id < event_count; ++id) {
                if ((representative[id / 64U] & (std::uint64_t{1} << (id % 64U))) != 0U) {
                    continue;
                }
                Bitset candidate = representative;
                candidate[id / 64U] |= std::uint64_t{1} << (id % 64U);
                next.insert(canonicalize(candidate));
            }
        }
        level.assign(next.begin(), next.end());
    }

    std::vector<CorpusClass> classes;
    classes.reserve(level.size());
    for (const Bitset& representative : level) {
        CorpusClass entry;
        entry.square_count = square_count;
        entry.weight = weight;
        for (EventId id = 0; id < event_count; ++id) {
            if ((representative[id / 64U] & (std::uint64_t{1} << (id % 64U))) != 0U) {
                entry.events.push_back(id);
            }
        }
        entry.topology = event_bitset_to_topology(square_count, representative);
        classes.push_back(std::move(entry));
    }
    return classes;
}

CorpusReport run_corpus(
    std::uint32_t square_count,
    std::uint32_t weight,
    const SolveConfig& config
) {
    if (config.workers == 0) {
        throw std::invalid_argument("run_corpus requires at least one worker");
    }
    CorpusReport report;
    report.square_count = square_count;
    report.weight = weight;
    report.config = config;

    std::vector<CorpusClass> classes = corpus_classes(square_count, weight);
    report.classes.resize(classes.size());
    for (std::size_t index = 0; index < classes.size(); ++index) {
        report.classes[index].corpus = std::move(classes[index]);
    }

    const std::size_t worker_count = std::min<std::size_t>(
        config.workers,
        std::max<std::size_t>(report.classes.size(), 1U)
    );
    if (worker_count <= 1) {
        for (std::size_t index = 0; index < report.classes.size(); ++index) {
            report.classes[index].solve = realize_topology(
                report.classes[index].corpus.topology, config);
        }
        return report;
    }

    // One atomic index queue and one result slot per class. Each worker writes
    // only its own slot, so no result mutex is needed and class order in the
    // report does not depend on completion order. The first exception stops
    // the queue and is rethrown after every worker has joined.
    std::atomic<std::size_t> next{0};
    std::atomic<bool> stop{false};
    std::mutex error_mutex;
    std::exception_ptr first_error;
    const auto worker = [&]() {
        for (;;) {
            const std::size_t index = next.fetch_add(1, std::memory_order_relaxed);
            if (index >= report.classes.size() || stop.load(std::memory_order_relaxed)) {
                return;
            }
            try {
                report.classes[index].solve = realize_topology(
                    report.classes[index].corpus.topology, config);
            } catch (...) {
                {
                    std::lock_guard<std::mutex> lock(error_mutex);
                    if (!first_error) {
                        first_error = std::current_exception();
                    }
                }
                stop.store(true, std::memory_order_relaxed);
                return;
            }
        }
    };

    std::vector<std::thread> threads;
    threads.reserve(worker_count);
    for (std::size_t worker_index = 0; worker_index < worker_count; ++worker_index) {
        threads.emplace_back(worker);
    }
    for (auto& thread : threads) {
        thread.join();
    }
    if (first_error) {
        std::rethrow_exception(first_error);
    }
    return report;
}

namespace {

std::string json_escape(std::string_view text) {
    std::string escaped;
    escaped.reserve(text.size());
    for (const char character : text) {
        switch (character) {
            case '"':
                escaped += "\\\"";
                break;
            case '\\':
                escaped += "\\\\";
                break;
            case '\n':
                escaped += "\\n";
                break;
            default:
                escaped += character;
                break;
        }
    }
    return escaped;
}

void write_double(std::ostringstream& out, double value) {
    out.precision(17);
    if (std::isfinite(value)) {
        out << value;
    } else {
        out << "null";
    }
}

}  // namespace

std::string corpus_report_to_json(const CorpusReport& report) {
    std::uint64_t feasible = 0;
    std::uint64_t not_found = 0;
    std::uint64_t infeasible = 0;
    std::uint64_t exact_witnesses = 0;
    std::uint64_t weak_only = 0;
    std::uint64_t total_solves = 0;
    for (const auto& entry : report.classes) {
        switch (entry.solve.status) {
            case RealizabilityStatus::VerifiedFeasible:
                ++feasible;
                break;
            case RealizabilityStatus::NotFound:
                ++not_found;
                break;
            case RealizabilityStatus::ProvedInfeasible:
                ++infeasible;
                break;
        }
        if (entry.solve.exact_witness) {
            ++exact_witnesses;
        }
        if (entry.solve.weak_witness && !entry.solve.exact_witness) {
            ++weak_only;
        }
        total_solves += entry.solve.solves;
    }

    std::ostringstream out;
    out << "{\"schema\":\"sqtopology.realizability.v2\""
        << ",\"tool\":\"sqtopology_realize\""
        << ",\"n\":" << report.square_count
        << ",\"weight\":" << report.weight
        << ",\"class_count\":" << report.classes.size()
        << ",\"gauge_branches\":" << (1U << report.square_count)
        << ",\"group_size\":" << group_element_count(report.square_count)
        << ",\"event_count\":" << event_count_for_squares(report.square_count)
        << ",\"config\":{\"ladder\":[";
    for (std::size_t index = 0; index < report.config.ladder.size(); ++index) {
        if (index != 0U) {
            out << ',';
        }
        write_double(out, report.config.ladder[index]);
    }
    out << "],\"starts_per_rung\":" << report.config.starts_per_rung
        << ",\"lm_max_iterations\":" << report.config.lm_max_iterations
        << ",\"max_solves\":" << report.config.max_solves
        << ",\"minimize_container\":"
        << (report.config.minimize_container ? "true" : "false")
        << ",\"minimization_steps\":" << report.config.minimization_steps
        << ",\"seed\":\"" << report.config.seed << "\""
        << ",\"workers\":" << report.config.workers << "}"
        << ",\"status_counts\":{\"VERIFIED_FEASIBLE\":" << feasible
        << ",\"NOT_FOUND\":" << not_found
        << ",\"PROVED_INFEASIBLE\":" << infeasible << '}'
        << ",\"exact_witnesses\":" << exact_witnesses
        << ",\"weak_only\":" << weak_only
        << ",\"total_solves\":" << total_solves
        << ",\"classes\":[";

    for (std::size_t index = 0; index < report.classes.size(); ++index) {
        if (index != 0U) {
            out << ',';
        }
        const auto& entry = report.classes[index];
        out << "{\"weight\":" << entry.corpus.weight
            << ",\"support\":" << support_size(entry.corpus.topology)
            << ",\"events\":[";
        for (std::size_t event = 0; event < entry.corpus.events.size(); ++event) {
            if (event != 0U) {
                out << ',';
            }
            out << entry.corpus.events[event];
        }
        out << "],\"contacts\":" << topology_contact_keys_json(entry.corpus.topology)
            << ",\"status\":\"" << to_string(entry.solve.status) << '"'
            << ",\"exact_witness\":" << (entry.solve.exact_witness ? "true" : "false")
            << ",\"weak_witness\":" << (entry.solve.weak_witness ? "true" : "false")
            << ",\"filter_reason\":\"" << json_escape(entry.solve.filter_reason) << '"'
            << ",\"frame_branch\":" << entry.solve.frame_branch
            << ",\"weak_frame_branch\":" << entry.solve.weak_frame_branch
            << ",\"branches_tried\":" << entry.solve.branches_tried
            << ",\"container_side\":";
        write_double(out, entry.solve.container_side);
        out << ",\"bisection_lower\":";
        write_double(out, entry.solve.bisection_lower);
        out << ",\"solves\":" << entry.solve.solves;
        if (entry.solve.exact_witness) {
            out << ",\"witness\":" << scene_to_json(entry.solve.witness);
        } else if (entry.solve.weak_witness) {
            out << ",\"weak_scene\":" << scene_to_json(entry.solve.weak_scene);
        }
        out << '}';
    }
    out << "]}\n";
    return out.str();
}

}  // namespace sqtopology
