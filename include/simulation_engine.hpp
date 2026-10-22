#pragma once

#include <cstddef>
#include <vector>

#include "climate_grid.hpp"
#include "simulation_params.hpp"

namespace iceage {

// Advances a ClimateGrid through discrete time steps of length params.dt using
// a Budyko-Sellers energy balance (see simulation_params.hpp for the equation).
//
// Two feedbacks are intrinsic to the energy balance, linked by one coupling:
//   * ice-albedo     - ice raises albedo, cutting absorbed shortwave,
//   * CO2 greenhouse - cooling draws down well-mixed CO2, weakening forcing,
//   * heat transport - (a coupling, not a feedback) pulls every cell toward the
//     global mean, spreading a local cooling planet-wide; this is how a growing
//     ice cap chills its own margin and advances.
// The external driver is the solar multiplier: a uniform change in the Sun's
// output. Real orbital (Milankovitch) forcing instead shifts sunlight between
// latitudes and seasons with little change to the global total.
class SimulationEngine {
public:
    explicit SimulationEngine(ClimateGrid& grid, const Params& params = Params{});

    // Replace the parameters and rebuild cached latitude tables.
    void set_params(const Params& params);
    const Params& params() const noexcept { return params_; }

    // Live-adjust just the solar multiplier (the forcing knob) without resetting
    // the grid state - used to ramp or sweep the forcing over a run.
    void set_solar_mult(double value) noexcept { params_.solar_mult = value; }

    // Set every cell to the ice-free radiative equilibrium for the current
    // forcing. Use once to start a run "at rest".
    void seed_equilibrium();

    // Advance one temporal iteration of length params.dt.
    void step();

    std::size_t iteration() const noexcept { return iteration_; }
    double time() const noexcept { return static_cast<double>(iteration_) * params_.dt; }

    // Diagnostics.
    double sea_level_drop() const noexcept;     // metres of global sea-level fall
    double global_temperature() const noexcept; // area-weighted mean surface T (C)
    double planetary_albedo() const noexcept;   // area-weighted mean albedo
    double open_water_fraction() const noexcept; // ice-free share of surface (0..1)
    double co2() const noexcept { return co2_; } // well-mixed atmospheric CO2 (ppm)

private:
    // Per-cell albedo as a function of ice thickness.
    double cell_albedo(double ice) const noexcept;
    // cos(latitude) area-weighted global mean of a row-major grid field.
    double area_weighted_mean(const double* field) const noexcept;
    // Precompute per-row insolation / area-weight tables and the insolation
    // field. Derived from the parameters only; does not touch simulation state.
    void build_lat_tables();
    // Reset the dynamic state to its ice-free base (iteration, CO2, albedo /
    // CO2 fields). Called at construction and by seed_equilibrium, NOT by
    // set_params, so reconfiguring parameters mid-run preserves the run.
    void init_state();

    ClimateGrid& grid_;
    Params params_;
    std::size_t iteration_ = 0;
    double co2_ = 280.0;              // well-mixed atmospheric CO2 (ppm)
    std::vector<double> row_insol_;   // insolation per row (size = rows)
    std::vector<double> row_weight_;  // cos(latitude) area weight per row (size = rows)
    double weight_sum_ = 0.0;         // sum of row_weight_ (per column)
};

} // namespace iceage
