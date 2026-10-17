// Phase-2 geometric realizability front end. Kept separate from the
// production sqtopology binary: this tool exercises the residual solver and
// the independent verifier from realize.hpp and can dump the machine-readable
// corpus report. Solver outcomes are only ever reported as
// VERIFIED_FEASIBLE / NOT_FOUND / PROVED_INFEASIBLE, and extraction statuses
// are always decided by the verifier, never by solver residuals.
//
// Usage:
//   sqtopology_realize fixtures [--json FILE]
//   sqtopology_realize negative [--json FILE] [--max-solves N]
//   sqtopology_realize corpus --n 2 --weight W [--json FILE]
//       [--max-solves N] [--starts M] [--iterations I] [--steps S]
//       [--no-minimize] [--ladder a,b,c] [--seed S]

#include "sqtopology/export.hpp"
#include "sqtopology/geometry.hpp"
#include "sqtopology/realize.hpp"

#include <chrono>
#include <cmath>
#include <cstdint>
#include <exception>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

using namespace sqtopology;

std::uint32_t parse_positive(std::string_view text, std::string_view option, std::uint64_t maximum) {
    if (text.empty() || text.front() == '-') {
        throw std::invalid_argument(std::string(option) + " expects a positive integer");
    }
    std::size_t consumed = 0;
    const auto value = std::stoull(std::string(text), &consumed);
    if (consumed != text.size() || value == 0 || value > maximum) {
        throw std::invalid_argument(
            std::string(option) + " expects 1 <= value <= " + std::to_string(maximum)
        );
    }
    return static_cast<std::uint32_t>(value);
}

std::vector<double> parse_ladder(std::string_view text) {
    std::vector<double> ladder;
    std::size_t start = 0;
    while (start <= text.size()) {
        const auto comma = text.find(',', start);
        const auto end = comma == std::string_view::npos ? text.size() : comma;
        if (end > start) {
            std::size_t consumed = 0;
            const std::string piece(text.substr(start, end - start));
            const double value = std::stod(piece, &consumed);
            if (consumed != piece.size() || !(value > 0.0)) {
                throw std::invalid_argument("--ladder expects positive numbers");
            }
            ladder.push_back(value);
        }
        if (comma == std::string_view::npos) {
            break;
        }
        start = comma + 1;
    }
    if (ladder.empty()) {
        throw std::invalid_argument("--ladder expects a non-empty list");
    }
    return ladder;
}

void write_status_json(std::ostringstream& out, RealizabilityStatus status) {
    out << '"' << to_string(status) << '"';
}

// JSON has no infinity literal; an unbounded diagnostic (a scene with fewer
// than two squares has no pair slack) is reported as null.
void write_optional_double(std::ostringstream& out, double value) {
    out.precision(17);
    if (std::isfinite(value)) {
        out << value;
    } else {
        out << "null";
    }
}

std::string bool_json(bool value) {
    return value ? "true" : "false";
}

Topology contacts_to_topology(std::uint32_t square_count, const std::vector<Contact>& contacts) {
    Topology topology(square_count);
    for (const auto& contact : contacts) {
        topology.add_contact(contact);
    }
    return topology.normalized();
}

