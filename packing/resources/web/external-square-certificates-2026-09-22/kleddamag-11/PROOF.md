# Verified global lower bound for eleven unit squares

**s(11) > 31/8 = 3.875.**

Arbitrary independent rotations are allowed; square interiors must be disjoint and boundaries may touch. The exact minimum remains unresolved. No better packing or literature-priority claim is made.

The fixed certificate is `global-certificate.json`, SHA-256 `57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458`. Its container side is L=191/50 and parent side A=764/775. Site coordinates have denominator 10^10 and charge weights denominator 10^9. There are 679 site orbits, expanding to 5284 distinct sites; ordinary point weights are positive on 66 orbits (496 physical sites).

| Charge family | Positive orbits | Physical features | Budget |
|---|---:|---:|---:|
| Ordinary points | 66 | 496 | 2.247714156 |
| 2-of-3 | 132 | 1020 | 3.188007592 |
| 2-of-5 | 10 | 76 | 0.989672288 |
| 3-of-5 | 142 | 1124 | 4.574085908 |

| Exact verification quantity | Value |
|---|---:|
| Total budget M | 10.999479944 |
| Certified minimum core charge Γ | 0.999962528 |
| 11Γ | 10.999587808 |
| 11Γ−M | 0.000107864 |
| Complete angle intervals | 12028 |
| Minimum strict core margin | 1/1000000000000 |

Both full exact scans pass and their interval-minimum histograms agree. The Python scan uses 86,299,918 relevant slabs and certifies 511,649,694,680 open cells through range queries; the cells are not individually enumerated. The JavaScript scan uses 86,275,862 slabs. Independent controls check all 48112 rational quadratic containment inequalities and 5586 selected exact boundary/event centres.

The charge need not be normalized to 1: the exact positive inequality 11Γ>M above is the requirement. The following argument, instantiated by the complete checks of this fixed data, proves the stated strict bound.

Let L and A be positive rational numbers. A parent is any side-A square contained in [0,L]^2. Parents may rotate independently and touch at their boundaries; their interiors must be disjoint.

## Charges and their budgets

An ordinary weighted site contributes w≥0 to a closed core containing it, with budget w across pairwise disjoint closed cores.

For m distinct sites and an integer threshold k with 1≤k≤m, define a charge w≥0 when a core contains at least k of those sites. Its budget across pairwise disjoint closed cores is floor(m/k)w. Indeed, if q cores qualify, their disjoint captured subsets contain at least qk different sites, so qk≤m. Features may share sites with other features: each valid budget inequality can still be added.

Thus two-of-three has budget w; two-of-five has budget 2w; three-of-five has budget w. The actual certificate determines which features are used. All weights, sites, cardinalities, budgets and complete D4 orbits are checked exactly.

Write C(Q) for the total logical charge and M for the sum of feature budgets. Any eleven disjoint closed cores obey sum_i C(Q_i)≤M.

## Transport from every parent to a strict core

Use rational half-angle coordinates c(t)=(1−t²)/(1+t²), s(t)=2t/(1+t²). A row (a,b,t,B) assigns a concentric side-B closed core at angle 2 arctan(t) to every parent with half-angle u∈[a,b]. Catalogue intervals meet exactly from zero to beyond sqrt(2)−1. D4 invariance folds each parent's orientation separately into [0,π/4], without imposing symmetry on a packing.

The checker evaluates at u=a,b the relative width

c(t)c(u)+s(t)s(u)+|c(t)s(u)−s(t)c(u)|.

It verifies that relative angles lie in [−π/4,π/4] and that A exceeds B times the maximum endpoint width strictly. The maximum over the interval occurs at an endpoint, since cos δ+|sin δ| increases with |δ| on that range. Thus every assigned closed core lies strictly inside its parent.

For a parent orientation u the legal centre domain is [A(c(u)+s(u))/2,L−A(c(u)+s(u))/2]^2. Since c(u)+s(u) has no interior minimum on the covered range, the union of these domains is [r,L−r]^2 with r=A min(c(a)+s(a),c(b)+s(b))/2. The full union is scanned for the row's fixed core. A separate exact audit verifies universal strict containment through four rational quadratic inequalities per interval, including their interior critical points; it also checks the centre envelope.

## Exact finite sweep for general thresholds

In axes parallel to a core's edges, each site's capture set is a closed rectangle of centre positions. With Boolean capture indicators x_1,…,x_m,

1_{sum x_i≥k} = sum_{j=k}^m (−1)^(j−k) binom(j−1,k−1) sum_{|S|=j} product_{i∈S} x_i.

To prove the identity, let h be the number of captured sites and call the right side S(h). It vanishes for h<k. Pascal's identity gives

S(h)−S(h−1) = binom(h−1,k−1) sum_{i=0}^{h−k}(−1)^i binom(h−k,i),

which is 1 at h=k and 0 for h>k. Therefore S(h)=1 for all h≥k.

In particular, two-of-five is the sum of its 10 pair intersections, minus twice its 10 triple intersections, plus three times its 5 quadruple intersections, minus four times its quintuple intersection. Its absolute coefficient sum is 49. Two-of-three has absolute coefficient sum 5.

An intersection of capture rectangles is another rectangle, possibly empty or degenerate. The logical charge is consequently an exact signed rectangle sum at generic centres. Rectangle edges partition the rotated centre domain into open cells on which the charge is constant.

The Python scanner uses rational polygon-edge extrema to identify all reachable vertical-slab cells and integer range-minimum queries to bound their charges. Geometry is compared after clearing denominators with arbitrary-precision integers. The separate JavaScript scanner uses clamped-extrema formulae and BigInt geometry. The sum of absolute expanded weights, including all ordinary point weights, is checked below 2^50. Thus Python signed 64-bit accumulation and JavaScript integer-valued Number accumulation are exact. No floating geometric tolerance enters the proof check.

The independently implemented logical controls directly evaluate membership and threshold predicates at selected exact event and domain-boundary centres. Exhaustive finite controls check the charge identity on every Boolean capture pattern for supported feature sizes, and the budget on all disjoint-site assignments. These tests support the implementations; the universal algebraic and pigeonhole arguments above supply their mathematical justification.

## Boundaries

The signed expansion is not used as a positivity argument. The original charge is a nonnegative sum of indicators of closed sets: a threshold capture set is the finite union of intersections of k site-capture rectangles. It is therefore upper semicontinuous.

Every point of the closed centre domain is a limit of generic interior points. A lower bound Γ on every generic charge extends to the boundary by upper semicontinuity. Omitting zero-area rectangles from the generic sweep cannot hide a lower charge at an event line, a tangency or a domain boundary.

## Conclusion

If the complete exact scans establish C(Q)≥Γ for every assigned core and 11Γ>M, eleven side-A parents cannot fit in side L. Their strict interior closed cores would be pairwise disjoint even if parent boundaries touch, and would have total charge both at least 11Γ and at most M.

Scaling excludes eleven unit squares at container side L/A. The minimum is attained: a trivial grid packing supplies an upper bound 4, and side lengths, centres and orientations below it lie in a compact parameter space. Containment and non-overlap of interiors are closed conditions; an interior intersection at a limit would persist under small perturbations. Exclusion at L/A therefore yields the strict global lower bound s(11)>L/A.

This is a computer-assisted proof, not a proof-assistant formalization. Numerical search, pricing, shrunken-core discovery and adaptive catalogue construction supply proposals only. The present theorem is supported by the pinned final certificate, two complete exact scans, independent premise controls and the exact values above. No exact optimum, improved packing, external review or literature priority is claimed.
