"""Ice Age Simulator — Python control & visualization layer.

Re-exports the C++ core (built by CMake into this package as ``_core``) so
callers can simply ``from python_sim import ClimateGrid, SimulationEngine``.
"""
from ._core import ClimateGrid, SimulationEngine, Params, __version__  # noqa: F401

__all__ = ["ClimateGrid", "SimulationEngine", "Params", "__version__"]
