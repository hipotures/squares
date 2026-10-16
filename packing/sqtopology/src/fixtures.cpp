#include "sqtopology/fixtures.hpp"

#include <optional>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace sqtopology {
namespace {

FeatureRef corner(SquareId square, std::uint8_t index) {
    return FeatureRef{.square = square, .kind = FeatureKind::Corner, .index = index};
}

FeatureRef side(SquareId square, std::uint8_t index) {
    return FeatureRef{.square = square, .kind = FeatureKind::Side, .index = index};
}

Topology make_grid(
    int rows,
    int columns,
    std::optional<std::pair<int, int>> removed = std::nullopt
) {
    std::vector<int> ids(static_cast<std::size_t>(rows * columns), -1);
    SquareId next = 0;
    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            if (removed.has_value()
                && removed->first == row
                && removed->second == column) {
                continue;
            }
            ids[static_cast<std::size_t>(row * columns + column)] =
                static_cast<int>(next++);
        }
    }

    Topology topology(next);
    const auto id_at = [&](int row, int column) -> std::optional<SquareId> {
        if (row < 0 || row >= rows || column < 0 || column >= columns) {
            return std::nullopt;
        }
        const int value = ids[static_cast<std::size_t>(row * columns + column)];
        if (value < 0) {
            return std::nullopt;
        }
        return static_cast<SquareId>(value);
    };

    for (int row = 0; row < rows; ++row) {
        for (int column = 0; column < columns; ++column) {
            const auto current = id_at(row, column);
            if (!current.has_value()) {
                continue;
            }

            if (row == 0) {
                topology.add_contact(make_wall_contact(side(*current, 0), 0));
            }
            if (column == columns - 1) {
                topology.add_contact(make_wall_contact(side(*current, 1), 1));
            }
            if (row == rows - 1) {
                topology.add_contact(make_wall_contact(side(*current, 2), 2));
            }
            if (column == 0) {
                topology.add_contact(make_wall_contact(side(*current, 3), 3));
            }

            if (const auto right = id_at(row, column + 1); right.has_value()) {
                topology.add_contact(
                    make_square_contact(side(*current, 1), side(*right, 3))
                );
            }
            if (const auto down = id_at(row + 1, column); down.has_value()) {
                topology.add_contact(
                    make_square_contact(side(*current, 2), side(*down, 0))
                );
            }
            if (const auto down_right = id_at(row + 1, column + 1);
                down_right.has_value()) {
                topology.add_contact(
                    make_square_contact(corner(*current, 2), corner(*down_right, 0))
                );
            }
            if (const auto down_left = id_at(row + 1, column - 1);
                down_left.has_value()) {
                topology.add_contact(
                    make_square_contact(corner(*current, 3), corner(*down_left, 1))
                );
            }
        }
    }

    return topology.normalized();
}

}  // namespace

std::vector<std::string> fixture_names() {
    return {
        "isolated-1",
        "disjoint-2",
        "corner-corner-2",
        "corner-side-2",
        "side-side-2",
        "grid-2x2",
        "grid-3x3",
        "grid-4x4",
        "grid-4x4-minus-one",
    };
}

Topology make_fixture(std::string_view name) {
    if (name == "isolated-1") {
        return Topology(1);
    }
    if (name == "disjoint-2") {
        return Topology(2);
    }
    if (name == "corner-corner-2") {
        Topology topology(2);
        topology.add_contact(make_square_contact(corner(0, 2), corner(1, 0)));
        return topology.normalized();
    }
    if (name == "corner-side-2") {
        Topology topology(2);
        topology.add_contact(make_square_contact(corner(0, 1), side(1, 3)));
        return topology.normalized();
    }
    if (name == "side-side-2") {
        Topology topology(2);
        topology.add_contact(make_square_contact(side(0, 1), side(1, 3)));
        return topology.normalized();
    }
    if (name == "grid-2x2") {
        return make_grid(2, 2);
    }
    if (name == "grid-3x3") {
        return make_grid(3, 3);
    }
    if (name == "grid-4x4") {
        return make_grid(4, 4);
    }
    if (name == "grid-4x4-minus-one") {
        return make_grid(4, 4, std::pair{1, 1});
    }

    throw std::invalid_argument("unknown sqtopology fixture: " + std::string(name));
}

}  // namespace sqtopology
