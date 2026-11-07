"""Encrypted SSH export and separate-host restore rehearsal; operator invoked only.

No plaintext backup file, password SSH, host-key bypass or destructive cleanup.
Receipts are operational evidence, not independent authorization/acceptance.
"""

import argparse
import json
import os
from pathlib import Path
import re
import shlex
import subprocess

from . import backup, deploy, operate, provision

# Fixed remote program, no caller-provided hooks. Only age ciphertext crosses SSH.
REMOTE = r"""
import hashlib, json, os, pathlib, shutil, sys
m=hashlib.sha256(pathlib.Path('/etc/machine-id').read_bytes().strip()).hexdigest()
if len(sys.argv)>3 and sys.argv[3]==m: raise ValueError()
p=pathlib.Path(sys.argv[1]); expected=sys.argv[2]
if not p.is_absolute() or p.resolve()!=p or p.is_symlink(): raise ValueError()
s=p.parent.stat()
if s.st_uid!=os.geteuid() or s.st_mode & 0o077: raise ValueError()
if not p.exists():
    fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as f:
        shutil.copyfileobj(sys.stdin.buffer,f); f.flush(); os.fsync(f.fileno())
with p.open('rb') as f:
    if f.read(22)!=b'age-encryption.org/v1\n': raise ValueError()
    f.seek(0); h=hashlib.file_digest(f,'sha256').hexdigest()
if h!=expected: raise ValueError()
d=os.open(p.parent,os.O_RDONLY|os.O_DIRECTORY); os.fsync(d); os.close(d)
m=hashlib.sha256(pathlib.Path('/etc/machine-id').read_bytes().strip()).hexdigest()
print(json.dumps({'sha256':h,'machine':m}))
"""


def ssh_command(host, known_hosts, destination, sha):
    if not re.fullmatch(r"[a-z_][a-z0-9_-]*@[a-z0-9][a-z0-9.-]*", host):
        raise ValueError("APPROVED_OFFHOST_REQUIRED")
    destination = str(destination)
    if not re.fullmatch(r"/[a-zA-Z0-9_./-]+", destination):
        raise ValueError("REMOTE_PATH_INVALID")
    known_hosts = provision.external(known_hosts)
    if not known_hosts.is_file():
        raise ValueError("PINNED_HOST_KEYS_REQUIRED")
    return [
        "ssh",
        "-F",
        "/dev/null",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=yes",
        "-o",
        "UserKnownHostsFile=" + str(known_hosts),
        "-o",
        "GlobalKnownHostsFile=/dev/null",
        "-o",
        "PasswordAuthentication=no",
        "-o",
        "KbdInteractiveAuthentication=no",
        "-o",
        "ForwardAgent=no",
        "-o",
        "ClearAllForwardings=yes",
        "-o",
        "ConnectTimeout=15",
        host,
        shlex.join(["python3", "-c", REMOTE, destination, sha, operate.machine()]),
    ]


def export(config, rendered, recipient, output, host, known_hosts, remote, receipt):
    value, manifest, bound = operate.binding(config, rendered, built=True)
    operate.healthy(manifest, ("db", "app"), bound["images"])
    output = provision.external(output)
    if output.exists():
        # A valid previous encrypted file may be exported again after an SSH
        # failure, but never treated as a fresh dump or overwritten.
        raise ValueError("EXISTING_BACKUP_USE_EXPORT_EXISTING")
    result = backup.encrypted_backup(
        [str(deploy.HERE / "stack.sh"), str(manifest), "backup"], recipient, output
    )
    export_existing(
        config, rendered, output, host, known_hosts, remote, receipt, bound, result
    )


def export_existing(
    config,
    rendered,
    output,
    host,
    known_hosts,
    remote,
    receipt,
    bound=None,
    result=None,
):
    # Only export an already-created backup when a matching source sidecar exists.
    # This prevents attaching new image/config evidence to an old dump.
    sidecar = Path(str(output) + ".source.json")
    if bound is not None:
        operate.store(sidecar, {"binding": bound, "backup": result})
    saved = operate.json_file(sidecar)
    _, _, current = operate.binding(config, rendered, built=True)
    if (
        current != saved["binding"]
        or provision.digest(output) != saved["backup"]["sha256"]
    ):
        raise ValueError("BACKUP_SOURCE_CHANGED")
    with open(output, "rb") as stream:
        completed = subprocess.run(
            ssh_command(host, known_hosts, remote, saved["backup"]["sha256"]),
            stdin=stream,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=True,
            timeout=300,
        )
    remote_result = json.loads(completed.stdout)
    if (
        remote_result["sha256"] != saved["backup"]["sha256"]
        or remote_result["machine"] == operate.machine()
    ):
        raise ValueError("OFFHOST_READBACK_FAILED")
    operate.store(
        receipt,
        {
            **saved["backup"],
            "source_machine": current["machine"],
            "source_images": current["images"],
            "source_config": current["config"],
            "offhost_machine": remote_result["machine"],
            "offhost": host,
            "remote_path": str(remote),
            "independent_acceptance": False,
        },
    )


