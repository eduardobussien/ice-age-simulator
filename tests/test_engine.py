"""Physics and binding tests for the Ice Age Simulator core.

These lock in the calibration and invariants of the Budyko-Sellers model so a
future change cannot silently break the realistic present-day climate, the
zero-copy bindings, or the snowball behaviour.

Build the extension first, then run from the repo root:

    python -m pytest tests/ -v
"""
import numpy as np
import pytest

from python_sim import ClimateGrid, SimulationEngine, Params

# Small grid: the physics is resolution-independent, so this keeps tests fast
# while the calibration values (global ~15 C, etc.) still hold.
ROWS, COLS = 45, 90


def weights(rows: int = ROWS, cols: int = COLS) -> np.ndarray:
    """cos(latitude) area weights matching the engine's own weighting."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def fresh(**overrides):
    """A seeded engine + grid, with any Params fields overridden."""
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


def ice_cover(grid) -> float:
    w = weights()
    return float((w * (np.asarray(grid.ice) > 1.0)).sum() / w.sum())


# --------------------------------------------------------------------------
# Bindings / zero-copy
# --------------------------------------------------------------------------

def test_grid_shape_and_size():
    g = ClimateGrid(ROWS, COLS)
    assert g.shape == (ROWS, COLS)
    assert g.rows == ROWS and g.cols == COLS


def test_views_are_zero_copy():
    g = ClimateGrid(ROWS, COLS)
    T = g.T
    assert T.shape == (ROWS, COLS)
    assert not T.flags.owndata  # the view shares the C++ buffer, no copy


def test_view_shares_buffer_across_accesses():
    g = ClimateGrid(ROWS, COLS)
    g.ice[3, 7] = 1234.0          # write through one view
    assert g.ice[3, 7] == 1234.0  # seen through a freshly fetched view


def test_cpp_mutation_visible_in_view():
    g, e = fresh()
    T = g.T
    before = float(T.mean())
    e.set_solar_mult(0.8)
    run(e, 50)
    assert float(T.mean()) != before  # C++ step mutated the shared buffer


def test_iteration_and_time_advance():
    g, e = fresh()
    assert e.iteration == 0
    run(e, 10)
    assert e.iteration == 10
    assert e.time == pytest.approx(10 * e.params.dt)


# --------------------------------------------------------------------------
# Insolation distribution
# --------------------------------------------------------------------------

def test_insolation_area_mean_is_one():
    # Normalized to 1.0 in the continuous limit; a coarse latitude grid leaves a
    # small discretization residual (~1e-4 at 45 rows), which shrinks with rows.
    g, _ = fresh()
    S = np.asarray(g.solar)
    assert np.average(S, weights=weights()) == pytest.approx(1.0, abs=1e-3)

def test_insolation_equator_exceeds_pole():
    g, _ = fresh()
    S = np.asarray(g.solar)
    assert S[ROWS // 2].mean() > S[0].mean()


# --------------------------------------------------------------------------
# Present-day realism (the calibration we must not break)
# --------------------------------------------------------------------------

def test_present_day_baseline_is_realistic():
    g, e = fresh()
    run(e, 600)
    assert 14.0 < e.global_temperature < 16.0     # Earth ~15 C
    assert np.asarray(g.T)[ROWS // 2].mean() > 20  # warm equator
    assert np.asarray(g.T)[0].mean() < 0           # cold pole


def test_seed_starts_ice_free():
    g, _ = fresh()
    assert np.asarray(g.ice).max() == 0.0


def test_present_day_has_partial_ice_caps():
    g, e = fresh()
    run(e, 600)
    assert 0.0 < ice_cover(g) < 0.5  # polar caps, not a global snowball


# --------------------------------------------------------------------------
# Energy balance (analytic checks)
# --------------------------------------------------------------------------

def test_ice_free_global_matches_analytic_balance():
    # Suppress ice and the CO2 feedback so equilibrium is the pure radiative
    # balance: global mean T = (S0/4 * (1 - albedo) - A) / B.
    g, e = fresh(accum_rate=0.0, co2_solubility=0.0)
    run(e, 400)
    p = e.params
    expected = (p.solar_mult * p.solar_constant / 4.0 * (1.0 - p.base_albedo)
                - p.olr_a) / p.olr_b
    assert e.global_temperature == pytest.approx(expected, abs=0.2)


def test_global_temperature_matches_numpy():
    g, e = fresh()
    run(e, 200)
    ref = np.average(np.asarray(g.T), weights=weights())
    assert e.global_temperature == pytest.approx(ref, abs=1e-6)


def test_planetary_albedo_matches_numpy():
    g, e = fresh()
    run(e, 200)
    ref = np.average(np.asarray(g.albedo), weights=weights())
    assert e.planetary_albedo == pytest.approx(ref, abs=1e-6)


# --------------------------------------------------------------------------
# Ice and albedo bounds
# --------------------------------------------------------------------------

def test_ice_stays_within_bounds():
    g, e = fresh()
    e.set_solar_mult(0.90)
    run(e, 800)
    ice = np.asarray(g.ice)
    assert ice.min() >= 0.0
    assert ice.max() <= e.params.ice_max + 1e-9


def test_albedo_stays_within_bounds():
    g, e = fresh()
    e.set_solar_mult(0.94)
    run(e, 400)
    a = np.asarray(g.albedo)
    assert a.min() >= e.params.base_albedo - 1e-9
    assert a.max() <= e.params.ice_albedo + 1e-9


# --------------------------------------------------------------------------
# Sea level
# --------------------------------------------------------------------------

def test_sea_level_zero_when_ice_free():
    _, e = fresh()
    assert e.sea_level_drop == pytest.approx(0.0)


def test_sea_level_formula():
    g, e = fresh()
    g.ice[:] = 500.0  # uniform ice via the zero-copy view
    p = e.params
    expected = p.ice_density_ratio * 500.0 / p.ocean_fraction
    assert e.sea_level_drop == pytest.approx(expected, rel=1e-9)


# --------------------------------------------------------------------------
# Tipping behaviour
# --------------------------------------------------------------------------

def test_snowball_below_threshold():
    g, e = fresh()
    e.set_solar_mult(0.90)
    run(e, 1500)
    assert ice_cover(g) > 0.95
    assert e.global_temperature < -20.0


def test_more_ice_at_lower_solar():
    def cover_at(s):
        g, e = fresh()
        e.set_solar_mult(s)
        run(e, 1200)
        return ice_cover(g)
    assert cover_at(0.97) > cover_at(1.00)


# --------------------------------------------------------------------------
# CO2 feedback
# --------------------------------------------------------------------------

def test_co2_near_base_at_present_day():
    _, e = fresh()
    run(e, 600)
    assert e.co2 == pytest.approx(e.params.co2_base, abs=20.0)


def test_co2_draws_down_when_cold():
    _, e = fresh()
    e.set_solar_mult(0.95)
    run(e, 1000)
    assert e.co2 < e.params.co2_base


# --------------------------------------------------------------------------
# Determinism and parameter plumbing
# --------------------------------------------------------------------------

def test_run_is_deterministic():
    def final():
        g, e = fresh()
        e.set_solar_mult(0.96)
        run(e, 500)
        return (e.global_temperature, e.co2, float(np.asarray(g.ice).sum()))
    assert final() == final()


def test_set_solar_mult_is_live():
    _, e = fresh()
    assert e.params.solar_mult == pytest.approx(1.0)
    e.set_solar_mult(0.9)
    assert e.params.solar_mult == pytest.approx(0.9)


def test_set_params_takes_effect():
    _, e = fresh()
    p = Params()
    p.s2 = -0.30
    e.set_params(p)
    assert e.params.s2 == pytest.approx(-0.30)
