// Research-only command line front end for the independent event-set /
// group-action oracle. This tool is deliberately separate from the production
// sqtopology binary: its counting and distance results must be derivable from
// the semantic specification alone, with canonicalization only used for
// independent cross-checks elsewhere.
//
// Usage:
//   sqtopology_orbit count --n N [--contributions] [--no-conjugacy] [--json FILE]
//   sqtopology_orbit distance --first FIXTURE --second FIXTURE [--json FILE]
//   sqtopology_orbit matrix --fixtures A,B,C [--json FILE]

#include "sqtopology/export.hpp"
#include "sqtopology/fixtures.hpp"
#include "sqtopology/orbit.hpp"
#include "sqtopology/topology.hpp"

#include <cstdint>
#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using sqtopology::D4Element;
using sqtopology::GroupElement;
using sqtopology::OrbitDistanceResult;

std::uint32_t parse_square_count(std::string_view text) {
    if (text.empty() || text.front() == '-') {
        throw std::invalid_argument("--n expects a positive integer");
    }
    std::size_t consumed = 0;
    const auto value = std::stoul(std::string(text), &consumed);
    if (consumed != text.size() || value == 0 || value > sqtopology::kMaxOrbitSquares) {
        throw std::invalid_argument("--n expects 1 <= n <= 8");
    }
    return static_cast<std::uint32_t>(value);
}

std::vector<std::string> split_list(std::string_view text) {
    std::vector<std::string> result;
    std::size_t start = 0;
    while (start <= text.size()) {
        const auto comma = text.find(',', start);
        const auto end = comma == std::string_view::npos ? text.size() : comma;
        if (end > start) {
            result.emplace_back(text.substr(start, end - start));
        }
        if (comma == std::string_view::npos) {
            break;
        }
        start = comma + 1;
    }
    if (result.empty()) {
        throw std::invalid_argument("expected a non-empty comma-separated fixture list");
    }
    return result;
}

void write_d4_json(std::ostringstream& out, const D4Element& element) {
    out << "{\"rotation\":" << static_cast<int>(element.rotation)
        << ",\"reflected\":" << (element.reflected ? "true" : "false") << '}';
}

void write_group_element_json(std::ostringstream& out, const GroupElement& element) {
    out << "{\"square_map\":[";
    for (sqtopology::SquareId square = 0; square < element.square_count; ++square) {
        if (square != 0) {
            out << ',';
        }
        out << element.square_map[square];
    }
    out << "],\"local\":[";
    for (sqtopology::SquareId square = 0; square < element.square_count; ++square) {
        if (square != 0) {
            out << ',';
        }
        write_d4_json(out, element.local[square]);
    }
    out << "],\"container\":";
    write_d4_json(out, element.container);
    out << '}';
}

void write_distance_pair_json(
    std::ostringstream& out,
    std::string_view first,
    std::string_view second,
    const OrbitDistanceResult& result
) {
    const std::uint64_t weight_gap = result.first_weight > result.second_weight
        ? result.first_weight - result.second_weight
        : result.second_weight - result.first_weight;
    out << "{\"first\":\"" << first << "\",\"second\":\"" << second << "\""
        << ",\"distance\":" << result.distance
        << ",\"first_weight\":" << result.first_weight
        << ",\"second_weight\":" << result.second_weight
        << ",\"weight_gap\":" << weight_gap
        << ",\"structural_excess\":" << (result.distance - weight_gap)
        << ",\"witness\":";
    write_group_element_json(out, result.witness);
    out << ",\"witness_symmetric_difference\":" << result.witness_symmetric_difference
        << '}';
}

