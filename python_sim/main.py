"""End-to-end smoke test of the Budyko-Sellers climate model.

Checks that the calibrated present-day climate is realistic, then reduces the
solar forcing step by step (each run to equilibrium) to show the snowball
tipping point.

Run from the repo root once the extension is built:

    python -m python_sim.main
"""
import numpy as np

from python_sim import ClimateGrid, SimulationEngine, Params, __version__


def area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for a regular lat x lon grid."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def main() -> None:
    rows, cols = 90, 180
    grid = ClimateGrid(rows, cols)
    engine = SimulationEngine(grid, Params())
    engine.seed_equilibrium()

    T, Ice = grid.T, grid.ice
    w = area_weights(rows, cols)
    w_sum = w.sum()

    for _ in range(600):  # settle to present-day equilibrium
        engine.step()

    print(f"core v{__version__}")
    print("present-day equilibrium (solar 100%):")
    print(f"  global  = {engine.global_temperature:6.2f} C   (Earth ~15)")
    print(f"  equator = {T[rows // 2].mean():6.2f} C   (Earth ~26)")
    print(f"  pole    = {T[0].mean():6.2f} C   (Earth ~-16, Arctic)")
    print(f"  CO2     = {engine.co2:6.0f} ppm (Earth pre-industrial 280)")
    # Relative to an ice-free planet: melting all of today's land ice would
    # raise the real ocean by about 66 m.
    print(f"  sea lvl = {-engine.sea_level_drop:6.0f} m   (vs ice-free Earth; real ~-66)")

    print("\nreduce solar forcing in steps, each run to equilibrium:")
    print(f"{'solar':>7}{'global T':>11}{'CO2':>8}{'ice cover':>11}{'sea level':>11}")
    for pct in (100, 98, 96, 95, 94):
        engine.set_solar_mult(pct / 100.0)
        for _ in range(1500):
            engine.step()
        cover = float((w * (Ice > 1.0)).sum() / w_sum)
        print(f"{pct:6d}%{engine.global_temperature:9.2f} C"
              f"{engine.co2:7.0f}p{cover * 100:9.1f}%{-engine.sea_level_drop:9.0f} m")

    print("a few percent drop in sunlight tips the planet into a snowball")


if __name__ == "__main__":
    main()
