#pragma once

#include <cstddef>
#include <vector>

namespace iceage {

// Struct-of-Arrays climate state on a regular latitude x longitude grid.
//
// Each field is a contiguous, row-major (latitude-major) buffer of size
// rows * cols. Keeping one buffer per variable is cache-friendly for the
// per-variable physics updates and lets each field map to its own zero-copy
// NumPy array on the Python side.
class ClimateGrid {
public:
    ClimateGrid(std::size_t rows, std::size_t cols);

    std::size_t rows() const noexcept { return rows_; }
    std::size_t cols() const noexcept { return cols_; }
    std::size_t size() const noexcept { return rows_ * cols_; }

    // Raw buffer access (row-major). Non-const so Python holds mutable,
    // zero-copy views onto the same memory the C++ engine writes.
    double* temperature() noexcept { return T_.data(); }  // surface temp (C)
    double* ice()         noexcept { return I_.data(); }  // ice thickness (m)
    double* co2()         noexcept { return C_.data(); }  // CO2 proxy (ppm)
    double* solar()       noexcept { return S_.data(); }  // solar forcing (W/m^2)
    double* albedo()      noexcept { return A_.data(); }  // surface albedo (0..1)

    // Uniform initialization helper used before real physics lands.
    void fill_temperature(double value);

private:
    std::size_t rows_;
    std::size_t cols_;
    std::vector<double> T_;
    std::vector<double> I_;
    std::vector<double> C_;
    std::vector<double> S_;
    std::vector<double> A_;
};

} // namespace iceage
