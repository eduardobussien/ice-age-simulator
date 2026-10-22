"""Animate a full simulation run on Cartopy globes into a GIF.

The Robinson-projection version of `animate`: temperature and ice thickness on
a real map with coastlines, while a slow dimming of the Sun pulls the planet
into a snowball.

Note: the first run downloads Natural Earth coastline data (needs network);
Cartopy caches it afterwards.

Run from the repo root once the extension is built:

    python -m python_sim.animate_globe
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402
import cartopy.crs as ccrs  # noqa: E402

from python_sim import ClimateGrid, SimulationEngine, Params, settle


def _setup_globe(fig, pos, field, title, cmap, label, vmin, vmax):
    """Create a Robinson globe panel; return its updatable pcolormesh."""
    field = np.asarray(field)
    rows, cols = field.shape
    lon = np.linspace(-180.0, 180.0, cols + 1)
    lat = np.linspace(90.0, -90.0, rows + 1)

    ax = fig.add_subplot(pos, projection=ccrs.Robinson())
    mesh = ax.pcolormesh(lon, lat, field, transform=ccrs.PlateCarree(),
                         cmap=cmap, vmin=vmin, vmax=vmax, shading="flat")
    ax.coastlines(resolution="110m", linewidth=0.6, color="0.15")
    ax.set_global()
    ax.set_title(title)
    fig.colorbar(mesh, ax=ax, label=label, shrink=0.6, pad=0.03)
    return mesh


def animate(path: str = "figures/ice_age_globe.gif", frames: int = 60,
            steps_per_frame: int = 8, fps: int = 12,
            solar_start: float = 1.0, solar_end: float = 0.93) -> Path:
    grid = ClimateGrid(90, 180)
    params = Params()
    engine = SimulationEngine(grid, params)
    engine.set_solar_mult(solar_start)
    settle(engine)  # begin from the settled climate, not the ice-free seed

    T, Ice = grid.T, grid.ice
    solar_schedule = np.linspace(solar_start, solar_end, frames)

    fig = plt.figure(figsize=(13, 4.8))
    mesh_t = _setup_globe(fig, 121, T, "Surface temperature", "coolwarm",
                          "T (C)", -50.0, 50.0)
    mesh_i = _setup_globe(fig, 122, Ice, "Ice thickness", "Blues",
                          "ice (m)", 0.0, params.ice_max)
    header = fig.suptitle("", fontsize=12)

    def update(frame: int):
        engine.set_solar_mult(float(solar_schedule[frame]))
        if frame > 0:  # frame 0 shows the present-day state
            for _ in range(steps_per_frame):
                engine.step()
        mesh_t.set_array(np.asarray(T).ravel())
        mesh_i.set_array(np.asarray(Ice).ravel())
        header.set_text(
            f"solar={solar_schedule[frame] * 100:.1f}%    "
            f"global={engine.global_temperature:6.2f} C    "
            f"CO2={engine.co2:4.0f} ppm    "
            f"sea level={-engine.sea_level_drop:7.0f} m"
        )
        return mesh_t, mesh_i, header

    anim = FuncAnimation(fig, update, frames=frames, blit=False)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out, writer=PillowWriter(fps=fps), dpi=85)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(f"saved {animate().resolve()}")
