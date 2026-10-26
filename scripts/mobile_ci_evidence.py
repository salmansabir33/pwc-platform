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
cache=Path(os.environ['RUNNER_TEMP'])/'pwc-source-evidence.b64'
if not cache.exists():
    stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        for p in sorted(set(files)):
            archive.add(p,arcname=p.relative_to(root).as_posix())
    cache.write_text(base64.b64encode(stream.getvalue()).decode())
encoded=cache.read_text()
chunks=[encoded[i:i+3900] for i in range(0,len(encoded),3900)]
assert len(chunks)<=40, 'Source evidence exceeds bounded bootstrap budget'
group=int(os.environ.get('EVIDENCE_GROUP','0'))
for i, chunk in enumerate(chunks):
    if i//8==group:
        print(f'::notice title=PWC source bootstrap {i+1}/{len(chunks)}::{chunk}')
