#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
static uint64_t state=20260923;
static uint64_t next_rand(void){state^=state>>12;state^=state<<25;state^=state>>27;return state*2685821657736338717ULL;}
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static volatile uint64_t sink;
int main(int argc,char**argv){if(argc<3||argc>4)return 2;double mib=atof(argv[1]);uint64_t steps=strtoull(argv[2],0,10);size_t stride=argc==4?strtoull(argv[3],0,10):64;if(stride<64||stride%64)return 5;size_t n=(size_t)(mib*1024*1024/stride);if(n<2)return 3;uint64_t *lines=aligned_alloc(64,n*stride);uint32_t *perm=malloc(n*sizeof(uint32_t));if(!lines||!perm)return 4;for(size_t i=0;i<n;i++)perm[i]=i;for(size_t i=n-1;i>0;i--){size_t j=next_rand()%(i+1);uint32_t t=perm[i];perm[i]=perm[j];perm[j]=t;}for(size_t i=0;i<n;i++)lines[(size_t)perm[i]*(stride/8)]=perm[(i+1)%n];uint64_t cur=perm[0];free(perm);for(size_t i=0;i<n*2;i++)cur=lines[cur*(stride/8)];double start=now();for(uint64_t i=0;i<steps;i++)cur=lines[cur*(stride/8)];double elapsed=now()-start;sink=cur;printf("{\"mib\":%.2f,\"nodes\":%zu,\"stride\":%zu,\"steps\":%llu,\"elapsed_s\":%.9f,\"ns_per_access\":%.4f,\"checksum\":%llu}\n",mib,n,stride,(unsigned long long)steps,elapsed,elapsed*1e9/steps,(unsigned long long)cur);free(lines);}
