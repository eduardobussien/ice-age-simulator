"""End-to-end smoke test: temperature + ice + albedo feedback + sea level.

Tracks the run over time and reports the sea-level fall driven by the growing
land-ice volume.

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

    def report() -> None:
        gt = float(np.average(T, weights=w))
        cover = float((w * (Ice > 1.0)).sum() / w_sum)
        # Sea level relative to the ice-free start: a drop is negative.
        sea = -engine.sea_level_drop
        print(f"t={engine.time:5.0f}  global={gt:7.2f} C  "
              f"ice cover={cover * 100:5.1f}%  sea level={sea:8.1f} m")

    print(f"core v{__version__}")
    report()
    for _ in range(4):
        for _ in range(50):
            engine.step()
        report()

    print("sea level falls as land ice locks up ocean water")


if __name__ == "__main__":
    main()
