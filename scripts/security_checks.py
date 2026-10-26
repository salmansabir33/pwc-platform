"""Offline tracked-file checks, not a complete secret scanner or security proof."""

from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    "private-key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "github-token": re.compile(
        rb"\b(?:gh[pousr]_[A-Za-z0-9]{36,255}|github_pat_[A-Za-z0-9_]{60,255})\b"
    ),
    "aws-access-key": re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b"),
}


def inspect_file(name, data):
    errors = []
    path = Path(name)
    if path.name == ".env" or (
        path.name.startswith(".env.") and path.name != ".env.example"
    ):
        errors.append("environment-file")
    if any(
        part in {"node_modules", ".venv", ".dart_tool", "__pycache__"}
        for part in path.parts
    ):
        errors.append("machine-cache")
    if path.suffix.lower() in {".key", ".p12", ".pfx", ".jks", ".keystore"}:
        errors.append("credential-container")
    errors.extend(label for label, pattern in PATTERNS.items() if pattern.search(data))
    return errors


def workflow_errors(text):
    errors = []
    if not re.search(r"(?m)^permissions:\s*\n  contents: read\s*$", text):
        errors.append("contents-read-required")
    if "pull_request_target:" in text or "write-all" in text:
        errors.append("privileged-workflow")
    for action in re.findall(r"(?m)^\s*-?\s*uses:\s*([^\s#]+)", text):
        if not re.fullmatch(r"[\w.-]+/[\w./-]+@[0-9a-f]{40}", action):
            errors.append("unpinned-action")
    return errors


def main():
    paths = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    findings = []
    for name in filter(None, paths):
        data = (ROOT / name).read_bytes()
        findings.extend((name, label) for label in inspect_file(name, data))
        if name.startswith(".github/workflows/"):
            findings.extend((name, label) for label in workflow_errors(data.decode()))
    for name, label in findings:
        # Never print matched secret bytes or full file lines.
        print(f"FAIL {label}: {name}")
    print(f"Tracked-file security checks: {len(findings)} findings")
    return bool(findings)


if __name__ == "__main__":
    raise SystemExit(main())
