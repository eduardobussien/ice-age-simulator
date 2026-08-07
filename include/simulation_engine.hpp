#pragma once

#include <cstddef>

#include "climate_grid.hpp"

namespace iceage {

// Advances a ClimateGrid through discrete time steps of length dt.
//
// The dynamics here are intentionally a placeholder: this scaffold exists to
// prove the C++/pybind11/NumPy loop end to end. Real temperature, ice-sheet,
// and albedo-feedback physics replace SimulationEngine::step() next.
class SimulationEngine {
public:
    explicit SimulationEngine(ClimateGrid& grid, double dt = 1.0);

    // Advance one temporal iteration of length dt.
    void step();

    std::size_t iteration() const noexcept { return iteration_; }
    double dt() const noexcept { return dt_; }

private:
    ClimateGrid& grid_;
    double dt_;
    std::size_t iteration_ = 0;
};

} // namespace iceage
