// Unit tests for the Phase-2 geometry primitives and contact extraction in
// geometry.hpp. The test scenes are explicit poses chosen so that the exact
// extraction equals the committed canonical fixture contact sets; the
// fixture comparison is the ground truth for the extraction semantics.

#include "sqtopology/fixtures.hpp"
#include "sqtopology/geometry.hpp"
#include "sqtopology/topology.hpp"

#include <cmath>
#include <cstdint>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using namespace sqtopology;

constexpr double kPi = 3.14159265358979323846;

void expect(bool condition, const std::string& message) {
    if (!condition) {
        throw std::runtime_error(message);
    }
}

void expect_close(double actual, double expected, double tolerance, const std::string& message) {
    if (std::abs(actual - expected) > tolerance) {
        throw std::runtime_error(
            message + " (actual " + std::to_string(actual) + ", expected "
            + std::to_string(expected) + ")"
        );
    }
}

Scene grid_scene(
    int rows,
    int columns,
    std::optional<std::pair<int, int>> removed = std::nullopt
) {
    Scene scene;
    scene.container_side = static_cast<double>(std::max(rows, columns));
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            if (removed.has_value() && removed->first == row && removed->second == column) {
                continue;
            }
            scene.squares.push_back(SquarePose{
                static_cast<double>(column) + 0.5,
                static_cast<double>(rows - row) - 0.5,
                0.0,
            });
        }
    }
    return scene;
}

std::vector<std::string> fixture_keys(const Topology& topology) {
    return sorted_contact_keys(topology.contacts());
}

void expect_extraction_matches_fixture(
    const Scene& scene,
    const std::string& fixture_name,
    const std::string& label
) {
    const Topology fixture = make_fixture(fixture_name);
    const ExtractionResult extraction = extract_contacts(scene);
    const auto expected = fixture_keys(fixture);
    const auto exact = sorted_contact_keys(extraction.exact);
    if (exact != expected) {
        std::string report = label + ": exact extraction differs from " + fixture_name + "\nexpected:";
        for (const auto& key : expected) {
            report += "\n  " + key;
        }
        report += "\nactual:";
        for (const auto& key : exact) {
            report += "\n  " + key;
        }
        throw std::runtime_error(report);
    }
}

void test_primitives() {
    const Vec2 top_left = corner_offset(0);
    const Vec2 top_right = corner_offset(1);
    const Vec2 bottom_right = corner_offset(2);
    const Vec2 bottom_left = corner_offset(3);
    expect_close(top_left.x, -0.5, 1e-12, "corner 0 x");
    expect_close(top_left.y, 0.5, 1e-12, "corner 0 y");
    expect_close(top_right.x, 0.5, 1e-12, "corner 1 x");
    expect_close(top_right.y, 0.5, 1e-12, "corner 1 y");
    expect_close(bottom_right.x, 0.5, 1e-12, "corner 2 x");
    expect_close(bottom_right.y, -0.5, 1e-12, "corner 2 y");
    expect_close(bottom_left.x, -0.5, 1e-12, "corner 3 x");
    expect_close(bottom_left.y, -0.5, 1e-12, "corner 3 y");

    const SquarePose pose{1.0, 2.0, 0.0};
    const auto side_zero = side_endpoints(pose, 0);
    expect_close(side_zero[0].x, 0.5, 1e-12, "side 0 start x");
    expect_close(side_zero[0].y, 2.5, 1e-12, "side 0 start y");
    expect_close(side_zero[1].x, 1.5, 1e-12, "side 0 end x");
    expect_close(side_zero[1].y, 2.5, 1e-12, "side 0 end y");
    expect_close(side_midpoint_offset(0).y, 0.5, 1e-12, "side 0 midpoint");
    expect_close(side_midpoint_offset(1).x, 0.5, 1e-12, "side 1 midpoint");

    // Ring convention: ring = 2 * index + (side ? 1 : 0).
    for (std::uint8_t corner = 0; corner < 4; ++corner) {
        expect(
            feature_ring_index(FeatureRef{0, FeatureKind::Corner, corner})
                == 2U * corner,
            "corner ring index"
        );
    }
    for (std::uint8_t side = 0; side < 4; ++side) {
        expect(
            feature_ring_index(FeatureRef{0, FeatureKind::Side, side}) == 2U * side + 1U,
            "side ring index"
        );
    }
}

