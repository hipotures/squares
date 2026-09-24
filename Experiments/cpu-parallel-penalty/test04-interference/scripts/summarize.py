"""Rank pinned-target interference with idle controls and retain all cells."""
import json
import statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RAW=ROOT/"raw"
TARGETS=("prefix","slab","top13","direction","register")
BACKGROUNDS=("sleep","register","stream","prefix","slab","top13")

def metric(xs):
    return {"values":xs,"min":min(xs),"median":statistics.median(xs),
            "max":max(xs),"cv":statistics.pstdev(xs)/statistics.mean(xs)}

screen=[];repeat=[]
idle_repeat={}
for target in TARGETS:
    idle=json.loads((RAW/f'{target}-sleep-n0-screen-s1.json').read_text())
    baseline_files=[RAW/f'{target}-sleep-n0-repeat-s{i}.json' for i in (1,2,3)]
    if all(x.exists() for x in baseline_files):
        baseline=[json.loads(x.read_text()) for x in baseline_files]
        idle_repeat[target]={"wall_per_call":metric([x['wall_per_call'] for x in baseline]),
                             "ipc":metric([x['ipc'] for x in baseline])}
    for background in BACKGROUNDS:
        for count in (4,8,14):
            path=RAW/f'{target}-{background}-n{count}-screen-s1.json'
            d=json.loads(path.read_text())
            row={"target":target,"background":background,"bg_count":count,
                 "idle_wall_per_call":idle['wall_per_call'],
                 "wall_per_call":d['wall_per_call'],"cpu_per_call":d['cpu_per_call'],
                 "ipc":d['ipc'],"ipc_idle":idle['ipc'],
                 "wall_inflation":d['wall_per_call']/idle['wall_per_call'],
                 "instructions_per_call":d['counters']['instructions']['count']/d['calls'],
                 "cycles_per_call":d['counters']['cycles']['count']/d['calls'],
                 "dram_fills_per_call":d['counters']['ls_any_fills_from_sys.all_dram_io']['count']/d['calls']}
            screen.append(row)
            files=[RAW/f'{target}-{background}-n{count}-repeat-s{i}.json' for i in (1,2,3)]
            if all(x.exists() for x in files):
                vals=[json.loads(x.read_text()) for x in files]
                repeat.append({"target":target,"background":background,"bg_count":count,
                    "wall_per_call":metric([x['wall_per_call'] for x in vals]),
                    "cpu_per_call":metric([x['cpu_per_call'] for x in vals]),
                    "ipc":metric([x['ipc'] for x in vals]),
                    "dram_fills_per_call":metric([x['counters']['ls_any_fills_from_sys.all_dram_io']['count']/x['calls'] for x in vals]),
                    "wall_inflation_median":statistics.median(x['wall_per_call'] for x in vals)/
                        (idle_repeat[target]['wall_per_call']['median'] if target in idle_repeat
                         else idle['wall_per_call'])})
result={"screen":screen,"repeated":repeat,"screen_cells":len(screen),
        "repeated_cells":len(repeat),"idle_repeated":idle_repeat,"idle_controls":{
            t:json.loads((RAW/f'{t}-sleep-n0-screen-s1.json').read_text()) for t in TARGETS}}
(ROOT/"processed").mkdir(exist_ok=True)
(ROOT/"processed/matrix.json").write_text(json.dumps(result,indent=2)+'\n')
for row in sorted(screen,key=lambda x:x['wall_inflation'],reverse=True)[:25]:
    print(row['target'],row['background'],row['bg_count'],round(row['wall_inflation'],2))
