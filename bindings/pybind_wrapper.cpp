#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include <string>

#include "climate_grid.hpp"
#include "simulation_engine.hpp"
#include "simulation_params.hpp"

namespace py = pybind11;
using namespace iceage;

// Build a zero-copy 2-D NumPy view over a grid buffer.
//
// `owner` is the Python object that owns the underlying memory (the
// ClimateGrid). Passing it as the array's base keeps the grid alive for as
// long as any view exists and tells pybind11 not to copy or free the buffer.
static py::array_t<double> view(py::object owner, double* data,
                                std::size_t rows, std::size_t cols) {
    return py::array_t<double>(
        {rows, cols},                              // shape
        {cols * sizeof(double), sizeof(double)},   // strides (row-major)
        data,                                      // shared buffer
        std::move(owner));                         // base -> no copy
}

PYBIND11_MODULE(_core, m) {
    m.doc() = "Ice Age Simulator C++ core (SoA climate grid + engine).";
    m.attr("__version__") = "0.0.1";

    py::class_<ClimateGrid>(m, "ClimateGrid")
        .def(py::init<std::size_t, std::size_t>(),
             py::arg("rows"), py::arg("cols"))
        .def_property_readonly("rows", &ClimateGrid::rows)
        .def_property_readonly("cols", &ClimateGrid::cols)
        .def_property_readonly("shape", [](const ClimateGrid& g) {
            return py::make_tuple(g.rows(), g.cols());
        })
        .def("fill_temperature", &ClimateGrid::fill_temperature,
             py::arg("value"))
        // Zero-copy mutable views onto the Struct-of-Arrays buffers.
        .def_property_readonly("T", [](py::object self) {
            ClimateGrid& g = self.cast<ClimateGrid&>();
            return view(self, g.temperature(), g.rows(), g.cols());
        })
        .def_property_readonly("ice", [](py::object self) {
            ClimateGrid& g = self.cast<ClimateGrid&>();
            return view(self, g.ice(), g.rows(), g.cols());
        })
        .def_property_readonly("co2", [](py::object self) {
            ClimateGrid& g = self.cast<ClimateGrid&>();
            return view(self, g.co2(), g.rows(), g.cols());
        })
        .def_property_readonly("solar", [](py::object self) {
            ClimateGrid& g = self.cast<ClimateGrid&>();
            return view(self, g.solar(), g.rows(), g.cols());
        })
        .def_property_readonly("albedo", [](py::object self) {
            ClimateGrid& g = self.cast<ClimateGrid&>();
            return view(self, g.albedo(), g.rows(), g.cols());
        });

    py::class_<Params>(m, "Params")
        .def(py::init<>())
        .def_readwrite("dt", &Params::dt)
        .def_readwrite("t0_global", &Params::t0_global)
        .def_readwrite("cooling_rate", &Params::cooling_rate)
        .def_readwrite("lat_gradient", &Params::lat_gradient)
        .def_readwrite("relax_time", &Params::relax_time)
        .def_readwrite("s2", &Params::s2)
        .def_readwrite("t_freeze", &Params::t_freeze)
        .def_readwrite("accum_rate", &Params::accum_rate)
        .def_readwrite("melt_rate", &Params::melt_rate)
        .def_readwrite("ice_max", &Params::ice_max)
        .def_readwrite("base_albedo", &Params::base_albedo)
        .def_readwrite("ice_albedo", &Params::ice_albedo)
        .def_readwrite("ice_albedo_depth", &Params::ice_albedo_depth)
        .def_readwrite("albedo_gain", &Params::albedo_gain)
        .def_readwrite("planetary_gain", &Params::planetary_gain)
        .def("__repr__", [](const Params& p) {
            return "Params(dt=" + std::to_string(p.dt) +
                   ", t0_global=" + std::to_string(p.t0_global) +
                   ", cooling_rate=" + std::to_string(p.cooling_rate) +
                   ", lat_gradient=" + std::to_string(p.lat_gradient) +
                   ", relax_time=" + std::to_string(p.relax_time) +
                   ", s2=" + std::to_string(p.s2) +
                   ", t_freeze=" + std::to_string(p.t_freeze) +
                   ", accum_rate=" + std::to_string(p.accum_rate) +
                   ", melt_rate=" + std::to_string(p.melt_rate) +
                   ", ice_max=" + std::to_string(p.ice_max) +
                   ", base_albedo=" + std::to_string(p.base_albedo) +
                   ", ice_albedo=" + std::to_string(p.ice_albedo) +
                   ", ice_albedo_depth=" + std::to_string(p.ice_albedo_depth) +
                   ", albedo_gain=" + std::to_string(p.albedo_gain) +
                   ", planetary_gain=" + std::to_string(p.planetary_gain) + ")";
        });

    py::class_<SimulationEngine>(m, "SimulationEngine")
        .def(py::init<ClimateGrid&, const Params&>(),
             py::arg("grid"), py::arg("params") = Params{},
             py::keep_alive<1, 2>())  // engine keeps its grid alive
        .def("seed_equilibrium", &SimulationEngine::seed_equilibrium)
        .def("step", &SimulationEngine::step)
        .def("set_params", &SimulationEngine::set_params, py::arg("params"))
        .def_property_readonly("params", &SimulationEngine::params)
        .def_property_readonly("iteration", &SimulationEngine::iteration)
        .def_property_readonly("time", &SimulationEngine::time);
}
