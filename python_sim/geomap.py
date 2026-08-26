"""Cartopy globe rendering of the climate fields.

Draws the fields on a Robinson map projection with real coastlines, so the
simulation reads as an actual planet. This is the "pretty" renderer; the plain
Matplotlib `visualizer` stays as an offline fallback.

Note: the first run downloads Natural Earth coastline data (~small, needs a
network connection); it is then cached by Cartopy for later runs.

Run standalone once the extension is built:

    python -m python_sim.geomap
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402
import cartopy.crs as ccrs  # noqa: E402


def globe(fig, pos, field: np.ndarray, title: str, cmap: str, label: str,
          vmin: float | None = None, vmax: float | None = None):
    """Draw one lat x lon field as a Robinson globe with coastlines."""
    field = np.asarray(field)
    rows, cols = field.shape
    lon = np.linspace(-180.0, 180.0, cols + 1)
    lat = np.linspace(90.0, -90.0, rows + 1)  # row 0 is the North pole side

    ax = fig.add_subplot(pos, projection=ccrs.Robinson())
    mesh = ax.pcolormesh(lon, lat, field, transform=ccrs.PlateCarree(),
                         cmap=cmap, vmin=vmin, vmax=vmax, shading="flat")
    ax.coastlines(resolution="110m", linewidth=0.6, color="0.15")
    ax.gridlines(linewidth=0.3, color="gray", alpha=0.4)
    ax.set_global()
    ax.set_title(title)
    fig.colorbar(mesh, ax=ax, label=label, shrink=0.6, pad=0.03)
    return ax


def snapshot_map(grid, path, subtitle: str = ""):
    """Render temperature + ice + albedo as globes and save to `path`."""
    T = np.asarray(grid.T)
    Ice = np.asarray(grid.ice)
    Alb = np.asarray(grid.albedo)

    fig = plt.figure(figsize=(18, 4.8))
    tmax = float(np.abs(T).max()) or 1.0
    globe(fig, 131, T, "Surface temperature", "coolwarm", "T (C)",
          vmin=-tmax, vmax=tmax)
    globe(fig, 132, Ice, "Ice thickness", "Blues", "ice (m)", vmin=0.0)
    globe(fig, 133, Alb, "Surface albedo", "cividis", "albedo",
          vmin=0.0, vmax=1.0)
    if subtitle:
        fig.suptitle(subtitle, fontsize=13)

    fig.tight_layout(rect=(0, 0, 1, 0.96) if subtitle else (0, 0, 1, 1))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path


def _demo() -> None:
    from python_sim import ClimateGrid, SimulationEngine, Params

    grid = ClimateGrid(90, 180)
    engine = SimulationEngine(grid, Params())
    engine.seed_equilibrium()
    engine.set_solar_mult(0.96)  # a partial-glaciation state
    for _ in range(1000):
        engine.step()

    out = snapshot_map(
        grid, "figures/globe_glaciated.png",
        subtitle=f"Ice-age Earth  (solar {engine.params.solar_mult * 100:.0f}%,"
                 f" global {engine.global_temperature:.1f} C)",
    )
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    _demo()
