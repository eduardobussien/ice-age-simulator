"""Interactive solar-forcing explorer.

Opens a live window: drag the solar slider and watch the climate relax toward
the new forcing. Push the Sun down a few percent and the ice runs away into a
snowball; ease it back up to recover. Find the tipping point by hand.

Needs an interactive Matplotlib backend (the desktop default), so run it
directly rather than in a headless environment:

    python -m python_sim.interactive
"""
from __future__ import annotations

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.animation import FuncAnimation

from python_sim import ClimateGrid, SimulationEngine, Params


def _area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for the ice-cover diagnostic."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def build(rows: int = 90, cols: int = 180, steps_per_frame: int = 2):
    """Build the interactive figure. Returns (fig, update) for headless tests."""
    grid = ClimateGrid(rows, cols)
    engine = SimulationEngine(grid, Params())
    engine.seed_equilibrium()

    T, Ice = grid.T, grid.ice
    weights = _area_weights(rows, cols)
    weight_sum = weights.sum()
    extent = (-180.0, 180.0, -90.0, 90.0)

    fig, (ax_t, ax_i) = plt.subplots(1, 2, figsize=(13, 5))
    fig.subplots_adjust(bottom=0.22)  # leave room for the slider / readout

    im_t = ax_t.imshow(np.asarray(T), cmap="coolwarm", origin="upper",
                       aspect="auto", extent=extent, vmin=-50.0, vmax=50.0)
    ax_t.set_title("Surface temperature")
    ax_t.set_xlabel("Longitude")
    ax_t.set_ylabel("Latitude")
    fig.colorbar(im_t, ax=ax_t, label="T (C)", shrink=0.8)

    im_i = ax_i.imshow(np.asarray(Ice), cmap="Blues", origin="upper",
                       aspect="auto", extent=extent,
                       vmin=0.0, vmax=engine.params.ice_max)
    ax_i.set_title("Ice thickness")
    ax_i.set_xlabel("Longitude")
    ax_i.set_ylabel("Latitude")
    fig.colorbar(im_i, ax=ax_i, label="ice (m)", shrink=0.8)

    readout = fig.text(0.5, 0.13, "", ha="center", fontsize=11)

    ax_slider = fig.add_axes((0.25, 0.05, 0.5, 0.03))
    slider = Slider(ax_slider, "Solar %", 85.0, 115.0, valinit=100.0, valstep=0.5)
    slider.on_changed(lambda val: engine.set_solar_mult(val / 100.0))

    ax_reset = fig.add_axes((0.82, 0.045, 0.1, 0.05))
    button = Button(ax_reset, "Reset")

    def on_reset(_event):
        engine.set_solar_mult(slider.val / 100.0)
        engine.seed_equilibrium()

    button.on_clicked(on_reset)

    def update(_frame):
        for _ in range(steps_per_frame):
            engine.step()
        im_t.set_data(np.asarray(T))
        im_i.set_data(np.asarray(Ice))
        cover = float((weights * (Ice > 1.0)).sum() / weight_sum) * 100.0
        readout.set_text(
            f"solar={slider.val:5.1f}%     global={engine.global_temperature:6.2f} C"
            f"     CO2={engine.co2:4.0f} ppm     "
            f"sea level={-engine.sea_level_drop:6.0f} m     ice cover={cover:4.1f}%"
        )
        return im_t, im_i, readout

    anim = FuncAnimation(fig, update, interval=50, blit=False,
                         cache_frame_data=False)
    fig._climate_anim = anim  # keep a reference so it is not garbage-collected
    # Keep the widgets referenced too (same reason).
    fig._climate_widgets = (slider, button)
    return fig, update


def main() -> None:
    build()
    plt.show()


if __name__ == "__main__":
    main()
