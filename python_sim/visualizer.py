"""Visualization helpers for the Ice Age Simulator.

Matplotlib-only for now (offline, no geodata download). Cartopy map
projections and coastline overlays are a later enhancement.

Run standalone to render a snapshot of a short run:

    python -m python_sim.visualizer
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe: save PNGs without a display
import matplotlib.pyplot as plt  # noqa: E402


def heatmap(ax, field: np.ndarray, title: str, cmap: str, label: str,
            vmin: float | None = None, vmax: float | None = None):
    """Draw one lat x lon field onto `ax` with geographic axes."""
    im = ax.imshow(
        np.asarray(field), cmap=cmap, origin="upper", aspect="auto",
        extent=(-180, 180, -90, 90), vmin=vmin, vmax=vmax,
    )
    ax.set_title(title)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xticks([-180, -90, 0, 90, 180])
    ax.set_yticks([-90, -45, 0, 45, 90])
    ax.figure.colorbar(im, ax=ax, label=label, shrink=0.85)
    return im


def snapshot(grid, path, temp_title: str = "Surface temperature"):
    """Render temperature + insolation side by side and save to `path`."""
    T = np.asarray(grid.T)
    S = np.asarray(grid.solar)

    fig, (ax_t, ax_s) = plt.subplots(1, 2, figsize=(14, 4.5))
    # Diverging map centered near 0 C reads temperature intuitively.
    tmax = float(np.abs(T).max())
    heatmap(ax_t, T, temp_title, "coolwarm", "T (C)", vmin=-tmax, vmax=tmax)
    heatmap(ax_s, S, "Insolation (annual mean)", "inferno", "S / S_global")

    fig.tight_layout()
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def _demo() -> None:
    from python_sim import ClimateGrid, SimulationEngine, Params

    rows, cols = 90, 180
    grid = ClimateGrid(rows, cols)
    engine = SimulationEngine(grid, Params())
    engine.seed_equilibrium()
    for _ in range(50):
        engine.step()

    out = snapshot(
        grid, "figures/state_t50.png",
        temp_title=f"Surface temperature (t={engine.time:.0f})",
    )
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    _demo()
