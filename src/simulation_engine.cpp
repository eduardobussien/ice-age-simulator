#include "simulation_engine.hpp"

namespace iceage {

SimulationEngine::SimulationEngine(ClimateGrid& grid, double dt)
    : grid_(grid), dt_(dt) {}

void SimulationEngine::step() {
    // Placeholder dynamics: a small uniform cooling trend so the pipeline is
    // observable from Python. This is replaced by the real temperature / ice /
    // albedo-feedback physics in the next feature.
    double* T = grid_.temperature();
    const std::size_t n = grid_.size();
    const double cooling_per_step = 0.1 * dt_;  // degrees C

    for (std::size_t i = 0; i < n; ++i) {
        T[i] -= cooling_per_step;
    }

    ++iteration_;
}

} // namespace iceage
