#include "sqtopology/canonical.hpp"
#include "sqtopology/export.hpp"
#include "sqtopology/fixtures.hpp"
#include "sqtopology/rewrite.hpp"
#include "sqtopology/search.hpp"

#include <exception>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

using sqtopology::SearchOptions;
using sqtopology::Shard;

std::size_t parse_size(std::string_view text, std::string_view option) {
    if (text.empty() || text.front() == '-') {
        throw std::invalid_argument(std::string(option) + " expects a non-negative integer");
    }
    std::size_t consumed = 0;
    const auto value = std::stoull(std::string(text), &consumed);
    if (consumed != text.size()) {
        throw std::invalid_argument(std::string(option) + " expects an integer");
    }
    return static_cast<std::size_t>(value);
}

double parse_double(std::string_view text, std::string_view option) {
    std::size_t consumed = 0;
    const double value = std::stod(std::string(text), &consumed);
    if (consumed != text.size() || value < 0.0) {
        throw std::invalid_argument(std::string(option) + " expects a non-negative number");
    }
    return value;
}

Shard parse_shard(std::string_view text) {
    const auto slash = text.find('/');
    if (slash == std::string_view::npos) {
        throw std::invalid_argument("--shard expects INDEX/COUNT");
    }
    const auto index = parse_size(text.substr(0, slash), "--shard");
    const auto count = parse_size(text.substr(slash + 1), "--shard");
    if (count == 0 || index >= count) {
        throw std::invalid_argument("--shard requires 0 <= INDEX < COUNT");
    }
    return Shard{.index = index, .count = count};
}

std::string fingerprint_hex(std::uint64_t value) {
    std::ostringstream out;
    out << std::hex << std::setw(16) << std::setfill('0') << value;
    return out.str();
}

void usage() {
    std::cerr
        << "sqtopology phase-1 discrete topology engine\n\n"
        << "Usage:\n"
        << "  sqtopology list-fixtures\n"
        << "  sqtopology inspect FIXTURE [--json FILE] [--dot FILE] [--canonical]\n"
        << "  sqtopology neighbors FIXTURE [--max-additions N]\n"
        << "  sqtopology search FIXTURE [options]\n\n"
        << "Search options:\n"
        << "  --seconds S\n"
        << "  --max-candidates N      (0 = unlimited)\n"
        << "  --max-unique N          (0 = unlimited; use with care)\n"
        << "  --max-depth N\n"
        << "  --max-additions N\n"
        << "  --shard INDEX/COUNT\n"
        << "  --canonical-backend dense-nauty|sparse-nauty|traces (default: traces)\n"
        << "  --json\n"
        << "  --profile-canonical\n"
        << "  --emit-keys FILE\n";
}

int inspect_command(int argc, char** argv) {
    if (argc < 3) {
        throw std::invalid_argument("inspect requires a fixture name");
    }

    const std::string fixture = argv[2];
    std::string json_path;
    std::string dot_path;
    bool print_canonical = false;

    for (int i = 3; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--canonical") {
            print_canonical = true;
        } else if (arg == "--json" || arg == "--dot") {
            if (i + 1 >= argc) {
                throw std::invalid_argument(std::string(arg) + " requires a path");
            }
            const std::string path = argv[++i];
            if (arg == "--json") {
                json_path = path;
            } else {
                dot_path = path;
            }
        } else {
            throw std::invalid_argument("unknown inspect option: " + std::string(arg));
        }
    }

    const auto topology = sqtopology::make_fixture(fixture);
    const auto canonical = sqtopology::canonicalize(topology);

    if (!json_path.empty()) {
        sqtopology::write_text_file(
            json_path,
            sqtopology::topology_to_json(topology, canonical)
        );
    }
    if (!dot_path.empty()) {
        sqtopology::write_text_file(dot_path, sqtopology::topology_to_dot(topology));
    }

    std::cout << "fixture=" << fixture
              << " squares=" << topology.square_count()
              << " contacts=" << topology.contacts().size()
              << " canonical=" << fingerprint_hex(canonical.fingerprint)
              << '\n';
    if (print_canonical) {
        std::cout << canonical.encoding << '\n';
    }
    return 0;
}

