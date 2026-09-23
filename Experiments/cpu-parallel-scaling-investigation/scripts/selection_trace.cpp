#include <vector>
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <utility>
using I=long long;
int main(int argc,char**argv){if(argc<2)return 2;FILE*f=fopen(argv[1],"rb");if(!f)return 3;fseek(f,0,SEEK_END);I n=ftell(f)/8;rewind(f);std::vector<double>v(n);fread(v.data(),8,n,f);fclose(f);std::vector<I>ind(n);for(I i=0;i<n;i++)ind[i]=i;auto val=[&](I i){return v[ind[i]];};I low=0,high=n-1,kth=12;int depth=40;I comparisons=0,swaps=0;int iter=0;
 while(low+1<high){I ll=low+1,hh=high;if(depth<=0){printf("FALLBACK low=%lld high=%lld remaining=%lld\n",low,high,high-low+1);break;}I mid=low+(high-low)/2;
 if(val(high)<val(mid))std::swap(ind[high],ind[mid]);if(val(high)<val(low))std::swap(ind[high],ind[low]);if(val(low)<val(mid))std::swap(ind[low],ind[mid]);std::swap(ind[mid],ind[low+1]);double pivot=val(low);I scans=0;
 for(;;){do{ll++;scans++;}while(val(ll)<pivot);do{hh--;scans++;}while(pivot<val(hh));if(hh<ll)break;std::swap(ind[ll],ind[hh]);swaps++;}
 std::swap(ind[low],ind[hh]);I oldlow=low,oldhigh=high;if(hh>=kth)high=hh-1;if(hh<=kth)low=ll;
 printf("iter=%d low=%lld high=%lld pivot=%g hh=%lld new_low=%lld new_high=%lld scans=%lld swaps=%lld\n",iter++,oldlow,oldhigh,pivot,hh,low,high,scans,swaps);
 depth--;if(iter>150)break;
 }
 printf("final low=%lld high=%lld iterations=%d swaps=%lld kth=%lld\n",low,high,iter,swaps,kth);
}
