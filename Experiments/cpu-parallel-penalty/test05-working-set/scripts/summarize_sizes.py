"""Compare per-call worker CPU across the active-footprint screen."""
import json
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
RAW=HERE.parent/'raw'
SIZES=(256*1024,1*1024**2,2*1024**2,4*1024**2,8*1024**2,
       12*1024**2,16*1024**2,24*1024**2,32*1024**2)
out={}
for kind in ('prefix','top13'):
    records=[]
    for bytes_ in SIZES:
        cases={}
        for workers in (1,4,8,16):
            path=RAW/f'{kind}-{bytes_}-w{workers}-screen-s1.json'
            value=json.loads(path.read_text())
            cases[str(workers)]={"median_cpu_per_call":value['median_cpu_per_call'],
                                 "sample_wall":value['wall'],
                                 "actual_bytes":value['actual_bytes'],
                                 "checksum":value['records'][0]['checksum']}
        one=cases['1']['median_cpu_per_call']
        for v in cases.values():v['cpu_inflation_vs_one']=v['median_cpu_per_call']/one
        records.append({"requested_bytes":bytes_,"cases":cases})
    out[kind]=records
(HERE.parent/'processed').mkdir(exist_ok=True)
(HERE.parent/'processed/size-screen.json').write_text(json.dumps(out,indent=2)+'\n')
for kind,records in out.items():
    for row in records:
        print(kind,row['requested_bytes'],round(row['cases']['16']['cpu_inflation_vs_one'],3))
