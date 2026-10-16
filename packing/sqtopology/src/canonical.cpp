#include "sqtopology/canonical.hpp"

#include <algorithm>
#include <array>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string_view>

extern "C" {
#include <nauty/nauty.h>
}

namespace sqtopology {
namespace {

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

}  // namespace

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

CanonicalForm canonicalize_colored_graph(const ColoredGraph& graph) {
    if (graph.colors.empty()) {
        throw std::invalid_argument("cannot canonicalize an empty graph");
    }

    const int n = static_cast<int>(graph.vertex_count());
    const int m = SETWORDSNEEDED(n);
    nauty_check(WORDSIZE, m, n, NAUTYVERSIONID);

    std::vector<::graph> dense(static_cast<std::size_t>(m) * static_cast<std::size_t>(n));
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

    std::vector<int> lab(static_cast<std::size_t>(n));
    std::vector<int> ptn(static_cast<std::size_t>(n), 0);
    std::vector<int> orbits(static_cast<std::size_t>(n), 0);
    std::iota(lab.begin(), lab.end(), 0);

    std::stable_sort(
        lab.begin(),
        lab.end(),
        [&graph](int lhs, int rhs) {
            if (graph.colors[static_cast<std::size_t>(lhs)]
                != graph.colors[static_cast<std::size_t>(rhs)]) {
                return graph.colors[static_cast<std::size_t>(lhs)]
                    < graph.colors[static_cast<std::size_t>(rhs)];
            }
            return lhs < rhs;
        }
    );

    for (int i = 0; i + 1 < n; ++i) {
        const auto current = graph.colors[static_cast<std::size_t>(lab[i])];
        const auto next = graph.colors[static_cast<std::size_t>(lab[i + 1])];
        ptn[static_cast<std::size_t>(i)] = current == next ? 1 : 0;
    }
    ptn.back() = 0;

    DEFAULTOPTIONS_GRAPH(options);
    options.getcanon = TRUE;
    options.defaultptn = FALSE;
    statsblk stats{};

    densenauty(
        dense.data(),
        lab.data(),
        ptn.data(),
        orbits.data(),
        &options,
        &stats,
        m,
        n,
        canonical_dense.data()
    );

    if (stats.errstatus != 0) {
        throw std::runtime_error(
            "nauty canonicalization failed with errstatus "
            + std::to_string(stats.errstatus)
        );
    }

    CanonicalForm result;
    result.canonical_colors.resize(static_cast<std::size_t>(n));
    for (int i = 0; i < n; ++i) {
        result.canonical_colors[static_cast<std::size_t>(i)] =
            graph.colors[static_cast<std::size_t>(lab[static_cast<std::size_t>(i)])];
    }

    for (int i = 0; i < n; ++i) {
        const auto* row = GRAPHROW(canonical_dense.data(), i, m);
        for (int j = i + 1; j < n; ++j) {
            if (ISELEMENT(row, j)) {
                result.canonical_edges.emplace_back(
                    static_cast<std::uint32_t>(i),
                    static_cast<std::uint32_t>(j)
                );
            }
        }
    }

    std::ostringstream encoding;
    encoding << "SQT1|n:" << n << "|c:";
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
    result.fingerprint = stable_fingerprint(result.encoding);
    return result;
}

CanonicalForm canonicalize(const Topology& topology) {
    return canonicalize_colored_graph(to_incidence_graph(topology));
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
