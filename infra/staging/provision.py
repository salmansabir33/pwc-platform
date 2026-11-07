"""Operator-only, failure-atomic provisioning; never deploys or invents approval.

Issuer keys stay outside runtime mounts. Existing keys/secrets are never replaced.
All command diagnostics are redacted. Run from a reviewed checkout on the host.
"""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import tempfile

from . import deploy

CLIENTS = ("ngo_client", "ops_client", "health")


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def external(path):
    path = Path(path)
    if (
        not path.is_absolute()
        or path.resolve() != path
        or path.is_symlink()
        or path.resolve().is_relative_to(deploy.ROOT)
    ):
        raise ValueError("EXTERNAL_PATH_REQUIRED")
    return path


def private_directory(path):
    path = external(path)
    info = path.stat()
    if not path.is_dir() or info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_DIRECTORY_REQUIRED")
    return path


def load(path):
    path = external(path)
    private_directory(path.parent)
    info = path.stat()
    if info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError("PRIVATE_CONFIG_REQUIRED")
    return deploy.metadata(
        json.loads(path.read_text(), object_pairs_hook=deploy.unique)
    )


def write_new(path, data):
    path = external(path)
    private_directory(path.parent)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())


@contextmanager
def config_lock(path):
    path = external(path)
    private_directory(path.parent)
    fd = os.open(
        str(path) + ".provision.lock", os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600
    )
    try:
        info = os.fstat(fd)
        if info.st_uid != os.geteuid() or info.st_mode & 0o077:
            raise ValueError("PRIVATE_LOCK_REQUIRED")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


def save_config(path, value, expected):
    with config_lock(path):
        _save_config(path, value, expected)


def _save_config(path, value, expected):
    """CAS update with a retained exact original; no secret values in diagnostics."""
    path = external(path)
    if digest(path) != expected:
        raise ValueError("CONFIG_CHANGED")
    original = path.read_bytes()
    backup = path.with_name(path.name + ".before-" + expected)
    if backup.exists():
        if backup.read_bytes() != original:
            raise ValueError("BACKUP_CONFLICT")
    else:
        write_new(backup, original)
    fd, temporary = tempfile.mkstemp(prefix=".config-", dir=path.parent)
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        if digest(path) != expected:
            raise ValueError("CONFIG_CHANGED")
        os.replace(temporary, path)
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent)
        finally:
            os.close(parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def run(*args):
    if args[0] == "docker" or args[0] == str(deploy.HERE / "stack.sh"):
        command = [*args]
        if args[0] == "docker":
            command[1:1] = ["--context", "default"]
        # A terminal used for another project must not retarget this operation.
        environment = {
            k: v for k, v in os.environ.items() if not k.startswith("COMPOSE_")
        }
        return subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            env=environment,
        ).stdout
    return deploy.checked(list(args))


def checked_client(cert, key, ca, name):
    run("openssl", "verify", "-CAfile", str(ca), "-purpose", "sslclient", str(cert))
    run("openssl", "x509", "-in", str(cert), "-checkend", "604800", "-noout")
    if run("openssl", "x509", "-in", str(cert), "-pubkey", "-noout") != run(
        "openssl", "pkey", "-in", str(key), "-pubout"
    ):
        raise ValueError("CLIENT_KEY_MISMATCH")
    eku = run("openssl", "x509", "-in", str(cert), "-noout", "-ext", "extendedKeyUsage")
    if eku.decode().strip().splitlines()[-1].strip() != "TLS Web Client Authentication":
        raise ValueError("CLIENT_EKU_INVALID")
    san = run("openssl", "x509", "-in", str(cert), "-noout", "-ext", "subjectAltName")
    if san.decode().strip().splitlines()[-1].strip() != "DNS:" + name + ".pwc.internal":
        raise ValueError("CLIENT_SAN_INVALID")


