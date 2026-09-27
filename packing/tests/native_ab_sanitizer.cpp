/* Standalone ASan/UBSan control; never linked into production libraries. */
#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <limits>

extern "C" {
int ab_version(void);
int ab_scatter(double*, size_t, size_t, const int64_t*, const int64_t*,
               const int64_t*, const int64_t*, const double*, size_t);
int ab_compact(const double*, size_t, size_t, size_t, const int64_t*,
               const int64_t*, const int64_t*, const int64_t*, size_t,
               double*, size_t);
size_t ab_vertices(const double*, size_t, double, double*, int64_t*, size_t);
void prefix_axis0_rowmajor(double*, size_t, size_t);
size_t topk_finite(const double*, size_t, size_t, size_t*);
void *ab_exact_create(const char*);
void *ab_exact_query(const void*, const char*, int);
void ab_exact_free_string(void*);
void ab_exact_destroy(void*);
}
int main() {
    assert(ab_version() == 1);
    double grid[16] = {};
    int64_t left[2] = {0, 1}, right[2] = {2, 3};
    int64_t bottom[2] = {0, 1}, top[2] = {2, 3};
    double weights[2] = {1.0, 2.0};
    assert(ab_scatter(grid, 4, 4, left, right, bottom, top, weights, 2) == 0);
    assert(grid[0] == 1.0 && grid[5] == 2.0);
    double backup[16]; std::memcpy(backup, grid, sizeof(grid));
    top[1] = 99;
    assert(ab_scatter(grid, 4, 4, left, right, bottom, top, weights, 2) != 0);
    assert(std::memcmp(grid, backup, sizeof(grid)) == 0);
    int64_t ids[2] = {0, 2}, first[2] = {0, 1}, width[2] = {3, 2}, offset[2] = {0, 3};
    double out[5] = {};
    assert(ab_compact(grid, 3, 3, 4, ids, first, width, offset, 2, out, 5) == 0);
    width[1] = 99;
    assert(ab_compact(grid, 3, 3, 4, ids, first, width, offset, 2, out, 5) != 0);
    double prefix[6] = {1,2,3,4,5,6};
    prefix_axis0_rowmajor(prefix, 2, 3);
    assert(prefix[3] == 5 && prefix[4] == 7 && prefix[5] == 9);
    const double nan = std::numeric_limits<double>::quiet_NaN();
    double scores[5] = {nan, 3, -1, -1, 0}; size_t selected[3];
    assert(topk_finite(scores, 5, 3, selected) == 3);
    assert(selected[0] == 2 && selected[1] == 3 && selected[2] == 4);
    double lines[12] = {1,0,-1, 1,0,1, 0,1,-1, 0,1,1};
    const size_t n = ab_vertices(lines, 4, 2.0, nullptr, nullptr, 0);
    assert(n == 4);
    double points[8]; int64_t sources[8];
    assert(ab_vertices(lines, 4, 2.0, points, sources, 4) == 4);
    void *depth = ab_exact_create("1\n2 0 -1 1 0 2 -1 1 1 3\n");
    assert(depth);
    void *value = ab_exact_query(depth, "2\n1 1 2\n-1 -1 2\n", 0);
    assert(value && std::strcmp(static_cast<char*>(value), "2/3") == 0);
    ab_exact_free_string(value);
    assert(!ab_exact_query(depth, "1\n0 0 0\n", 0));
    assert(!ab_exact_query(depth, "0\n", 99));
    ab_exact_destroy(depth);
    assert(!ab_exact_create("1\n0 0 0 0 0 0 0 0 1 0\n"));
    return 0;
}
