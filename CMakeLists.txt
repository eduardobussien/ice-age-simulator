cmake_minimum_required(VERSION 3.18)
project(ice_age_core LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release)
endif()

find_package(Python 3.9 COMPONENTS Interpreter Development.Module REQUIRED)

# Locate pybind11 automatically from the active Python (works for both a manual
# `cmake` build and a scikit-build-core wheel build). An explicit -Dpybind11_DIR
# still wins if provided.
if(NOT pybind11_DIR AND NOT DEFINED CMAKE_PREFIX_PATH)
  execute_process(
    COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
    OUTPUT_VARIABLE _pybind11_cmakedir
    OUTPUT_STRIP_TRAILING_WHITESPACE
    RESULT_VARIABLE _pybind11_found)
  if(_pybind11_found EQUAL 0)
    set(pybind11_DIR "${_pybind11_cmakedir}")
  endif()
endif()
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

if(DEFINED SKBUILD)
  # Wheel build (scikit-build-core): install the module into the package so it
  # is packed into the wheel at python_sim/_core*.
  install(TARGETS _core LIBRARY DESTINATION python_sim
                        RUNTIME DESTINATION python_sim)
else()
  # Manual/dev build: emit the extension next to the Python package so
  # `import python_sim` works straight from the repo root without installing.
  # The per-config properties keep the output flat on multi-config generators
  # (MSVC), which otherwise nest it under python_sim/Release, python_sim/Debug.
  foreach(cfg "" _DEBUG _RELEASE _RELWITHDEBINFO _MINSIZEREL)
    set_target_properties(_core PROPERTIES
      LIBRARY_OUTPUT_DIRECTORY${cfg} "${CMAKE_SOURCE_DIR}/python_sim"
      RUNTIME_OUTPUT_DIRECTORY${cfg} "${CMAKE_SOURCE_DIR}/python_sim")
  endforeach()
endif()
