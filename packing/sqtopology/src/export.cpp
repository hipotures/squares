#include "sqtopology/export.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <string_view>

namespace sqtopology {
namespace {

std::string json_escape(std::string_view value) {
    std::ostringstream out;
    for (const char ch : value) {
        switch (ch) {
            case '\\':
                out << "\\\\";
                break;
            case '"':
                out << "\\\"";
                break;
            case '\n':
                out << "\\n";
                break;
            case '\r':
                out << "\\r";
                break;
            case '\t':
                out << "\\t";
                break;
            default:
                out << ch;
                break;
        }
    }
    return out.str();
}

std::string feature_json(const FeatureRef& feature) {
    std::ostringstream out;
    out << "{\"square\":" << feature.square
        << ",\"kind\":\"" << to_string(feature.kind)
        << "\",\"index\":" << static_cast<int>(feature.index)
        << '}';
    return out.str();
}

std::string port_name(const FeatureRef& feature) {
    return "s" + std::to_string(feature.square)
        + "p" + std::to_string(feature_ring_index(feature));
}

}  // namespace

std::string topology_to_json(
    const Topology& input,
    const CanonicalForm& canonical
) {
    const Topology topology = input.normalized();
    std::ostringstream out;
    out << "{\n"
        << "  \"schema\":\"sqtopology.semantic.v1\",\n"
        << "  \"square_count\":" << topology.square_count() << ",\n"
        << "  \"canonical_fingerprint\":\""
        << std::hex << std::setw(16) << std::setfill('0') << canonical.fingerprint
        << std::dec << "\",\n"
        << "  \"canonical_encoding\":\"" << json_escape(canonical.encoding) << "\",\n"
        << "  \"contacts\":[\n";

    for (std::size_t i = 0; i < topology.contacts().size(); ++i) {
        const auto& contact = topology.contacts()[i];
        out << "    {\"kind\":\"" << to_string(contact.kind)
            << "\",\"a\":" << feature_json(contact.a);
        if (contact.b.has_value()) {
            out << ",\"b\":" << feature_json(*contact.b);
        }
        if (contact.wall.has_value()) {
            out << ",\"wall\":" << static_cast<int>(*contact.wall);
        }
        out << '}';
        if (i + 1 != topology.contacts().size()) {
            out << ',';
        }
        out << '\n';
    }

    out << "  ]\n}\n";
    return out.str();
}

std::string topology_to_dot(const Topology& input) {
    const Topology topology = input.normalized();
    std::ostringstream out;
    out << "graph sqtopology {\n"
        << "  graph [overlap=false, splines=true];\n"
        << "  node [fontname=\"Helvetica\", fontsize=9];\n"
        << "  edge [color=\"#777777\"];\n";

    for (SquareId square = 0; square < topology.square_count(); ++square) {
        out << "  subgraph cluster_s" << square << " {\n"
            << "    label=\"square " << square << "\";\n"
            << "    color=\"#cccccc\";\n"
            << "    s" << square
            << " [label=\"S" << square << "\", shape=box, style=filled, fillcolor=\"#eeeeee\"];\n";

        for (std::uint8_t ring = 0; ring < 8; ++ring) {
            const auto feature = feature_from_ring_index(square, ring);
            out << "    s" << square << "p" << static_cast<int>(ring)
                << " [label=\"" << (feature.kind == FeatureKind::Corner ? "C" : "E")
                << static_cast<int>(feature.index)
                << "\", shape=" << (feature.kind == FeatureKind::Corner ? "circle" : "ellipse")
                << "];\n"
                << "    s" << square << " -- s" << square << "p"
                << static_cast<int>(ring)
                << " [color=\"#bbbbbb\"];\n";
        }
        for (std::uint8_t ring = 0; ring < 8; ++ring) {
            out << "    s" << square << "p" << static_cast<int>(ring)
                << " -- s" << square << "p" << static_cast<int>((ring + 1U) % 8U)
                << " [color=\"#dddddd\"];\n";
        }
        out << "  }\n";
    }

    out << "  container [label=\"container\", shape=box, style=filled, fillcolor=\"#ddeeff\"];\n";
    for (std::uint8_t wall = 0; wall < 4; ++wall) {
        out << "  w" << static_cast<int>(wall)
            << " [label=\"wall " << static_cast<int>(wall)
            << "\", shape=box];\n"
            << "  container -- w" << static_cast<int>(wall)
            << " [color=\"#99aacc\"];\n";
    }
    for (std::uint8_t wall = 0; wall < 4; ++wall) {
        out << "  w" << static_cast<int>(wall)
            << " -- w" << static_cast<int>((wall + 1U) % 4U)
            << " [color=\"#bbccdd\"];\n";
    }

    for (std::size_t i = 0; i < topology.contacts().size(); ++i) {
        const auto& contact = topology.contacts()[i];
        out << "  e" << i
            << " [label=\"" << to_string(contact.kind)
            << "\", shape=diamond, style=filled, fillcolor=\"#fff0cc\"];\n"
            << "  e" << i << " -- " << port_name(contact.a)
            << " [penwidth=2];\n";
        if (contact.b.has_value()) {
            out << "  e" << i << " -- " << port_name(*contact.b)
                << " [penwidth=2];\n";
        }
        if (contact.wall.has_value()) {
            out << "  e" << i << " -- w" << static_cast<int>(*contact.wall)
                << " [penwidth=2];\n";
        }
    }

    out << "}\n";
    return out.str();
}

void write_text_file(const std::string& path, const std::string& content) {
    const std::filesystem::path output(path);
    if (output.has_parent_path()) {
        std::filesystem::create_directories(output.parent_path());
    }
    std::ofstream handle(output, std::ios::binary);
    if (!handle) {
        throw std::runtime_error("cannot open output file: " + path);
    }
    handle << content;
    if (!handle) {
        throw std::runtime_error("failed writing output file: " + path);
    }
}

}  // namespace sqtopology
