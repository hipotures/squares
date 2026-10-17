#pragma once

#include "sqtopology/topology.hpp"

#include <string>
#include <string_view>
#include <vector>

namespace sqtopology {

[[nodiscard]] std::vector<std::string> fixture_names();
[[nodiscard]] Topology make_fixture(std::string_view name);

}  // namespace sqtopology
