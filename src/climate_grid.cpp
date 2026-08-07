#include "climate_grid.hpp"

#include <algorithm>

namespace iceage {

ClimateGrid::ClimateGrid(std::size_t rows, std::size_t cols)
    : rows_(rows),
      cols_(cols),
      T_(rows * cols, 0.0),
      I_(rows * cols, 0.0),
      C_(rows * cols, 0.0),
      S_(rows * cols, 0.0),
      A_(rows * cols, 0.0) {}

void ClimateGrid::fill_temperature(double value) {
    std::fill(T_.begin(), T_.end(), value);
}

} // namespace iceage
