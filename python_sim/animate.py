"""Animate a full simulation run into a GIF.

Renders temperature and ice thickness side by side while the world cools into
a snowball, with a live readout of global temperature, CO2, and sea level.

Run from the repo root once the extension is built:

    python -m python_sim.animate
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe: render frames without a display
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402

from python_sim import ClimateGrid, SimulationEngine, Params, settle


def _panel(ax, field, title, cmap, label, vmin, vmax):
    im = ax.imshow(field, cmap=cmap, origin="upper", aspect="auto",
                   extent=(-180, 180, -90, 90), vmin=vmin, vmax=vmax)
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-90, -45, 0, 45, 90])
    ax.figure.colorbar(im, ax=ax, label=label, shrink=0.85)
    return im


def animate(path: str = "figures/ice_age.gif", frames: int = 60,
            steps_per_frame: int = 8, fps: int = 12,
            solar_start: float = 1.0, solar_end: float = 0.93) -> Path:
    grid = ClimateGrid(90, 180)
    params = Params()
    engine = SimulationEngine(grid, params)
    engine.set_solar_mult(solar_start)
    settle(engine)  # begin from the settled climate, not the ice-free seed

    T, Ice = grid.T, grid.ice
    # Forcing: slowly dim the whole Sun across the run.
    solar_schedule = np.linspace(solar_start, solar_end, frames)

    fig, (ax_t, ax_i) = plt.subplots(1, 2, figsize=(13, 4.6))
    im_t = _panel(ax_t, T, "Surface temperature", "coolwarm", "T (C)",
                  vmin=-50.0, vmax=50.0)
    im_i = _panel(ax_i, Ice, "Ice thickness", "Blues", "ice (m)",
                  vmin=0.0, vmax=params.ice_max)
    header = fig.suptitle("", fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))

    def draw_header(solar: float) -> None:
        header.set_text(
            f"solar={solar * 100:.1f}%    global={engine.global_temperature:6.2f} C"
            f"    CO2={engine.co2:4.0f} ppm"
            f"    sea level={-engine.sea_level_drop:7.0f} m"
        )

    def update(frame: int):
        engine.set_solar_mult(float(solar_schedule[frame]))
        if frame > 0:  # frame 0 shows the initial present-day state
            for _ in range(steps_per_frame):
                engine.step()
        im_t.set_data(np.asarray(T))
        im_i.set_data(np.asarray(Ice))
        draw_header(float(solar_schedule[frame]))
        return im_t, im_i, header

    anim = FuncAnimation(fig, update, frames=frames, blit=False)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out, writer=PillowWriter(fps=fps), dpi=80)
    plt.close(fig)
    return out


if __name__ == "__main__":
    out = animate()
    print(f"saved {out.resolve()}")