int fixtures_command(int argc, char** argv) {
    std::string json_path;
    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--json") {
            json_path = std::string(value);
        } else {
            throw std::invalid_argument("unknown fixtures option: " + std::string(arg));
        }
    }

    std::ostringstream out;
    out.precision(17);
    out << "{\"schema\":\"sqtopology.realizability-fixtures.v1\""
        << ",\"fixtures\":[";
    bool all_matches = true;
    bool all_contained = true;
    bool all_separated = true;
    const auto fixtures = scene_fixtures();
    for (std::size_t index = 0; index < fixtures.size(); ++index) {
        const auto& fixture = fixtures[index];
        if (index != 0U) {
            out << ',';
        }
        const std::uint32_t square_count =
            static_cast<std::uint32_t>(fixture.scene.squares.size());
        const Topology expected =
            expected_fixture_topology(fixture.expected_fixture, square_count);
        const ExtractionResult extraction = extract_contacts(fixture.scene);
        const WitnessReport report = verify_witness(fixture.scene, expected);
        const auto expected_keys = sorted_contact_keys(expected.contacts());
        const auto extracted_keys = sorted_contact_keys(extraction.exact);
        const bool matches = expected_keys == extracted_keys;
        all_matches = all_matches && matches;
        all_contained = all_contained && report.contained;
        all_separated = all_separated && report.separated;

        out << "{\"name\":\"" << fixture.name << '"'
            << ",\"expected_fixture\":\"" << fixture.expected_fixture << '"'
            << ",\"expected_contacts\":" << topology_contact_keys_json(expected)
            << ",\"extracted_contacts\":" << topology_contact_keys_json(
                   contacts_to_topology(square_count, extraction.exact))
            << ",\"weak_contacts\":" << topology_contact_keys_json(
                   contacts_to_topology(square_count, extraction.weak))
            << ",\"matches\":" << bool_json(matches)
            << ",\"report\":{\"contained\":" << bool_json(report.contained)
            << ",\"separated\":" << bool_json(report.separated)
            << ",\"exact_accepted\":" << bool_json(report.exact_accepted)
            << ",\"weak_accepted\":" << bool_json(report.weak_accepted)
            << ",\"min_separation_slack\":";
        write_optional_double(out, report.min_separation_slack);
        out << ",\"missing_exact\":[";
        for (std::size_t missing = 0; missing < report.missing_exact.size(); ++missing) {
            if (missing != 0U) {
                out << ',';
            }
            out << '"' << report.missing_exact[missing] << '"';
        }
        out << "],\"extra_exact\":[";
        for (std::size_t extra = 0; extra < report.extra_exact.size(); ++extra) {
            if (extra != 0U) {
                out << ',';
            }
            out << '"' << report.extra_exact[extra] << '"';
        }
        out << "]}}";
    }
    out << "],\"checks\":{\"all_matches\":" << bool_json(all_matches)
        << ",\"all_contained\":" << bool_json(all_contained)
        << ",\"all_separated\":" << bool_json(all_separated) << "}}\n";

    const std::string json = out.str();
    if (!json_path.empty()) {
        write_text_file(json_path, json);
    }
    std::cout << json;
    if (!all_matches || !all_contained || !all_separated) {
        std::cerr << "sqtopology_realize: fixture checks failed\n";
        return 1;
    }
    return 0;
}

int negative_command(int argc, char** argv) {
    std::string json_path;
    SolveConfig config;
    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--json") {
            json_path = std::string(value);
        } else if (arg == "--max-solves") {
            config.max_solves = parse_positive(value, "--max-solves", 1000000);
        } else {
            throw std::invalid_argument("unknown negative option: " + std::string(arg));
        }
    }

    std::ostringstream out;
    out.precision(17);
    out << "{\"schema\":\"sqtopology.realizability-negatives.v1\""
        << ",\"fixtures\":[";
    bool all_match_status = true;
    const auto fixtures = negative_fixtures();
    for (std::size_t index = 0; index < fixtures.size(); ++index) {
        const auto& fixture = fixtures[index];
        if (index != 0U) {
            out << ',';
        }
        const SolveResult result = realize_topology(fixture.topology, config);
        const bool status_matches = result.status == fixture.expected_status;
        all_match_status = all_match_status && status_matches;
        out << "{\"name\":\"" << fixture.name << '"'
            << ",\"expected_status\":";
        write_status_json(out, fixture.expected_status);
        out << ",\"status\":";
        write_status_json(out, result.status);
        out << ",\"status_matches\":" << bool_json(status_matches)
            << ",\"filter_reason\":\"" << result.filter_reason << '"'
            << ",\"exact_witness\":" << bool_json(result.exact_witness)
            << ",\"weak_witness\":" << bool_json(result.weak_witness)
            << ",\"solves\":" << result.solves << '}';
    }
    out << "],\"checks\":{\"all_statuses_match\":" << bool_json(all_match_status)
        << "}}\n";

    const std::string json = out.str();
    if (!json_path.empty()) {
        write_text_file(json_path, json);
    }
    std::cout << json;
    if (!all_match_status) {
        std::cerr << "sqtopology_realize: negative fixture statuses differ\n";
        return 1;
    }
    return 0;
}