def clients(config, output, csrs, issuer_key, replace_ca, approval):
    """Sign supplied CSRs or derive CSR from the existing health key.

    Missing original issuer is not silently replaced. Rotation explicitly reissues
    ALL three client identities and atomically changes their paths plus client_ca.
    Public/app/DB certificates, all runtime secrets and all private leaf keys stay.
    """
    value = load(config)
    expected = digest(config)
    if approval != expected:
        raise ValueError("EXACT_CONFIG_APPROVAL_REQUIRED")
    if set(csrs) != {"ngo_client", "ops_client"}:
        raise ValueError("BOTH_PENDING_CSRS_REQUIRED")
    output = external(output)
    private_directory(output.parent)
    if output.exists():
        # No overwrites, including interrupted generations. Reuse only a completed
        # generation already referenced by the current validated configuration.
        if all(Path(value["files"][n + "_cert"]).parent == output for n in CLIENTS):
            deploy.files(value)
            return
        raise ValueError("NEW_GENERATION_REQUIRED")
    key = external(issuer_key)
    private_directory(key.parent)
    output.mkdir(mode=0o700)
    ca = Path(value["files"]["client_ca"])
    if replace_ca:
        if key.exists():
            raise ValueError("NEW_ISSUER_KEY_PATH_REQUIRED")
        # Issuer directory is separate from leaf generations and Compose mounts.
        if key.is_relative_to(output) or output.is_relative_to(key.parent):
            raise ValueError("ISSUER_MUST_BE_SEPARATE")
        ca = output / "client-ca.pem"
        run(
            "openssl",
            "req",
            "-x509",
            "-newkey",
            "rsa:3072",
            "-nodes",
            "-days",
            "365",
            "-subj",
            "/CN=PWC approved staging client CA",
            "-keyout",
            str(key),
            "-out",
            str(ca),
            "-addext",
            "basicConstraints=critical,CA:TRUE,pathlen:0",
            "-addext",
            "keyUsage=critical,keyCertSign,cRLSign",
        )
        key.chmod(0o600)
        ca.chmod(0o644)
        value["files"]["client_ca"] = str(ca)
    info = key.stat()
    if info.st_uid != os.geteuid() or info.st_mode & 0o077:
        raise ValueError("ISSUER_KEY_PERMISSIONS")
    if run("openssl", "x509", "-in", str(ca), "-pubkey", "-noout") != run(
        "openssl", "pkey", "-in", str(key), "-pubout"
    ):
        raise ValueError("ISSUER_KEY_MISMATCH")
    for name in CLIENTS:
        leaf_key = Path(value["files"][name + "_key"])
        if name == "health":
            csr = output / "health.csr"
            run(
                "openssl",
                "req",
                "-new",
                "-key",
                str(leaf_key),
                "-subj",
                "/CN=health.pwc.internal",
                "-out",
                str(csr),
            )
        else:
            csr = external(csrs[name])
        run("openssl", "req", "-in", str(csr), "-verify", "-noout")
        if run("openssl", "req", "-in", str(csr), "-pubkey", "-noout") != run(
            "openssl", "pkey", "-in", str(leaf_key), "-pubout"
        ):
            raise ValueError("CSR_KEY_MISMATCH")
        extension = output / (name + ".ext")
        write_new(
            extension,
            (
                "basicConstraints=critical,CA:FALSE\n"
                "keyUsage=critical,digitalSignature\n"
                "extendedKeyUsage=clientAuth\nsubjectAltName=DNS:"
                + name
                + ".pwc.internal\n"
            ).encode(),
        )
        cert = output / (name + ".pem")
        run(
            "openssl",
            "x509",
            "-req",
            "-in",
            str(csr),
            "-CA",
            str(ca),
            "-CAkey",
            str(key),
            "-set_serial",
            "0x" + secrets.token_hex(16),
            "-days",
            "90",
            "-extfile",
            str(extension),
            "-out",
            str(cert),
        )
        cert.chmod(0o644)
        checked_client(cert, leaf_key, ca, name)
        value["files"][name + "_cert"] = str(cert)
    # Full existing renderer validation before switching any configuration paths.
    deploy.files(value)
    save_config(config, value, expected)


