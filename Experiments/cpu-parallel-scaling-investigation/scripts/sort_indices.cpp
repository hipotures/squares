#include <algorithm>
#include <chrono>
#include <cstdio>
#include <numeric>
#include <vector>
using clock_type=std::chrono::steady_clock;
int main(int argc,char**argv){if(argc!=2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);size_t n=ftell(f)/8;rewind(f);std::vector<double>v(n);if(fread(v.data(),8,n,f)!=n)return 4;fclose(f);std::vector<size_t>i(n);std::iota(i.begin(),i.end(),0);auto t=clock_type::now();std::sort(i.begin(),i.end(),[&](size_t a,size_t b){return v[a]<v[b];});auto s=std::chrono::duration<double>(clock_type::now()-t).count();printf("{\"n\":%zu,\"seconds\":%.9f,\"first_index\":%zu,\"first_value\":%.17g}\n",n,s,i[0],v[i[0]]);}
