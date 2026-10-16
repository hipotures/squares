#pragma once

#include "sqtopology/topology.hpp"

#include <cstddef>
#include <cstdint>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace sqtopology {

enum class VertexColor : int {
    SquareObject = 1,
    SquareCornerPort = 2,
    SquareSidePort = 3,
    ContainerObject = 4,
    ContainerWall = 5,
    ContactCornerCorner = 6,
    ContactCornerSide = 7,
    ContactSideSide = 8,
    ContactWall = 9,
};

enum class CanonicalBackend : std::uint8_t {
    DenseNauty = 1,
    SparseNauty = 2,
    Traces = 3,
};

[[nodiscard]] std::string_view to_string(CanonicalBackend backend) noexcept;
[[nodiscard]] CanonicalBackend canonical_backend_from_string(std::string_view text);

struct ColoredGraph {
    std::vector<int> colors;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> edges;

    [[nodiscard]] std::size_t vertex_count() const noexcept { return colors.size(); }
    void normalize_edges();
};

struct CanonicalForm {
    std::string encoding;
    std::uint64_t fingerprint{};
    std::vector<int> canonical_colors;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> canonical_edges;
};

// Exact search equality key. fingerprint is only the unordered-set bucket hash;
// bytes remain the equality oracle. SQK2 keys are backend-tagged because different
// canonical-labeling engines are not required to choose identical canonical labels.
struct CanonicalKey {
    std::string bytes;
    std::uint64_t fingerprint{};

    [[nodiscard]] bool operator==(const CanonicalKey& other) const noexcept {
        return bytes == other.bytes;
    }
};

struct CanonicalKeyHash {
    [[nodiscard]] std::size_t operator()(const CanonicalKey& key) const noexcept {
        return static_cast<std::size_t>(key.fingerprint);
    }
};

struct CanonicalProfile {
    std::uint64_t calls{};
    double input_build_seconds{};
    double partition_seconds{};
    double engine_seconds{};
    double output_conversion_seconds{};
    double key_build_seconds{};
    double extraction_seconds{};
    double encoding_seconds{};
    double hash_seconds{};
};

[[nodiscard]] ColoredGraph to_incidence_graph(const Topology& topology);

// Hot-path entry point: caller guarantees semantic validation and normalized contact order.
[[nodiscard]] ColoredGraph to_incidence_graph_validated(const Topology& topology);

// Search-only exact key. All three backends consume the same ColoredGraph and return
// exact backend-local canonical keys.
[[nodiscard]] CanonicalKey canonical_key_colored_graph(
    const ColoredGraph& graph,
    CanonicalBackend backend = CanonicalBackend::Traces,
    CanonicalProfile* profile = nullptr
);
[[nodiscard]] std::string canonical_key_hex(const CanonicalKey& key);

// Human-facing SQT1 form remains dense-nauty based for stable inspection/export.
[[nodiscard]] CanonicalForm canonicalize_colored_graph(
    const ColoredGraph& graph,
    CanonicalProfile* profile = nullptr
);
[[nodiscard]] CanonicalForm canonicalize(
    const Topology& topology,
    CanonicalProfile* profile = nullptr
);
[[nodiscard]] std::uint64_t stable_fingerprint(std::string_view bytes);

}  // namespace sqtopology
