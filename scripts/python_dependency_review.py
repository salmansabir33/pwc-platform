"""OSV review of exact Python requirement pins, including build/test tools.

No suppression list. Network/schema failure is failure, never zero findings.
Use HTTPS registry installs; this public-version scan does not verify wheel hashes.
"""

import json
from pathlib import Path
import re
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "apps/backend/requirements.txt",
    "packages/api-contracts/requirements.txt",
    "requirements-tooling.txt",
)


def pins(text):
    result = {}
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(
            r"([A-Za-z0-9_.-]+)(?:\[[A-Za-z0-9_,.-]+\])?==([A-Za-z0-9_.+-]+)", line
        )
        if not match:
            raise ValueError(
                "All reviewed Python requirements must be exact registry pins"
            )
        name, version = match.groups()
        name = re.sub(r"[-_.]+", "-", name).lower()
        if name in result and result[name] != version:
            raise ValueError("Conflicting dependency versions")
        result[name] = version
    return result


def findings(packages, response):
    results = response["results"]
    if not isinstance(results, list) or len(results) != len(packages):
        raise ValueError("Invalid advisory response")
    output = []
    for (name, version), result in zip(packages, results):
        if (
            not isinstance(result, dict)
            or set(result) - {"vulns"}
            or not isinstance(result.get("vulns", []), list)
        ):
            raise ValueError("Invalid advisory result")
        for advisory in result.get("vulns", []):
            identifier = advisory["id"]
            if not isinstance(identifier, str) or not re.fullmatch(
                r"[A-Za-z0-9_.-]+", identifier
            ):
                raise ValueError("Invalid advisory identifier")
            output.append({"name": name, "version": version, "id": identifier})
    return output


def main():
    try:
        packages = sorted(
            pins("\n".join((ROOT / name).read_text() for name in FILES)).items()
        )
        request = urllib.request.Request(
            "https://api.osv.dev/v1/querybatch",
            data=json.dumps(
                {
                    "queries": [
                        {
                            "package": {"name": name, "ecosystem": "PyPI"},
                            "version": version,
                        }
                        for name, version in packages
                    ]
                }
            ).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=90) as response:
            report = findings(packages, json.load(response))
    except Exception as error:
        print(
            f"Python advisory review unavailable/invalid: {type(error).__name__}; no zero-finding claim"
        )
        return 1
    for item in report:
        print(f"FAIL advisory: {item['name']} {item['version']} {item['id']}")
    print(
        f"::notice title=Python advisory review::{len(packages)} pinned versions, {len(report)} findings"
    )
    return bool(report)


if __name__ == "__main__":
    raise SystemExit(main())
