"""Time-series of a full run: the temporal view the maps cannot show.

Slowly dims the Sun over a run and records the global mean temperature, CO2,
sea level, and ice cover at every step. The plot makes the tipping point
obvious: each curve declines gently, then plunges when the ice-albedo feedback
catches and the planet snowballs.

Run from the repo root once the extension is built:

    python -m python_sim.timeseries
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402

from python_sim import ClimateGrid, SimulationEngine, Params, settle


def area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for a regular lat x lon grid."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def run(steps: int = 12800, solar_start: float = 1.0, solar_end: float = 0.90):
    # The ramp must be slow compared with the climate's own response, otherwise
    # the planet lags the Sun and appears to tip later than it really does: an
    # 800-step ramp tips near 93.2% sunlight, while the settled tipping point is
    # about 95%. At 12800 steps the ramp tips at 94.9%.
    grid = ClimateGrid(90, 180)
    engine = SimulationEngine(grid, Params())
    engine.set_solar_mult(solar_start)
    settle(engine)  # begin from the settled climate, not the ice-free seed
    t_start = engine.time  # report time from the start of the run

    Ice = grid.ice
    w = area_weights(90, 180)
    w_sum = w.sum()
    schedule = np.linspace(solar_start, solar_end, steps)

    rec = {k: [] for k in ("t", "solar", "gt", "co2", "sea", "cover")}
    for i in range(steps):
        engine.set_solar_mult(float(schedule[i]))
        engine.step()
        rec["t"].append(engine.time - t_start)
        rec["solar"].append(schedule[i] * 100.0)
        rec["gt"].append(engine.global_temperature)
        rec["co2"].append(engine.co2)
        rec["sea"].append(-engine.sea_level_drop)
        rec["cover"].append(float((w * (Ice > 1.0)).sum() / w_sum) * 100.0)
    return {k: np.asarray(v) for k, v in rec.items()}


def plot(data, path):
    fig, axes = plt.subplots(4, 1, figsize=(9, 10), sharex=True)

    ax = axes[0]
    ax.plot(data["t"], data["gt"], color="#d7301f", lw=2, label="global T")
    ax.set_ylabel("Global T (C)")
    ax.axhline(0.0, color="gray", lw=0.6, ls=":")
    # Show the solar forcing (the driver) on a secondary axis.
    ax2 = ax.twinx()
    ax2.plot(data["t"], data["solar"], color="0.5", lw=1.2, ls="--",
             label="solar forcing")
    ax2.set_ylabel("Solar (% of present)", color="0.4")
    ax2.tick_params(axis="y", colors="0.4")

    axes[1].plot(data["t"], data["co2"], color="#2c7fb8", lw=2)
    axes[1].set_ylabel("CO2 (ppm)")

    axes[2].plot(data["t"], data["sea"], color="#238b45", lw=2)
    axes[2].set_ylabel("Sea level (m)")

    axes[3].plot(data["t"], data["cover"], color="#6a51a3", lw=2)
    axes[3].set_ylabel("Ice cover (%)")
    axes[3].set_xlabel("time (model steps, not years)")

    for a in axes:
        a.grid(True, alpha=0.3)
    fig.suptitle("Tipping into a snowball as the Sun slowly dims", fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, 0.97))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main() -> None:
    data = run()
    out = plot(data, "figures/timeseries.png")
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    main()
