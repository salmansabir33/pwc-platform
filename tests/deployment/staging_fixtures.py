"""Ephemeral synthetic PKI only. Never a staging provisioning/acceptance tool."""

import importlib.util
from pathlib import Path
import secrets
import subprocess

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "staging_deploy", ROOT / "infra/staging/deploy.py"
)
deploy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(deploy)


def config(directory):
    return {
        "project": "pwc-staging-ci",
        "release": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "ngo_host": "ngo.pwc.test",
        "ops_host": "ops.pwc.test",
        "images": {name: name + "@sha256:" + "a" * 64 for name in deploy.IMAGES},
        "files": {name: str(Path(directory) / name) for name in deploy.FILES},
    }


def certificates(value):
    """Requires root: match production bind-mounted UID/GID contract."""

    def openssl(*args):
        subprocess.run(
            ["openssl", *args],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    files = value["files"]
    root = Path(files["app_key"]).parent
    for name in ("public", "app", "db", "client"):
        openssl(
            "req",
            "-x509",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-days",
            "14",
            "-subj",
            "/CN=Synthetic-" + name,
            "-keyout",
            str(root / (name + "_ca_key")),
            "-out",
            files[name + "_ca"],
            "-addext",
            "basicConstraints=critical,CA:TRUE",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        )
    for name in deploy.PAIRS:
        client = name.endswith("client") or name == "health"
        ca = "client" if client else "public" if name in ("ngo", "ops") else name
        host = (
            value[name + "_host"] if name in ("ngo", "ops") else name + ".pwc.internal"
        )
        openssl(
            "req",
            "-new",
            "-newkey",
            "rsa:2048",
            "-nodes",
            "-subj",
            "/CN=Synthetic-" + name,
            "-keyout",
            files[name + "_key"],
            "-out",
            str(root / "request.csr"),
        )
        (root / "extension.cnf").write_text(
            "basicConstraints=critical,CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage="
            + ("clientAuth" if client else "serverAuth")
            + "\nsubjectAltName=DNS:"
            + host
            + "\n"
        )
        openssl(
            "x509",
            "-req",
            "-in",
            str(root / "request.csr"),
            "-CA",
            files[ca + "_ca"],
            "-CAkey",
            str(root / (ca + "_ca_key")),
            "-CAcreateserial",
            "-days",
            "14",
            "-extfile",
            str(root / "extension.cnf"),
            "-out",
            files[name + "_cert"],
        )
    for name in deploy.PASSWORDS:
        Path(files[name]).write_text(secrets.token_urlsafe(64))
    for name, path in files.items():
        file = Path(path)
        if name in deploy.PASSWORDS or name.endswith("_key"):
            import os

            os.chown(file, 0, 10001)
            file.chmod(0o640)
        else:
            file.chmod(0o644)
