#include "simulation_engine.hpp"

#include <cmath>

namespace iceage {

namespace {
constexpr double kPi = 3.14159265358979323846;

// Second Legendre polynomial P2(x) = (3x^2 - 1) / 2.
inline double legendre_p2(double x) noexcept { return 0.5 * (3.0 * x * x - 1.0); }
} // namespace

SimulationEngine::SimulationEngine(ClimateGrid& grid, const Params& params)
    : grid_(grid), params_(params) {
    build_lat_tables();
}

void SimulationEngine::set_params(const Params& params) {
    params_ = params;
    build_lat_tables();
}

void SimulationEngine::build_lat_tables() {
    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    row_offset_.assign(rows, 0.0);

    double* S = grid_.solar();
    const double dlat = 180.0 / static_cast<double>(rows);  // degrees per row

    for (std::size_t i = 0; i < rows; ++i) {
        // Cell-centered latitude; row 0 is the North-pole side (+90).
        const double lat_deg = 90.0 - (static_cast<double>(i) + 0.5) * dlat;
        const double sin_lat = std::sin(lat_deg * kPi / 180.0);
        // Normalized annual-mean insolation (global mean = 1).
        const double insol = 1.0 + params_.s2 * legendre_p2(sin_lat);

        row_offset_[i] = params_.lat_gradient * (insol - 1.0);

        // Publish the insolation field for visualization (constant along a row).
        double* srow = S + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            srow[j] = insol;
        }
    }
}

double SimulationEngine::global_equilibrium(double t) const noexcept {
    return params_.t0_global - params_.cooling_rate * t;
}

void SimulationEngine::seed_equilibrium() {
    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    double* T = grid_.temperature();

    const double t_ref = global_equilibrium(time());
    for (std::size_t i = 0; i < rows; ++i) {
        const double t_eq = t_ref + row_offset_[i];
        double* trow = T + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            trow[j] = t_eq;
        }
    }
}

void SimulationEngine::step() {
    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    double* T = grid_.temperature();

    double* I = grid_.ice();

    // Global mean at the end of this step.
    const double t_ref = global_equilibrium(time() + params_.dt);
    // Exact relaxation factor for a constant target over dt: unconditionally
    // stable, unlike raw forward Euler which can overshoot when dt > relax_time.
    const double k = 1.0 - std::exp(-params_.dt / params_.relax_time);
    const double dt = params_.dt;
    const bool saturating = params_.ice_max > 0.0;

    for (std::size_t i = 0; i < rows; ++i) {
        const double t_eq = t_ref + row_offset_[i];
        double* trow = T + i * cols;
        double* irow = I + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            // 1) Relax temperature toward its local equilibrium.
            trow[j] += (t_eq - trow[j]) * k;

            // 2) Ice mass balance driven by the updated temperature.
            const double temp = trow[j];
            double ice = irow[j];
            if (temp < params_.t_freeze) {
                const double head = saturating ? (1.0 - ice / params_.ice_max)
                                               : 1.0;
                ice += params_.accum_rate * head * dt;
            } else {
                ice -= params_.melt_rate * (temp - params_.t_freeze) * dt;
            }
            if (ice < 0.0) {
                ice = 0.0;
            } else if (saturating && ice > params_.ice_max) {
                ice = params_.ice_max;
            }
            irow[j] = ice;
        }
    }

    ++iteration_;
}

} // namespace iceage