int count_command(int argc, char** argv) {
    std::uint32_t square_count = 0;
    bool contributions = false;
    bool conjugacy = true;
    std::string json_path;

    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--contributions") {
            contributions = true;
            continue;
        }
        if (arg == "--no-conjugacy") {
            conjugacy = false;
            continue;
        }
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--n") {
            square_count = parse_square_count(value);
        } else if (arg == "--json") {
            json_path = std::string(value);
        } else {
            throw std::invalid_argument("unknown count option: " + std::string(arg));
        }
    }
    if (square_count == 0) {
        throw std::invalid_argument("count requires --n");
    }

    sqtopology::OrbitCountOptions options;
    options.emit_contributions = contributions;
    options.count_conjugacy_classes = conjugacy;
    const auto result = sqtopology::burnside_orbit_count(square_count, options);
    const std::string json = sqtopology::orbit_count_to_json(result);
    if (!json_path.empty()) {
        sqtopology::write_text_file(json_path, json);
    }
    std::cout << json;
    return 0;
}

int distance_command(int argc, char** argv) {
    std::string first;
    std::string second;
    std::string json_path;
    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--first") {
            first = std::string(value);
        } else if (arg == "--second") {
            second = std::string(value);
        } else if (arg == "--json") {
            json_path = std::string(value);
        } else {
            throw std::invalid_argument("unknown distance option: " + std::string(arg));
        }
    }
    if (first.empty() || second.empty()) {
        throw std::invalid_argument("distance requires --first and --second");
    }

    const auto first_topology = sqtopology::make_fixture(first);
    const auto second_topology = sqtopology::make_fixture(second);
    const auto result = sqtopology::orbit_hamming_distance(first_topology, second_topology);

    std::ostringstream out;
    out << "{\"schema\":\"sqtopology.orbit-distance.v1\""
        << ",\"n\":" << first_topology.square_count()
        << ",\"event_count\":"
        << sqtopology::event_count_for_squares(first_topology.square_count())
        << ",\"group_size\":"
        << sqtopology::group_element_count(first_topology.square_count())
        << ",\"pair\":";
    write_distance_pair_json(out, first, second, result);
    out << "}\n";

    if (!json_path.empty()) {
        sqtopology::write_text_file(json_path, out.str());
    }
    std::cout << out.str();
    return 0;
}

