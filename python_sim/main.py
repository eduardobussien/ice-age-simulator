"""End-to-end smoke test: temperature + ice growth + albedo feedback.

Runs the same cooling scenario twice -- with the ice-albedo feedback on and
off -- to show how the feedback amplifies cooling and ice growth.

Run from the repo root once the extension is built:

    python -m python_sim.main
"""
import numpy as np

from python_sim import ClimateGrid, SimulationEngine, Params, __version__


def area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for a regular lat x lon grid."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def run(local_gain: float, planetary_gain: float, steps: int = 200):
    rows, cols = 90, 180
    grid = ClimateGrid(rows, cols)

    params = Params()
    params.albedo_gain = local_gain
    params.planetary_gain = planetary_gain
    engine = SimulationEngine(grid, params)
    engine.seed_equilibrium()

    T, Ice = grid.T, grid.ice
    w = area_weights(rows, cols)
    w_sum = w.sum()
    for _ in range(steps):
        engine.step()

    global_t = float(np.average(T, weights=w))
    cover = float((w * (Ice > 1.0)).sum() / w_sum)
    return global_t, cover


def main() -> None:
    defaults = Params()
    print(f"core v{__version__}")
    print(f"{'scenario':<22}{'global T':>10}{'ice cover':>12}")

    t_off, cov_off = run(local_gain=0.0, planetary_gain=0.0)
    print(f"{'feedback OFF':<22}{t_off:>9.2f}C{cov_off * 100:>11.1f}%")

    t_on, cov_on = run(local_gain=defaults.albedo_gain,
                       planetary_gain=defaults.planetary_gain)
    print(f"{'feedback ON':<22}{t_on:>9.2f}C{cov_on * 100:>11.1f}%")

    print("\nfeedback amplification after 200 steps of identical forcing:")
    print(f"  extra cooling  : {t_off - t_on:5.2f} C")
    print(f"  extra ice cover: {(cov_on - cov_off) * 100:4.1f} percentage points")


if __name__ == "__main__":
    main()
