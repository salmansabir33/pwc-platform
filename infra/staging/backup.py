"""Failure-atomic age-encrypted backup. Running requires separate host permission.

No plaintext files, shell interpolation, deployment or approval switches. The
existing stack/owner/TLS boundary supplies pg_dump. The host's reviewed age CLI
supplies encryption; a magic header is a format check, not authenticity proof.
"""

import argparse
import hashlib
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
HEADER = b"age-encryption.org/v1\n"


class BackupError(Exception):
    """Bounded error only; never expose dump, provider stderr or secret paths."""


def destination(path):
    path = Path(path)
    parent = path.parent
    if not path.is_absolute() or path.name in {"", ".", ".."}:
        raise BackupError("BACKUP_DESTINATION_INVALID")
    if parent.is_symlink() or parent.resolve() != parent or path.is_symlink():
        raise BackupError("BACKUP_DESTINATION_INVALID")
    info = parent.stat()
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or stat.S_IMODE(info.st_mode) & 0o077
        or path.resolve().is_relative_to(ROOT)
    ):
        raise BackupError("BACKUP_DESTINATION_INVALID")
    if path.exists():
        raise BackupError("BACKUP_ALREADY_EXISTS")
    return path


def stop(process):
    if process is None or process.poll() is not None:
        return
    # Kill descendants too (Compose/age plugins); never leave a timed-out dump.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait()


def encrypted_backup(producer, recipient, output, *, age="age", timeout=300):
    """Explicit operator invocation only. Return encrypted size/hash, no payload.

    Private destination directory must already exist, be owned by the caller and
    mode 0700. Atomic no-replace hard-link publication keeps older backups intact.
    Filesystems without link/fsync support fail closed. stdout/stderr are never
    used for data or diagnostics; age receives plaintext only through a pipe.
    """
    if (
        not isinstance(recipient, str)
        or not re.fullmatch(r"age1[a-z0-9]{58}", recipient)
        or type(timeout) is not int
        or not 1 <= timeout <= 3600
    ):
        raise BackupError("BACKUP_ARGUMENT_INVALID")
    temporary = None
    dump = encrypt = None
    published = False
    try:
        output = destination(output)
        deadline = time.monotonic() + timeout
        fd, temporary = tempfile.mkstemp(prefix=".pwc-backup-", dir=output.parent)
        with os.fdopen(fd, "wb") as stream:
            dump = subprocess.Popen(
                producer,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
            )
            try:
                encrypt = subprocess.Popen(
                    [age, "--encrypt", "--recipient", recipient],
                    stdin=dump.stdout,
                    stdout=stream,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            finally:
                dump.stdout.close()
            encryption_status = encrypt.wait(
                timeout=max(0.001, deadline - time.monotonic())
            )
            dump_status = dump.wait(timeout=max(0.001, deadline - time.monotonic()))
            if encryption_status != 0 or dump_status != 0:
                raise BackupError("BACKUP_PIPELINE_FAILED")
            stream.flush()
            os.fsync(stream.fileno())
        digest = hashlib.sha256()
        with open(temporary, "rb") as stream:
            if stream.read(len(HEADER)) != HEADER:
                raise BackupError("BACKUP_FORMAT_INVALID")
            stream.seek(0)
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
        size = os.stat(temporary).st_size
        if size <= len(HEADER):
            raise BackupError("BACKUP_FORMAT_INVALID")
        os.link(
            temporary, output
        )  # Atomic create, never overwrite an existing file/symlink.
        published = True
        os.unlink(temporary)
        temporary = None
        directory_fd = os.open(output.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        return {"encrypted_bytes": size, "sha256": digest.hexdigest()}
    except (OSError, ValueError, TypeError, subprocess.SubprocessError, BackupError):
        # If publication succeeded but directory fsync failed, retain the encrypted
        # file: its durability is uncertain and must not destroy a recoverable copy.
        raise BackupError(
            "BACKUP_PUBLICATION_UNCERTAIN" if published else "BACKUP_FAILED"
        ) from None
    finally:
        stop(encrypt)
        stop(dump)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument(
        "--recipient",
        required=True,
        help="Approved public native-age recipient, never a private key",
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    try:
        if (
            not args.manifest.is_absolute()
            or args.manifest.name != "compose.json"
            or not args.manifest.is_file()
        ):
            raise BackupError("BACKUP_MANIFEST_INVALID")
        result = encrypted_backup(
            [str(ROOT / "infra/staging/stack.sh"), str(args.manifest), "backup"],
            args.recipient,
            args.output,
            timeout=args.timeout,
        )
        print(
            "Encrypted backup published; bytes="
            + str(result["encrypted_bytes"])
            + "; sha256="
            + result["sha256"]
        )
        return 0
    except (BackupError, OSError):
        print(
            "Backup failed or publication uncertain; no automatic retry or authorization implied."
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
