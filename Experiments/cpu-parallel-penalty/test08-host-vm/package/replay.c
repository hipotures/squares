#define _GNU_SOURCE
#include <errno.h>
#include <math.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

/* Portable native replay of the current scatter, prefix, interval copy,
   and stable top-13 path. The numerical loops preserve production order. */

typedef struct { double value; size_t index; } item;
static int greater(item a, item b) {
    return a.value > b.value || (a.value == b.value && a.index > b.index);
}
static void swap(item *a, item *b) { item t = *a; *a = *b; *b = t; }
static size_t topk_finite(const double *values, size_t length, size_t k, size_t *result) {
    if (k == 0 || k > 64) return 0;
    item heap[64];
    size_t size = 0;
    for (size_t index = 0; index < length; index++) {
        double value = values[index];
        if (!isfinite(value)) continue;
        item current = {value, index};
        if (size < k) {
            size_t pos = size++;
            heap[pos] = current;
            while (pos) {
                size_t parent = (pos - 1) / 2;
                if (!greater(heap[pos], heap[parent])) break;
                swap(&heap[pos], &heap[parent]);
                pos = parent;
            }
        } else if (greater(heap[0], current)) {
            heap[0] = current;
            size_t pos = 0;
            while (2 * pos + 1 < size) {
                size_t child = 2 * pos + 1;
                if (child + 1 < size && greater(heap[child + 1], heap[child])) child++;
                if (!greater(heap[child], heap[pos])) break;
                swap(&heap[child], &heap[pos]);
                pos = child;
            }
        }
    }
    for (size_t i = 0; i < size; i++) {
        size_t best = i;
        for (size_t j = i + 1; j < size; j++)
            if (greater(heap[best], heap[j])) best = j;
        swap(&heap[i], &heap[best]);
        result[i] = heap[i].index;
    }
    return size;
}

typedef struct {
    uint32_t rows, columns, live, flat_length;
    uint64_t expected_diff, expected_mass, expected_select;
    uint32_t *left, *right, *bottom, *top, *first, *last;
    double *weight;
} grid_case;

typedef struct {
    double wall, cpu;
    uint64_t checksum, calls;
    int error;
} worker_result;

static uint64_t fnv(const void *input, size_t bytes, uint64_t state) {
    const unsigned char *p = input;
    for (size_t i = 0; i < bytes; i++) {
        state ^= p[i];
        state *= UINT64_C(1099511628211);
    }
    return state;
}
static uint64_t fnv_start(void) { return UINT64_C(14695981039346656037); }
static void read_exact(FILE *file, void *out, size_t size) {
    if (fread(out, 1, size, file) != size) {
        fprintf(stderr, "truncated input file\n"); exit(2);
    }
}
static void *alloc(size_t bytes) {
    void *p = malloc(bytes ? bytes : 1);
    if (!p) { perror("malloc"); exit(2); }
    return p;
}
static double elapsed(struct timespec start, struct timespec end) {
    return (double)(end.tv_sec - start.tv_sec) +
           (double)(end.tv_nsec - start.tv_nsec) * 1e-9;
}

static grid_case *load_cases(const char *name, uint32_t *case_count,
                             size_t *max_cells, size_t *max_flat) {
    FILE *file = fopen(name, "rb");
    if (!file) { perror(name); exit(2); }
    char magic[8]; uint32_t version;
    read_exact(file, magic, 8); read_exact(file, &version, 4);
    read_exact(file, case_count, 4);
    if (memcmp(magic, "SQCPUV1\0", 8) || version != 1 ||
        *case_count != 181) { fprintf(stderr, "wrong input version\n"); exit(2); }
    grid_case *cases = alloc((size_t)*case_count * sizeof(*cases));
    memset(cases, 0, (size_t)*case_count * sizeof(*cases));
    *max_cells = *max_flat = 0;
    for (uint32_t k = 0; k < *case_count; k++) {
        grid_case *c = &cases[k];
        read_exact(file, &c->rows, 4); read_exact(file, &c->columns, 4);
        read_exact(file, &c->live, 4); read_exact(file, &c->flat_length, 4);
        read_exact(file, &c->expected_diff, 8);
        read_exact(file, &c->expected_mass, 8);
        read_exact(file, &c->expected_select, 8);
        if (c->rows < 2 || c->columns < 2 || c->rows > 10000 ||
            c->columns > 10000 || c->live > 100000 ||
            c->flat_length > (size_t)c->rows * c->columns) {
            fprintf(stderr, "invalid case dimensions %u\n", k); exit(2);
        }
        size_t n = c->live, r = c->rows - 1;
        c->left = alloc(n * 4); c->right = alloc(n * 4);
        c->bottom = alloc(n * 4); c->top = alloc(n * 4);
        c->weight = alloc(n * 8); c->first = alloc(r * 4); c->last = alloc(r * 4);
        read_exact(file, c->left, n * 4); read_exact(file, c->right, n * 4);
        read_exact(file, c->bottom, n * 4); read_exact(file, c->top, n * 4);
        read_exact(file, c->weight, n * 8);
        read_exact(file, c->first, r * 4); read_exact(file, c->last, r * 4);
        size_t width_sum = 0;
        for (size_t i = 0; i < r; i++) {
            if (c->last[i] < c->first[i] || c->last[i] >= c->columns) {
                fprintf(stderr, "invalid interval in case %u\n", k); exit(2);
            }
            width_sum += c->last[i] - c->first[i];
        }
        if (width_sum != c->flat_length) {
            fprintf(stderr, "flat length mismatch in case %u\n", k); exit(2);
        }
        size_t cells = (size_t)c->rows * c->columns;
        if (cells > *max_cells) *max_cells = cells;
        if (c->flat_length > *max_flat) *max_flat = c->flat_length;
    }
    if (fgetc(file) != EOF) { fprintf(stderr, "trailing input bytes\n"); exit(2); }
    fclose(file);
    return cases;
}

