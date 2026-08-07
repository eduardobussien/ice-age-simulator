"""Visualization helpers for the Ice Age Simulator.

Matplotlib-only for now (no external geodata needed). Cartopy map projections
and ice-extent overlays arrive alongside the real physics.
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt


def heatmap(field: np.ndarray, title: str = "", cmap: str = "coolwarm",
            label: str = "value"):
    """Render a lat x lon field as a heatmap. Returns (fig, ax)."""
    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(
        field, cmap=cmap, origin="upper", aspect="auto",
        extent=(-180, 180, -90, 90),
    )
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(title)
    fig.colorbar(im, ax=ax, label=label)
    fig.tight_layout()
    return fig, ax
