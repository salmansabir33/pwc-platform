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
# Inspect selected components, not textual constraints or evicted graph versions.
init=Path(os.environ['RUNNER_TEMP'])/'pwc-resolved-runtime.gradle'
init.write_text(r'''gradle.projectsEvaluated {
    def application = gradle.rootProject.findProject(':app')
    application.tasks.register('pwcResolvedRuntime') {
        doLast {
            application.configurations.getByName('debugRuntimeClasspath').incoming.resolutionResult.allComponents.each { component ->
                def id = component.id
                if (id instanceof org.gradle.api.artifacts.component.ModuleComponentIdentifier) {
                    println("PWC_RESOLVED|${id.group}:${id.module}|${id.version}")
                }
            }
        }
    }
}
''')
process=subprocess.run(['./gradlew','-I',str(init),':app:pwcResolvedRuntime','--console=plain'],cwd=root,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
if process.returncode:
    text=process.stdout[-10000:]
    for i in range(0,len(text),3000):
        chunk=text[i:i+3000].replace('%','%25').replace('\r','%0D').replace('\n','%0A')
        print(f'::error title=Gradle selected-component inventory {i//3000+1}::{chunk}')
    raise SystemExit(process.returncode)
text=process.stdout
coordinates=set()
for name,version in re.findall(r'^PWC_RESOLVED\|([^|]+)\|([^|\s]+)$',text,re.MULTILINE):
    if name.startswith('io.flutter:'):continue
    coordinates.add((name,version))
if not coordinates:
    print('::error title=Android inventory unavailable::No selected Maven coordinates captured; no advisory pass claimed')
    raise SystemExit(1)
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
