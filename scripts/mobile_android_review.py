"""Query public OSV for resolved Android runtime Maven coordinates, not guesses.

The pinned Flutter engine artifacts are SDK provenance, not Maven advisories.
Build tools/OS and release acceptance remain separately reviewed gates.
"""
import json
import os
from pathlib import Path
import re
import subprocess
import urllib.request
root=Path(__file__).resolve().parent.parent/'apps/mobile/android'
text=subprocess.check_output(['./gradlew',':app:dependencies','--configuration','debugRuntimeClasspath','--console=plain'],cwd=root,text=True)
coordinates=set()
for name,version,selected in re.findall(r'([A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+):([^\s:]+)(?: -> ([^\s]+))?',text):
    version=selected or version
    if name.startswith('io.flutter:') or not re.fullmatch(r'[0-9][A-Za-z0-9_.+-]*',version):continue
    coordinates.add((name,version))
assert coordinates,'No resolved Android Maven coordinates captured'
coordinates=sorted(coordinates)
request=urllib.request.Request('https://api.osv.dev/v1/querybatch',data=json.dumps({'queries':[{'package':{'ecosystem':'Maven','name':name},'version':version} for name,version in coordinates]}).encode(),headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request,timeout=90) as response:results=json.load(response)['results']
except Exception as error:
    print(f'::error title=Android advisory check unavailable::{type(error).__name__}; no zero-advisory claim')
    raise SystemExit(1) from None
assert len(results)==len(coordinates)
findings=[(name,version,[v['id'] for v in r.get('vulns',[])]) for (name,version),r in zip(coordinates,results) if r.get('vulns')]
print(f'::notice title=Android Maven advisory review::{len(coordinates)} resolved runtime Maven versions queried; {len(findings)} coordinates with OSV findings')
for name,version,ids in findings:print(f'::error title=Android advisory::{name} {version}: {", ".join(ids)}')
(Path(os.environ['RUNNER_TEMP'])/'pwc-android-dependencies.json').write_text(json.dumps({'coordinates':coordinates,'findings':findings},indent=2)+'\n')
if findings:raise SystemExit(1)
