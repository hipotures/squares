#pragma once

#include "sqtopology/canonical.hpp"
#include "sqtopology/topology.hpp"

#include <string>

namespace sqtopology {

[[nodiscard]] std::string topology_to_json(
    const Topology& topology,
    const CanonicalForm& canonical
);
[[nodiscard]] std::string topology_to_dot(const Topology& topology);

void write_text_file(const std::string& path, const std::string& content);

}  // namespace sqtopology
