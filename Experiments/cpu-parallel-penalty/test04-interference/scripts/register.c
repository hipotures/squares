/* Tiny-state integer loop for the frequency/compute control. */
#include <stdint.h>
uint64_t register_spin(uint64_t n, uint64_t seed) {
    uint64_t x = seed | 1;
    for (uint64_t i=0; i<n; i++) {
        x ^= x << 13;
        x ^= x >> 7;
        x ^= x << 17;
        x *= UINT64_C(0x9e3779b97f4a7c15);
    }
    return x;
}
