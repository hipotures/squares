#include "sqtopology/canonical.hpp"

#include <algorithm>
#include <array>
#include <bit>
#include <chrono>
#include <cstdint>
#include <functional>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

extern "C" {
#include <nauty/nausparse.h>
#include <nauty/nauty.h>
}

// Ubuntu 24.04's nauty 2.8.x is configured with C11 TLS and exposes
// TLS_ATTR as _Thread_local through traces.h/gtools.h.  C++ spells the
// equivalent storage specifier thread_local, so translate the token while
// parsing that C header.  The installed library ABI still uses ELF TLS.
#ifdef __cplusplus
#define _Thread_local thread_local
#ifdef NORET_ATTR
#undef NORET_ATTR
#endif
#define NORET_ATTR
#endif
#ifdef SQTOPOLOGY_CACHED_TRACES
#define Traces sqtopology_Traces
#endif
extern "C" {
#include <nauty/traces.h>
#ifdef SQTOPOLOGY_CACHED_TRACES
void sqtopology_traces_freedyn(void);
#endif
}
#ifdef SQTOPOLOGY_CACHED_TRACES
#undef Traces
#endif
#ifdef __cplusplus
#undef NORET_ATTR
#undef _Thread_local
#endif

namespace sqtopology {
namespace {

#ifdef SQTOPOLOGY_CACHED_TRACES
constexpr auto traces_engine = &sqtopology_Traces;
struct TracesScratchCleanup {
    ~TracesScratchCleanup() { sqtopology_traces_freedyn(); }
};
#else
constexpr auto traces_engine = &Traces;
#endif

using Clock = std::chrono::steady_clock;

double seconds_between(Clock::time_point start, Clock::time_point end) {
    return std::chrono::duration<double>(end - start).count();
}

std::uint32_t add_vertex(ColoredGraph& graph, VertexColor color) {
    const auto id = static_cast<std::uint32_t>(graph.colors.size());
    graph.colors.push_back(static_cast<int>(color));
    return id;
}

void add_edge(ColoredGraph& graph, std::uint32_t a, std::uint32_t b) {
    if (a == b) {
        throw std::logic_error("incidence graph attempted to add a self-loop");
    }
    if (b < a) {
        std::swap(a, b);
    }
    graph.edges.emplace_back(a, b);
}

VertexColor contact_color(ContactKind kind) {
    switch (kind) {
        case ContactKind::CornerCorner:
            return VertexColor::ContactCornerCorner;
        case ContactKind::CornerSide:
            return VertexColor::ContactCornerSide;
        case ContactKind::SideSide:
            return VertexColor::ContactSideSide;
        case ContactKind::Wall:
            return VertexColor::ContactWall;
    }
    throw std::logic_error("unknown contact kind");
}

std::string validation_message(const ValidationResult& validation) {
    std::ostringstream out;
    out << "invalid topology";
    for (const auto& error : validation.errors) {
        out << "; " << error;
    }
    return out.str();
}

ColoredGraph build_incidence_graph(const Topology& topology) {
    ColoredGraph graph;
    graph.colors.reserve(
        static_cast<std::size_t>(topology.square_count()) * 9U
        + 5U
        + topology.contacts().size()
    );
    graph.edges.reserve(
        static_cast<std::size_t>(topology.square_count()) * 16U
        + 8U
        + topology.contacts().size() * 2U
    );

    std::vector<std::array<std::uint32_t, 8>> ports(topology.square_count());

    for (SquareId square = 0; square < topology.square_count(); ++square) {
        const auto center = add_vertex(graph, VertexColor::SquareObject);
        for (std::uint8_t ring = 0; ring < 8; ++ring) {
            const bool side = (ring & 1U) != 0;
            const auto port = add_vertex(
                graph,
                side ? VertexColor::SquareSidePort : VertexColor::SquareCornerPort
            );
            ports[square][ring] = port;
            add_edge(graph, center, port);
        }
        for (std::uint8_t ring = 0; ring < 8; ++ring) {
            add_edge(graph, ports[square][ring], ports[square][(ring + 1U) % 8U]);
        }
    }

    const auto container = add_vertex(graph, VertexColor::ContainerObject);
    std::array<std::uint32_t, 4> walls{};
    for (std::uint8_t wall = 0; wall < 4; ++wall) {
        walls[wall] = add_vertex(graph, VertexColor::ContainerWall);
        add_edge(graph, container, walls[wall]);
    }
    for (std::uint8_t wall = 0; wall < 4; ++wall) {
        add_edge(graph, walls[wall], walls[(wall + 1U) % 4U]);
    }

    for (const auto& contact : topology.contacts()) {
        const auto event = add_vertex(graph, contact_color(contact.kind));
        const auto a_port = ports[contact.a.square][feature_ring_index(contact.a)];
        add_edge(graph, event, a_port);

        if (contact.kind == ContactKind::Wall) {
            if (!contact.wall.has_value()) {
                throw std::logic_error("validated wall contact lost wall index");
            }
            add_edge(graph, event, walls[*contact.wall]);
        } else {
            if (!contact.b.has_value()) {
                throw std::logic_error("validated square contact lost second feature");
            }
            const auto b_port = ports[contact.b->square][feature_ring_index(*contact.b)];
            add_edge(graph, event, b_port);
        }
    }

    return graph;
}

struct Partition {
    std::vector<int> lab;
    std::vector<int> ptn;
    std::vector<int> orbits;
};

Partition build_partition(const ColoredGraph& graph) {
    const auto n = graph.vertex_count();

    Partition partition{
        .lab = std::vector<int>(n),
        .ptn = std::vector<int>(n, 0),
        .orbits = std::vector<int>(n, 0),
    };
    // Incidence colors occupy a small integer range. Stable counting placement
    // produces exactly the old (color, vertex ID) ordering without comparison
    // sorting or stable_sort's temporary allocation. Keep the general graph API.
    std::array<std::size_t, 256> counts{};
    int max_color = 0;
    bool byte_colors = true;
    for (const auto color : graph.colors) {
        if (color < 0 || color > 255) {
            byte_colors = false;
            break;
        }
        ++counts[static_cast<std::size_t>(color)];
        max_color = std::max(max_color, color);
    }
    if (byte_colors) {
        std::size_t offset = 0;
        for (int color = 0; color <= max_color; ++color) {
            const auto count = counts[static_cast<std::size_t>(color)];
            counts[static_cast<std::size_t>(color)] = offset;
            offset += count;
        }
        for (std::size_t vertex = 0; vertex < n; ++vertex) {
            const auto color = static_cast<std::size_t>(graph.colors[vertex]);
            partition.lab[counts[color]++] = static_cast<int>(vertex);
        }
    } else {
        std::iota(partition.lab.begin(), partition.lab.end(), 0);
        std::sort(partition.lab.begin(), partition.lab.end(), [&graph](int lhs, int rhs) {
            const auto lhs_color = graph.colors[static_cast<std::size_t>(lhs)];
            const auto rhs_color = graph.colors[static_cast<std::size_t>(rhs)];
            return lhs_color != rhs_color ? lhs_color < rhs_color : lhs < rhs;
        });
    }

    for (std::size_t i = 0; i + 1U < n; ++i) {
        const auto current = graph.colors[
            static_cast<std::size_t>(partition.lab[i])
        ];
        const auto next = graph.colors[
            static_cast<std::size_t>(partition.lab[i + 1U])
        ];
        partition.ptn[i] = current == next ? 1 : 0;
    }
    if (!partition.ptn.empty()) {
        partition.ptn.back() = 0;
    }

    return partition;
}

class SparseGraphOwner {
public:
    SparseGraphOwner() {
        SG_INIT(graph_);
    }