def restore_plan(config, rendered, encrypted, receipt):
    value, manifest, bound = operate.binding(config, rendered, built=True)
    source = operate.json_file(receipt)
    if (
        source["source_machine"] == bound["machine"]
        or source["offhost_machine"] == bound["machine"]
        or source["source_images"] != bound["images"]
        or provision.digest(encrypted) != source["sha256"]
    ):
        raise ValueError("SEPARATE_RESTORE_HOST_AND_MATCHING_IMAGES_REQUIRED")
    bound["backup_sha256"] = source["sha256"]
    bound["action"] = "fresh-isolated-restore"
    return manifest, bound


def rehearse(config, rendered, encrypted, source_receipt, identity, receipt, approval):
    manifest, bound = restore_plan(config, rendered, encrypted, source_receipt)
    if operate.token(bound) != approval:
        raise ValueError("EXACT_RESTORE_APPROVAL_REQUIRED")
    value = provision.load(config)
    # Check canonical name as well as containers: unlabeled volumes also count.
    if operate.run(
        *operate.compose(manifest, "ps", "--all", "--quiet")
    ).strip() or operate.has_db_volume(value["project"]):
        raise ValueError("RESTORE_HOST_NOT_FRESH")
    identity = provision.external(identity)
    operate.run(
        *operate.compose(
            manifest,
            "up",
            "-d",
            "--no-build",
            "--pull",
            "never",
            "--wait",
            "--wait-timeout",
            "180",
            "db",
        )
    )
    decrypt = consumer = None
    try:
        decrypt = subprocess.Popen(
            ["age", "--decrypt", "-i", str(identity), str(encrypted)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
        consumer = subprocess.Popen(
            [str(deploy.HERE / "stack.sh"), str(manifest), "restore"],
            stdin=decrypt.stdout,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "PWC_CONFIRM_FRESH_RESTORE": "YES"},
            start_new_session=True,
        )
        decrypt.stdout.close()
        consumed = consumer.wait(timeout=300)
        decrypted = decrypt.wait(timeout=30)
        if consumed or decrypted:
            raise ValueError("RESTORE_PIPELINE_FAILED")
    finally:
        backup.stop(consumer)
        backup.stop(decrypt)
    operate.run(
        *operate.compose(
            manifest, "--profile", "maintenance", "run", "--rm", "--no-deps", "migrate"
        )
    )
    operate.run(
        *operate.compose(
            manifest,
            "up",
            "-d",
            "--no-build",
            "--pull",
            "never",
            "--wait",
            "--wait-timeout",
            "180",
            "app",
        )
    )
    operate.healthy(manifest, ("db", "app"), bound["images"])
    operate.store(
        receipt,
        {
            "restore_machine": operate.machine(),
            "backup_sha256": bound["backup_sha256"],
            "source_images": bound["images"],
            "result": "RESTORE_APP_DB_HEALTHY_NOT_HOST_ACCEPTANCE",
            "independent_acceptance": False,
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=["export", "export-existing", "plan-restore", "restore"]
    )
    for name in ("config", "render", "backup", "receipt"):
        parser.add_argument("--" + name, required=True)
    for name in (
        "recipient",
        "offhost",
        "known-hosts",
        "remote-path",
        "source-receipt",
        "identity",
        "approve-plan-sha256",
    ):
        parser.add_argument("--" + name)
    args = parser.parse_args()
    os.umask(0o077)
    try:
        if args.command in {"export", "export-existing"}:
            func = export if args.command == "export" else export_existing
            common = (args.config, args.render)
            if args.command == "export":
                common += (args.recipient,)
            func(
                *common,
                args.backup,
                args.offhost,
                args.known_hosts,
                args.remote_path,
                args.receipt,
            )
        elif args.command == "plan-restore":
            _, bound = restore_plan(
                args.config, args.render, args.backup, args.source_receipt
            )
            print(
                json.dumps(
                    {
                        "plan_sha256": operate.token(bound),
                        "action": bound["action"],
                        "host_acceptance": False,
                    }
                )
            )
        else:
            rehearse(
                args.config,
                args.render,
                args.backup,
                args.source_receipt,
                args.identity,
                args.receipt,
                args.approve_plan_sha256,
            )
        return 0
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.SubprocessError,
        backup.BackupError,
    ):
        print(
            "Recovery operation blocked or failed (details redacted); preserve encrypted files and inspect privately"
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
