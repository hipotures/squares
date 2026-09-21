// Adapted from the pinned Guzhou R038 scanner. New: threshold capture rectangles.
'use strict';
const fs=require('fs'),crypto=require('crypto');
function arg(k,d=null){let i=process.argv.indexOf(k);return i>=0?process.argv[i+1]:d}
const path=arg('--certificate'); if(!path) throw Error('--certificate required / 必须提供 --certificate');
const start=Number(arg('--start','0')), stopArg=arg('--stop',null), ASTR=arg('--A','99974999999/100000000000'), measure=arg('--measure','base'); if(!['base','combined'].includes(measure)) throw Error('bad --measure / --measure 参数无效'); const raw=fs.readFileSync(path);
const sha=crypto.createHash('sha256').update(raw).digest('hex');
if(sha!==arg('--expected-sha','5ffb7746fb8aa8d436256710a035235436eecc5e6cfeca3d150dc01b18b801c3')) throw Error('certificate SHA mismatch / 证书 SHA 不匹配');
const c=JSON.parse(raw);const POSDEN=BigInt(c.coordinate_denominator||100000),LONG=4613n*POSDEN/1000n;if(POSDEN<=0n||4613n*POSDEN%1000n!==0n||LONG>=9007199254740992n)throw Error('invalid coordinate denominator');const stop=stopArg===null?c.entries.length:Number(stopArg); if(!(0<=start&&start<stop&&stop<=c.entries.length))throw Error('bad range / 行区间无效');
const abs=x=>x<0n?-x:x;function gcd(a,b){a=abs(a);b=abs(b);while(b){let t=a%b;a=b;b=t}return a||1n}const lcm=(a,b)=>a/gcd(a,b)*b;
class Fr{constructor(n,d=1n){if(typeof n==='string'){let p=n.split('/');n=BigInt(p[0]);d=p[1]?BigInt(p[1]):1n}if(d<0n){n=-n;d=-d}let g=gcd(n,d);this.n=n/g;this.d=d/g}add(o){o=F(o);return new Fr(this.n*o.d+o.n*this.d,this.d*o.d)}sub(o){o=F(o);return new Fr(this.n*o.d-o.n*this.d,this.d*o.d)}mul(o){o=F(o);return new Fr(this.n*o.n,this.d*o.d)}div(o){o=F(o);return new Fr(this.n*o.d,this.d*o.n)}cmp(o){o=F(o);let z=this.n*o.d-o.n*this.d;return z<0n?-1:z>0n?1:0}}const F=x=>x instanceof Fr?x:new Fr(x),ONE=F('1'),TWO=F('2'),A=F(ASTR);
function trig(u){u=F(u);let u2=u.mul(u),d=ONE.add(u2);return[ONE.sub(u2).div(d),TWO.mul(u).div(d)]}
const jobs=c.entries.map(r=>{let[a,b,t,B]=r.map(F),wa=trig(a),wb=trig(b),fa=wa[0].add(wa[1]),fb=wb[0].add(wb[1]),m=fa.cmp(fb)<=0?fa:fb,rr=A.mul(m).div(TWO);return{p:t.n,q:t.d,bn:B.n,bd:B.d,rn:rr.n,rd:rr.d}});
const atoms=[];const seen=new Set();
for(const [x,y,w] of c.point_orbits){let imgs=new Set();for(const[u,v]of[[x,y],[y,x]])for(const X of[u,Number(LONG)-u])for(const Y of[v,Number(LONG)-v])imgs.add(X+','+Y);let oo=[...imgs].map(z=>z.split(',').map(Number)).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);for(const [X,Y] of oo){let k=X+','+Y;if(seen.has(k))throw Error('duplicate orbit');seen.add(k);atoms.push({x:BigInt(X),y:BigInt(Y),w});}}
const triggers=[];for(const o of c.threshold_orbits)for(const tri of o.triples)triggers.push({tri,w:o.weight});
const budget=atoms.reduce((s,a)=>s+a.w,0)+triggers.reduce((s,a)=>s+a.w,0);
if(budget!==c.budget_units||atoms.reduce((s,a)=>s+a.w,0)+5*triggers.reduce((s,a)=>s+a.w,0)>=2**50)throw Error('budget mismatch/overflow');
const lower=(v,n,d)=>{let a=0,b=v.length;while(a<b){let m=(a+b)>>1;if(v[m]*d<n)a=m+1;else b=m}return a},upper=(v,n,d)=>{let a=0,b=v.length;while(a<b){let m=(a+b)>>1;if(v[m]*d<=n)a=m+1;else b=m}return a};
class Seg{constructor(z){let n=1;while(n<z)n<<=1;this.n=n;this.mn=new Float64Array(2*n);this.lazy=new Float64Array(2*n)}add(L,R,V,k=1,a=0,b=this.n){if(L>=b||R<=a)return;if(L<=a&&b<=R){this.mn[k]+=V;this.lazy[k]+=V;return}let m=(a+b)>>1;this.add(L,R,V,k*2,a,m);this.add(L,R,V,k*2+1,m,b);this.mn[k]=Math.min(this.mn[k*2],this.mn[k*2+1])+this.lazy[k]}get(L,R,k=1,a=0,b=this.n){if(L>=b||R<=a)return Number.MAX_SAFE_INTEGER;if(L<=a&&b<=R)return this.mn[k];let m=(a+b)>>1;return Math.min(this.get(L,R,k*2,a,m),this.get(L,R,k*2+1,m,b))+this.lazy[k]}}
function rowmin(J){
let{p,q,bn,bd,rn,rd}=J,G=lcm(lcm((2n*POSDEN),2n*bd),rd),li=LONG*(G/(2n*POSDEN)),bi=bn*(G/(2n*bd)),rg=rn*(G/rd),C=q*q-p*p,S=2n*p*q,R=q*q+p*p,H=(li-rg)*R,edge=H*(C+S),vertex=H*(C-S),K=R*R*H,half=bi*R*R,vs=[-edge-1n,edge+1n],ev=[],U=[],V=[],scale=G/(2n*POSDEN);
for(let i=0;i<atoms.length;i++){let a=atoms[i],x=(2n*a.x-LONG)*scale,y=(2n*a.y-LONG)*scale;U[i]=R*(C*x+S*y);V[i]=R*(-S*x+C*y);}
const boxes=[];
function put(indices,w){if(!w)return;let loU=U[indices[0]],hiU=loU,loV=V[indices[0]],hiV=loV;for(let i of indices){if(U[i]>loU)loU=U[i];if(U[i]<hiU)hiU=U[i];if(V[i]>loV)loV=V[i];if(V[i]<hiV)hiV=V[i];}loU-=half;hiU+=half;loV-=half;hiV+=half;if(loU>=hiU||loV>=hiV)return;let i=boxes.length;boxes.push({loV,hiV,w});vs.push(loV,hiV);ev.push([loU,i,1],[hiU,i,-1]);}
for(let i=0;i<atoms.length;i++)put([i],atoms[i].w);
for(let z of triggers){let[a,b,d]=z.tri;put([a,b],z.w);put([a,d],z.w);put([b,d],z.w);put([a,b,d],-2*z.w);}
vs.sort((a,b)=>a<b?-1:a>b?1:0);let vv=[];for(let x of vs)if(!vv.length||x!==vv[vv.length-1])vv.push(x);
ev.push([-edge,-1,0],[edge,-1,0]);ev.sort((a,b)=>a[0]<b[0]?-1:a[0]>b[0]?1:0);
let lo=new Int32Array(boxes.length),hi=new Int32Array(boxes.length);for(let i=0;i<boxes.length;i++){lo[i]=lower(vv,boxes[i].loV,1n);hi[i]=lower(vv,boxes[i].hiV,1n)}
let seg=new Seg(vv.length-1),best=Number.MAX_SAFE_INTEGER,slabs=0,j=0;
while(j<ev.length){let e=j+1;while(e<ev.length&&ev[e][0]===ev[j][0])e++;for(let z=j;z<e;z++){let[,i,s]=ev[z];if(i>=0)seg.add(lo[i],hi[i],s*boxes[i].w)}if(e===ev.length)break;let L=ev[j][0]>-edge?ev[j][0]:-edge,RR=ev[e][0]<edge?ev[e][0]:edge;j=e;if(L>=RR)continue;let an,ad,bn2,bd2;if(S===0n){an=-H*R;ad=1n;bn2=H*R;bd2=1n}else{let ua=L>vertex?(L<RR?L:RR):(vertex<RR?vertex:RR),nv=-vertex,ub=L>nv?(L<RR?L:RR):(nv<RR?nv:RR),a1=C*ua-K,d1=S,a2=-K-S*ua,d2=C;if(a1*d2<a2*d1){an=a2;ad=d2}else{an=a1;ad=d1}let b1=C*ub+K,e1=S,b2=K-S*ub,e2=C;if(b1*e2<b2*e1){bn2=b1;bd2=e1}else{bn2=b2;bd2=e2}}if(an*bd2>=bn2*ad)throw Error('degenerate slab');let l=upper(vv,an,ad)-1,r=lower(vv,bn2,bd2);if(!(l>=0&&r<=vv.length-1&&l<r))throw Error('invalid query range');let z=seg.get(l,r);if(z<best)best=z;slabs++;}
return{minimum_units:best,slabs};}
let hist={},global=Number.MAX_SAFE_INTEGER,slabs=0,bad=[];for(let i=start;i<stop;i++){let r=rowmin(jobs[i]);global=Math.min(global,r.minimum_units);hist[r.minimum_units]=(hist[r.minimum_units]||0)+1;slabs+=r.slabs;if(r.minimum_units<c.minimum_units)bad.push([i,r.minimum_units])}
const result={status:bad.length?'REFUSED':'PASS_EXACT_MOVABLE_SUPPORT_SCAN',certificate_sha256:sha,parent_side:ASTR,measure,range:[start,stop],atoms:atoms.length,thresholds:triggers.length,budget_units:budget,minimum_units:global,histogram:hist,center_slabs:slabs,escape_rows:bad};console.log(JSON.stringify(result,null,2));if(bad.length)process.exit(1);
