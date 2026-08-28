# Ice Age Simulator

High-performance climate simulator modeling hypothetical global-cooling
scenarios: continental ice-sheet growth, albedo feedback, and CO2/solar
forcing on a 2-D latitude x longitude grid.

- **C++ core** (`include/`, `src/`) - Struct-of-Arrays climate state
  (`float64`) stepped over discrete time iterations.
- **pybind11 bindings** (`bindings/`) - expose the grid buffers to Python as
  **zero-copy** NumPy arrays.
- **Python layer** (`python_sim/`) - run control, parameters, and
  Matplotlib/Cartopy visualization.

## Build (Windows / MSVC)

Prereqs: Python 3.9+, CMake 3.18+, and Visual Studio Build Tools (C++ workload).

```bash
python -m pip install -r requirements.txt
cmake -S . -B build -Dpybind11_DIR="$(python -m pybind11 --cmakedir)"
cmake --build build --config Release
```

The extension is emitted into `python_sim/` as `_core*.pyd`.

## Smoke test

```bash
python -m python_sim.main
```

Expected: mean temperature drops 1.0 C over 10 steps, with `owndata == False`
confirming the NumPy views share the C++ buffers.
