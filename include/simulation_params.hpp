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
};

} // namespace iceage
