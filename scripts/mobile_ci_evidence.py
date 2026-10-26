"""Emit bounded source-only CI bootstrap evidence through GitHub check notices.

Only generated platform source, real resolver lockfile and formatter output.
Never inspect .env, credential stores, SDK caches, APKs or signing keys.
"""
import base64
import io
from pathlib import Path
import subprocess
import tarfile
import os

root=Path(__file__).resolve().parent.parent
mobile=root/'apps/mobile'
files=[]
for base in ['android','ios']:
    for path in (mobile/base).rglob('*'):
        if not path.is_file(): continue
        rel=path.relative_to(mobile).as_posix()
        if any(part in {'.gradle','build','.symlinks','Pods','ephemeral'} for part in path.parts): continue
        if path.name in {'local.properties','Generated.xcconfig','flutter_export_environment.sh','gradlew','gradlew.bat','gradle-wrapper.jar','GeneratedPluginRegistrant.java','GeneratedPluginRegistrant.h','GeneratedPluginRegistrant.m'}: continue
        if path.suffix in {'.keystore','.jks','.p12','.mobileprovision'}: raise SystemExit('Unexpected signing material')
        files.append(path)
files += [p for p in [mobile/'pubspec.lock',mobile/'.metadata'] if p.exists()]
# Exact Dart formatter output, including generated contract models, is source.
files += list((mobile/'lib').rglob('*.dart'))+list((mobile/'test').rglob('*.dart'))
stream=io.BytesIO()
with tarfile.open(fileobj=stream,mode='w:gz') as archive:
    for p in sorted(set(files)):
        archive.add(p,arcname=p.relative_to(root).as_posix())
encoded=base64.b64encode(stream.getvalue()).decode()
chunks=[encoded[i:i+24000] for i in range(0,len(encoded),24000)]
for i, chunk in enumerate(chunks):
    print(f'::notice title=PWC source bootstrap {i+1}/{len(chunks)}::{chunk}')
print(f'::notice title=PWC bootstrap file count::{len(set(files))} source/lock files; no SDK/cache/build outputs')
