"""Snowball bifurcation experiment (Budyko-Sellers ice-albedo instability).

Sweeps the solar forcing down from present day until the planet snowballs, then
back up until it deglaciates. Because the ice-albedo feedback makes the climate
bistable, the two thresholds differ - the classic hysteresis loop. Greenhouse
CO2 is held fixed so this isolates the pure solar / ice-albedo bifurcation.

Run from the repo root once the extension is built:

    python -m python_sim.tipping
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from python_sim import ClimateGrid, SimulationEngine, Params


ROWS, COLS = 90, 180
LAT = 90.0 - (np.arange(ROWS) + 0.5) * (180.0 / ROWS)  # row-center latitude


def equilibrate(engine, tol: float = 3e-3, block: int = 60,
                max_blocks: int = 30) -> None:
    """Step until the global mean temperature stops changing."""
    prev = None
    for _ in range(max_blocks):
        for _ in range(block):
            engine.step()
        gt = engine.global_temperature
        if prev is not None and abs(gt - prev) < tol:
            break
        prev = gt


def ice_line_latitude(ice: np.ndarray) -> float:
    """Latitude of the equatorward-most ice margin (90 = ice-free, 0 = snowball)."""
    zonal = ice.mean(axis=1)
    iced = np.abs(LAT)[zonal > 1.0]
    return float(iced.min()) if iced.size else 90.0


def sweep(engine, ice, solar_values):
    """Equilibrate at each solar level in order; record the branch."""
    out = []
    for s in solar_values:
        engine.set_solar_mult(float(s))
        equilibrate(engine)
        out.append((s * 100.0, ice_line_latitude(ice), engine.global_temperature))
    return np.array(out)


def main() -> None:
    params = Params()
    params.co2_solubility = 0.0  # hold greenhouse fixed: pure solar/ice-albedo test
    grid = ClimateGrid(ROWS, COLS)
    engine = SimulationEngine(grid, params)
    ice = grid.ice
    engine.seed_equilibrium()
    equilibrate(engine)

    # Cool down from present day into the snowball, then warm back out. A frozen
    # snowball is very hard to melt (albedo 0.6 everywhere), so the warming
    # branch runs to a much higher solar level before it can deglaciate.
    down = np.round(np.arange(1.00, 0.899, -0.01), 3)
    up = np.round(np.arange(0.90, 1.601, 0.02), 3)
    cool = sweep(engine, ice, down)
    warm = sweep(engine, ice, up)

    # Thresholds: where the ice line collapses (cooling) / recovers (warming).
    cool_snow = cool[cool[:, 1] < 5.0, 0]
    warm_free = warm[warm[:, 1] > 5.0, 0]
    snowball = float(cool_snow.max()) if cool_snow.size else float("nan")
    deglaciate = float(warm_free.min()) if warm_free.size else float("nan")

    print("Snowball bifurcation (CO2 fixed):")
    print(f"  cooling  -> snowball at solar <= {snowball:.0f}% of present")
    if np.isnan(deglaciate):
        print("  warming  -> still frozen at 160% solar (hard snowball: "
              "needs greenhouse CO2 to escape, not sunlight)")
    else:
        print(f"  warming  -> deglaciation at solar >= {deglaciate:.0f}% of present")
        print(f"  hysteresis width: {deglaciate - snowball:.0f} percentage points of solar")

    # --- Plot the hysteresis loop ---
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    for ax, col, ylabel, title in (
        (ax1, 1, "Ice-line latitude (deg)", "Ice margin"),
        (ax2, 2, "Global mean temperature (C)", "Global temperature"),
    ):
        ax.plot(cool[:, 0], cool[:, col], "o-", color="#2c7fb8",
                label="cooling (down)")
        ax.plot(warm[:, 0], warm[:, col], "s-", color="#d95f0e",
                label="warming (up)")
        ax.set_xlabel("Solar forcing (% of present)")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.grid(True, alpha=0.3)
        ax.legend()
    fig.suptitle("Snowball-Earth hysteresis: the climate is bistable "
                 "(ice-albedo feedback)", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    out = Path("figures/tipping_point.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    main()
