"""Failure-atomic publication tests; fake consumer is explicitly not cryptography."""

import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from infra.staging.backup import BackupError, HEADER, encrypted_backup

RECIPIENT = "age1" + "a" * 58


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.output = self.directory / "snapshot.age"
        self.consumer = self.directory / "consumer"
        self.consumer.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\nsys.stdout.buffer.write("
            + repr(HEADER)
            + "+sys.stdin.buffer.read())\n"
        )
        self.consumer.chmod(0o700)

    def backup(
        self, source="import sys;sys.stdout.buffer.write(b'PGDMP synthetic')", **changes
    ):
        return encrypted_backup(
            [sys.executable, "-c", source],
            RECIPIENT,
            self.output,
            age=str(self.consumer),
            **changes,
        )

    def test_success_publishes_private_file_and_hash_without_plaintext_temp(self):
        result = self.backup()
        self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
        self.assertEqual(
            result["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest()
        )
        self.assertEqual(result["encrypted_bytes"], self.output.stat().st_size)
        self.assertFalse(list(self.directory.glob(".pwc-backup-*")))

    def test_dump_failure_after_output_cannot_publish_even_if_consumer_succeeds(self):
        with self.assertRaises(BackupError):
            self.backup(
                "import sys;sys.stdout.buffer.write(b'partial private data');sys.exit(7)"
            )
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.directory.glob(".pwc-backup-*")))

    def test_consumer_failure_cannot_publish_partial_file(self):
        self.consumer.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\nsys.stdout.write('partial');sys.exit(8)\n"
        )
        with self.assertRaises(BackupError):
            self.backup()
        self.assertFalse(self.output.exists())

    def test_previous_backup_and_symlink_are_never_overwritten(self):
        self.output.write_bytes(b"previous")
        with self.assertRaises(BackupError):
            self.backup()
        self.assertEqual(self.output.read_bytes(), b"previous")
        self.output.unlink()
        target = self.directory / "private-target"
        target.write_bytes(b"retain")
        self.output.symlink_to(target)
        with self.assertRaises(BackupError):
            self.backup()
        self.assertEqual(target.read_bytes(), b"retain")

    def test_public_directory_and_relative_paths_are_refused_before_process_start(self):
        self.directory.chmod(0o755)
        with patch("infra.staging.backup.subprocess.Popen") as process:
            with self.assertRaises(BackupError):
                self.backup()
            process.assert_not_called()
        with self.assertRaises(BackupError):
            encrypted_backup([], RECIPIENT, "relative.age")

    def test_link_race_preserves_other_file(self):
        real = os.link

        def racing(source, destination):
            Path(destination).write_bytes(b"other")
            return real(source, destination)

        with patch("infra.staging.backup.os.link", side_effect=racing):
            with self.assertRaises(BackupError):
                self.backup()
        self.assertEqual(self.output.read_bytes(), b"other")
        self.assertFalse(list(self.directory.glob(".pwc-backup-*")))

    def test_timeout_reaps_pipeline_and_removes_partial_output(self):
        with self.assertRaises(BackupError):
            self.backup("import time;time.sleep(30)", timeout=1)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.directory.glob(".pwc-backup-*")))

    def test_missing_encryptor_is_redacted_and_does_not_leave_dump_running(self):
        with self.assertRaises(BackupError) as error:
            encrypted_backup(
                [sys.executable, "-c", "import time;time.sleep(30)"],
                RECIPIENT,
                self.output,
                age="/does/not/exist",
            )
        self.assertEqual(str(error.exception), "BACKUP_FAILED")
        self.assertFalse(self.output.exists())

    def test_wrong_format_from_successful_consumer_is_not_published(self):
        self.consumer.write_text(
            "#!"
            + sys.executable
            + "\nimport sys\nsys.stdout.buffer.write(sys.stdin.buffer.read())\n"
        )
        with self.assertRaises(BackupError):
            self.backup()
        self.assertFalse(self.output.exists())

    def test_invalid_recipient_and_timeout_cannot_start_processes(self):
        with patch("infra.staging.backup.subprocess.Popen") as process:
            for recipient, timeout in (
                ("private-key", 10),
                (RECIPIENT, True),
                (RECIPIENT, 0),
            ):
                with self.assertRaises(BackupError):
                    encrypted_backup([], recipient, self.output, timeout=timeout)
            process.assert_not_called()

    def test_directory_fsync_failure_keeps_ciphertext_and_reports_uncertainty(self):
        real = os.fsync

        def fail_directory(fd):
            import stat

            if stat.S_ISDIR(os.fstat(fd).st_mode):
                raise OSError("sensitive path")
            return real(fd)

        with patch("infra.staging.backup.os.fsync", side_effect=fail_directory):
            with self.assertRaises(BackupError) as error:
                self.backup()
        self.assertEqual(str(error.exception), "BACKUP_PUBLICATION_UNCERTAIN")
        self.assertTrue(self.output.exists())

    @unittest.skipUnless(
        shutil.which("age") and shutil.which("age-keygen"),
        "Actual age CLI is required for encryption integration",
    )
    def test_real_age_round_trip_and_no_plaintext_file(self):
        identity = self.directory / "identity.txt"
        subprocess.run(
            ["age-keygen", "-o", str(identity)], check=True, stderr=subprocess.DEVNULL
        )
        recipient = subprocess.check_output(
            ["age-keygen", "-y", str(identity)], text=True
        ).strip()
        payload = b"PGDMP disposable synthetic database bytes"
        encrypted_backup(
            [
                sys.executable,
                "-c",
                "import sys;sys.stdout.buffer.write(" + repr(payload) + ")",
            ],
            recipient,
            self.output,
        )
        self.assertNotIn(payload, self.output.read_bytes())
        restored = subprocess.check_output(
            ["age", "--decrypt", "--identity", str(identity), str(self.output)],
            stderr=subprocess.DEVNULL,
        )
        self.assertEqual(restored, payload)
