/* Research-only row-major second pass of a two-dimensional prefix sum.
   Compile with: cc -O3 -fPIC -shared -o raw/libprefix_rows.so scripts/prefix_rows.c
   Each column keeps the same top-to-bottom floating-point addition order as
   NumPy's axis-0 accumulate; adjacent columns are traversed together. */
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
