"""Regenerate the showcase images used by the README.

Reuses the project's own plotting scripts, then copies their output into
docs/images/ (which, unlike figures/, is committed). Re-run this whenever the
model changes so the README pictures stay truthful.

Run from the repo root once the extension is built:

    python docs/make_images.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))  # a script in docs/ does not see the repo root

import matplotlib  # noqa: E402
matplotlib.use("Agg")

from python_sim import (animate_polar, polar, snowball_cycle,  # noqa: E402
                        timeseries, tipping)

OUT = REPO / "docs" / "images"
FIGURES = REPO / "figures"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    polar._demo()        # ice caps from space at 96% sunlight
    tipping.main()       # the snowball hysteresis loop
    timeseries.main()    # the abrupt tip, over time
    snowball_cycle.main()  # freeze, CO2 build-up, thaw, recovery
    for src, dst in (
        ("polar_ice.png", "ice_caps_from_space.png"),
        ("tipping_point.png", "tipping_point.png"),
        ("timeseries.png", "timeseries.png"),
        ("snowball_cycle.png", "snowball_cycle.png"),
    ):
        shutil.copyfile(FIGURES / src, OUT / dst)

    # A shorter, lighter version of the polar-cap animation for the README.
    animate_polar.animate(path=str(OUT / "ice_caps.gif"), frames=40,
                          steps_per_frame=12, fps=10)

    for f in sorted(OUT.iterdir()):
        print(f"{f.name:28s} {f.stat().st_size / 1024:7.0f} KB")


if __name__ == "__main__":
    main()
