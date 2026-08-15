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
    row_insol_.assign(rows, 0.0);
    row_weight_.assign(rows, 0.0);
    weight_sum_ = 0.0;
    co2_ = params_.co2_base;

    double* S = grid_.solar();
    double* A = grid_.albedo();
    double* C = grid_.co2();
    const double dlat = 180.0 / static_cast<double>(rows);  // degrees per row

    for (std::size_t i = 0; i < rows; ++i) {
        // Cell-centered latitude; row 0 is the North-pole side (+90).
        const double lat_deg = 90.0 - (static_cast<double>(i) + 0.5) * dlat;
        const double lat_rad = lat_deg * kPi / 180.0;
        const double sin_lat = std::sin(lat_rad);
        // Normalized annual-mean insolation (global mean = 1).
        const double insol = 1.0 + params_.s2 * legendre_p2(sin_lat);

        row_offset_[i] = params_.lat_gradient * (insol - 1.0);
        row_insol_[i] = insol;
        row_weight_[i] = std::cos(lat_rad);  // cell-area weight
        weight_sum_ += row_weight_[i];

        double* srow = S + i * cols;
        double* arow = A + i * cols;
        double* crow = C + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            srow[j] = insol;                 // static insolation field (for viz)
            arow[j] = params_.base_albedo;   // ice-free until ice accumulates
            crow[j] = co2_;                  // well-mixed CO2 (uniform field)
        }
    }
}

double SimulationEngine::area_weighted_mean(const double* field) const noexcept {
    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    if (weight_sum_ <= 0.0) {
        return 0.0;
    }
    double weighted = 0.0;
    for (std::size_t i = 0; i < rows; ++i) {
        const double* frow = field + i * cols;
        double row_sum = 0.0;
        for (std::size_t j = 0; j < cols; ++j) {
            row_sum += frow[j];
        }
        weighted += row_weight_[i] * (row_sum / static_cast<double>(cols));
    }
    return weighted / weight_sum_;
}

double SimulationEngine::planetary_albedo() const noexcept {
    return area_weighted_mean(grid_.albedo());
}

double SimulationEngine::global_temperature() const noexcept {
    return area_weighted_mean(grid_.temperature());
}

double SimulationEngine::sea_level_drop() const noexcept {
    if (params_.ocean_fraction <= 0.0) {
        return 0.0;
    }
    // Area-weighted mean ice thickness over the whole globe (all ice treated
    // as grounded land ice: the toy has no land/ocean mask).
    const double mean_ice = area_weighted_mean(grid_.ice());
    return params_.ice_density_ratio * mean_ice / params_.ocean_fraction;
}

double SimulationEngine::cell_albedo(double ice) const noexcept {
    double f;
    if (params_.ice_albedo_depth > 0.0) {
        f = ice / params_.ice_albedo_depth;
    } else {
        f = (ice > 0.0) ? 1.0 : 0.0;
    }
    if (f < 0.0) f = 0.0;
    else if (f > 1.0) f = 1.0;
    return params_.base_albedo + (params_.ice_albedo - params_.base_albedo) * f;
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
    double* A = grid_.albedo();
    double* C = grid_.co2();

    // --- CO2 greenhouse feedback (well-mixed global scalar) ---
    // Colder oceans dissolve more CO2, lowering the atmospheric equilibrium;
    // CO2 relaxes toward it on a slow ocean timescale. Uses the previous step's
    // global mean temperature (stable one-step lag).
    const double t_global = global_temperature();
    double co2_eq = params_.co2_base +
        params_.co2_solubility * (t_global - params_.t0_global);
    if (co2_eq < params_.co2_floor) co2_eq = params_.co2_floor;
    const double k_co2 = 1.0 - std::exp(-params_.dt / params_.co2_relax_time);
    co2_ += (co2_eq - co2_) * k_co2;
    if (co2_ < params_.co2_floor) co2_ = params_.co2_floor;
    // Logarithmic greenhouse forcing as a temperature anomaly (0 at co2_base).
    const double greenhouse = params_.co2_climate_sens *
        std::log2(co2_ / params_.co2_base);

    // Global reference temperature at the end of this step: the secular cooling
    // trend, cooled further by the planetary-albedo feedback (previous step's
    // albedo, a stable one-step lag that closes the global energy balance), and
    // shifted by the CO2 greenhouse anomaly. The albedo channel lets a growing
    // ice cap advance its own margin equatorward.
    const double planet_alb = planetary_albedo();
    const double t_ref = global_equilibrium(time() + params_.dt) -
        params_.planetary_gain * (planet_alb - params_.base_albedo) +
        greenhouse;
    // Exact relaxation factor for a constant target over dt: unconditionally
    // stable, unlike raw forward Euler which can overshoot when dt > relax_time.
    const double k = 1.0 - std::exp(-params_.dt / params_.relax_time);
    const double dt = params_.dt;
    const bool saturating = params_.ice_max > 0.0;

    for (std::size_t i = 0; i < rows; ++i) {
        const double base_eq = t_ref + row_offset_[i];
        const double insol = row_insol_[i];
        double* trow = T + i * cols;
        double* irow = I + i * cols;
        double* arow = A + i * cols;
        double* crow = C + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            // 0) Publish the well-mixed CO2 into the field (uniform).
            crow[j] = co2_;

            // 1) Albedo from the current ice cover.
            const double alb = cell_albedo(irow[j]);
            arow[j] = alb;

            // 2) Local equilibrium including the ice-albedo feedback: reflective
            //    cells absorb less sunlight (weighted by insolation) and cool.
            const double t_eq = base_eq -
                params_.albedo_gain * insol * (alb - params_.base_albedo);

            // 3) Relax temperature toward that equilibrium.
            trow[j] += (t_eq - trow[j]) * k;

            // 4) Ice mass balance driven by the updated temperature.
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
