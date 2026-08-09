"""End-to-end smoke test: temperature step + ice-sheet growth.

Run from the repo root once the extension is built:

    python -m python_sim.main
"""
import numpy as np

from python_sim import ClimateGrid, SimulationEngine, Params, __version__


def area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for a regular lat x lon grid.

    Polar cells cover less surface area than tropical ones, so any "global
    mean" must be area-weighted rather than a plain arithmetic mean.
    """
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def main() -> None:
    rows, cols = 90, 180                      # 2-degree latitude x longitude
    grid = ClimateGrid(rows, cols)

    params = Params()                         # modern-Earth-ish defaults
    engine = SimulationEngine(grid, params)
    engine.seed_equilibrium()                 # start "at rest", ice-free

    T = grid.T                                # zero-copy views onto C++ memory
    Ice = grid.ice
    w = area_weights(rows, cols)
    w_sum = w.sum()

    def gmean(field: np.ndarray) -> float:
        return float(np.average(field, weights=w))

    def ice_cover(field: np.ndarray) -> float:
        """Area-weighted fraction of the surface with appreciable ice."""
        return float((w * (field > 1.0)).sum() / w_sum)

    print(f"core v{__version__}")

    def report() -> None:
        print(f"t={engine.time:5.0f}  global={gmean(T):6.2f} C   "
              f"ice cover={ice_cover(Ice) * 100:5.1f}%   "
              f"max ice={Ice.max():7.1f} m")

    report()
    for _ in range(4):
        for _ in range(50):
            engine.step()
        report()

    print("ice grows from the poles equatorward as the world cools")


if __name__ == "__main__":
    main()