def import_clients(config, certificates, approval):
    """Accept public signed leaves returned by an external approved issuer."""
    value = load(config)
    if digest(config) != approval or set(certificates) != {"ngo_client", "ops_client"}:
        raise ValueError("EXACT_CONFIG_AND_BOTH_CERTIFICATES_REQUIRED")
    for name, certificate in certificates.items():
        certificate = external(certificate)
        checked_client(
            certificate,
            value["files"][name + "_key"],
            value["files"]["client_ca"],
            name,
        )
        value["files"][name + "_cert"] = str(certificate)
    deploy.files(value)
    if value != load(config):
        save_config(config, value, approval)


def resolve_images(candidates, output):
    """Resolve candidates for REVIEW; never automatically apply resolved tags."""
    if set(candidates) != set(deploy.IMAGES):
        raise ValueError("FIVE_IMAGES_REQUIRED")
    resolved = {}
    for name, tag in candidates.items():
        if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9./_:-]*", tag):
            raise ValueError("INVALID_IMAGE")
        run("docker", "pull", tag)
        references = json.loads(
            run("docker", "image", "inspect", tag, "--format", "{{json .RepoDigests}}")
        )
        if not references or len(references) != 1:
            raise ValueError("AMBIGUOUS_IMAGE_DIGEST")
        resolved[name] = references[0]
    write_new(output, (json.dumps(resolved, indent=2) + "\n").encode())


def apply_images(config, images, approval):
    value = load(config)
    if digest(config) != approval:
        raise ValueError("EXACT_CONFIG_APPROVAL_REQUIRED")
    value["images"] = images
    value["release"] = (
        run("git", "-C", str(deploy.ROOT), "rev-parse", "HEAD").decode().strip()
    )
    deploy.metadata(value)
    if load(config) == value:
        return
    save_config(config, value, approval)


def error_code(error):
    text = str(error)
    return (
        text
        if re.fullmatch(r"[A-Z][A-Z0-9_]{2,80}", text)
        else type(error).__name__.upper()
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("clients")
    p.add_argument("--config", required=True)
    p.add_argument("--output", required=True)
    p.add_argument("--ngo-csr", required=True)
    p.add_argument("--ops-csr", required=True)
    p.add_argument("--issuer-key", required=True)
    p.add_argument("--replace-client-ca", action="store_true")
    p.add_argument("--approve-config-sha256", required=True)
    p = sub.add_parser("import-clients")
    p.add_argument("--config", required=True)
    p.add_argument("--certificates", required=True)
    p.add_argument("--approve-config-sha256", required=True)
    p = sub.add_parser("resolve-images")
    p.add_argument("--candidates", required=True)
    p.add_argument("--output", required=True)
    p = sub.add_parser("apply-images")
    p.add_argument("--config", required=True)
    p.add_argument("--reviewed-images", required=True)
    p.add_argument("--approve-config-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command == "clients":
            clients(
                args.config,
                args.output,
                {"ngo_client": args.ngo_csr, "ops_client": args.ops_csr},
                args.issuer_key,
                args.replace_client_ca,
                args.approve_config_sha256,
            )
        elif args.command == "import-clients":
            import_clients(
                args.config,
                json.loads(
                    Path(args.certificates).read_text(), object_pairs_hook=deploy.unique
                ),
                args.approve_config_sha256,
            )
        elif args.command == "resolve-images":
            resolve_images(
                json.loads(
                    Path(args.candidates).read_text(), object_pairs_hook=deploy.unique
                ),
                args.output,
            )
        else:
            apply_images(
                args.config,
                json.loads(
                    Path(args.reviewed_images).read_text(),
                    object_pairs_hook=deploy.unique,
                ),
                args.approve_config_sha256,
            )
        print("Provisioning operation complete; no deployment or acceptance implied")
        return 0
    except (
        ValueError,
        OSError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
    ) as error:
        print("Provisioning blocker: " + error_code(error))
        print(
            "Provisioning failed; configuration not approved or inputs invalid (details redacted)"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
