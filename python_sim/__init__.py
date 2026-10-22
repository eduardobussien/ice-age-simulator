"""Ice Age Simulator - Python control & visualization layer.

Re-exports the C++ core (built by CMake into this package as ``_core``) so
callers can simply ``from python_sim import ClimateGrid, SimulationEngine``.
"""
from ._core import ClimateGrid, SimulationEngine, Params, __version__  # noqa: F401

__all__ = ["ClimateGrid", "SimulationEngine", "Params", "__version__",
           "settle", "SETTLE_STEPS"]

# Steps for a run to reach equilibrium from rest. The climate settles fully by
# about 300 steps; 600 leaves a safe margin and costs a few hundredths of a second.
SETTLE_STEPS = 600


def settle(engine: SimulationEngine, steps: int = SETTLE_STEPS) -> None:
    """Restart `engine` from rest and let it settle at its current sunlight.

    seed_equilibrium() starts the planet ice-free, which is not a realistic
    state: at today's sunlight it is 16.6 C with no ice at all. Stepping lets
    the polar caps grow and the climate settle, so a run begins from today's
    15 C with small polar caps (or the equivalent for other sunlight levels).
    """
    engine.seed_equilibrium()
    for _ in range(steps):
        engine.step()
