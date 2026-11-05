"""Allowlisted package evidence from retained Trivy reports, never image config."""

import json
from pathlib import Path
import re
import sys

IMAGES = ("app", "ngo", "ops", "db", "haproxy")
FIELDS = ("VulnerabilityID", "PkgName", "InstalledVersion", "FixedVersion", "Severity")


def rows(directory):
    result = []
    for index, image in enumerate(IMAGES, 1):
        paths = list(Path(directory).rglob(f"image-{index}.json"))
        if len(paths) != 1:
            raise ValueError("Missing or duplicate advisory report")
        value = json.loads(paths[0].read_text())
        if value.get("SchemaVersion") != 2 or not isinstance(
            value.get("Results"), list
        ):
            raise ValueError("Invalid advisory report")
        for target in value["Results"]:
            for item in target.get("Vulnerabilities") or []:
                if item.get("Severity") not in {"HIGH", "CRITICAL"}:
                    continue
                row = {key: item.get(key) or "" for key in FIELDS}
                if any(
                    not isinstance(v, str)
                    or len(v) > 300
                    or re.search(r"[^\x20-\x7e]", v)
                    for v in row.values()
                ):
                    raise ValueError("Invalid public advisory field")
                result.append({"image": image, **row})
    return result


def main(directory):
    evidence = rows(directory)
    # GitHub limits notices per step and truncates individual messages. Compact
    # tuples preserve all unique image/CVE/package/version/fix/severity rows.
    compact = sorted(
        {
            json.dumps([r["image"], *(r[k] for k in FIELDS)], separators=(",", ":"))
            for r in evidence
        }
    )
    chunks, chunk = [], []
    for row in compact:
        if len("[" + ",".join([*chunk, row]) + "]") > 3500:
            chunks.append(chunk)
            chunk = []
        chunk.append(row)
    if chunk:
        chunks.append(chunk)
    if len(chunks) > 10:
        raise ValueError("Use retained JSON: annotation capacity exceeded")
    for chunk in chunks:
        print(
            "::notice title=Package advisory::["
            + ",".join(chunk).replace("%", "%25")
            + "]"
        )
    return evidence


if __name__ == "__main__":
    try:
        evidence = main(sys.argv[1])
        Path(sys.argv[2]).write_text(json.dumps(evidence, indent=2) + "\n")
    except (OSError, ValueError, TypeError, KeyError):
        print("::error::Advisory evidence unavailable; no remediation claim")
        raise SystemExit(1) from None