void test_wall_predicates() {
    // Wall 0 is y = L, wall 1 is x = L, wall 2 is y = 0, wall 3 is x = 0.
    expect_close(wall_signed_distance(Vec2{1.5, 3.5}, 0, 3.0), 0.5, 1e-12, "wall 0 outside");
    expect_close(wall_signed_distance(Vec2{1.5, 2.5}, 0, 3.0), -0.5, 1e-12, "wall 0 inside");
    expect_close(wall_signed_distance(Vec2{3.5, 1.0}, 1, 3.0), 0.5, 1e-12, "wall 1 outside");
    expect_close(wall_signed_distance(Vec2{1.0, -0.5}, 2, 3.0), 0.5, 1e-12, "wall 2 outside");
    expect_close(wall_signed_distance(Vec2{-0.5, 1.0}, 3, 3.0), 0.5, 1e-12, "wall 3 outside");

    expect_close(wall_segment_distance(Vec2{1.5, 3.0}, 0, 3.0), 0.0, 1e-12, "on wall 0");
    expect_close(wall_segment_distance(Vec2{4.0, 3.0}, 0, 3.0), 1.0, 1e-12, "past wall 0 end");
    expect_close(wall_segment_distance(Vec2{1.5, 4.0}, 0, 3.0), 1.0, 1e-12, "normal to wall 0");

    const auto before = wall_segment_violations(Vec2{-0.5, 3.0}, 0, 3.0);
    expect_close(before[0], 0.5, 1e-12, "wall 0 low violation");
    expect_close(before[1], 0.0, 1e-12, "wall 0 low no high violation");
    const auto past = wall_segment_violations(Vec2{3.5, 3.0}, 0, 3.0);
    expect_close(past[0], 0.0, 1e-12, "wall 0 high no low violation");
    expect_close(past[1], 0.5, 1e-12, "wall 0 high violation");
    const auto inside = wall_segment_violations(Vec2{1.5, 3.0}, 0, 3.0);
    expect_close(inside[0], 0.0, 1e-12, "wall 0 low clear");
    expect_close(inside[1], 0.0, 1e-12, "wall 0 high clear");
}

void test_segment_predicates() {
    expect_close(
        point_segment_distance(Vec2{0.5, 1.0}, Vec2{0.0, 0.0}, Vec2{1.0, 0.0}),
        1.0,
        1e-12,
        "point above segment"
    );
    expect_close(
        point_segment_distance(Vec2{-1.0, 0.0}, Vec2{0.0, 0.0}, Vec2{1.0, 0.0}),
        1.0,
        1e-12,
        "point before segment"
    );
    expect_close(
        point_segment_parameter(Vec2{0.25, 0.5}, Vec2{0.0, 0.0}, Vec2{1.0, 0.0}),
        0.25,
        1e-12,
        "projection parameter"
    );
    expect_close(
        segment_segment_distance(Vec2{0.0, 0.0}, Vec2{1.0, 0.0}, Vec2{0.5, -1.0}, Vec2{0.5, 1.0}),
        0.0,
        1e-12,
        "crossing segments"
    );

    const CollinearOverlap overlap = collinear_overlap(
        Vec2{0.0, 0.0}, Vec2{1.0, 0.0}, Vec2{0.5, 0.0}, Vec2{1.5, 0.0}, 1e-9
    );
    expect(overlap.collinear, "collinear overlap detected");
    expect_close(overlap.overlap, 0.5, 1e-12, "collinear overlap length");
    const CollinearOverlap touching = collinear_overlap(
        Vec2{0.0, 0.0}, Vec2{1.0, 0.0}, Vec2{1.0, 0.0}, Vec2{2.0, 0.0}, 1e-9
    );
    expect(touching.collinear, "touching segments collinear");
    expect_close(touching.overlap, 0.0, 1e-12, "touching overlap zero");
    const CollinearOverlap parallel = collinear_overlap(
        Vec2{0.0, 0.0}, Vec2{1.0, 0.0}, Vec2{0.0, 0.1}, Vec2{1.0, 0.1}, 1e-9
    );
    expect(!parallel.collinear, "offset segments not collinear");
}

void test_sat() {
    const SquarePose left{1.0, 1.0, 0.0};
    const SquarePose right{2.0, 1.0, 0.0};
    const SatResult touching = sat_separation(left, right, 1e-9);
    expect_close(touching.slack, 0.0, 1e-12, "touching slack");
    expect(touching.interior_disjoint, "touching interiors disjoint");

    const SquarePose diagonal{2.0, 2.0, 0.0};
    const SatResult corner_touch = sat_separation(left, diagonal, 1e-9);
    expect_close(corner_touch.slack, 0.0, 1e-12, "diagonal slack");
    expect(corner_touch.interior_disjoint, "diagonal interiors disjoint");

    const SquarePose overlapped{1.5, 1.0, 0.0};
    const SatResult overlap = sat_separation(left, overlapped, 1e-9);
    expect_close(overlap.slack, -0.5, 1e-12, "overlap slack");
    expect(!overlap.interior_disjoint, "overlapping interiors found");

    const SquarePose rotated{1.5 + std::sqrt(2.0) / 2.0, 1.0, kPi / 4.0};
    const SatResult rotated_touch = sat_separation(left, rotated, 1e-9);
    expect(rotated_touch.interior_disjoint, "rotated touch disjoint");
    expect_close(rotated_touch.slack, 0.0, 1e-12, "rotated touch slack");
}

void test_grid_fixtures() {
    expect_extraction_matches_fixture(grid_scene(2, 2), "grid-2x2", "grid 2x2");
    expect_extraction_matches_fixture(grid_scene(3, 3), "grid-3x3", "grid 3x3");
    expect_extraction_matches_fixture(grid_scene(4, 4), "grid-4x4", "grid 4x4");
    expect_extraction_matches_fixture(
        grid_scene(4, 4, std::pair{1, 1}),
        "grid-4x4-minus-one",
        "grid 4x4 minus one"
    );
}

