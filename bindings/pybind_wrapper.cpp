#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>

#include "climate_grid.hpp"
#include "simulation_engine.hpp"

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

    py::class_<SimulationEngine>(m, "SimulationEngine")
        .def(py::init<ClimateGrid&, double>(),
             py::arg("grid"), py::arg("dt") = 1.0,
             py::keep_alive<1, 2>())  // engine keeps its grid alive
        .def("step", &SimulationEngine::step)
        .def_property_readonly("iteration", &SimulationEngine::iteration)
        .def_property_readonly("dt", &SimulationEngine::dt);
}
