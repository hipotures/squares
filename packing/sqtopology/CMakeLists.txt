cmake_minimum_required(VERSION 3.20)

project(sqtopology LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

find_package(PkgConfig REQUIRED)
pkg_check_modules(NAUTY REQUIRED IMPORTED_TARGET libnauty)

add_library(
    sqtopology_core
    src/canonical.cpp
    src/export.cpp
    src/fixtures.cpp
    src/rewrite.cpp
    src/search.cpp
    src/topology.cpp
)
target_include_directories(sqtopology_core PUBLIC include)
target_link_libraries(sqtopology_core PUBLIC PkgConfig::NAUTY)
target_compile_options(sqtopology_core PRIVATE -Wall -Wextra -Wpedantic)

add_executable(sqtopology src/main.cpp)
target_link_libraries(sqtopology PRIVATE sqtopology_core)
target_compile_options(sqtopology PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_executable(sqtopology_tests tests/test_sqtopology.cpp)
target_link_libraries(sqtopology_tests PRIVATE sqtopology_core)
target_compile_options(sqtopology_tests PRIVATE -Wall -Wextra -Wpedantic)
add_test(NAME sqtopology_tests COMMAND sqtopology_tests)