static uint64_t execute(const grid_case *c, double *grid, double *flat, int verify) {
    size_t rows = c->rows, columns = c->columns;
    memset(grid, 0, rows * columns * sizeof(double));
    for (size_t i = 0; i < c->live; i++)
        grid[(size_t)c->left[i] * columns + c->bottom[i]] += c->weight[i];
    for (size_t i = 0; i < c->live; i++)
        grid[(size_t)c->right[i] * columns + c->bottom[i]] += -c->weight[i];
    for (size_t i = 0; i < c->live; i++)
        grid[(size_t)c->left[i] * columns + c->top[i]] += -c->weight[i];
    for (size_t i = 0; i < c->live; i++)
        grid[(size_t)c->right[i] * columns + c->top[i]] += c->weight[i];
    if (verify && fnv(grid, rows * columns * 8, fnv_start()) != c->expected_diff)
        return 0;
    for (size_t row = 0; row < rows; row++) {
        double *current = grid + row * columns;
        for (size_t column = 1; column < columns; column++)
            current[column] += current[column - 1];
    }
    for (size_t row = 1; row < rows; row++) {
        double *current = grid + row * columns;
        const double *previous = grid + (row - 1) * columns;
        for (size_t column = 0; column < columns; column++)
            current[column] += previous[column];
    }
    if (verify) {
        uint64_t mass_hash = fnv_start();
        for (size_t row = 0; row < rows - 1; row++)
            mass_hash = fnv(grid + row * columns, (columns - 1) * 8, mass_hash);
        if (mass_hash != c->expected_mass) return 0;
    }
    size_t filled = 0;
    for (size_t row = 0; row < rows - 1; row++) {
        size_t first = c->first[row], width = c->last[row] - first;
        if (width) {
            memcpy(flat + filled, grid + row * columns + first, width * 8);
            filled += width;
        }
    }
    if (filled != c->flat_length) return 0;
    size_t top[13];
    if (topk_finite(flat, filled, 13, top) != 13) return 0;
    uint64_t selection_hash = fnv_start();
    for (size_t i = 0; i < 13; i++) {
        uint64_t index = top[i];
        selection_hash = fnv(&index, 8, selection_hash);
        selection_hash = fnv(&flat[index], 8, selection_hash);
    }
    if (verify && selection_hash != c->expected_select) return 0;
    return selection_hash;
}

static void child(int index, int workers, int repeats, int go_fd, int result_fd,
                  grid_case *cases, uint32_t ncases, size_t max_cells,
                  size_t max_flat) {
    cpu_set_t set; CPU_ZERO(&set); CPU_SET(index, &set);
    if (sched_setaffinity(0, sizeof(set), &set)) { perror("sched_setaffinity"); _exit(2); }
    double *grid = alloc(max_cells * 8);
    double *flat = alloc(max_flat * 8);
    for (uint32_t c = index; c < ncases; c += workers) {
        if (!execute(&cases[c], grid, flat, 1)) {
            fprintf(stderr, "warm checksum mismatch case %u worker %d\n", c, index);
            _exit(2);
        }
    }
    char ready = 'R';
    if (write(result_fd, &ready, 1) != 1) _exit(2);
    char go;
    if (read(go_fd, &go, 1) != 1 || go != 'G') _exit(2);
    struct timespec start_wall, end_wall, start_cpu, end_cpu;
    clock_gettime(CLOCK_MONOTONIC, &start_wall);
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &start_cpu);
    uint64_t checksum = fnv_start(), calls = 0;
    for (int iteration = 0; iteration < repeats; iteration++) {
        for (uint32_t c = index; c < ncases; c += workers) {
            uint64_t selected = execute(&cases[c], grid, flat, 0);
            if (!selected) _exit(2);
            checksum = fnv(&selected, 8, checksum);
            calls++;
        }
    }
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &end_cpu);
    clock_gettime(CLOCK_MONOTONIC, &end_wall);
    worker_result result = {elapsed(start_wall, end_wall),
                            elapsed(start_cpu, end_cpu), checksum, calls, 0};
    if (write(result_fd, &result, sizeof(result)) != sizeof(result)) _exit(2);
    _exit(0);
}

