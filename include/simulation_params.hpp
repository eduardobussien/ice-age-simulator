#pragma once

namespace iceage {

// Physical parameters for a Budyko-Sellers energy-balance climate model.
//
// Radiative terms are in W/m^2; the published coefficients reproduce realistic
// present-day temperatures (global ~15 C, equator ~25 C, pole ~-13 C). The
// energy balance per cell is
//
//     solar_mult * (S0/4) * insol * (1 - albedo)          [absorbed shortwave]
//         = olr_a + olr_b * T                             [outgoing longwave]
//         + transport_c * (T - T_global)                  [meridional transport]
//         - co2_forcing * ln(CO2 / co2_base)              [greenhouse]
//
// solved for the local equilibrium temperature each step. The ice-albedo
// feedback is therefore intrinsic (albedo enters the absorbed term) rather than
// an ad-hoc gain.
struct Params {
    // Time integration.
    double dt = 1.0;             // time step (abstract "cycle" units)
    double relax_time = 5.0;     // timescale to approach radiative equilibrium

    // Shortwave / insolation.
    double s2 = -0.48;               // 2nd-Legendre insolation coefficient (EBM)
    double solar_constant = 1361.0;  // solar constant S0 (W/m^2)
    double solar_mult = 1.0;         // fractional multiplier on S0 (forcing knob)

    // Outgoing longwave radiation OLR = olr_a + olr_b * T (Budyko 1969 fit).
    double olr_a = 200.0;        // (W/m^2); tuned within Budyko's range for ~15 C baseline
    double olr_b = 2.09;         // (W/m^2 per C)
    double transport_c = 3.8;    // meridional heat-transport coefficient (W/m^2 per C)

    // Albedo.
    double base_albedo = 0.31;        // ice-free surface (planetary, 0..1)
    double ice_albedo = 0.60;         // fully ice-covered surface (0..1)
    double ice_albedo_depth = 100.0;  // ice thickness at which albedo saturates (~m)

    // Ice-sheet mass balance.
    double t_freeze = 0.0;       // ice accumulates below this temperature (C)
    double accum_rate = 100.0;   // max ice accumulation rate (thickness per time)
    double melt_rate = 50.0;     // melt per degree above freezing (thickness/C/time)
    double ice_max = 3000.0;     // saturation ice thickness (~m)

    // Sea level (derived from total land-ice volume).
    double ocean_fraction = 0.71;      // ocean fraction of the surface
    double ice_density_ratio = 0.917;  // rho_ice / rho_water

    // CO2 greenhouse feedback (well-mixed global scalar).
    double co2_base = 280.0;      // reference / starting CO2 (ppm)
    double co2_forcing = 5.35;    // radiative forcing coefficient (W/m^2 per ln)
    double co2_ref_temp = 15.0;   // global temp at which CO2 == co2_base (C)
    double co2_solubility = 10.0; // equilibrium CO2 shift per degree of global T (ppm/C)
    double co2_relax_time = 10.0; // ocean CO2 adjustment timescale (time units)
    double co2_floor = 10.0;      // minimum CO2 (ppm), keeps ln finite
};

} // namespace iceage
