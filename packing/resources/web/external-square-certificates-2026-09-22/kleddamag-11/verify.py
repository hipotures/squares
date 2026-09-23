
if not __debug__:
    raise SystemExit("Verification requires Python assertions; remove -O/-OO and unset PYTHONOPTIMIZE.")
from pathlib import Path
from fractions import Fraction as F
import argparse,json,hashlib,subprocess,sys,os
R=Path(__file__).resolve().parent
EXPECTED={'bound': '31/8', 'certificate_sha256': '57e9927da5c13f42dd8bcbf8f08c84363635fece626657ee63a810c61cd44458', 'intervals': 12028, 'minimum_units': 999962528, 'budget_units': 10999479944, 'surplus_units': 107864}

def main():
 p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);a=p.parse_args();out=a.output_dir.resolve();out.mkdir(parents=True,exist_ok=False);cert=R/'global-certificate.json';raw=cert.read_bytes();c=json.loads(raw);assert hashlib.sha256(raw).hexdigest()==EXPECTED['certificate_sha256'];assert F(c['L'])/F(c['A'])==F(EXPECTED['bound']);env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 commands=[['replay_parallel.py',str(cert),'--output',str(out/'python.json'),'--jobs','3'],['replay_secondary_parallel.py',str(cert),'--output-dir',str(out/'secondary'),'--jobs','3'],['independent_controls.py',str(cert),'--output',str(out/'controls.json')]]
 for i,cmd in enumerate(commands):
  with (out/f'check-{i+1}.log').open('w') as f:subprocess.run([sys.executable,str(R/cmd[0]),*cmd[1:]],stdout=f,stderr=subprocess.STDOUT,env=env,check=True)
 py=json.loads((out/'python.json').read_text());js=json.loads((out/'secondary/RESULT.json').read_text());co=json.loads((out/'controls.json').read_text());assert py['status']=='PASS_FULL_EXACT_PYTHON_REPLAY' and js['status']=='PASS_FULL_EXACT_BIGINT_REPLAY' and co['status']=='PASS_INDEPENDENT_EXACT_CONTROLS';assert all(x['certificate_sha256']==EXPECTED['certificate_sha256'] for x in [py,js,co]);assert py['histogram']==js['histogram'] and sum(py['histogram'].values())==EXPECTED['intervals'];assert py['minimum_units']==js['minimum_units']==EXPECTED['minimum_units'] and py['budget_units']==js['budget_units']==EXPECTED['budget_units'];assert py['counting_surplus_units']==EXPECTED['surplus_units']>0 and co['containment']['intervals']==EXPECTED['intervals'] and not js['escape_rows'];result={'status':'PASS_FRESH_PORTABLE_FULL_VERIFICATION',**EXPECTED};(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
