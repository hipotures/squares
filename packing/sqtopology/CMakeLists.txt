cmake_minimum_required(VERSION 3.20)

project(sqtopology LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Optional profile-guided optimization.  The profile is produced by a two-phase
# build driven by tools/pgo_train.sh: configure with SQTOPOLOGY_PGO=generate,
# build, run a training search, then configure with SQTOPOLOGY_PGO=use and
# rebuild in the same build tree.  The .gcda data therefore lives only in the
# build directory and is never committed.  PGO changes inlining and block
# layout but keeps the compiler's default target ISA, so the resulting binary
# still runs on any x86-64 host; only the tuning is host-specific.
set(SQTOPOLOGY_PGO "" CACHE STRING "Profile-guided optimization: empty, generate, or use")
if(SQTOPOLOGY_PGO STREQUAL "generate")
    add_compile_options(-fprofile-generate)
    add_link_options(-fprofile-generate)
elseif(SQTOPOLOGY_PGO STREQUAL "use")
    add_compile_options(-fprofile-use -fprofile-correction -Wno-missing-profile)
elseif(NOT SQTOPOLOGY_PGO STREQUAL "")
    message(FATAL_ERROR "SQTOPOLOGY_PGO must be empty, generate, or use")
endif()

# Ubuntu 26.04 ships libnauty.pc, while Ubuntu 24.04's libnauty-dev does not.
# Prefer pkg-config when present, but keep a direct header/library fallback so the
# native experiment builds on both supported development hosts.
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
    pkg_check_modules(NAUTY QUIET IMPORTED_TARGET libnauty)
endif()

if(TARGET PkgConfig::NAUTY)
    set(SQTOPOLOGY_NAUTY_TARGET PkgConfig::NAUTY)
else()
    find_path(NAUTY_INCLUDE_DIR NAMES nauty.h PATH_SUFFIXES nauty REQUIRED)
    find_library(NAUTY_LIBRARY NAMES nauty REQUIRED)
    add_library(sqtopology_nauty UNKNOWN IMPORTED)
    set_target_properties(
        sqtopology_nauty
        PROPERTIES
            IMPORTED_LOCATION "${NAUTY_LIBRARY}"
            INTERFACE_INCLUDE_DIRECTORIES "${NAUTY_INCLUDE_DIR}"
    )
    set(SQTOPOLOGY_NAUTY_TARGET sqtopology_nauty)
endif()

# Bind nauty's TLS directly into the executable when its archive is available.
# The discovered target retains include paths and secondary link dependencies.
option(SQTOPOLOGY_STATIC_NAUTY "Prefer the installed static nauty archive" ON)
if(SQTOPOLOGY_STATIC_NAUTY)
    find_library(SQTOPOLOGY_NAUTY_ARCHIVE NAMES libnauty.a HINTS ${NAUTY_LIBRARY_DIRS})
    if(SQTOPOLOGY_NAUTY_ARCHIVE)
        add_library(sqtopology_static_nauty INTERFACE)
        target_link_libraries(sqtopology_static_nauty INTERFACE
            ${SQTOPOLOGY_NAUTY_ARCHIVE} ${SQTOPOLOGY_NAUTY_TARGET})
        set(SQTOPOLOGY_NAUTY_TARGET sqtopology_static_nauty)
    endif()
endif()

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
target_link_libraries(sqtopology_core PUBLIC ${SQTOPOLOGY_NAUTY_TARGET})
target_compile_options(sqtopology_core PRIVATE -Wall -Wextra -Wpedantic)

option(SQTOPOLOGY_CACHED_TRACES "Reuse bounded Traces 2.9.3 TLS scratch arrays" ON)
if(SQTOPOLOGY_CACHED_TRACES AND NAUTY_VERSION VERSION_EQUAL "2.9.3")
    enable_language(C)
    add_library(sqtopology_cached_traces OBJECT third_party/nauty/traces.c)
    set_target_properties(sqtopology_cached_traces PROPERTIES POSITION_INDEPENDENT_CODE ON)
    target_link_libraries(sqtopology_cached_traces PRIVATE ${SQTOPOLOGY_NAUTY_TARGET})
    target_compile_definitions(sqtopology_cached_traces PRIVATE
        Traces=sqtopology_Traces
        refine_tr=sqtopology_refine_tr
        traces_freedyn=sqtopology_traces_freedyn
        SQTOPOLOGY_TRACES_CACHE_LIMIT=4096)
    target_sources(sqtopology_core PRIVATE $<TARGET_OBJECTS:sqtopology_cached_traces>)
    target_compile_definitions(sqtopology_core PRIVATE SQTOPOLOGY_CACHED_TRACES=1)
elseif(SQTOPOLOGY_CACHED_TRACES)
    message(STATUS "Cached Traces requires nauty 2.9.3; using the installed engine")
endif()

add_executable(sqtopology src/main.cpp)
target_link_libraries(sqtopology PRIVATE sqtopology_core)
target_compile_options(sqtopology PRIVATE -Wall -Wextra -Wpedantic)

enable_testing()
add_executable(sqtopology_tests tests/test_sqtopology.cpp)
target_link_libraries(sqtopology_tests PRIVATE sqtopology_core)
target_compile_options(sqtopology_tests PRIVATE -Wall -Wextra -Wpedantic)
add_test(NAME sqtopology_tests COMMAND sqtopology_tests)

option(SQTOPOLOGY_BOOST_FLAT_SET "Use Boost's exact flat set for search deduplication" ON)
if(SQTOPOLOGY_BOOST_FLAT_SET)
    find_path(SQTOPOLOGY_BOOST_INCLUDE_DIR boost/unordered/unordered_flat_set.hpp)
    if(SQTOPOLOGY_BOOST_INCLUDE_DIR)
        foreach(target sqtopology_core sqtopology_tests)
            target_include_directories(${target} PRIVATE ${SQTOPOLOGY_BOOST_INCLUDE_DIR})
            target_compile_definitions(${target} PRIVATE SQTOPOLOGY_BOOST_FLAT_SET=1)
        endforeach()
    else()
        message(STATUS "Boost unordered_flat_set unavailable; using std::unordered_set")
    endif()
endif()
