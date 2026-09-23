#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <time.h>
#include <sys/resource.h>
static double now(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec*1e-9;}
static volatile uint64_t sink;
static uint64_t calc(uint64_t x, uint64_t n){for(uint64_t i=0;i<n;i++){x^=x>>12;x^=x<<25;x^=x>>27;x*=2685821657736338717ULL;}return x;}
int main(int argc,char**argv){if(argc<3){fprintf(stderr,"usage: stress compute|stream seconds|fixed-count\n");return 2;} double duration=atof(argv[2]);double start=now();uint64_t count=0,x=123456789;struct rusage ru0,ru1;getrusage(RUSAGE_SELF,&ru0);
 if(!strcmp(argv[1],"compute")||!strcmp(argv[1],"fixed")){
  uint64_t limit=!strcmp(argv[1],"fixed")?strtoull(argv[2],0,10):UINT64_MAX;
  while(count<limit){uint64_t batch=1000000;if(limit-count<batch)batch=limit-count;x=calc(x,batch);count+=batch;if(!strcmp(argv[1],"compute")&&now()-start>=duration)break;}
 }else if(!strcmp(argv[1],"stream")){
  size_t n=(size_t)((argc>3?atof(argv[3]):64.0)*1024*1024)/sizeof(uint64_t);uint64_t*a=aligned_alloc(64,n*sizeof(uint64_t));uint64_t*b=aligned_alloc(64,n*sizeof(uint64_t));if(!a||!b)return 3;for(size_t i=0;i<n;i++){a[i]=i;b[i]=i+1;}
  start=now();while(now()-start<duration){for(size_t i=0;i<n;i+=8){b[i]=a[i]+b[i];x+=b[i];}count++;}
  free(a);free(b);
 }else if(!strcmp(argv[1],"idle")){struct timespec t={(time_t)duration,(long)((duration-(time_t)duration)*1e9)};nanosleep(&t,0);}else return 2;
 sink=x;getrusage(RUSAGE_SELF,&ru1);printf("{\"kind\":\"%s\",\"elapsed\":%.9f,\"count\":%llu,\"checksum\":%llu,\"minor_faults\":%ld}\n",argv[1],now()-start,(unsigned long long)count,(unsigned long long)x,ru1.ru_minflt-ru0.ru_minflt);return 0;}
