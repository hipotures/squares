/* Experimental kernels. Single-threaded; the Python broker owns parallelism.
 * Build without fast-math or FP contraction. No input pointer is retained.
 * The accepted prefix/top-k sources are linked into the same local library.
 */
#include <math.h>
#include <stddef.h>
#include <stdint.h>
#include <string.h>

int ab_version(void) { return 1; }

int ab_scatter(double *grid, size_t rows, size_t cols,
               const int64_t *left, const int64_t *right,
               const int64_t *bottom, const int64_t *top,
               const double *weights, size_t n) {
    if (!rows || !cols || rows > SIZE_MAX / cols) return 1;
    /* Validate the entire input before modifying the grid. */
    for (size_t k = 0; k < n; ++k) {
        if (left[k] < 0 || right[k] < 0 || bottom[k] < 0 || top[k] < 0 ||
            (uint64_t)left[k] >= rows || (uint64_t)right[k] >= rows ||
            (uint64_t)bottom[k] >= cols || (uint64_t)top[k] >= cols) return 2;
    }
    /* Four distinct passes preserve np.add.at's original update order,
       including duplicate indices and signed-zero behavior. */
    for (size_t k = 0; k < n; ++k) grid[left[k] * cols + bottom[k]] += weights[k];
    for (size_t k = 0; k < n; ++k) grid[right[k] * cols + bottom[k]] += -weights[k];
    for (size_t k = 0; k < n; ++k) grid[left[k] * cols + top[k]] += -weights[k];
    for (size_t k = 0; k < n; ++k) grid[right[k] * cols + top[k]] += weights[k];
    return 0;
}

int ab_compact(const double *grid, size_t rows, size_t cols, size_t row_stride,
               const int64_t *ids, const int64_t *firsts, const int64_t *widths,
               const int64_t *offsets, size_t n, double *out, size_t capacity) {
    if (row_stride < cols || (rows && row_stride > SIZE_MAX / rows)) return 1;
    for (size_t k = 0; k < n; ++k) {
        if (ids[k] < 0 || firsts[k] < 0 || widths[k] < 0 || offsets[k] < 0 ||
            (uint64_t)ids[k] >= rows || (uint64_t)firsts[k] > cols ||
            (uint64_t)widths[k] > cols - (uint64_t)firsts[k] ||
            (uint64_t)offsets[k] > capacity ||
            (uint64_t)widths[k] > capacity - (uint64_t)offsets[k]) return 2;
    }
    for (size_t k = 0; k < n; ++k) {
        memcpy(out + offsets[k], grid + ids[k] * row_stride + firsts[k],
               (size_t)widths[k] * sizeof(double));
    }
    return 0;
}

/* Same i,j order and scalar operations as colgen._vertices. A NULL output
 * performs the sizing pass. Python checks allocation sizes before the fill.
 */
size_t ab_vertices(const double *lines, size_t n, double half,
                   double *points, int64_t *sources, size_t capacity) {
    size_t count = 0;
    for (size_t i = 0; i < n; ++i) {
        const double a = lines[3*i], b = lines[3*i+1], e = lines[3*i+2];
        for (size_t j = i + 1; j < n; ++j) {
            const double c = lines[3*j], d = lines[3*j+1], f = lines[3*j+2];
            const double determinant = a*d - b*c;
            if (!(fabs(determinant) > 1e-12)) continue;
            const double x = (e*d - f*b) / determinant;
            const double y = (a*f - c*e) / determinant;
            if (!(fabs(x) <= half && fabs(y) <= half)) continue;
            if (points && count < capacity) {
                points[2*count] = x;
                points[2*count+1] = y;
                sources[2*count] = (int64_t)i;
                sources[2*count+1] = (int64_t)j;
            }
            ++count;
        }
    }
    return count;
}
