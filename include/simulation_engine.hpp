#pragma once

#include <cstddef>
#include <vector>

#include "climate_grid.hpp"
#include "simulation_params.hpp"

namespace iceage {

// Advances a ClimateGrid through discrete time steps of length params.dt.
//
// Model so far:
//   * latitudinal insolation via the 2nd-Legendre EBM form,
//   * a secular global-mean cooling trend,
//   * per-cell relaxation toward the local equilibrium temperature, and
//   * ice-sheet mass balance (saturating accumulation / temperature-driven melt).
// Albedo feedback is added as a later feature.
class SimulationEngine {
public:
    explicit SimulationEngine(ClimateGrid& grid, const Params& params = Params{});

    // Replace the parameters and rebuild cached latitude tables.
    void set_params(const Params& params);
    const Params& params() const noexcept { return params_; }

    // Set every cell to the equilibrium temperature at the current time.
    // Use once to start a run "at rest" with the latitudinal profile in place.
    void seed_equilibrium();

    // Advance one temporal iteration of length params.dt.
    void step();

    std::size_t iteration() const noexcept { return iteration_; }
    double time() const noexcept { return static_cast<double>(iteration_) * params_.dt; }

private:
    // Global-mean equilibrium temperature at time t (secular cooling).
    double global_equilibrium(double t) const noexcept;
    // Precompute per-row latitudinal temperature offset + insolation field.
    void build_lat_tables();

    ClimateGrid& grid_;
    Params params_;
    std::size_t iteration_ = 0;
    std::vector<double> row_offset_;  // latitudinal dT per row (size = rows)
};

} // namespace iceage
