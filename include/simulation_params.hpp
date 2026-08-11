#pragma once

namespace iceage {

// Tunable parameters for the climate step. Defaults are rough modern-Earth
// annual-mean values; every field is adjustable from Python and applied via
// SimulationEngine::set_params (which rebuilds cached latitude tables).
struct Params {
    double dt = 1.0;             // time step, in abstract "cycle" units
    double t0_global = 14.0;     // global-mean equilibrium temperature at t=0 (C)
    double cooling_rate = 0.05;  // secular cooling of the global mean (C per unit time)
    double lat_gradient = 70.0;  // equator-to-pole temperature scaling (C)
    double relax_time = 5.0;     // relaxation timescale toward equilibrium (time units)
    double s2 = -0.48;           // 2nd-Legendre insolation coefficient (EBM)

    // Ice-sheet mass balance.
    double t_freeze = 0.0;       // ice accumulates below this temperature (C)
    double accum_rate = 100.0;   // max ice accumulation rate (thickness per time)
    double melt_rate = 50.0;     // melt rate per degree above freezing (thickness/C/time)
    double ice_max = 3000.0;     // saturation ice thickness (~metres)

    // Albedo feedback.
    double base_albedo = 0.30;      // reflectivity of ice-free surface (0..1)
    double ice_albedo = 0.60;       // reflectivity of fully ice-covered surface (0..1)
    double ice_albedo_depth = 100.0;  // ice thickness at which albedo saturates (~metres)
    double albedo_gain = 60.0;      // LOCAL cooling per unit (albedo x insolation) anomaly (C)
    double planetary_gain = 80.0;   // GLOBAL cooling per unit planetary-albedo anomaly (C)
};

} // namespace iceage