    ~SparseGraphOwner() {
        SG_FREE(graph_);
    }

    SparseGraphOwner(const SparseGraphOwner&) = delete;
    SparseGraphOwner& operator=(const SparseGraphOwner&) = delete;

    [[nodiscard]] sparsegraph* get() noexcept {
        return &graph_;
    }

    [[nodiscard]] const sparsegraph* get() const noexcept {
        return &graph_;
    }

private:
    sparsegraph graph_{};
};

void fill_sparse_graph(
    const ColoredGraph& graph,
    sparsegraph& sparse
) {
    const auto n = graph.vertex_count();
    const auto directed_edges = graph.edges.size() * 2U;

    SG_ALLOC(
        sparse,
        n,
        directed_edges,
        "sqtopology sparse canonical graph"
    );

    sparse.nv = static_cast<int>(n);
    sparse.nde = directed_edges;

    for (std::size_t vertex = 0; vertex < n; ++vertex) {
        sparse.d[vertex] = 0;
    }

    for (const auto& [a_raw, b_raw] : graph.edges) {
        if (a_raw >= n || b_raw >= n) {
            throw std::invalid_argument("colored graph edge endpoint outside vertex range");
        }
        if (a_raw == b_raw) {
            throw std::invalid_argument("colored graph contains a self-loop");
        }
        ++sparse.d[a_raw];
        ++sparse.d[b_raw];
    }

    std::size_t cursor = 0;
    for (std::size_t vertex = 0; vertex < n; ++vertex) {
        sparse.v[vertex] = cursor;
        cursor += static_cast<std::size_t>(sparse.d[vertex]);
    }

    std::vector<std::size_t> next(n);
    for (std::size_t vertex = 0; vertex < n; ++vertex) {
        next[vertex] = sparse.v[vertex];
    }

    for (const auto& [a_raw, b_raw] : graph.edges) {
        sparse.e[next[a_raw]++] = static_cast<int>(b_raw);
        sparse.e[next[b_raw]++] = static_cast<int>(a_raw);
    }
}

struct CanonicalBackendResult {
    CanonicalBackend backend{CanonicalBackend::DenseNauty};
    int n{};
    int m{};
    std::vector<int> lab;
    std::vector<::graph> canonical_dense;
    std::vector<std::pair<std::uint32_t, std::uint32_t>> canonical_edges;
};

std::vector<std::pair<std::uint32_t, std::uint32_t>> extract_dense_edges(
    const std::vector<::graph>& dense,
    int m,
    int n
) {
    std::vector<std::pair<std::uint32_t, std::uint32_t>> edges;
    for (int i = 0; i < n; ++i) {
        const auto* row = GRAPHROW(dense.data(), i, m);
        for (int j = i + 1; j < n; ++j) {
            if (ISELEMENT(row, j)) {
                edges.emplace_back(
                    static_cast<std::uint32_t>(i),
                    static_cast<std::uint32_t>(j)
                );
            }
        }
    }
    return edges;
}

std::vector<std::pair<std::uint32_t, std::uint32_t>> extract_sparse_edges(
    const sparsegraph& sparse
) {
    if (sparse.nv < 0) {
        throw std::logic_error("canonical sparse graph has negative vertex count");
    }

    const auto n = static_cast<std::size_t>(sparse.nv);
    std::vector<std::pair<std::uint32_t, std::uint32_t>> edges;
    edges.reserve(static_cast<std::size_t>(sparse.nde) / 2U);

    if (n <= 256U) {
        // Exact row ordering with four machine words avoids temporary neighbor
        // vectors and comparison sorting. Iterate only occupied words/bits.
        for (std::size_t vertex = 0; vertex < n; ++vertex) {
            std::array<std::uint64_t, 4> neighbors{};
            unsigned occupied = 0;
            for (int offset = 0; offset < sparse.d[vertex]; ++offset) {
                const int raw = sparse.e[sparse.v[vertex] + static_cast<std::size_t>(offset)];
                if (raw < 0 || static_cast<std::size_t>(raw) >= n || raw == static_cast<int>(vertex)) {
                    throw std::logic_error("canonical sparse graph has an invalid endpoint");
                }
                const auto neighbor = static_cast<unsigned>(raw);
                if (vertex < neighbor) {
                    const auto word = neighbor / 64U;
                    const auto bit = std::uint64_t{1} << (neighbor % 64U);
                    if (neighbors[word] & bit) {
                        throw std::logic_error("canonical sparse graph contains duplicate edges");
                    }
                    neighbors[word] |= bit;
                    occupied |= 1U << word;
                }
            }
            while (occupied) {
                const auto word = std::countr_zero(occupied);
                occupied &= occupied - 1U;
                auto bits = neighbors[static_cast<std::size_t>(word)];
                while (bits) {
                    const auto neighbor = static_cast<std::uint32_t>(word * 64 + std::countr_zero(bits));
                    bits &= bits - 1U;
                    edges.emplace_back(static_cast<std::uint32_t>(vertex), neighbor);
                }
            }
        }
        if (edges.size() * 2U != static_cast<std::size_t>(sparse.nde)) {
            throw std::logic_error("canonical sparse graph is not simple and undirected");
        }
        return edges;
    }

    // Canonical vertices are visited in ascending order, so only each vertex's
    // forward-neighbor list needs sorting. Incidence degrees are small; this is
    // cheaper than collecting every edge and globally sorting O(E log E).
    std::vector<std::uint32_t> forward_neighbors;
    for (std::size_t vertex = 0; vertex < n; ++vertex) {
        forward_neighbors.clear();
        const auto begin = sparse.v[vertex];
        const auto degree = static_cast<std::size_t>(sparse.d[vertex]);
        forward_neighbors.reserve(
            std::max(forward_neighbors.capacity(), degree)
        );

        for (std::size_t offset = 0; offset < degree; ++offset) {
            const int neighbor_raw = sparse.e[begin + offset];
            if (neighbor_raw < 0
                || static_cast<std::size_t>(neighbor_raw) >= n) {
                throw std::logic_error(
                    "canonical sparse graph edge endpoint outside vertex range"
                );
            }
            const auto neighbor = static_cast<std::size_t>(neighbor_raw);
            if (neighbor == vertex) {
                throw std::logic_error(
                    "canonical sparse graph unexpectedly contains a self-loop"
                );
            }
            if (vertex < neighbor) {
                forward_neighbors.push_back(
                    static_cast<std::uint32_t>(neighbor)
                );
            }
        }

        std::sort(forward_neighbors.begin(), forward_neighbors.end());
        if (std::adjacent_find(
                forward_neighbors.begin(),
                forward_neighbors.end()
            ) != forward_neighbors.end()) {
            throw std::logic_error(
                "canonical sparse graph unexpectedly contains duplicate edges"
            );
        }

        for (const auto neighbor : forward_neighbors) {
            edges.emplace_back(
                static_cast<std::uint32_t>(vertex),
                neighbor
            );
        }
    }

    if (edges.size() * 2U != static_cast<std::size_t>(sparse.nde)) {
        throw std::logic_error(
            "canonical sparse graph is not a simple undirected graph"
        );
    }
    return edges;
}

void profile_add(
    double& destination,
    CanonicalProfile* profile,
    Clock::time_point start
) {
    if (profile != nullptr) {
        destination += seconds_between(start, Clock::now());
    }
}

CanonicalBackendResult run_dense_nauty(
    const ColoredGraph& graph,
    CanonicalProfile* profile
) {
    const int n = static_cast<int>(graph.vertex_count());
    const int m = SETWORDSNEEDED(n);
    nauty_check(WORDSIZE, m, n, NAUTYVERSIONID);

    auto stage_started = Clock::now();

    std::vector<::graph> dense(
        static_cast<std::size_t>(m) * static_cast<std::size_t>(n)
    );
    std::vector<::graph> canonical_dense(
        static_cast<std::size_t>(m) * static_cast<std::size_t>(n)
    );
    EMPTYGRAPH(dense.data(), m, n);

    for (const auto& [a_raw, b_raw] : graph.edges) {
        if (a_raw >= graph.vertex_count() || b_raw >= graph.vertex_count()) {
            throw std::invalid_argument("colored graph edge endpoint outside vertex range");
        }
        if (a_raw == b_raw) {
            throw std::invalid_argument("colored graph contains a self-loop");
        }
        ADDONEEDGE(
            dense.data(),
            static_cast<int>(a_raw),
            static_cast<int>(b_raw),
            m
        );
    }

    if (profile != nullptr) {
        profile_add(profile->input_build_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    auto partition = build_partition(graph);

    if (profile != nullptr) {
        profile_add(profile->partition_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    DEFAULTOPTIONS_GRAPH(options);
    options.getcanon = TRUE;
    options.defaultptn = FALSE;
    statsblk stats{};

    densenauty(
        dense.data(),
        partition.lab.data(),
        partition.ptn.data(),
        partition.orbits.data(),
        &options,
        &stats,
        m,
        n,
        canonical_dense.data()
    );

    if (profile != nullptr) {
        profile_add(profile->engine_seconds, profile, stage_started);
    }

    if (stats.errstatus != 0) {
        throw std::runtime_error(
            "densenauty canonicalization failed with errstatus "
            + std::to_string(stats.errstatus)
        );
    }

    return CanonicalBackendResult{
        .backend = CanonicalBackend::DenseNauty,
        .n = n,
        .m = m,
        .lab = std::move(partition.lab),
        .canonical_dense = std::move(canonical_dense),
        .canonical_edges = {},
    };
}

CanonicalBackendResult run_sparse_backend(
    const ColoredGraph& graph,
    CanonicalBackend backend,
    CanonicalProfile* profile
) {
    if (backend != CanonicalBackend::SparseNauty
        && backend != CanonicalBackend::Traces) {
        throw std::logic_error("run_sparse_backend called with a dense backend");
    }

    const int n = static_cast<int>(graph.vertex_count());
    const int m = SETWORDSNEEDED(n);
    nauty_check(WORDSIZE, m, n, NAUTYVERSIONID);

    auto stage_started = Clock::now();

    SparseGraphOwner input;
    SparseGraphOwner canonical;
    fill_sparse_graph(graph, *input.get());

    if (profile != nullptr) {
        profile_add(profile->input_build_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    auto partition = build_partition(graph);

    if (profile != nullptr) {
        profile_add(profile->partition_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    if (backend == CanonicalBackend::SparseNauty) {
        DEFAULTOPTIONS_SPARSEGRAPH(options);
        options.getcanon = TRUE;
        options.defaultptn = FALSE;
        statsblk stats{};

        sparsenauty(
            input.get(),
            partition.lab.data(),
            partition.ptn.data(),
            partition.orbits.data(),
            &options,
            &stats,
            canonical.get()
        );

        if (profile != nullptr) {
            profile_add(profile->engine_seconds, profile, stage_started);
            stage_started = Clock::now();
        }

        if (stats.errstatus != 0) {
            throw std::runtime_error(
                "sparsenauty canonicalization failed with errstatus "
                + std::to_string(stats.errstatus)
            );
        }
    } else {
        DEFAULTOPTIONS_TRACES(options);
        options.getcanon = TRUE;
        options.defaultptn = FALSE;
        TracesStats stats{};

#ifdef SQTOPOLOGY_CACHED_TRACES
        // The private engine retains bounded scratch, never canonical results.
        // TLS ownership follows the library's thread model and ends with this thread.
        thread_local TracesScratchCleanup scratch_cleanup;
        (void)scratch_cleanup;
#endif
        traces_engine(
            input.get(),
            partition.lab.data(),
            partition.ptn.data(),
            partition.orbits.data(),
            &options,
            &stats,
            canonical.get()
        );

        if (profile != nullptr) {
            profile_add(profile->engine_seconds, profile, stage_started);
            stage_started = Clock::now();
        }

        if (stats.errstatus != 0) {
            throw std::runtime_error(
                "Traces canonicalization failed with errstatus "
                + std::to_string(stats.errstatus)
            );
        }
    }

    auto canonical_edges = extract_sparse_edges(*canonical.get());

    if (profile != nullptr) {
        profile_add(profile->output_prepare_seconds, profile, stage_started);
    }

    return CanonicalBackendResult{
        .backend = backend,
        .n = n,
        .m = 0,
        .lab = std::move(partition.lab),
        .canonical_dense = {},
        .canonical_edges = std::move(canonical_edges),
    };
}

CanonicalBackendResult run_backend(
    const ColoredGraph& graph,
    CanonicalBackend backend,
    CanonicalProfile* profile
) {
    if (graph.colors.empty()) {
        throw std::invalid_argument("cannot canonicalize an empty graph");
    }
    if (profile != nullptr) {
        ++profile->calls;
    }

    switch (backend) {
        case CanonicalBackend::DenseNauty:
            return run_dense_nauty(graph, profile);
        case CanonicalBackend::SparseNauty:
        case CanonicalBackend::Traces:
            return run_sparse_backend(graph, backend, profile);
    }
    throw std::logic_error("unknown canonical backend");
}

void append_u32_be(std::string& bytes, std::uint32_t value) {
    bytes.push_back(static_cast<char>((value >> 24U) & 0xffU));
    bytes.push_back(static_cast<char>((value >> 16U) & 0xffU));
    bytes.push_back(static_cast<char>((value >> 8U) & 0xffU));
    bytes.push_back(static_cast<char>(value & 0xffU));
}

std::uint8_t endpoint_width_for_vertex_count(std::uint32_t n) {
    if (n <= 256U) {
        return 1U;
    }
    if (n <= 65536U) {
        return 2U;
    }
    return 4U;
}

void append_index_be(
    std::string& bytes,
    std::uint32_t value,
    std::uint8_t width
) {
    for (std::uint8_t byte = 0; byte < width; ++byte) {
        const auto shift = static_cast<unsigned>((width - 1U - byte) * 8U);
        bytes.push_back(static_cast<char>((value >> shift) & 0xffU));
    }
}

std::string build_binary_key_bytes(
    const ColoredGraph& graph,
    const CanonicalBackendResult& canonical
) {
    constexpr std::string_view magic = "SQK4";

    if (canonical.n <= 0) {
        throw std::logic_error("SQK4 requires a non-empty canonical graph");
    }

    std::vector<std::pair<std::uint32_t, std::uint32_t>> dense_edges;
    const std::vector<std::pair<std::uint32_t, std::uint32_t>>* edges =
        &canonical.canonical_edges;

    if (canonical.backend == CanonicalBackend::DenseNauty) {
        dense_edges = extract_dense_edges(
            canonical.canonical_dense,
            canonical.m,
            canonical.n
        );
        edges = &dense_edges;
    }

    if (edges->size() > std::numeric_limits<std::uint32_t>::max()) {
        throw std::logic_error("SQK4 edge count exceeds 32-bit encoding");
    }

    const auto n = static_cast<std::uint32_t>(canonical.n);
    const auto endpoint_width = endpoint_width_for_vertex_count(n);
    const auto edge_bytes =
        edges->size()
        * 2U
        * static_cast<std::size_t>(endpoint_width);

    std::string bytes;
    bytes.reserve(
        magic.size()
        + 1U
        + 4U
        + 1U
        + 4U
        + static_cast<std::size_t>(n)
        + edge_bytes
    );

    bytes.append(magic);
    bytes.push_back(static_cast<char>(canonical.backend));
    append_u32_be(bytes, n);
    bytes.push_back(static_cast<char>(endpoint_width));
    append_u32_be(bytes, static_cast<std::uint32_t>(edges->size()));

    for (int i = 0; i < canonical.n; ++i) {
        const auto color = graph.colors[
            static_cast<std::size_t>(canonical.lab[static_cast<std::size_t>(i)])
        ];
        if (color < 0 || color > 255) {
            throw std::logic_error("canonical vertex color outside SQK4 byte range");
        }
        bytes.push_back(static_cast<char>(color));
    }

    if (endpoint_width == 1U) {
        // The common incidence graph fits in a byte. Allocate the final range
        // once and write endpoints directly, preserving SQK4 byte for byte.
        const auto offset = bytes.size();
        bytes.resize(offset + edge_bytes);
        auto* output = bytes.data() + offset;
        for (const auto& [a, b] : *edges) {
            if (a >= b || b >= n) {
                throw std::logic_error("SQK4 canonical edge list is not normalized");
            }
            *output++ = static_cast<char>(a);
            *output++ = static_cast<char>(b);
        }
    } else {
        for (const auto& [a, b] : *edges) {
            if (a >= b || b >= n) {
                throw std::logic_error("SQK4 canonical edge list is not normalized");
            }
            append_index_be(bytes, a, endpoint_width);
            append_index_be(bytes, b, endpoint_width);
        }
    }

    return bytes;
}

}  // namespace

std::string_view to_string(CanonicalBackend backend) noexcept {
    switch (backend) {
        case CanonicalBackend::DenseNauty:
            return "dense-nauty";
        case CanonicalBackend::SparseNauty:
            return "sparse-nauty";
        case CanonicalBackend::Traces:
            return "traces";
    }
    return "unknown";
}

CanonicalBackend canonical_backend_from_string(std::string_view text) {
    if (text == "dense-nauty" || text == "dense") {
        return CanonicalBackend::DenseNauty;
    }
    if (text == "sparse-nauty" || text == "sparse") {
        return CanonicalBackend::SparseNauty;
    }
    if (text == "traces") {
        return CanonicalBackend::Traces;
    }
    throw std::invalid_argument(
        "unknown canonical backend '" + std::string(text)
        + "' (expected dense-nauty, sparse-nauty, or traces)"
    );
}

void ColoredGraph::normalize_edges() {
    for (auto& [a, b] : edges) {
        if (b < a) {
            std::swap(a, b);
        }
    }
    std::sort(edges.begin(), edges.end());
    edges.erase(std::unique(edges.begin(), edges.end()), edges.end());
}

ColoredGraph to_incidence_graph(const Topology& input) {
    const auto validation = input.validate();
    if (!validation.ok()) {
        throw std::invalid_argument(validation_message(validation));
    }

    const Topology topology = input.normalized();
    return build_incidence_graph(topology);
}

ColoredGraph to_incidence_graph_validated(const Topology& topology) {
    return build_incidence_graph(topology);
}

CanonicalKey canonical_key_colored_graph(
    const ColoredGraph& graph,
    CanonicalBackend backend,
    CanonicalProfile* profile
) {
    const auto canonical = run_backend(graph, backend, profile);

    Clock::time_point stage_started{};
    if (profile != nullptr) {
        stage_started = Clock::now();
    }

    CanonicalKey key;
    key.bytes = build_binary_key_bytes(graph, canonical);

    if (profile != nullptr) {
        profile_add(profile->key_build_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    // Bucket selection only: full bytes remain the equality oracle. libstdc++
    // hashes blocks rather than the serial byte-at-a-time inspection FNV hash.
    key.fingerprint = std::hash<std::string_view>{}(key.bytes);

    if (profile != nullptr) {
        profile_add(profile->hash_seconds, profile, stage_started);
    }

    return key;
}

std::string canonical_key_hex(const CanonicalKey& key) {
    constexpr char hex[] = "0123456789abcdef";
    std::string text;
    text.reserve(8U + key.bytes.size() * 2U);
    text.append("SQK4HEX:");
    for (const unsigned char byte : key.bytes) {
        text.push_back(hex[byte >> 4U]);
        text.push_back(hex[byte & 0x0fU]);
    }
    return text;
}

CanonicalForm canonicalize_colored_graph(
    const ColoredGraph& graph,
    CanonicalProfile* profile
) {
    const auto canonical = run_backend(
        graph,
        CanonicalBackend::DenseNauty,
        profile
    );

    Clock::time_point stage_started{};
    if (profile != nullptr) {
        stage_started = Clock::now();
    }

    CanonicalForm result;
    result.canonical_colors.resize(static_cast<std::size_t>(canonical.n));
    for (int i = 0; i < canonical.n; ++i) {
        result.canonical_colors[static_cast<std::size_t>(i)] =
            graph.colors[
                static_cast<std::size_t>(canonical.lab[static_cast<std::size_t>(i)])
            ];
    }

    for (int i = 0; i < canonical.n; ++i) {
        const auto* row = GRAPHROW(
            canonical.canonical_dense.data(),
            i,
            canonical.m
        );
        for (int j = i + 1; j < canonical.n; ++j) {
            if (ISELEMENT(row, j)) {
                result.canonical_edges.emplace_back(
                    static_cast<std::uint32_t>(i),
                    static_cast<std::uint32_t>(j)
                );
            }
        }
    }

    if (profile != nullptr) {
        profile_add(profile->extraction_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    std::ostringstream encoding;
    encoding << "SQT1|n:" << canonical.n << "|c:";
    for (std::size_t i = 0; i < result.canonical_colors.size(); ++i) {
        if (i != 0) {
            encoding << ',';
        }
        encoding << result.canonical_colors[i];
    }
    encoding << "|e:";
    for (std::size_t i = 0; i < result.canonical_edges.size(); ++i) {
        if (i != 0) {
            encoding << ',';
        }
        encoding << result.canonical_edges[i].first
                 << '-'
                 << result.canonical_edges[i].second;
    }
    result.encoding = encoding.str();

    if (profile != nullptr) {
        profile_add(profile->encoding_seconds, profile, stage_started);
        stage_started = Clock::now();
    }

    result.fingerprint = stable_fingerprint(result.encoding);

    if (profile != nullptr) {
        profile_add(profile->hash_seconds, profile, stage_started);
    }

    return result;
}

CanonicalForm canonicalize(
    const Topology& topology,
    CanonicalProfile* profile
) {
    return canonicalize_colored_graph(to_incidence_graph(topology), profile);
}

std::uint64_t stable_fingerprint(std::string_view bytes) {
    constexpr std::uint64_t offset = 14695981039346656037ULL;
    constexpr std::uint64_t prime = 1099511628211ULL;
    std::uint64_t hash = offset;
    for (const unsigned char byte : bytes) {
        hash ^= static_cast<std::uint64_t>(byte);
        hash *= prime;
    }
    return hash;
}

}  // namespace sqtopology