int matrix_command(int argc, char** argv) {
    std::string fixture_list;
    std::string json_path;
    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--fixtures") {
            fixture_list = std::string(value);
        } else if (arg == "--json") {
            json_path = std::string(value);
        } else {
            throw std::invalid_argument("unknown matrix option: " + std::string(arg));
        }
    }
    if (fixture_list.empty()) {
        throw std::invalid_argument("matrix requires --fixtures");
    }

    const auto names = split_list(fixture_list);
    std::vector<sqtopology::Topology> topologies;
    topologies.reserve(names.size());
    for (const auto& name : names) {
        topologies.push_back(sqtopology::make_fixture(name));
    }
    const std::uint32_t square_count = topologies.front().square_count();
    for (std::size_t index = 1; index < topologies.size(); ++index) {
        if (topologies[index].square_count() != square_count) {
            throw std::invalid_argument("all matrix fixtures must share the square count");
        }
    }

    const std::size_t size = names.size();
    std::vector<std::uint64_t> matrix(size * size, 0);
    std::vector<OrbitDistanceResult> pair_results;
    pair_results.reserve(size * size);
    for (std::size_t row = 0; row < size; ++row) {
        for (std::size_t column = 0; column < size; ++column) {
            OrbitDistanceResult result;
            if (row == column) {
                result.first_weight = sqtopology::event_bitset_popcount(
                    sqtopology::topology_to_event_bitset(topologies[row])
                );
                result.second_weight = result.first_weight;
                result.witness = sqtopology::identity_group_element(square_count);
                result.distance = 0;
                result.witness_symmetric_difference = 0;
            } else {
                result = sqtopology::orbit_hamming_distance(
                    topologies[row],
                    topologies[column]
                );
            }
            matrix[row * size + column] = result.distance;
            pair_results.push_back(result);
        }
    }

    bool symmetric = true;
    bool weight_bound = true;
    bool parity = true;
    bool triangles = true;
    for (std::size_t row = 0; row < size; ++row) {
        for (std::size_t column = 0; column < size; ++column) {
            const auto& result = pair_results[row * size + column];
            const std::uint64_t weight_gap = result.first_weight > result.second_weight
                ? result.first_weight - result.second_weight
                : result.second_weight - result.first_weight;
            if (result.distance < weight_gap) {
                weight_bound = false;
            }
            if ((result.distance + result.first_weight + result.second_weight) % 2U != 0U) {
                parity = false;
            }
            if (matrix[row * size + column] != matrix[column * size + row]) {
                symmetric = false;
            }
        }
    }
    for (std::size_t a = 0; a < size; ++a) {
        for (std::size_t b = 0; b < size; ++b) {
            for (std::size_t c = 0; c < size; ++c) {
                if (matrix[a * size + b] + matrix[b * size + c]
                    < matrix[a * size + c]) {
                    triangles = false;
                }
            }
        }
    }

    std::ostringstream out;
    out << std::setprecision(17);
    out << "{\"schema\":\"sqtopology.orbit-distances.v1\""
        << ",\"n\":" << square_count
        << ",\"event_count\":" << sqtopology::event_count_for_squares(square_count)
        << ",\"group_size\":" << sqtopology::group_element_count(square_count)
        << ",\"fixtures\":[";
    for (std::size_t index = 0; index < size; ++index) {
        if (index != 0) {
            out << ',';
        }
        out << '"' << names[index] << '"';
    }
    out << "],\"contact_counts\":[";
    for (std::size_t index = 0; index < size; ++index) {
        if (index != 0) {
            out << ',';
        }
        out << topologies[index].contacts().size();
    }
    out << "],\"matrix\":[";
    for (std::size_t row = 0; row < size; ++row) {
        if (row != 0) {
            out << ',';
        }
        out << '[';
        for (std::size_t column = 0; column < size; ++column) {
            if (column != 0) {
                out << ',';
            }
            out << matrix[row * size + column];
        }
        out << ']';
    }
    out << "],\"pairs\":[";
    bool first_pair = true;
    for (std::size_t row = 0; row < size; ++row) {
        for (std::size_t column = row + 1; column < size; ++column) {
            if (!first_pair) {
                out << ',';
            }
            first_pair = false;
            write_distance_pair_json(
                out,
                names[row],
                names[column],
                pair_results[row * size + column]
            );
        }
    }
    out << "],\"checks\":{\"symmetric_matrix\":" << (symmetric ? "true" : "false")
        << ",\"weight_lower_bound\":" << (weight_bound ? "true" : "false")
        << ",\"weight_parity\":" << (parity ? "true" : "false")
        << ",\"triangle_inequality\":" << (triangles ? "true" : "false")
        << "}}\n";

    if (!json_path.empty()) {
        sqtopology::write_text_file(json_path, out.str());
    }
    std::cout << out.str();
    return 0;
}

void usage() {
    std::cerr
        << "sqtopology_orbit: exact orbit counting and orbit-Hamming distances\n\n"
        << "Usage:\n"
        << "  sqtopology_orbit count --n N [--contributions] [--no-conjugacy] [--json FILE]\n"
        << "  sqtopology_orbit distance --first FIXTURE --second FIXTURE [--json FILE]\n"
        << "  sqtopology_orbit matrix --fixtures A,B,C [--json FILE]\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            usage();
            return 2;
        }
        const std::string_view command = argv[1];
        if (command == "count") {
            return count_command(argc, argv);
        }
        if (command == "distance") {
            return distance_command(argc, argv);
        }
        if (command == "matrix") {
            return matrix_command(argc, argv);
        }
        usage();
        throw std::invalid_argument("unknown command: " + std::string(command));
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_orbit: " << error.what() << '\n';
        return 1;
    }
}
