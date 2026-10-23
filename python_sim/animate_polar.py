"""Animate the from-space ice caps growing over a run into a GIF.

North-pole and South-pole orthographic hemispheres side by side, showing the
ice caps spreading equatorward as a slow dimming of the Sun pulls the planet
toward a snowball.

Note: the first run downloads Natural Earth coastline data (needs network);
Cartopy caches it afterwards.

Run from the repo root once the extension is built:

    python -m python_sim.animate_polar
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


def _setup(fig, pos, data, central_lat, title, cmap, vmin, vmax):
    """Create an orthographic hemisphere; return its updatable pcolormesh."""
    rows, cols = data.shape
    lon = np.linspace(-180.0, 180.0, cols + 1)
    lat = np.linspace(90.0, -90.0, rows + 1)

    ax = fig.add_subplot(
        pos, projection=ccrs.Orthographic(central_longitude=0.0,
                                           central_latitude=central_lat))
    mesh = ax.pcolormesh(lon, lat, data, transform=ccrs.PlateCarree(),
                         cmap=cmap, vmin=vmin, vmax=vmax, shading="flat")
    ax.coastlines(resolution="110m", linewidth=0.6, color="0.15")
    ax.gridlines(linewidth=0.3, color="gray", alpha=0.4)
    ax.set_global()
    ax.set_title(title)
    return mesh


def animate(path: str = "figures/ice_caps_polar.gif", frames: int = 60,
            steps_per_frame: int = 8, fps: int = 12,
            solar_start: float = 1.0, solar_end: float = 0.90) -> Path:
    grid = ClimateGrid(90, 180)
    params = Params()
    engine = SimulationEngine(grid, params)
    engine.set_solar_mult(solar_start)
    settle(engine)  # begin from the settled climate, not the ice-free seed

    Ice = grid.ice
    solar_schedule = np.linspace(solar_start, solar_end, frames)

    fig = plt.figure(figsize=(11, 6))
    mesh_n = _setup(fig, 121, Ice, 90.0, "North polar view", "Blues",
                    0.0, params.ice_max)
    mesh_s = _setup(fig, 122, Ice, -90.0, "South polar view", "Blues",
                    0.0, params.ice_max)
    fig.colorbar(mesh_n, ax=fig.axes, label="ice thickness (m)",
                 orientation="horizontal", shrink=0.5, pad=0.06, fraction=0.05)
    header = fig.suptitle("", fontsize=13)

    def update(frame: int):
        engine.set_solar_mult(float(solar_schedule[frame]))
        if frame > 0:  # frame 0 shows the present-day state
            for _ in range(steps_per_frame):
                engine.step()
        arr = np.asarray(Ice).ravel()
        mesh_n.set_array(arr)
        mesh_s.set_array(arr)
        header.set_text(
            f"solar={solar_schedule[frame] * 100:.1f}%    "
            f"global={engine.global_temperature:6.2f} C    "
            f"sea level={-engine.sea_level_drop:7.0f} m"
        )
        return mesh_n, mesh_s, header

    anim = FuncAnimation(fig, update, frames=frames, blit=False)

    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    anim.save(out, writer=PillowWriter(fps=fps), dpi=85)
    plt.close(fig)
    return out


if __name__ == "__main__":
    print(f"saved {animate().resolve()}")
