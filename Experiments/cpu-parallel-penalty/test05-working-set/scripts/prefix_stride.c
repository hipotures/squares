/* Research-only row-major second prefix pass for padded row strides. */
#include <stddef.h>
void prefix_axis0_stride(double *grid, size_t rows, size_t columns, size_t stride) {
    for (size_t row=1; row<rows; row++) {
        double *current=grid+row*stride;
        const double *previous=grid+(row-1)*stride;
        for (size_t column=0; column<columns; column++)
            current[column]+=previous[column];
    }
}
