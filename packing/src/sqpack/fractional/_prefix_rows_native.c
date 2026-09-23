/* Row-major second pass of a two-dimensional prefix sum. Each column keeps
   the same top-to-bottom addition order as NumPy's axis-0 accumulate. */
#include <stddef.h>

void prefix_axis0_rowmajor(double *grid, size_t rows, size_t columns) {
    for (size_t row = 1; row < rows; row++) {
        double *current = grid + row * columns;
        const double *previous = grid + (row - 1) * columns;
        for (size_t column = 0; column < columns; column++) {
            current[column] += previous[column];
        }
    }
}
