"""From-space polar views of the climate fields (orthographic projection).

Renders the North-pole and South-pole hemispheres side by side, which makes
ice-cap growth read like a planet seen from orbit. Choose the field with
`field=` ("ice", "T", or "albedo").

Note: the first run downloads Natural Earth coastline data (needs network);
Cartopy caches it afterwards.

Run standalone once the extension is built:

    python -m python_sim.polar
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402
import cartopy.crs as ccrs  # noqa: E402


# field name -> (title, colormap, colorbar label)
FIELDS = {
    "T": ("Surface temperature", "coolwarm", "T (C)"),
    "ice": ("Ice thickness", "Blues", "ice (m)"),
    "albedo": ("Surface albedo", "cividis", "albedo"),
}


def _hemisphere(fig, pos, data, central_lat, title, cmap, vmin, vmax):
    """Draw one orthographic hemisphere; return its pcolormesh."""
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


def polar_pair(grid, path, field: str = "ice", subtitle: str = ""):
    """Render the North and South hemispheres of `field` and save to `path`."""
    title, cmap, label = FIELDS[field]
    data = np.asarray(getattr(grid, field))

    if field == "T":
        vmax = float(np.abs(data).max()) or 1.0
        vmin = -vmax
    elif field == "albedo":
        vmin, vmax = 0.0, 1.0
    else:  # ice
        vmin, vmax = 0.0, float(data.max()) or 1.0

    fig = plt.figure(figsize=(11, 6))
    mesh = _hemisphere(fig, 121, data, 90.0, "North polar view", cmap, vmin, vmax)
    _hemisphere(fig, 122, data, -90.0, "South polar view", cmap, vmin, vmax)
    fig.colorbar(mesh, ax=fig.axes, label=label, orientation="horizontal",
                 shrink=0.5, pad=0.06, fraction=0.05)
    fig.suptitle(subtitle or f"{title} (from space)", fontsize=13)

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
    engine.set_solar_mult(0.96)  # partial glaciation: visible cap edge
    for _ in range(1500):
        engine.step()

    out = polar_pair(
        grid, "figures/polar_ice.png", field="ice",
        subtitle=f"Ice caps from space  (solar {engine.params.solar_mult * 100:.0f}%,"
                 f" global {engine.global_temperature:.1f} C)",
    )
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    _demo()
