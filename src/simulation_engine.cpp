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
    init_state();
}

void SimulationEngine::set_params(const Params& params) {
    params_ = params;
    build_lat_tables();
}

void SimulationEngine::build_lat_tables() {
    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    row_insol_.assign(rows, 0.0);
    row_weight_.assign(rows, 0.0);
    weight_sum_ = 0.0;

    double* S = grid_.solar();
    const double dlat = 180.0 / static_cast<double>(rows);  // degrees per row

    for (std::size_t i = 0; i < rows; ++i) {
        // Cell-centered latitude; row 0 is the North-pole side (+90).
        const double lat_deg = 90.0 - (static_cast<double>(i) + 0.5) * dlat;
        const double lat_rad = lat_deg * kPi / 180.0;
        const double sin_lat = std::sin(lat_rad);
        // Normalized annual-mean insolation (global mean = 1).
        const double insol = 1.0 + params_.s2 * legendre_p2(sin_lat);

        row_insol_[i] = insol;
        row_weight_[i] = std::cos(lat_rad);  // cell-area weight
        weight_sum_ += row_weight_[i];

        double* srow = S + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            srow[j] = insol;  // static insolation field (for viz)
        }
    }
}

void SimulationEngine::init_state() {
    // Dynamic state reset to the ice-free base for the current parameters. Ice
    // and temperature are left to the caller (the grid zero-initializes them;
    // seed_equilibrium sets both explicitly).
    const std::size_t n = grid_.size();
    double* A = grid_.albedo();
    double* C = grid_.co2();

    iteration_ = 0;
    co2_ = params_.co2_base;
    for (std::size_t i = 0; i < n; ++i) {
        A[i] = params_.base_albedo;  // ice-free until ice accumulates
        C[i] = co2_;                 // well-mixed CO2 (uniform field)
    }
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

double SimulationEngine::open_water_fraction() const noexcept {
    // cell_albedo is linear in each cell's ice fraction, so the area-weighted
    // planetary albedo gives the ice-covered share of the surface directly
    // (thin ice counts partly, exactly as it does for albedo).
    const double albedo_range = params_.ice_albedo - params_.base_albedo;
    if (albedo_range <= 0.0) {
        return 1.0;  // no albedo contrast, so ice cover cannot be inferred
    }
    double open = (params_.ice_albedo - planetary_albedo()) / albedo_range;
    if (open < 0.0) open = 0.0;
    else if (open > 1.0) open = 1.0;
    return open;
}

double SimulationEngine::global_temperature() const noexcept {
    return area_weighted_mean(grid_.temperature());
}

double SimulationEngine::sea_level_drop() const noexcept {
    if (params_.ocean_fraction <= 0.0) {
        return 0.0;
    }
    // Only ice resting on land lowers sea level: ice over the ocean floats and
    // already displaces its own weight. The grid has no land/ocean mask, so the
    // land share of every ice-covered cell is taken as the global land fraction.
    // The water locked in that grounded ice is drawn from the ocean area.
    const double land_fraction = 1.0 - params_.ocean_fraction;
    const double mean_ice = area_weighted_mean(grid_.ice());
    return params_.ice_density_ratio * mean_ice * land_fraction /
           params_.ocean_fraction;
}

void SimulationEngine::seed_equilibrium() {
    // Reset to a fully consistent "at rest, ice-free" state for the current
    // forcing: no ice, base albedo, CO2 at base, iteration count zero (via
    // init_state), and temperature at its ice-free radiative equilibrium. Safe
    // to reuse to restart a run, not only to initialize a fresh engine.
    init_state();

    const std::size_t rows = grid_.rows();
    const std::size_t cols = grid_.cols();
    double* T = grid_.temperature();
    double* I = grid_.ice();

    const double qfac = params_.solar_mult * params_.solar_constant / 4.0;
    const double denom = params_.olr_b + params_.transport_c;
    // Ice-free global mean (transport nets to zero globally, CO2 at base -> F=0).
    const double t_global =
        (qfac * (1.0 - params_.base_albedo) - params_.olr_a) / params_.olr_b;
    const double c1 = -params_.olr_a + params_.transport_c * t_global;

    for (std::size_t i = 0; i < rows; ++i) {
        const double q = qfac * row_insol_[i];
        const double t_eq = (q * (1.0 - params_.base_albedo) + c1) / denom;
        double* trow = T + i * cols;
        double* irow = I + i * cols;
        for (std::size_t j = 0; j < cols; ++j) {
            trow[j] = t_eq;
            irow[j] = 0.0;
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
    // CO2 relaxes toward it on a slow ocean timescale. The exchange happens only
    // through open water: sea ice caps the ocean, so the rate scales with the
    // ice-free share of the surface and stops entirely once the ocean freezes
    // over. Open seawater cannot be colder than its freezing point, so cooling
    // below that cannot keep pulling CO2 into the ocean. Uses the previous
    // step's fields (stable one-step lag).
    const double t_global = global_temperature();
    const double t_ocean =
        (t_global > params_.t_freeze) ? t_global : params_.t_freeze;
    double co2_eq = params_.co2_base +
        params_.co2_solubility * (t_ocean - params_.co2_ref_temp);
    if (co2_eq < params_.co2_floor) co2_eq = params_.co2_floor;
    const double k_co2 = open_water_fraction() *
        (1.0 - std::exp(-params_.dt / params_.co2_relax_time));
    co2_ += (co2_eq - co2_) * k_co2;
    if (co2_ < params_.co2_floor) co2_ = params_.co2_floor;
    const double greenhouse_f = params_.co2_forcing * std::log(co2_ / params_.co2_base);

    // --- Energy-balance equilibrium temperature ---
    // T_eq = [ Q*(1-albedo) - olr_a + F + transport_c*T_global ] / (olr_b + transport_c)
    // The transport term (using the lagged global mean) is the planetary channel
    // that lets a growing ice cap cool the rest of the world and advance its
    // margin equatorward.
    const double qfac = params_.solar_mult * params_.solar_constant / 4.0;
    const double denom = params_.olr_b + params_.transport_c;
    const double c1 = -params_.olr_a + greenhouse_f + params_.transport_c * t_global;
    // Exact relaxation factor for a constant target over dt (unconditionally stable).
    const double k = 1.0 - std::exp(-params_.dt / params_.relax_time);
    const double dt = params_.dt;
    const bool saturating = params_.ice_max > 0.0;

    for (std::size_t i = 0; i < rows; ++i) {
        const double q = qfac * row_insol_[i];
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

            // 2) Local energy-balance equilibrium temperature.
            const double t_eq = (q * (1.0 - alb) + c1) / denom;

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
