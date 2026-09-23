/* Build: cc -O3 -fPIC -shared -o /tmp/libtop13.so heap_select.c */
#include <math.h>
#include <stddef.h>

typedef struct { double value; size_t index; } item;
static int greater(item a, item b) {
    return a.value > b.value || (a.value == b.value && a.index > b.index);
}
static void swap(item *a, item *b) { item t = *a; *a = *b; *b = t; }

size_t topk_finite(const double *values, size_t length, size_t k, size_t *result) {
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