int corpus_command(int argc, char** argv) {
    std::uint32_t square_count = 0;
    std::uint32_t weight = 0;
    std::string json_path;
    SolveConfig config;
    for (int i = 2; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--no-minimize") {
            config.minimize_container = false;
            continue;
        }
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];
        if (arg == "--n") {
            square_count = parse_positive(value, "--n", 2);
        } else if (arg == "--weight") {
            weight = parse_positive(value, "--weight", 6);
        } else if (arg == "--json") {
            json_path = std::string(value);
        } else if (arg == "--max-solves") {
            config.max_solves = parse_positive(value, "--max-solves", 10000000);
        } else if (arg == "--starts") {
            config.starts_per_rung = parse_positive(value, "--starts", 4096);
        } else if (arg == "--iterations") {
            config.lm_max_iterations = parse_positive(value, "--iterations", 100000);
        } else if (arg == "--steps") {
            config.minimization_steps = parse_positive(value, "--steps", 64);
        } else if (arg == "--ladder") {
            config.ladder = parse_ladder(value);
        } else if (arg == "--seed") {
            config.seed = std::stoull(std::string(value));
        } else {
            throw std::invalid_argument("unknown corpus option: " + std::string(arg));
        }
    }
    if (square_count == 0 || weight == 0) {
        throw std::invalid_argument("corpus requires --n and --weight");
    }

    const auto started = std::chrono::steady_clock::now();
    const CorpusReport report = run_corpus(square_count, weight, config);
    const std::string json = corpus_report_to_json(report);
    const double seconds = std::chrono::duration<double>(
        std::chrono::steady_clock::now() - started
    ).count();

    if (!json_path.empty()) {
        write_text_file(json_path, json);
    }
    std::cout << json;

    std::uint64_t feasible = 0;
    std::uint64_t not_found = 0;
    std::uint64_t infeasible = 0;
    std::uint64_t solves = 0;
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
        solves += entry.solve.solves;
    }
    std::cerr << "sqtopology_realize: n=" << square_count << " weight=" << weight
              << " classes=" << report.classes.size()
              << " feasible=" << feasible << " not_found=" << not_found
              << " proved_infeasible=" << infeasible
              << " solves=" << solves
              << " seconds=" << seconds << '\n';
    return 0;
}

void usage() {
    std::cerr
        << "sqtopology_realize: Phase-2 geometric realizability layer\n\n"
        << "Usage:\n"
        << "  sqtopology_realize fixtures [--json FILE]\n"
        << "  sqtopology_realize negative [--json FILE] [--max-solves N]\n"
        << "  sqtopology_realize corpus --n 2 --weight W [--json FILE]\n"
        << "      [--max-solves N] [--starts M] [--iterations I] [--steps S]\n"
        << "      [--no-minimize] [--ladder a,b,c] [--seed S]\n";
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            usage();
            return 2;
        }
        const std::string_view command = argv[1];
        if (command == "fixtures") {
            return fixtures_command(argc, argv);
        }
        if (command == "negative") {
            return negative_command(argc, argv);
        }
        if (command == "corpus") {
            return corpus_command(argc, argv);
        }
        usage();
        throw std::invalid_argument("unknown command: " + std::string(command));
    } catch (const std::exception& error) {
        std::cerr << "sqtopology_realize: " << error.what() << '\n';
        return 1;
    }
}
