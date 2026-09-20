# Ice Age Simulator

A hybrid C++/Python climate simulator that models global cooling, continental
ice-sheet growth, and the feedbacks that drive ice ages on a 2-D latitude x
longitude grid. The physics is a **Budyko-Sellers energy-balance model** with
published coefficients, so the present-day climate and the snowball tipping
point come out realistic rather than arbitrary.

- **C++ core** (`include/`, `src/`): Struct-of-Arrays climate state (`float64`)
  stepped over discrete time iterations.
- **pybind11 bindings** (`bindings/`): expose the grid buffers to Python as
  **zero-copy** NumPy arrays (no copies between the engine and the plots).
- **Python layer** (`python_sim/`): run control, tunable parameters, and
  Matplotlib / Cartopy visualization.

## The model

Each grid cell relaxes toward the local energy-balance equilibrium temperature:

```
solar_mult * (S0/4) * insol * (1 - albedo)      absorbed shortwave
    = olr_a + olr_b * T                          outgoing longwave (Budyko)
    + transport_c * (T - T_global)               meridional heat transport
    - co2_forcing * ln(CO2 / co2_base)           greenhouse forcing
```

Published coefficients (S0 = 1361 W/m2, olr_a = 200, olr_b = 2.09,
transport_c = 3.8, albedo 0.31 ice-free / 0.60 ice) give a realistic present
day: **global 15 C, equator 25 C, pole -12 C, CO2 280 ppm**.

Three feedbacks are intrinsic to the balance (not bolted-on gains):

- **Ice-albedo** (local): ice raises albedo, cutting absorbed sunlight.
- **Heat transport** (planetary): couples every cell to the global mean, so a
  growing ice cap cools the whole world and advances its own margin.
- **CO2 greenhouse**: cooling draws down well-mixed CO2, weakening the
  greenhouse and cooling further.

The external driver is the **solar multiplier** (Milankovitch / solar forcing).
Every coefficient lives in the `Params` struct and is settable from Python.

## Install

Prereqs: a C++17 compiler (MinGW GCC or MSVC), CMake 3.18+, Python 3.9+. The
C++ extension builds automatically; scikit-build-core drives CMake.

```bash
pip install .
```

For an editable/development install (rebuilds on import when sources change):

```bash
pip install -e .
```

On Windows with MinGW, force the Ninja generator so CMake uses GCC rather than
looking for MSVC (PowerShell shown; use `set CMAKE_GENERATOR=Ninja` in cmd, or
`export` in bash):

```bash
$env:CMAKE_GENERATOR="Ninja"
pip install .
```

## Build from source (development)

To build the extension in place without installing (so `import python_sim`
works from the repo root):

```bash
python -m pip install -r requirements.txt
cmake -S . -B build -G Ninja
cmake --build build --config Release
```

pybind11 is discovered automatically from the active Python. The extension is
emitted into `python_sim/` as `_core*.pyd`; on MinGW the C++ runtime is
statically linked (handled in `CMakeLists.txt`), so the module is
self-contained.

## Run

All scripts run from the repo root once the extension is built.

| Command | What it does |
| --- | --- |
| `python -m python_sim.main` | Smoke test: prints the realistic present-day climate, then reduces solar forcing step by step to the snowball tipping point. |
| `python -m python_sim.visualizer` | Flat lat/lon snapshot (temperature, ice, albedo) to `figures/`. Matplotlib only, no network. |
| `python -m python_sim.geomap` | Cartopy globe snapshot on a Robinson projection with coastlines. |
| `python -m python_sim.animate` | GIF of a full run (flat maps). |
| `python -m python_sim.animate_globe` | GIF of a full run on the Cartopy globe. |
| `python -m python_sim.tipping` | Snowball bifurcation experiment: sweeps solar forcing down and back up, plots the hysteresis loop. |
| `python -m python_sim.interactive` | Live window: drag the solar slider and watch the climate respond in real time. Find the tipping point by hand. Needs an interactive backend. |

The Cartopy scripts download Natural Earth coastline data on first run (needs a
network connection), then cache it. Generated figures land in `figures/`, which
is git-ignored.

## Tests

A `pytest` suite in `tests/` locks in the physics: zero-copy bindings, the
realistic present-day baseline (~15 C), the analytic energy balance, the
sea-level formula, and the snowball tipping behaviour. Build the extension
first, then:

```bash
python -m pytest tests/ -v
```

## Key results

- **Present day** (solar 100%): global 15 C with permanent polar ice caps.
- **Snowball tipping**: a solar reduction of only a few percent tips the planet
  into a full snowball.
- **Bistability / hysteresis**: once frozen, the snowball does not deglaciate
  until solar rises far above present, because ice is so reflective. Two stable
  climates coexist over a wide range of forcing - the classic Budyko result.

## Layout

```
include/   simulation_params.hpp, simulation_engine.hpp, climate_grid.hpp
src/       simulation_engine.cpp, climate_grid.cpp
bindings/  pybind_wrapper.cpp        (zero-copy NumPy views)
python_sim/ __init__.py, main.py, visualizer.py, geomap.py,
            animate.py, animate_globe.py, tipping.py
CMakeLists.txt, requirements.txt
```
