"""Review real resolved hosted packages in CI; no local credentials or cache upload.

OSV public-version advisory query is supplemental, not a native-security signoff.
Failures are explicit. All findings require review; none silently suppressed.
"""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

root=Path(__file__).resolve().parent.parent/'apps/mobile'
data=json.loads(subprocess.check_output(['dart','pub','deps','--json'],cwd=root,text=True))
packages=[p for p in data['packages'] if p['source']=='hosted']
queries=[{'package':{'name':p['name'],'ecosystem':'Pub'},'version':p['version']} for p in packages]
request=urllib.request.Request('https://api.osv.dev/v1/querybatch',data=json.dumps({'queries':queries}).encode(),headers={'Content-Type':'application/json'})
try:
    with urllib.request.urlopen(request,timeout=90) as response:
        results=json.load(response)['results']
except Exception as error:
    print(f'::error title=Dependency advisory check unavailable::{type(error).__name__}; no zero-advisory claim')
    raise SystemExit(1) from None
assert len(results)==len(packages)
findings=[(p['name'],p['version'],[v['id'] for v in result.get('vulns',[])]) for p,result in zip(packages,results) if result.get('vulns')]
print(f'::notice title=Resolved package advisory review::{len(packages)} hosted package versions queried; {len(findings)} packages with OSV findings')
for name,version,ids in findings:
    print(f'::error title=Dependency advisory::{name} {version}: {", ".join(ids)}')
cache=Path(os.environ.get('PUB_CACHE',str(Path.home()/'.pub-cache')))/'hosted/pub.dev'
licenses=[]
for p in packages:
    directory=cache/f"{p['name']}-{p['version']}"
    candidates=list(directory.glob('LICENSE*'))+list(directory.glob('COPYING*'))
    if not candidates:
        print(f"::error title=Missing license evidence::{p['name']} {p['version']}")
        raise SystemExit(1)
    text='\n'.join(f.read_text(errors='replace') for f in candidates).lower()
    license_name='MIT' if 'permission is hereby granted, free of charge' in text else 'Apache-2.0' if 'apache license' in text else 'BSD-family' if 'redistribution and use in source and binary forms' in text else 'REVIEW_REQUIRED'
    licenses.append({'name':p['name'],'version':p['version'],'license':license_name})
report={'advisories':findings,'packages':licenses,'scope':'Resolved Dart hosted packages, not Flutter SDK engine/native OS or native Gradle/CocoaPods transitive advisories'}
output=Path(os.environ['RUNNER_TEMP'])/'pwc-mobile-dependency-review.json';output.write_text(json.dumps(report,indent=2)+'\n')
print(f'::notice title=Resolved license evidence::{len(licenses)} package license files inspected; '+', '.join(sorted({p['license'] for p in licenses})))
if findings or any(p['license']=='REVIEW_REQUIRED' for p in licenses):raise SystemExit(1)
