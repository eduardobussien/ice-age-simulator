"""Tests for the Python-side scenario helpers.

Kept free of plotting imports so they run in CI, which installs only numpy and
pytest alongside the package.
"""
import numpy as np
import pytest

from python_sim import ClimateGrid, SimulationEngine, Params, settle, SETTLE_STEPS

ROWS, COLS = 45, 90


def test_settle_reaches_present_day():
    # From rest the planet is ice-free (16.6 C); settling must reach today's
    # climate instead: ~15 C, small polar caps, CO2 near 280 ppm.
    g = ClimateGrid(ROWS, COLS)
    e = SimulationEngine(g, Params())
    settle(e)
    ice = np.asarray(g.ice)
    assert 14.0 < e.global_temperature < 16.0
    assert ice.max() > 0.0   # polar caps have formed
    assert ice.min() == 0.0  # but the tropics are ice-free
    assert e.co2 == pytest.approx(Params().co2_base, abs=5.0)


def test_settle_restarts_from_rest():
    # Settling after a snowball must start over, not inherit the frozen state.
    g = ClimateGrid(ROWS, COLS)
    e = SimulationEngine(g, Params())
    e.set_solar_mult(0.90)
    settle(e)
    assert np.asarray(g.ice).min() > 0.0  # precondition: a full snowball

    e.set_solar_mult(1.0)
    settle(e)
    assert 14.0 < e.global_temperature < 16.0
    assert e.iteration == SETTLE_STEPS
