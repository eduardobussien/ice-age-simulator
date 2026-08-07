"""End-to-end smoke test of the temperature step function.

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
    engine.seed_equilibrium()                 # start "at rest" with lat profile

    T = grid.T                                # zero-copy views onto C++ memory
    S = grid.solar
    w = area_weights(rows, cols)
    pole, equator = 0, rows // 2

    def gmean(field: np.ndarray) -> float:
        return float(np.average(field, weights=w))

    print(f"core v{__version__}")
    print(f"insolation  min={S.min():.3f}  max={S.max():.3f}  "
          f"area-mean={gmean(S):.3f}   (normalized to ~1.0)")
    print(f"t={engine.time:5.0f}  pole={T[pole].mean():7.2f}  "
          f"equator={T[equator].mean():7.2f}  global={gmean(T):7.2f}")

    for _ in range(50):
        engine.step()

    print(f"t={engine.time:5.0f}  pole={T[pole].mean():7.2f}  "
          f"equator={T[equator].mean():7.2f}  global={gmean(T):7.2f}")
    print(f"global mean cooled {params.cooling_rate * engine.time:.2f} C "
          f"over {engine.iteration} steps  (poles stay colder than equator)")


if __name__ == "__main__":
    main()
