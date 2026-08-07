cmake_minimum_required(VERSION 3.18)
project(ice_age_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(Python 3.9 COMPONENTS Interpreter Development.Module REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

pybind11_add_module(_core
  bindings/pybind_wrapper.cpp
  src/climate_grid.cpp
  src/simulation_engine.cpp
)
target_include_directories(_core PRIVATE include)
target_compile_features(_core PRIVATE cxx_std_17)

# On MinGW/GCC, statically link the GCC runtime (libstdc++, libgcc, winpthread)
# so the extension has no external MinGW DLL dependencies. Without this the
# .pyd imports only when those DLLs happen to be on PATH. MSVC builds are
# unaffected (MSVC redistributables are handled separately).
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND WIN32)
  target_link_options(_core PRIVATE
    -static -static-libgcc -static-libstdc++)
endif()

# Emit the built extension next to the Python package so `import python_sim`
# works straight from the repo root without an install step. The per-config
# properties keep the output flat on multi-config generators (MSVC), which
# otherwise nest it under python_sim/Release, python_sim/Debug, etc.
foreach(cfg "" _DEBUG _RELEASE _RELWITHDEBINFO _MINSIZEREL)
  set_target_properties(_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY${cfg} "${CMAKE_SOURCE_DIR}/python_sim"
    RUNTIME_OUTPUT_DIRECTORY${cfg} "${CMAKE_SOURCE_DIR}/python_sim")
endforeach()
