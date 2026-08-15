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
//   * per-cell relaxation toward the local equilibrium temperature,
//   * ice-sheet mass balance (saturating accumulation / temperature-driven melt),
//   * ice-albedo feedback (reflective ice cools its own cell, closing the loop),
//   * CO2 greenhouse feedback (cooling draws down well-mixed CO2, amplifying it).
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

    // Global-mean sea-level fall (metres) from total land-ice volume, relative
    // to the ice-free state. Radius-independent: it depends only on the
    // area-weighted mean ice thickness, the ocean fraction, and ice density.
    double sea_level_drop() const noexcept;

    // Area-weighted global mean surface temperature (C).
    double global_temperature() const noexcept;
    // Current well-mixed atmospheric CO2 (ppm).
    double co2() const noexcept { return co2_; }

private:
    // Global-mean equilibrium temperature at time t (secular cooling).
    double global_equilibrium(double t) const noexcept;
    // Precompute per-row latitudinal temperature offset + insolation field.
    void build_lat_tables();

    // Per-cell albedo as a function of ice thickness.
    double cell_albedo(double ice) const noexcept;
    // cos(latitude) area-weighted global mean of a row-major grid field.
    double area_weighted_mean(const double* field) const noexcept;
    // Area-weighted (cos-latitude) mean of the current albedo field.
    double planetary_albedo() const noexcept;

    ClimateGrid& grid_;
    Params params_;
    std::size_t iteration_ = 0;
    double co2_ = 280.0;              // well-mixed atmospheric CO2 (ppm)
    std::vector<double> row_offset_;  // latitudinal dT per row (size = rows)
    std::vector<double> row_insol_;   // insolation per row (size = rows)
    std::vector<double> row_weight_;  // cos(latitude) area weight per row (size = rows)
    double weight_sum_ = 0.0;         // sum of row_weight_ (per column)
};

} // namespace iceage
