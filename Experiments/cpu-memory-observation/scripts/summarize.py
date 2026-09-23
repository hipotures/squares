#!/usr/bin/env python3
import json, pathlib, statistics
root=pathlib.Path(__file__).resolve().parents[1]
rows=[json.loads(x) for x in (root/'raw/stream-samples.jsonl').read_text().splitlines() if x]
summary={}
for op in ('read','copy','write','triad'):
    summary[op]={}
    for w in (1,2,4,8,16):
        q=[x for x in rows if x['operation']==op and x['workers']==w]
        vals=[x['gb_s_decimal'] for x in q]
        summary[op][str(w)]={'samples':len(q),'median_gb_s':statistics.median(vals),'min_gb_s':min(vals),'max_gb_s':max(vals),'durations_s':[x['elapsed_s'] for x in q]}
(root/'raw/stream-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
