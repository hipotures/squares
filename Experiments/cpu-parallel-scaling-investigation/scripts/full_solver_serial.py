#!/usr/bin/env python3
import json
from fractions import Fraction
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[3] / 'packing'))
from devtools import bench_colgen
p=Path(__file__).resolve().parents[1]/'raw/full_solver_generic_serial.json'
case=bench_colgen.Case(n=12,outer_side=Fraction(99,25))
grids=bench_colgen.site_counts_for_side(case.outer_side,case.square_side,inset=case.inset)
report=bench_colgen.bench_rounds(case,grids)
p.write_text(json.dumps(report,indent=2)+'\n')
print({k:report['row_run'][k] for k in ('seconds','separation_seconds','lp_seconds','rounds','rows','objective','stopped')})
