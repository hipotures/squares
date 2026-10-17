#include "sqtopology/geometry.hpp"

#include <algorithm>
#include <cmath>
#include <limits>
#include <utility>

namespace sqtopology {
namespace {

constexpr double kPi = 3.14159265358979323846;
constexpr double kDegToRad = kPi / 180.0;
constexpr double kCornerRadius = 0.70710678118654752440;  // sqrt(2)/2

// Numerical slack for the zero-overlap boundary of the side-side stratum:
// projections of exactly touching segments carry a few ulps of rounding error
// (~1e-16), while a genuine overlap below this slack has no physical meaning at
// the 1e-7/1e-6 contact tolerances. Raw overlaps above the slack are treated as
// strictly positive, which is what drives the absorption rule.
constexpr double kOverlapSlack = 1e-9;

double radians_from_degrees(double degrees) noexcept {
    return degrees * kDegToRad;
}

// Wall endpoints in counterclockwise scratch order (endpoints only; the
// protocol never depends on the traversal direction).
std::array<Vec2, 2> wall_endpoints(std::uint8_t wall, double container_side) noexcept {
    switch (wall) {
        case 0:
            return {Vec2{0.0, container_side}, Vec2{container_side, container_side}};
        case 1:
            return {Vec2{container_side, container_side}, Vec2{container_side, 0.0}};
        case 2:
            return {Vec2{container_side, 0.0}, Vec2{0.0, 0.0}};
        default:
            return {Vec2{0.0, 0.0}, Vec2{0.0, container_side}};
    }
}

}  // namespace

Vec2 operator+(Vec2 a, Vec2 b) noexcept {
    return Vec2{a.x + b.x, a.y + b.y};
}

Vec2 operator-(Vec2 a, Vec2 b) noexcept {
    return Vec2{a.x - b.x, a.y - b.y};
}

Vec2 operator*(double scale, Vec2 v) noexcept {
    return Vec2{scale * v.x, scale * v.y};
}

double dot(Vec2 a, Vec2 b) noexcept {
    return a.x * b.x + a.y * b.y;
}

double cross(Vec2 a, Vec2 b) noexcept {
    return a.x * b.y - a.y * b.x;
}

double norm(Vec2 v) noexcept {
    return std::hypot(v.x, v.y);
}

Vec2 rotate(Vec2 v, double theta) noexcept {
    const double c = std::cos(theta);
    const double s = std::sin(theta);
    return Vec2{c * v.x - s * v.y, s * v.x + c * v.y};
}

Vec2 corner_offset(std::uint8_t corner) noexcept {
    const auto index = static_cast<std::uint8_t>(corner % 4U);
    const double angle = radians_from_degrees(135.0 - 90.0 * index);
    return Vec2{
        kCornerRadius * std::cos(angle),
        kCornerRadius * std::sin(angle),
    };
}

Vec2 side_midpoint_offset(std::uint8_t side) noexcept {
    const auto index = static_cast<std::uint8_t>(side % 4U);
    const Vec2 a = corner_offset(index);
    const Vec2 b = corner_offset(static_cast<std::uint8_t>((index + 1U) % 4U));
    return 0.5 * (a + b);
}

Vec2 corner_position(const SquarePose& pose, std::uint8_t corner) noexcept {
    return Vec2{pose.x, pose.y} + rotate(corner_offset(corner), pose.theta);
}

std::array<Vec2, 2> side_endpoints(const SquarePose& pose, std::uint8_t side) noexcept {
    const auto index = static_cast<std::uint8_t>(side % 4U);
    return {
        corner_position(pose, index),
        corner_position(pose, static_cast<std::uint8_t>((index + 1U) % 4U)),
    };
}

std::array<Vec2, 4> square_corners(const SquarePose& pose) noexcept {
    return {
        corner_position(pose, 0),
        corner_position(pose, 1),
        corner_position(pose, 2),
        corner_position(pose, 3),
    };
}

double wall_signed_distance(Vec2 point, std::uint8_t wall, double container_side) noexcept {
    switch (wall % 4U) {
        case 0:
            return point.y - container_side;  // outside above the top wall
        case 1:
            return point.x - container_side;
        case 2:
            return -point.y;  // outside below the bottom wall
        default:
            return -point.x;
    }
}

double wall_segment_distance(Vec2 point, std::uint8_t wall, double container_side) noexcept {
    const auto endpoints = wall_endpoints(wall % 4U, container_side);
    return point_segment_distance(point, endpoints[0], endpoints[1]);
}

std::array<double, 2> wall_segment_violations(
    Vec2 point,
    std::uint8_t wall,
    double container_side
) noexcept {
    switch (wall % 4U) {
        case 0:
        case 2:
            return {
                std::max(0.0, -point.x),
                std::max(0.0, point.x - container_side),
            };
        default:
            return {
                std::max(0.0, -point.y),
                std::max(0.0, point.y - container_side),
            };
    }
}

double point_segment_distance(Vec2 p, Vec2 a, Vec2 b) noexcept {
    const Vec2 ab = b - a;
    const double length_squared = dot(ab, ab);
    if (length_squared <= 0.0) {
        return norm(p - a);
    }
    const double t = std::clamp(dot(p - a, ab) / length_squared, 0.0, 1.0);
    return norm(p - (a + t * ab));
}

double point_segment_parameter(Vec2 p, Vec2 a, Vec2 b) noexcept {
    const Vec2 ab = b - a;
    const double length_squared = dot(ab, ab);
    if (length_squared <= 0.0) {
        return 0.0;
    }
    return dot(p - a, ab) / length_squared;
}

double segment_segment_distance(Vec2 a0, Vec2 a1, Vec2 b0, Vec2 b1) noexcept {
    // Interiors of convex segments always intersect when the segments properly
    // cross; otherwise the minimum is attained at an endpoint of one of them.
    const double ab = cross(a1 - a0, b1 - b0);
    if (ab != 0.0) {
        const double t = cross(b0 - a0, b1 - b0) / ab;
        const double s = cross(b0 - a0, a1 - a0) / ab;
        if (t >= 0.0 && t <= 1.0 && s >= 0.0 && s <= 1.0) {
            return 0.0;
        }
    }
    return std::min({
        point_segment_distance(a0, b0, b1),
        point_segment_distance(a1, b0, b1),
        point_segment_distance(b0, a0, a1),
        point_segment_distance(b1, a0, a1),
    });
}

CollinearOverlap collinear_overlap(
    Vec2 a0,
    Vec2 a1,
    Vec2 b0,
    Vec2 b1,
    double tolerance
) noexcept {
    CollinearOverlap result;
    const Vec2 axis = a1 - a0;
    const double length = norm(axis);
    if (length <= 0.0) {
        return result;
    }
    const Vec2 direction = (1.0 / length) * axis;

    const double perp0 = std::abs(cross(direction, b0 - a0));
    const double perp1 = std::abs(cross(direction, b1 - a0));
    if (perp0 > tolerance || perp1 > tolerance) {
        return result;
    }
    result.collinear = true;

    const double t0 = dot(b0 - a0, direction);
    const double t1 = dot(b1 - a0, direction);
    const double low = std::min(t0, t1);
    const double high = std::max(t0, t1);
    const double overlap_start = std::max(low, 0.0);
    const double overlap_end = std::min(high, length);
    result.overlap = std::max(0.0, overlap_end - overlap_start);
    return result;
}

SatResult sat_separation(
    const SquarePose& a,
    const SquarePose& b,
    double overlap_tolerance
) noexcept {
    SatResult result;
    result.slack = -std::numeric_limits<double>::infinity();
    const Vec2 delta = Vec2{b.x - a.x, b.y - a.y};

    double slack = -std::numeric_limits<double>::infinity();
    std::uint8_t witness = 0;
    for (std::uint8_t axis = 0; axis < 4; ++axis) {
        const bool use_b = axis >= 2;
        const double pose_angle = use_b ? b.theta : a.theta;
        const double quarter_turn = (axis % 2 == 0) ? 0.0 : (kPi / 2.0);
        const double angle = pose_angle + quarter_turn;
        const Vec2 normal{std::cos(angle), std::sin(angle)};

        const double half_a = 0.5 * (std::abs(std::cos(angle - a.theta))
                                     + std::abs(std::sin(angle - a.theta)));
        const double half_b = 0.5 * (std::abs(std::cos(angle - b.theta))
                                     + std::abs(std::sin(angle - b.theta)));
        const double gap = std::abs(dot(normal, delta)) - (half_a + half_b);
        if (gap > slack) {
            slack = gap;
            witness = axis;
        }
    }

    result.slack = slack;
    result.witness_axis = witness;
    result.interior_disjoint = slack >= -overlap_tolerance;
    return result;
}

namespace {

struct SideOverlapCandidate {
    std::uint8_t first_side{0};
    std::uint8_t second_side{0};
    bool positive{false};
    std::array<Vec2, 2> first_segment{};
    std::array<Vec2, 2> second_segment{};
};

bool point_on_segment(Vec2 point, const std::array<Vec2, 2>& segment, double tolerance) {
    return point_segment_distance(point, segment[0], segment[1]) <= tolerance;
}

// A coincident point is absorbed by a positive-overlap side-side contact when
// it lies on both overlapping sides (it is then automatically an endpoint of
// the overlap, which is precisely the canonical contact-set convention).
bool absorbed_by_side_overlap(
    Vec2 point,
    const std::vector<SideOverlapCandidate>& overlaps,
    double tolerance
) {
    for (const auto& overlap : overlaps) {
        if (!overlap.positive) {
            continue;
        }
        const bool on_first = point_on_segment(point, overlap.first_segment, tolerance);
        const bool on_second = point_on_segment(point, overlap.second_segment, tolerance);
        if (on_first && on_second) {
            return true;
        }
    }
    return false;
}

FeatureRef corner_feature(SquareId square, std::uint8_t corner) {
    return FeatureRef{.square = square, .kind = FeatureKind::Corner, .index = corner};
}

FeatureRef side_feature(SquareId square, std::uint8_t side) {
    return FeatureRef{.square = square, .kind = FeatureKind::Side, .index = side};
}

std::vector<Contact> extract_stratum(const Scene& scene, const ContactTolerances& tolerances, bool weak) {
    std::vector<Contact> contacts;
    const auto square_count = static_cast<SquareId>(scene.squares.size());
    const double contact_tolerance = tolerances.contact;

    for (SquareId first = 0; first < square_count; ++first) {
        for (SquareId second = first + 1U; second < square_count; ++second) {
            const SquarePose& pose_first = scene.squares[first];
            const SquarePose& pose_second = scene.squares[second];
            std::vector<SideOverlapCandidate> overlaps;

            for (std::uint8_t first_side = 0; first_side < 4; ++first_side) {
                const auto first_segment = side_endpoints(pose_first, first_side);
                for (std::uint8_t second_side = 0; second_side < 4; ++second_side) {
                    const auto second_segment = side_endpoints(pose_second, second_side);
                    const CollinearOverlap overlap = collinear_overlap(
                        first_segment[0],
                        first_segment[1],
                        second_segment[0],
                        second_segment[1],
                        contact_tolerance
                    );
                    if (!overlap.collinear) {
                        continue;
                    }
                    const bool holds = weak
                        ? overlap.overlap >= -kOverlapSlack
                        : overlap.overlap >= tolerances.overlap;
                    overlaps.push_back(SideOverlapCandidate{
                        .first_side = first_side,
                        .second_side = second_side,
                        .positive = overlap.overlap > kOverlapSlack,
                        .first_segment = first_segment,
                        .second_segment = second_segment,
                    });
                    if (holds) {
                        contacts.push_back(make_square_contact(
                            side_feature(first, first_side),
                            side_feature(second, second_side)
                        ));
                    }
                }
            }

            for (std::uint8_t first_corner = 0; first_corner < 4; ++first_corner) {
                const Vec2 first_point = corner_position(pose_first, first_corner);
                for (std::uint8_t second_corner = 0; second_corner < 4; ++second_corner) {
                    const Vec2 second_point = corner_position(pose_second, second_corner);
                    if (norm(first_point - second_point) > contact_tolerance) {
                        continue;
                    }
                    if (absorbed_by_side_overlap(first_point, overlaps, contact_tolerance)) {
                        continue;
                    }
                    contacts.push_back(make_square_contact(
                        corner_feature(first, first_corner),
                        corner_feature(second, second_corner)
                    ));
                }
            }

            const std::pair<SquareId, std::uint8_t> corner_configurations[2] = {
                {first, second},
                {second, first},
            };
            for (const auto& [corner_square, side_square] : corner_configurations) {
                const SquarePose& corner_pose = scene.squares[corner_square];
                const SquarePose& side_pose = scene.squares[side_square];
                for (std::uint8_t corner = 0; corner < 4; ++corner) {
                    const Vec2 point = corner_position(corner_pose, corner);
                    for (std::uint8_t side = 0; side < 4; ++side) {
                        const auto segment = side_endpoints(side_pose, side);
                        const double distance =
                            point_segment_distance(point, segment[0], segment[1]);
                        if (distance > contact_tolerance) {
                            continue;
                        }
                        if (!weak) {
                            const double parameter =
                                point_segment_parameter(point, segment[0], segment[1]);
                            if (parameter < tolerances.interior
                                || parameter > 1.0 - tolerances.interior) {
                                continue;
                            }
                        }
                        if (absorbed_by_side_overlap(point, overlaps, contact_tolerance)) {
                            continue;
                        }
                        contacts.push_back(make_square_contact(
                            corner_feature(corner_square, corner),
                            side_feature(side_square, side)
                        ));
                    }
                }
            }
        }
    }

    // Wall contacts. A side-wall contact absorbs the corner-wall contacts of
    // its own endpoints on the same wall.
    for (SquareId square = 0; square < square_count; ++square) {
        const SquarePose& pose = scene.squares[square];
        for (std::uint8_t wall = 0; wall < 4; ++wall) {
            bool side_on_wall[4] = {false, false, false, false};
            for (std::uint8_t side = 0; side < 4; ++side) {
                const auto segment = side_endpoints(pose, side);
                const double first_distance =
                    wall_segment_distance(segment[0], wall, scene.container_side);
                const double second_distance =
                    wall_segment_distance(segment[1], wall, scene.container_side);
                if (first_distance <= contact_tolerance
                    && second_distance <= contact_tolerance) {
                    side_on_wall[side] = true;
                    contacts.push_back(make_wall_contact(side_feature(square, side), wall));
                }
            }
            for (std::uint8_t corner = 0; corner < 4; ++corner) {
                const Vec2 point = corner_position(pose, corner);
                if (wall_segment_distance(point, wall, scene.container_side)
                    > contact_tolerance) {
                    continue;
                }
                const std::uint8_t previous_side =
                    static_cast<std::uint8_t>((corner + 3U) % 4U);
                if (side_on_wall[corner] || side_on_wall[previous_side]) {
                    continue;
                }
                contacts.push_back(make_wall_contact(corner_feature(square, corner), wall));
            }
        }
    }

    return contacts;
}

}  // namespace

ExtractionResult extract_contacts(const Scene& scene, const ContactTolerances& tolerances) {
    ExtractionResult result;
    result.exact = extract_stratum(scene, tolerances, /*weak=*/false);
    result.weak = extract_stratum(scene, tolerances, /*weak=*/true);
    const auto key_less = [](const Contact& lhs, const Contact& rhs) {
        return contact_key(lhs) < contact_key(rhs);
    };
    std::sort(result.exact.begin(), result.exact.end(), key_less);
    std::sort(result.weak.begin(), result.weak.end(), key_less);
    return result;
}

std::vector<std::string> sorted_contact_keys(const std::vector<Contact>& contacts) {
    std::vector<std::string> keys;
    keys.reserve(contacts.size());
    for (const auto& contact : contacts) {
        keys.push_back(contact_key(contact));
    }
    std::sort(keys.begin(), keys.end());
    keys.erase(std::unique(keys.begin(), keys.end()), keys.end());
    return keys;
}

std::vector<ContactMargin> scene_contact_margins(
    const Scene& scene,
    const ContactTolerances& tolerances
) {
    std::vector<ContactMargin> margins;
    const auto square_count = static_cast<SquareId>(scene.squares.size());
    const double contact_tolerance = tolerances.contact;
    constexpr double kRelevantDistance = 0.25;

    for (SquareId square = 0; square < square_count; ++square) {
        const SquarePose& pose = scene.squares[square];
        bool side_on_wall[4][4] = {{false}};
        for (std::uint8_t wall = 0; wall < 4; ++wall) {
            for (std::uint8_t side = 0; side < 4; ++side) {
                const auto segment = side_endpoints(pose, side);
                const double first_distance =
                    wall_segment_distance(segment[0], wall, scene.container_side);
                const double second_distance =
                    wall_segment_distance(segment[1], wall, scene.container_side);
                if (first_distance <= contact_tolerance
                    && second_distance <= contact_tolerance) {
                    side_on_wall[wall][side] = true;
                }
                const double margin =
                    std::max(first_distance, second_distance) - contact_tolerance;
                if (margin <= kRelevantDistance) {
                    const bool held = first_distance <= contact_tolerance
                        && second_distance <= contact_tolerance;
                    margins.push_back(ContactMargin{
                        .contact = make_wall_contact(side_feature(square, side), wall),
                        .margin = margin,
                        .exact_held = held,
                        .weak_held = held,
                        .absorbed = false,
                    });
                }
            }
            for (std::uint8_t corner = 0; corner < 4; ++corner) {
                const Vec2 point = corner_position(pose, corner);
                const double distance =
                    wall_segment_distance(point, wall, scene.container_side);
                const double margin = distance - contact_tolerance;
                if (margin > kRelevantDistance) {
                    continue;
                }
                const std::uint8_t previous_side =
                    static_cast<std::uint8_t>((corner + 3U) % 4U);
                const bool absorbed =
                    side_on_wall[wall][corner] || side_on_wall[wall][previous_side];
                const bool held = distance <= contact_tolerance;
                margins.push_back(ContactMargin{
                    .contact = make_wall_contact(corner_feature(square, corner), wall),
                    .margin = margin,
                    .exact_held = held,
                    .weak_held = held,
                    .absorbed = absorbed,
                });
            }
        }
    }

    for (SquareId first = 0; first < square_count; ++first) {
        for (SquareId second = first + 1U; second < square_count; ++second) {
            const SquarePose& pose_first = scene.squares[first];
            const SquarePose& pose_second = scene.squares[second];
            std::vector<SideOverlapCandidate> overlaps;

            for (std::uint8_t first_side = 0; first_side < 4; ++first_side) {
                const auto first_segment = side_endpoints(pose_first, first_side);
                const Vec2 axis = first_segment[1] - first_segment[0];
                const double length = norm(axis);
                if (length <= 0.0) {
                    continue;
                }
                const Vec2 direction = (1.0 / length) * axis;
                for (std::uint8_t second_side = 0; second_side < 4; ++second_side) {
                    const auto second_segment = side_endpoints(pose_second, second_side);
                    const double perpendicular = std::max(
                        std::abs(cross(direction, second_segment[0] - first_segment[0])),
                        std::abs(cross(direction, second_segment[1] - first_segment[0]))
                    );
                    const CollinearOverlap overlap = collinear_overlap(
                        first_segment[0],
                        first_segment[1],
                        second_segment[0],
                        second_segment[1],
                        contact_tolerance
                    );
                    const double margin = std::max(
                        perpendicular - contact_tolerance,
                        tolerances.overlap - overlap.overlap
                    );
                    if (margin > kRelevantDistance) {
                        continue;
                    }
                    const bool exact_held = overlap.collinear
                        && overlap.overlap >= tolerances.overlap;
                    const bool weak_held = overlap.collinear
                        && overlap.overlap >= -kOverlapSlack;
                    overlaps.push_back(SideOverlapCandidate{
                        .first_side = first_side,
                        .second_side = second_side,
                        .positive = overlap.overlap > kOverlapSlack,
                        .first_segment = first_segment,
                        .second_segment = second_segment,
                    });
                    margins.push_back(ContactMargin{
                        .contact = make_square_contact(
                            side_feature(first, first_side),
                            side_feature(second, second_side)
                        ),
                        .margin = margin,
                        .exact_held = exact_held,
                        .weak_held = weak_held,
                        .absorbed = false,
                    });
                }
            }

            for (std::uint8_t first_corner = 0; first_corner < 4; ++first_corner) {
                const Vec2 first_point = corner_position(pose_first, first_corner);
                for (std::uint8_t second_corner = 0; second_corner < 4; ++second_corner) {
                    const Vec2 second_point = corner_position(pose_second, second_corner);
                    const double distance = norm(first_point - second_point);
                    const double margin = distance - contact_tolerance;
                    if (margin > kRelevantDistance) {
                        continue;
                    }
                    const bool absorbed =
                        absorbed_by_side_overlap(first_point, overlaps, contact_tolerance);
                    const bool held = distance <= contact_tolerance;
                    margins.push_back(ContactMargin{
                        .contact = make_square_contact(
                            corner_feature(first, first_corner),
                            corner_feature(second, second_corner)
                        ),
                        .margin = margin,
                        .exact_held = held && !absorbed,
                        .weak_held = held && !absorbed,
                        .absorbed = absorbed,
                    });
                }
            }

            const std::pair<SquareId, std::uint8_t> configurations[2] = {
                {first, second},
                {second, first},
            };
            for (const auto& [corner_square, side_square] : configurations) {
                const SquarePose& corner_pose = scene.squares[corner_square];
                const SquarePose& side_pose = scene.squares[side_square];
                for (std::uint8_t corner = 0; corner < 4; ++corner) {
                    const Vec2 point = corner_position(corner_pose, corner);
                    for (std::uint8_t side = 0; side < 4; ++side) {
                        const auto segment = side_endpoints(side_pose, side);
                        const double distance =
                            point_segment_distance(point, segment[0], segment[1]);
                        const double margin = distance - contact_tolerance;
                        if (margin > kRelevantDistance) {
                            continue;
                        }
                        const double parameter =
                            point_segment_parameter(point, segment[0], segment[1]);
                        const bool interior = parameter >= tolerances.interior
                            && parameter <= 1.0 - tolerances.interior;
                        const bool touching = distance <= contact_tolerance;
                        const bool absorbed =
                            absorbed_by_side_overlap(point, overlaps, contact_tolerance);
                        margins.push_back(ContactMargin{
                            .contact = make_square_contact(
                                corner_feature(corner_square, corner),
                                side_feature(side_square, side)
                            ),
                            .margin = margin,
                            .exact_held = touching && interior && !absorbed,
                            .weak_held = touching && !absorbed,
                            .absorbed = absorbed,
                        });
                    }
                }
            }
        }
    }

    return margins;
}

}  // namespace sqtopology
