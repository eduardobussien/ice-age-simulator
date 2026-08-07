"""Minimal end-to-end smoke test of the C++ core via zero-copy NumPy views.

Run from the repo root once the extension is built:

    python -m python_sim.main
"""
from python_sim import ClimateGrid, SimulationEngine, __version__


def main() -> None:
    grid = ClimateGrid(rows=90, cols=180)   # 2-degree latitude x longitude
    grid.fill_temperature(15.0)             # uniform ~15 C baseline

    T = grid.T                              # zero-copy view onto C++ memory
    assert T.shape == (90, 180)
    assert not T.flags.owndata              # proves the view shares the buffer

    engine = SimulationEngine(grid, dt=1.0)

    print(f"core v{__version__}")
    print(f"start                mean T = {T.mean():7.3f} C")
    for _ in range(10):
        engine.step()
    print(f"after {engine.iteration:2d} steps        mean T = {T.mean():7.3f} C")
    print("zero-copy OK — the same buffer was mutated in place by C++")


if __name__ == "__main__":
    main()