void test_pair_fixtures() {
    Scene corner_corner;
    corner_corner.container_side = 3.0;
    corner_corner.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    expect_extraction_matches_fixture(corner_corner, "corner-corner-2", "pair corner-corner");

    Scene corner_side;
    corner_side.container_side = 3.0;
    corner_side.squares = {
        SquarePose{1.5 - std::sqrt(2.0) / 2.0, 2.0, -kPi / 4.0},
        SquarePose{2.0, 2.0, 0.0},
    };
    expect_extraction_matches_fixture(corner_side, "corner-side-2", "pair corner-side");

    Scene side_side;
    side_side.container_side = 3.0;
    side_side.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 2.0, 0.0}};
    expect_extraction_matches_fixture(side_side, "side-side-2", "pair side-side");
}

void test_wall_fixtures() {
    Scene wall_corner;
    wall_corner.container_side = 3.0;
    wall_corner.squares = {SquarePose{1.5, 3.0 - std::sqrt(2.0) / 2.0, -kPi / 4.0}};
    Topology corner_topology(1);
    corner_topology.add_contact(make_wall_contact(
        FeatureRef{0, FeatureKind::Corner, 0}, 0
    ));
    const ExtractionResult corner_result = extract_contacts(wall_corner);
    expect(
        sorted_contact_keys(corner_result.exact) == fixture_keys(corner_topology),
        "wall-corner fixture extraction"
    );

    Scene wall_side;
    wall_side.container_side = 3.0;
    wall_side.squares = {SquarePose{1.5, 2.5, 0.0}};
    Topology side_topology(1);
    side_topology.add_contact(make_wall_contact(FeatureRef{0, FeatureKind::Side, 0}, 0));
    const ExtractionResult side_result = extract_contacts(wall_side);
    expect(
        sorted_contact_keys(side_result.exact) == fixture_keys(side_topology),
        "wall-side fixture extraction"
    );
}

void test_empty_fixtures() {
    Scene isolated;
    isolated.container_side = 2.0;
    isolated.squares = {SquarePose{1.0, 1.0, 0.0}};
    expect(extract_contacts(isolated).exact.empty(), "isolated square has no contacts");

    Scene disjoint;
    disjoint.container_side = 3.0;
    disjoint.squares = {SquarePose{0.75, 0.75, 0.0}, SquarePose{2.25, 2.25, 0.0}};
    const ExtractionResult result = extract_contacts(disjoint);
    expect(result.exact.empty(), "disjoint pair has no exact contacts");
    expect(result.weak.empty(), "disjoint pair has no weak contacts");
}

void test_weak_stratum_differs() {
    // Two squares touching corner-to-corner: the exact stratum is the single
    // corner-corner contact. The weak (closure) stratum additionally sees the
    // touching corner on the four closed side segments of the other square,
    // plus the two pairs of collinear touching sides (zero overlap).
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    const ExtractionResult result = extract_contacts(scene);
    expect(result.exact.size() == 1, "corner-corner exact size");
    expect(result.exact[0].kind == ContactKind::CornerCorner, "corner-corner kind");
    expect(result.weak.size() == 7, "corner-corner weak closure size");
    expect(
        sorted_contact_keys(result.weak).size() == 7,
        "corner-corner weak keys unique"
    );
}

void test_absorption_exactness() {
    // A partial side-side overlap absorbs the endpoint corner contacts: the
    // exact extraction is the single side-side contact.
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 2.4, 0.0}};
    const ExtractionResult result = extract_contacts(scene);
    expect(result.exact.size() == 1, "partial overlap exact size");
    expect(result.exact[0].kind == ContactKind::SideSide, "partial overlap kind");
}

void test_margins() {
    Scene scene;
    scene.container_side = 3.0;
    scene.squares = {SquarePose{1.0, 2.0, 0.0}, SquarePose{2.0, 1.0, 0.0}};
    const auto margins = scene_contact_margins(scene);
    bool found_cc = false;
    for (const auto& margin : margins) {
        if (margin.contact.kind == ContactKind::CornerCorner
            && margin.contact.a.square == 0) {
            found_cc = true;
            expect_close(margin.margin, -1e-7, 1e-9, "held CC margin");
            expect(margin.exact_held, "held CC exact flag");
        }
    }
    expect(found_cc, "corner-corner margin present in scan");
}

}  // namespace

int main() {
    try {
        test_primitives();
        test_wall_predicates();
        test_segment_predicates();
        test_sat();
        test_grid_fixtures();
        test_pair_fixtures();
        test_wall_fixtures();
        test_empty_fixtures();
        test_weak_stratum_differs();
        test_absorption_exactness();
        test_margins();
        std::cout << "sqtopology_geometry_tests: all tests passed\n";
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_geometry_tests: FAIL: " << error.what() << '\n';
        return 1;
    }
}