int main(int argc, char **argv) {
    const char *data = NULL; int workers = 0, repeats = 0;
    for (int i = 1; i < argc; i++) {
        if (!strcmp(argv[i], "--data") && ++i < argc) data = argv[i];
        else if (!strcmp(argv[i], "--workers") && ++i < argc) workers = atoi(argv[i]);
        else if (!strcmp(argv[i], "--repeats") && ++i < argc) repeats = atoi(argv[i]);
        else { fprintf(stderr, "usage: replay --data FILE --workers N --repeats R\n"); return 2; }
    }
    if (!data || workers < 1 || workers > 16 || repeats < 1) return 2;
    uint32_t ncases; size_t max_cells, max_flat;
    grid_case *cases = load_cases(data, &ncases, &max_cells, &max_flat);
    int go[16][2], result[16][2]; pid_t pids[16];
    for (int i = 0; i < workers; i++) {
        if (pipe(go[i]) || pipe(result[i])) { perror("pipe"); return 2; }
        pids[i] = fork();
        if (pids[i] < 0) { perror("fork"); return 2; }
        if (pids[i] == 0) {
            close(go[i][1]); close(result[i][0]);
            child(i, workers, repeats, go[i][0], result[i][1], cases,
                  ncases, max_cells, max_flat);
        }
        close(go[i][0]); close(result[i][1]);
    }
    for (int i = 0; i < workers; i++) {
        char ready;
        if (read(result[i][0], &ready, 1) != 1 || ready != 'R') {
            fprintf(stderr, "worker %d failed during warmup\n", i); return 2;
        }
    }
    printf("READY ");
    for (int i = 0; i < workers; i++) printf("%s%d", i ? "," : "", pids[i]);
    printf("\n"); fflush(stdout);
    if (getchar() == EOF) return 2;
    struct timespec start, end;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (int i = 0; i < workers; i++) {
        char go_byte = 'G';
        if (write(go[i][1], &go_byte, 1) != 1) return 2;
    }
    worker_result values[16];
    for (int i = 0; i < workers; i++) {
        if (read(result[i][0], &values[i], sizeof(values[i])) != sizeof(values[i])) {
            fprintf(stderr, "worker %d failed during replay\n", i); return 2;
        }
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double wall = elapsed(start, end), cpu = 0, max_worker_wall = 0;
    uint64_t combined = fnv_start(), calls = 0;
    for (int i = 0; i < workers; i++) {
        int status;
        if (waitpid(pids[i], &status, 0) != pids[i] || !WIFEXITED(status) ||
            WEXITSTATUS(status)) { fprintf(stderr, "worker %d exited badly\n", i); return 2; }
        cpu += values[i].cpu; calls += values[i].calls;
        if (values[i].wall > max_worker_wall) max_worker_wall = values[i].wall;
        combined = fnv(&values[i].checksum, 8, combined);
    }
    printf("RESULT {\"workers\":%d,\"repeats\":%d,\"directions\":%u,"
           "\"wall\":%.9f,\"max_worker_wall\":%.9f,\"worker_cpu\":%.9f,"
           "\"calls\":%llu,\"checksum\":\"%016llx\",\"workers_detail\":[",
           workers, repeats, ncases, wall, max_worker_wall, cpu,
           (unsigned long long)calls, (unsigned long long)combined);
    for (int i = 0; i < workers; i++)
        printf("%s{\"cpu\":%d,\"pid\":%d,\"wall\":%.9f,\"cpu_time\":%.9f,"
               "\"calls\":%llu,\"checksum\":\"%016llx\"}",
               i ? "," : "", i, pids[i], values[i].wall, values[i].cpu,
               (unsigned long long)values[i].calls,
               (unsigned long long)values[i].checksum);
    printf("]}\n"); fflush(stdout);
    return 0;
}
