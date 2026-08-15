"""End-to-end smoke test of the full climate model.

Temperature + ice growth + albedo feedback + sea level + CO2 greenhouse
feedback. Tracks a run over time, then isolates the CO2 feedback with an
on/off comparison.

Run from the repo root once the extension is built:

    python -m python_sim.main
"""
from python_sim import ClimateGrid, SimulationEngine, Params, __version__


def build(co2_solubility: float) -> SimulationEngine:
    grid = ClimateGrid(90, 180)
    params = Params()
    params.co2_solubility = co2_solubility  # 0 disables the CO2 drawdown feedback
    engine = SimulationEngine(grid, params)
    engine.seed_equilibrium()
    return engine


def main() -> None:
    print(f"core v{__version__}")

    # --- Time progression with the full model ---
    engine = build(co2_solubility=Params().co2_solubility)
    print(f"{'t':>5}{'global T':>11}{'CO2':>9}{'sea level':>12}")

    def report() -> None:
        print(f"{engine.time:5.0f}{engine.global_temperature:9.2f} C"
              f"{engine.co2:7.0f}p{-engine.sea_level_drop:10.1f} m")

    report()
    for _ in range(4):
        for _ in range(50):
            engine.step()
        report()

    # --- Isolate the CO2 feedback (identical forcing, drawdown off vs on) ---
    off = build(co2_solubility=0.0)
    for _ in range(200):
        off.step()
    print("\nCO2 feedback after 200 steps of identical forcing:")
    print(f"  drawdown OFF : global {off.global_temperature:6.2f} C   "
          f"CO2 {off.co2:4.0f} ppm")
    print(f"  drawdown ON  : global {engine.global_temperature:6.2f} C   "
          f"CO2 {engine.co2:4.0f} ppm")
    print(f"  extra cooling: {off.global_temperature - engine.global_temperature:5.2f} C")


if __name__ == "__main__":
    main()
