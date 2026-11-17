"""Tests for the long-term carbon cycle (volcanic source, weathering sink).

The cycle is off by default; these switch it on. Every longitude is identical
in this model, so a two-column grid keeps the long runs fast.
"""
import numpy as np
import pytest

from python_sim import ClimateGrid, SimulationEngine, Params, settle

ROWS, COLS = 45, 2


def make(**overrides):
    p = Params()
    for k, v in overrides.items():
        setattr(p, k, v)
    grid = ClimateGrid(ROWS, COLS)
    engine = SimulationEngine(grid, p)
    engine.seed_equilibrium()
    return grid, engine


def run(engine, n: int) -> None:
    for _ in range(n):
        engine.step()


def frozen_over(grid) -> bool:
    return bool(np.asarray(grid.ice).min() > 1.0)


def test_off_by_default():
    # With no volcanoes the long-term carbon level never moves.
    assert Params().volcanic_rate == 0.0
    _, e = make()
    e.set_solar_mult(0.96)
    run(e, 800)
    assert e.carbon_reservoir == e.params.co2_base


def test_present_day_is_in_balance():
    # Weathering is calibrated to cancel the volcanoes in today's climate, so
    # switching the cycle on must leave today's climate where it was.
    _, e = make(volcanic_rate=2.0)
    settle(e, 6000)
    assert 14.0 < e.global_temperature < 16.0
    assert e.co2 == pytest.approx(e.params.co2_base, abs=15.0)
    assert e.weathering_ratio == pytest.approx(1.0, abs=0.01)


def test_co2_builds_up_on_a_frozen_planet():
    # No open ground or water: weathering and ocean uptake stop, so CO2 rises
    # at exactly the volcanic rate.
    g, e = make(volcanic_rate=0.5)
    e.set_solar_mult(0.85)
    run(e, 2000)
    assert frozen_over(g)
    assert e.weathering_ratio == pytest.approx(0.0, abs=1e-12)
    co2_before, carbon_before = e.co2, e.carbon_reservoir
    run(e, 1000)
    assert e.co2 - co2_before == pytest.approx(0.5 * 1000, rel=1e-9)
    # The long-term carbon level rises with it, so the CO2 is still there
    # when the ocean reopens.
    assert e.carbon_reservoir - carbon_before == pytest.approx(0.5 * 1000, rel=1e-9)


def test_thermostat_prevents_a_slow_freeze():
    # 94% sunlight freezes the planet without volcanoes. With them, weathering
    # slows in the cold, CO2 rises, and the planet stays open.
    g, e = make()
    settle(e)
    e.set_solar_mult(0.94)
    run(e, 3000)
    assert frozen_over(g)

    g, e = make(volcanic_rate=2.0)
    settle(e, 6000)
    e.set_solar_mult(0.94)
    run(e, 30000)
    assert not frozen_over(g)
    assert e.co2 > 2.0 * e.params.co2_base
    assert e.weathering_ratio == pytest.approx(1.0, abs=0.02)


def test_snowball_thaws_and_recovers():
    # The full cycle, with the darker ice the experiment script uses: a cold
    # snap freezes the planet, CO2 builds up, the ice melts into a hothouse,
    # and weathering brings the climate back.
    g, e = make(volcanic_rate=0.5, ice_albedo=0.50)
    settle(e, 6000)
    e.set_solar_mult(0.85)
    run(e, 1500)
    e.set_solar_mult(0.94)
    assert frozen_over(g)

    steps = 0
    while frozen_over(g) and steps < 400_000:
        run(e, 200)
        steps += 200
    assert not frozen_over(g), "the snowball never thawed"
    assert 20_000 < e.co2 < 80_000  # a few percent CO2, as in the literature

    run(e, 2000)
    assert e.global_temperature > 15.0  # hothouse

    run(e, 150_000)
    assert 0.0 < e.global_temperature < 15.0  # recovered, temperate
    assert e.co2 < 3000.0
    assert e.weathering_ratio == pytest.approx(1.0, abs=0.02)


def test_seed_resets_the_carbon_level():
    g, e = make(volcanic_rate=0.5)
    e.set_solar_mult(0.85)
    run(e, 3000)
    assert e.carbon_reservoir > e.params.co2_base
    e.seed_equilibrium()
    assert e.carbon_reservoir == e.params.co2_base
