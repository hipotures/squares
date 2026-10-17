#pragma once

#include "sqtopology/topology.hpp"

#include <array>
#include <cstdint>
#include <string>
#include <vector>

namespace sqtopology {

// ---------------------------------------------------------------------------
// Geometric layer for contact realizability (Phase 2).
//
// Conventions are fixed by the engine's fixture set and the ring indexing in
// topology.hpp:
//
//  - squares have unit side and are posed by their center (x, y), an
//    orientation theta (radians, counterclockwise), and a boolean
//    frame_reflected. In the body frame, corner c sits at angle
//    135 - 90 c degrees (corner 0 top-left, 1 top-right, 2 bottom-right,
//    3 bottom-left) at distance sqrt(2)/2, and side s is the segment from
//    corner s to corner s+1 (mod 4), so side 0 is the top side, 1 right,
//    2 bottom, 3 left. When frame_reflected is set, the corner/side indices
//    are mapped through the body reflection (x, y) -> (-y, -x) first (the
//    reflection with ring map r -> 8 - r, fixing corners 0 and 2); the
//    occupied point set is unchanged, only the labeling changes.
//  - ring index r = 2 * index + (side ? 1 : 0), matching feature_ring_index.
//  - the container is the axis-aligned square [0, L]^2; wall 0 is the line
//    y = L (top), 1 is x = L (right), 2 is y = 0 (bottom), 3 is x = 0 (left),
//    so side w faces wall w at theta = 0.
//
// This module defines the geometry primitives and the contact-extraction
// semantics used by the independent verifier in realize.hpp. The optimizer in
// realize.cpp uses a different (residual/penalty) formulation of the same
// contact kinds; the verifier here is written directly from the geometric
// predicates and never shares code with the solver.
// ---------------------------------------------------------------------------

struct Vec2 {
    double x{0.0};
    double y{0.0};
};

[[nodiscard]] Vec2 operator+(Vec2 a, Vec2 b) noexcept;
[[nodiscard]] Vec2 operator-(Vec2 a, Vec2 b) noexcept;
[[nodiscard]] Vec2 operator*(double scale, Vec2 v) noexcept;
[[nodiscard]] double dot(Vec2 a, Vec2 b) noexcept;
[[nodiscard]] double cross(Vec2 a, Vec2 b) noexcept;
[[nodiscard]] double norm(Vec2 v) noexcept;

// Pose of a unit square. `frame_reflected` is the chirality of the semantic
// feature frame: it says whether corner/side indices are mapped to the physical
// square through the body frame (false) or through its mirror (true).
//
// The physical square is the same set of points for both values (a square is
// achiral and the corner set is invariant under the mirror), so the flag is a
// pure label gauge. It is what lets the scene action cover mixed-parity
// elements of G_n, where one square's feature labels are reflected while the
// container is not (or vice versa). Without it, (x, y, theta) represents only
// orientation-preserving feature frames.
struct SquarePose {
    double x{0.0};
    double y{0.0};
    double theta{0.0};
    bool frame_reflected{false};
};

struct Scene {
    double container_side{0.0};
    std::vector<SquarePose> squares;
};

[[nodiscard]] Vec2 rotate(Vec2 v, double theta) noexcept;
[[nodiscard]] Vec2 corner_offset(std::uint8_t corner) noexcept;
[[nodiscard]] Vec2 side_midpoint_offset(std::uint8_t side) noexcept;
[[nodiscard]] Vec2 corner_position(const SquarePose& pose, std::uint8_t corner) noexcept;
[[nodiscard]] Vec2 side_midpoint_position(
    const SquarePose& pose,
    std::uint8_t side
) noexcept;
[[nodiscard]] std::array<Vec2, 2> side_endpoints(
    const SquarePose& pose,
    std::uint8_t side
) noexcept;
[[nodiscard]] std::array<Vec2, 4> square_corners(const SquarePose& pose) noexcept;

// Signed distance from a point to the wall line, positive outside the
// container. wall must be in 0..3.
[[nodiscard]] double wall_signed_distance(
    Vec2 point,
    std::uint8_t wall,
    double container_side
) noexcept;

// Distance from a point to the closed wall segment.
[[nodiscard]] double wall_segment_distance(
    Vec2 point,
    std::uint8_t wall,
    double container_side
) noexcept;

// The two free-coordinate hinges of a wall: returns (low, high) violations of
// the wall's in-segment range for the point, both >= 0.
[[nodiscard]] std::array<double, 2> wall_segment_violations(
    Vec2 point,
    std::uint8_t wall,
    double container_side
) noexcept;

// Segment predicates.
[[nodiscard]] double point_segment_distance(Vec2 p, Vec2 a, Vec2 b) noexcept;
[[nodiscard]] double point_segment_parameter(Vec2 p, Vec2 a, Vec2 b) noexcept;
[[nodiscard]] double segment_segment_distance(
    Vec2 a0,
    Vec2 a1,
    Vec2 b0,
    Vec2 b1
) noexcept;

struct CollinearOverlap {
    bool collinear{false};
    double overlap{0.0};
};

// Overlap length of two segments that lie on a common line (within the
// tolerance); overlap is 0 for segments that only touch.
[[nodiscard]] CollinearOverlap collinear_overlap(
    Vec2 a0,
    Vec2 a1,
    Vec2 b0,
    Vec2 b1,
    double tolerance
) noexcept;

// SAT separation for two unit squares. slack is the largest signed gap over
// the four edge-normal axes: slack >= 0 means the closed squares are
// separated on the witness axis (interiors disjoint), slack < 0 means the
// interiors overlap.
struct SatResult {
    double slack{0.0};
    std::uint8_t witness_axis{0};
    bool interior_disjoint{false};
};

[[nodiscard]] SatResult sat_separation(
    const SquarePose& a,
    const SquarePose& b,
    double overlap_tolerance
) noexcept;

// Contact extraction tolerances. All lengths are absolute (unit square side).
struct ContactTolerances {
    // Coincidence tolerance: a relation holds when its natural distance is
    // at most this value.
    double contact{1e-7};
    // Strict-interior margin for corner-side exact contacts, as a fraction of
    // the side length.
    double interior{1e-6};
    // Strictly-positive overlap margin for side-side exact contacts.
    double overlap{1e-6};
};

struct ExtractionResult {
    // Exact-stratum contacts: the canonical contact set of the scene, with
    // corner-side contacts strictly inside a side and side-side contacts
    // strictly overlapping. Corner coincidences (and corner-wall contacts)
    // that are absorbed by a positive-overlap side contact are not listed.
    std::vector<Contact> exact;
    // Weak (closure) contacts: same extraction with closed side segments and
    // non-negative side-side overlap (a 1e-9 numerical slack around zero
    // separates rounding noise from a genuine gap). Absorption still requires
    // a strictly positive side-side overlap, so point contacts at a segment
    // endpoint remain corner-corner contacts in both strata. Every exact
    // contact is also a weak contact.
    std::vector<Contact> weak;
};

[[nodiscard]] ExtractionResult extract_contacts(
    const Scene& scene,
    const ContactTolerances& tolerances = {}
);

// Deterministic keys (contact_key) for set comparison; sorted.
[[nodiscard]] std::vector<std::string> sorted_contact_keys(
    const std::vector<Contact>& contacts
);

// Candidate relation margin used by the verifier's clearance scan: the
// distance at which the relation would start to hold (0 means it holds).
struct ContactMargin {
    Contact contact;
    double margin{0.0};
    bool exact_held{false};
    bool weak_held{false};
    bool absorbed{false};
};

[[nodiscard]] std::vector<ContactMargin> scene_contact_margins(
    const Scene& scene,
    const ContactTolerances& tolerances = {}
);

}  // namespace sqtopology
