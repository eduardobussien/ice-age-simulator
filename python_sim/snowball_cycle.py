"""A full Snowball Earth cycle: freeze, CO2 build-up, sudden thaw, recovery.

Switches on the long-term carbon cycle (volcanoes adding CO2, rock weathering
removing it) and follows the planet through four phases under the fainter Sun
of 700 million years ago (94% of today's):

  1. Thermostat. Weathering slows down when it is cold, so CO2 rises until it
     balances the volcanoes again. The planet stays unfrozen at a level of
     sunlight that would freeze it without volcanoes.
  2. Cold snap. A short, sharp dimming of the Sun outruns the slow thermostat
     and the planet freezes over.
  3. Snowball. With the ground and ocean under ice, weathering stops but the
     volcanoes do not, so CO2 climbs for a very long time.
  4. Thaw and hothouse. The greenhouse finally beats the ice, which melts
     abruptly into a hot, CO2-rich world. Weathering then draws the CO2 down.

Two settings differ from the model's defaults, both stated on the figure:
volcanoes are on (`volcanic_rate`), and the ice is darker (`ice_albedo` 0.50
instead of 0.60), standing in for old, dusty ice. With the default 0.60 the
frozen planet cannot be thawed by any realistic amount of CO2.

Run from the repo root once the extension is built:

    python -m python_sim.snowball_cycle
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")  # headless-safe
import matplotlib.pyplot as plt  # noqa: E402

from python_sim import ClimateGrid, SimulationEngine, Params, settle

# Every longitude is identical in this model, so two columns give the same
# answer as 180 and let the million-step run finish in a few seconds.
ROWS, COLS = 90, 2

SUN = 0.94             # the Sun 700 million years ago (Gough 1981)
VOLCANIC_RATE = 0.1    # ppm of CO2 per model step; slow next to the ice
DUSTY_ICE_ALBEDO = 0.50

THERMOSTAT_STEPS = 200_000  # unrecorded: let the thermostat settle at SUN
LEAD_IN_STEPS = 40_000      # recorded stretch of the settled thermostat
SNAP_SUN = 0.85             # the cold snap that triggers the freeze
SNAP_STEPS = 1_500
RECOVERY_STEPS = 250_000    # recorded after the thaw
MAX_FROZEN_STEPS = 3_000_000
RECORD_EVERY = 100


def _area_weights(rows: int, cols: int) -> np.ndarray:
    """cos(latitude) cell-area weights for the ice-cover diagnostic."""
    lat = np.deg2rad(90.0 - (np.arange(rows) + 0.5) * (180.0 / rows))
    return np.broadcast_to(np.cos(lat)[:, None], (rows, cols))


def run():
    """Run the cycle. Returns (series, events): arrays and key moments."""
    params = Params()
    params.volcanic_rate = VOLCANIC_RATE
    params.ice_albedo = DUSTY_ICE_ALBEDO
    grid = ClimateGrid(ROWS, COLS)
    engine = SimulationEngine(grid, params)
    settle(engine)

    ice = grid.ice
    weights = _area_weights(ROWS, COLS)
    weight_sum = weights.sum()

    def cover() -> float:
        return float((weights * (ice > 1.0)).sum() / weight_sum) * 100.0

    rec = {k: [] for k in ("t", "solar", "gt", "co2", "cover")}
    clock = 0

    def advance(steps: int, record: bool = True, until=None) -> bool:
        """Step the engine; stop early (returning True) once `until()` holds."""
        nonlocal clock
        for i in range(steps):
            engine.step()
            clock += 1
            if i % RECORD_EVERY:
                continue
            if record:
                rec["t"].append(clock)
                rec["solar"].append(engine.params.solar_mult * 100.0)
                rec["gt"].append(engine.global_temperature)
                rec["co2"].append(engine.co2)
                rec["cover"].append(cover())
            if until is not None and until():
                return True
        return False

    events = {}

    # 1. Thermostat: dim the Sun and let the carbon cycle find its balance.
    engine.set_solar_mult(SUN)
    advance(THERMOSTAT_STEPS, record=False)
    clock = 0
    advance(LEAD_IN_STEPS)
    events["thermostat"] = (clock, engine.co2, engine.global_temperature, cover())

    # 2. Cold snap: too fast for the thermostat to answer.
    events["snap_start"] = clock
    engine.set_solar_mult(SNAP_SUN)
    advance(SNAP_STEPS)
    engine.set_solar_mult(SUN)
    events["frozen"] = (clock, engine.co2, engine.global_temperature, cover())

    # 3. Snowball: wait for the volcanoes. Stops at the first open water.
    thawed = advance(MAX_FROZEN_STEPS, until=lambda: cover() < 99.0)
    events["thaw"] = (clock, engine.co2, engine.global_temperature) if thawed else None

    # 4. Hothouse and recovery.
    if thawed:
        start = len(rec["t"])
        advance(RECOVERY_STEPS)
        peak = start + int(np.argmax(rec["gt"][start:]))
        events["peak"] = (rec["t"][peak], rec["co2"][peak], rec["gt"][peak])
        events["end"] = (clock, engine.co2, engine.global_temperature, cover())

    return {k: np.asarray(v) for k, v in rec.items()}, events


def plot(data, events, path):
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), sharex=True)
    t = data["t"] / 1000.0  # thousands of steps

    axes[0].plot(t, data["gt"], color="#d7301f", lw=2)
    axes[0].axhline(0.0, color="gray", lw=0.6, ls=":")
    axes[0].set_ylabel("Global T (C)")

    axes[1].semilogy(t, data["co2"], color="#2c7fb8", lw=2)
    axes[1].set_ylabel("CO2 (ppm, log scale)")

    axes[2].plot(t, data["cover"], color="#6a51a3", lw=2)
    axes[2].set_ylabel("Ice cover (%)")
    axes[2].set_xlabel("time (thousands of model steps, not years)")

    snap = events["snap_start"] / 1000.0
    thaw = events["thaw"][0] / 1000.0 if events.get("thaw") else None
    for ax in axes:
        ax.grid(True, alpha=0.3)
        ax.axvline(snap, color="0.4", lw=0.8, ls="--")
        if thaw is not None:
            ax.axvline(thaw, color="0.4", lw=0.8, ls="--")

    top = axes[0]
    y = top.get_ylim()[1]
    top.annotate("thermostat", (snap / 2.0, y), ha="center", va="bottom",
                 fontsize=9, annotation_clip=False)
    if thaw is not None:
        top.annotate("snowball: volcanoes build up CO2", ((snap + thaw) / 2.0, y),
                     ha="center", va="bottom", fontsize=9, annotation_clip=False)
        top.annotate("hothouse, then recovery", ((thaw + t[-1]) / 2.0, y),
                     ha="center", va="bottom", fontsize=9, annotation_clip=False)

    fig.suptitle(
        "A Snowball Earth cycle with volcanoes and weathering\n"
        f"(Sun {SUN * 100:.0f}%, dusty-ice albedo {DUSTY_ICE_ALBEDO:.2f}, "
        f"cold snap to {SNAP_SUN * 100:.0f}% at the first dashed line)",
        fontsize=12)
    fig.tight_layout(rect=(0, 0, 1, 0.95))

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path


def main() -> None:
    data, events = run()
    _, co2, gt, cov = events["thermostat"]
    print(f"Snowball cycle (Sun {SUN * 100:.0f}%, volcanoes on, "
          f"ice albedo {DUSTY_ICE_ALBEDO:.2f}):")
    print(f"  thermostat holds  : {gt:6.1f} C, {co2:7.0f} ppm, {cov:3.0f}% ice")
    _, co2, gt, cov = events["frozen"]
    print(f"  after the cold snap: {gt:6.1f} C, {co2:7.0f} ppm, {cov:3.0f}% ice")
    if events["thaw"] is None:
        print(f"  still frozen after {MAX_FROZEN_STEPS} steps: no thaw")
    else:
        step, co2, gt = events["thaw"]
        frozen_for = step - events["frozen"][0]
        print(f"  thaw begins       : {gt:6.1f} C, {co2:7.0f} ppm "
              f"(after {frozen_for} steps frozen)")
        _, co2, gt = events["peak"]
        print(f"  hothouse peak     : {gt:6.1f} C, {co2:7.0f} ppm")
        _, co2, gt, cov = events["end"]
        print(f"  recovered climate : {gt:6.1f} C, {co2:7.0f} ppm, {cov:3.0f}% ice")
    out = plot(data, events, "figures/snowball_cycle.png")
    print(f"saved {out.resolve()}")


if __name__ == "__main__":
    main()
