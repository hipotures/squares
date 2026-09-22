"""Check byte identity of all files in the release inventory."""

if not __debug__:
    raise SystemExit("Verification requires Python assertions; remove -O/-OO and unset PYTHONOPTIMIZE.")
from pathlib import Path
import json,hashlib
R=Path(__file__).resolve().parent
m=json.loads((R/'MANIFEST.json').read_text())
for item in m['files']:
 p=R/item['path'];b=p.read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
print('PASS',len(m['files']),'pinned files')
