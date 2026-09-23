#define _GNU_SOURCE
#include <pthread.h>
#include <sched.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

static double *a, *b, *c;
static size_t n, workers;
static int seconds;
static char operation[16];
static pthread_barrier_t barrier;
static double checksums[16];

static double now(void) { struct timespec t; clock_gettime(CLOCK_MONOTONIC, &t); return t.tv_sec + t.tv_nsec * 1e-9; }

static void *run(void *arg) {
  size_t id = (size_t)arg, lo = n * id / workers, hi = n * (id + 1) / workers;
  cpu_set_t set; CPU_ZERO(&set); CPU_SET((int)id, &set); pthread_setaffinity_np(pthread_self(), sizeof(set), &set);
  pthread_barrier_wait(&barrier);
  double t0 = now(), t1;
  uint64_t reps = 0; double sum = 0;
  do {
    if (!strcmp(operation, "read")) {
      double s = 0; for (size_t i=lo; i<hi; i++) s += a[i]; sum += s;
    } else if (!strcmp(operation, "copy")) {
      for (size_t i=lo; i<hi; i++) c[i] = a[i];
    } else if (!strcmp(operation, "write")) {
      for (size_t i=lo; i<hi; i++) c[i] = (double)(reps + i) * 0.000001;
    } else {
      for (size_t i=lo; i<hi; i++) c[i] = a[i] + 3.0 * b[i];
    }
    reps++; t1 = now();
  } while (t1 - t0 < seconds);
  checksums[id] = sum;
  return (void *)(uintptr_t)reps;
}

int main(int argc, char **argv) {
  if (argc != 5) { fprintf(stderr, "usage: %s WORKERS MIB_PER_ARRAY SECONDS read|copy|write|triad\n", argv[0]); return 2; }
  workers = strtoul(argv[1], 0, 10); size_t mib = strtoul(argv[2], 0, 10); seconds = atoi(argv[3]);
  snprintf(operation, sizeof(operation), "%s", argv[4]); n = mib * 1024UL * 1024UL / sizeof(double);
  if (!workers || workers > 16 || !n || seconds < 1) return 2;
  if (posix_memalign((void **)&a, 64, n*sizeof(double)) || posix_memalign((void **)&b, 64, n*sizeof(double)) || posix_memalign((void **)&c, 64, n*sizeof(double))) return 3;
  for (size_t i=0; i<n; i++) { a[i] = (double)(i%101)*0.01; b[i] = (double)(i%37)*0.02; c[i] = 0; }
  pthread_barrier_init(&barrier, 0, (unsigned)workers + 1);
  pthread_t th[16]; for (size_t i=0; i<workers; i++) pthread_create(&th[i], 0, run, (void *)i);
  double begin = now(); pthread_barrier_wait(&barrier); uint64_t total=0;
  for (size_t i=0; i<workers; i++) { void *v; pthread_join(th[i], &v); total += (uintptr_t)v; }
  double elapsed = now()-begin, checksum = 0; for (size_t i=0; i<workers; i++) checksum += checksums[i];
  double per_pass = (double)n*sizeof(double);
  /* Each worker touches 1/workers of the arrays; sum of worker repetitions
     therefore needs division by workers to get full-array passes. */
  double bytes = per_pass * (double)total / (double)workers * (!strcmp(operation,"copy") ? 2.0 : !strcmp(operation,"triad") ? 3.0 : 1.0);
  printf("{\"workers\":%zu,\"mib_per_array\":%zu,\"seconds_requested\":%d,\"operation\":\"%s\",\"elapsed_s\":%.9f,\"aggregate_passes\":%llu,\"bytes_estimate\":%.0f,\"gb_s_decimal\":%.6f,\"checksum\":%.6f}\n", workers,mib,seconds,operation,elapsed,(unsigned long long)total,bytes,bytes/elapsed/1e9,checksum);
  return 0;
}
