#!/usr/bin/env python3
"""Copy the tagged accepted-SHA replay samples into this observation's raw/ folder."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
source=root.parent/'cpu-post-integration-profile'/'raw'
target=root/'raw'
files=sorted(source.glob('separation-w16-memory-observation-s*.json'))
if len(files)!=3: raise SystemExit(f'expected 3 replay samples, found {len(files)}')
for file in files: shutil.copy2(file,target/file.name)
print(f'copied {len(files)} replay samples into {target}')
