"""Preload one real late-round direction and its exact pre-prefix difference grid."""
from fractions import Fraction
from pathlib import Path
import ctypes
import numpy as np

from devtools import bench_colgen
from sqpack.fractional import generate
from sqpack.fractional.generate import direction_net

ROOT=Path(__file__).resolve().parents[4]
DATA=ROOT/"Experiments/cpu-post-integration-profile/raw/current-states.npz"

def capture(round_index=18,direction_index=90):
    stored=np.load(DATA)
    weights,points,membership=(stored[x] for x in ("weights","points","membership"))
    case=bench_colgen.Case(n=12,outer_side=Fraction(99,25))
    direction=direction_net(case.half_tangents())[direction_index]
    site_weights=weights[round_index][membership]
    outer,side=float(case.outer_side),float(case.square_side)
    cells=generate.event_grid(points,site_weights,direction,outer,side,
                              build_reachable=False)
    cosine,sine=float(direction.ux),float(direction.uy)
    half=side/2
    u=points[:,0]*cosine+points[:,1]*sine
    v=-points[:,0]*sine+points[:,1]*cosine
    domain=generate._CentreDomain.at(direction,outer,side,None)
    live=site_weights>0
    if not live.any():
        live=np.zeros(points.shape[0],dtype=bool)
        live[::max(1,points.shape[0]//600)]=True
    lu,lv,lw=u[live],v[live],site_weights[live]
    ue=np.unique(np.concatenate([lu-half,lu+half,[domain.u_low,domain.u_high]]))
    ve=np.unique(np.concatenate([lv-half,lv+half,[domain.v_low,domain.v_high]]))
    assert np.array_equal(ue,cells.u_events) and np.array_equal(ve,cells.v_events)
    diff=np.zeros((ue.size,ve.size),dtype=np.float64)
    left=np.searchsorted(ue,lu-half)
    right=np.searchsorted(ue,lu+half)
    bottom=np.searchsorted(ve,lv-half)
    top=np.searchsorted(ve,lv+half)
    np.add.at(diff,(left,bottom),lw)
    np.add.at(diff,(right,bottom),-lw)
    np.add.at(diff,(left,top),-lw)
    np.add.at(diff,(right,top),lw)
    verify=diff.copy()
    np.add.accumulate(verify,axis=1,out=verify)
    generate.accumulate_axis0(verify)
    assert np.array_equal(verify[:-1,:-1],cells.mass)
    flat,*_=generate._reachable_values(cells)
    assert np.array_equal(generate._least_finite_indices(flat,13),
                          generate._least_finite_indices(flat,13))
    return {"points":points,"weights":site_weights,"direction":direction,
            "outer":outer,"side":side,"cells":cells,"diff":diff,"flat":flat}


class Operation:
    def __init__(self,kind,data,register_path):
        self.kind=kind
        self.data=data
        self.buffer=np.empty_like(data["diff"]) if kind=="prefix" else None
        self.stream_a=np.empty(8*1024*1024,dtype=np.float64) if kind=="stream" else None
        self.stream_b=np.empty_like(self.stream_a) if kind=="stream" else None
        if kind=="stream":
            self.stream_a.fill(1.0)
            self.stream_b.fill(2.0)
        if kind=="register":
            lib=ctypes.CDLL(str(register_path))
            self.spin=lib.register_spin
            self.spin.argtypes=[ctypes.c_uint64,ctypes.c_uint64]
            self.spin.restype=ctypes.c_uint64
        self.state=1
        self.calls=0

    def __call__(self):
        d=self.data
        if self.kind=="prefix":
            np.copyto(self.buffer,d["diff"])
            np.add.accumulate(self.buffer,axis=1,out=self.buffer)
            generate.accumulate_axis0(self.buffer)
            value=self.buffer[0,0]
        elif self.kind=="slab":
            value=generate._reachable_values(d["cells"])[0].size
        elif self.kind=="top13":
            value=generate._least_finite_indices(d["flat"],13)[0]
        elif self.kind=="direction":
            value=len(generate.placement_cells(d["points"],d["weights"],d["direction"],
                d["outer"],d["side"],keep=3))
        elif self.kind=="register":
            self.state=self.spin(1000000,self.state)
            value=self.state
        elif self.kind=="stream":
            np.add(self.stream_a,self.stream_b,out=self.stream_a)
            value=self.stream_a[0]
        elif self.kind=="sleep":
            import time
            time.sleep(.01)
            value=0
        else:raise ValueError(self.kind)
        self.calls+=1
        return value