int neighbors_command(int argc, char** argv) {
    if (argc < 3) {
        throw std::invalid_argument("neighbors requires a fixture name");
    }
    const std::string fixture = argv[2];
    std::size_t max_additions = 256;

    for (int i = 3; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--max-additions") {
            if (i + 1 >= argc) {
                throw std::invalid_argument("--max-additions requires a value");
            }
            max_additions = parse_size(argv[++i], "--max-additions");
        } else {
            throw std::invalid_argument("unknown neighbors option: " + std::string(arg));
        }
    }

    const auto topology = sqtopology::make_fixture(fixture);
    const auto rewrites = sqtopology::generate_rewrites(
        topology,
        sqtopology::RewriteOptions{
            .include_removals = true,
            .include_additions = true,
            .max_additions = max_additions,
        }
    );

    std::cout << "rewrites=" << rewrites.size() << '\n';
    for (const auto& rewrite : rewrites) {
        const auto form = sqtopology::canonicalize(rewrite.topology);
        std::cout << fingerprint_hex(form.fingerprint)
                  << ' ' << rewrite.label << '\n';
    }
    return 0;
}

int search_command(int argc, char** argv) {
    if (argc < 3) {
        throw std::invalid_argument("search requires a fixture name");
    }

    const std::string fixture = argv[2];
    SearchOptions options;
    bool json = false;
    std::string emit_keys;

    for (int i = 3; i < argc; ++i) {
        const std::string_view arg = argv[i];
        if (arg == "--json") {
            json = true;
            continue;
        }
        if (arg == "--profile-canonical") {
            options.profile_canonical = true;
            continue;
        }
        if (i + 1 >= argc) {
            throw std::invalid_argument(std::string(arg) + " requires a value");
        }
        const std::string_view value = argv[++i];

        if (arg == "--seconds") {
            options.wall_seconds = parse_double(value, arg);
        } else if (arg == "--max-candidates") {
            options.max_candidates = parse_size(value, arg);
        } else if (arg == "--max-unique") {
            options.max_unique = parse_size(value, arg);
        } else if (arg == "--max-depth") {
            options.max_depth = parse_size(value, arg);
        } else if (arg == "--max-additions") {
            options.max_additions_per_parent = parse_size(value, arg);
        } else if (arg == "--shard") {
            options.shard = parse_shard(value);
        } else if (arg == "--canonical-backend") {
            options.canonical_backend = sqtopology::canonical_backend_from_string(value);
        } else if (arg == "--emit-keys") {
            emit_keys = std::string(value);
            options.retain_keys = true;
        } else {
            throw std::invalid_argument("unknown search option: " + std::string(arg));
        }
    }

    const auto seed = sqtopology::make_fixture(fixture);
    const auto result = sqtopology::run_search(seed, options);

    if (!emit_keys.empty()) {
        std::ostringstream keys;
        for (const auto& key : result.unique_encodings) {
            keys << key << '\n';
        }
        sqtopology::write_text_file(emit_keys, keys.str());
    }

    if (json) {
        std::cout << sqtopology::search_stats_to_json(result.stats, options.shard);
    } else {
        const auto& stats = result.stats;
        const double throughput = stats.wall_seconds > 0.0
            ? static_cast<double>(stats.raw_candidates) / stats.wall_seconds
            : 0.0;
        std::cout
            << "backend=" << sqtopology::to_string(options.canonical_backend)
            << " shard=" << options.shard.index << '/' << options.shard.count
            << " candidates=" << stats.raw_candidates
            << " valid=" << stats.valid_candidates
            << " canonicalizations=" << stats.canonicalizations
            << " duplicates=" << stats.duplicates
            << " unique=" << stats.unique_states
            << " wall_s=" << stats.wall_seconds
            << " candidates_per_s=" << throughput
            << '\n';
    }
    return 0;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        if (argc < 2) {
            usage();
            return 2;
        }

        const std::string_view command = argv[1];
        if (command == "list-fixtures") {
            for (const auto& name : sqtopology::fixture_names()) {
                std::cout << name << '\n';
            }
            return 0;
        }
        if (command == "inspect") {
            return inspect_command(argc, argv);
        }
        if (command == "neighbors") {
            return neighbors_command(argc, argv);
        }
        if (command == "search") {
            return search_command(argc, argv);
        }

        usage();
        throw std::invalid_argument("unknown command: " + std::string(command));
    } catch (const std::exception& error) {
        std::cerr << "sqtopology: " << error.what() << '\n';
        return 1;
    }
}
