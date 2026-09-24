"""Bitwise row-strip prefix check on real retained round/direction grids."""
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path[:0]=[str(ROOT/"packing"),str(ROOT/"Experiments/cpu-parallel-penalty/test04-interference/scripts")]
from workload import capture
from bench_tile import prefix

def main():
    checks=0;cells=0;shapes=[]
    for round_index in (0,1,10,18,22):
        for direction_index in range(181):
            diff=capture(round_index,direction_index)["diff"]
            reference=diff.copy();prefix(reference,0)
            for block_rows in (32,64,128,256):
                candidate=diff.copy();prefix(candidate,block_rows)
                assert np.array_equal(candidate,reference),(round_index,direction_index,block_rows)
                checks+=1;cells+=candidate.size
            shapes.append(diff.shape)
    result={"rounds":[0,1,10,18,22],"directions_per_round":181,
            "grids":len(shapes),"variants_per_grid":4,"bitwise_checks":checks,
            "cells_compared":cells,"shape_min":list(min(shapes)),
            "shape_max":list(max(shapes)),"passed":True}
    raw=HERE.parent/"raw";raw.mkdir(parents=True,exist_ok=True)
    (raw/"tile-bitwise.json").write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':main()
