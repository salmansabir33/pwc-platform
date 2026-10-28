"""Public advisory counts/IDs only; never echo image configuration/environment."""

import json
from pathlib import Path
import re
import sys


def main(directory):
    reports = sorted(Path(directory).glob("image-*.json"))
    if len(reports) != 5:
        print(
            "::error title=Image scan::Incomplete scanner reports; no clean-scan claim"
        )
        return 1
    failed = False
    for report in reports:
        value = json.loads(report.read_text())
        findings = [
            item
            for result in value.get("Results", [])
            for item in result.get("Vulnerabilities", [])
            if item.get("Severity") in {"HIGH", "CRITICAL"}
        ]
        fixable = [item for item in findings if item.get("FixedVersion")]
        identifiers = sorted(
            {
                item["VulnerabilityID"]
                for item in findings
                if re.fullmatch(
                    r"(?:CVE-[0-9]{4}-[0-9]+|GHSA-[a-z0-9-]+)",
                    item.get("VulnerabilityID", ""),
                )
            }
        )
        level = "error" if fixable else "notice"
        print(
            f"::{level} title=Image advisory summary::{report.name}: {len(findings)} HIGH/CRITICAL; {len(fixable)} fixable; IDs="
            + ",".join(identifiers)
        )
        failed |= bool(fixable)
    return int(failed)


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1]))
    except (OSError, ValueError, KeyError, TypeError):
        print(
            "::error title=Image scan::Invalid/unavailable scanner reports; no clean-scan claim"
        )
        raise SystemExit(1) from None
