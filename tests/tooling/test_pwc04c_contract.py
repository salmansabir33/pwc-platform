"""Review lock negative tests; no domain implementation or acceptance simulation."""

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.check_pwc04c_contract import (
    ContractLockError,
    DOCUMENT,
    LOCK,
    ROOT,
    check_contract,
    section_bytes,
)


class FixtureContractLockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (DOCUMENT, LOCK):
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / path).read_bytes())

    def rewrite_lock(self, **changes):
        path = self.root / LOCK
        value = json.loads(path.read_text())
        value.update(changes)
        path.write_text(json.dumps(value))

    def test_checked_in_bytes_match_without_approving_anything(self):
        self.assertEqual(check_contract(), "C04C-FIXTURE-20261103.1")
        self.assertEqual(check_contract(self.root), check_contract())

    def test_normative_rule_edit_invalidates_lock(self):
        path = self.root / DOCUMENT
        path.write_bytes(path.read_bytes().replace(b"GM06 B:", b"GM06 A:", 1))
        with self.assertRaises(ContractLockError):
            check_contract(self.root)

    def test_fixed_e05_constraints_cannot_drift_silently(self):
        path = self.root / DOCUMENT
        path.write_bytes(
            path.read_bytes().replace(
                b"nonfinance grant 90 days/source cutoff",
                b"nonfinance grant 91 days/source cutoff",
                1,
            )
        )
        with self.assertRaises(ContractLockError):
            check_contract(self.root)

    def test_unlocked_execution_notes_do_not_change_review_bytes(self):
        path = self.root / DOCUMENT
        path.write_bytes(path.read_bytes() + b"\nNon-normative execution note.\n")
        self.assertEqual(check_contract(self.root), check_contract())

    def test_lock_never_accepts_approval_flags_or_path_redirection(self):
        for changes in (
            {"approved": True},
            {"document": "../../outside"},
            {"baseline_commit": "0" * 40},
            {"contract_id": "accepted"},
            {"contract_sha256": "0" * 64},
            {"fixed_constraints_sha256": None},
        ):
            with self.subTest(changes=changes):
                (self.root / LOCK).write_bytes((ROOT / LOCK).read_bytes())
                self.rewrite_lock(**changes)
                with self.assertRaises(ContractLockError):
                    check_contract(self.root)

    def test_missing_malformed_duplicate_and_non_utf8_inputs_fail_closed(self):
        for raw in (
            b"[]",
            b"{",
            b"{}",
            b"\xff",
            b'{"contract_id":"a","contract_id":"b"}',
        ):
            with self.subTest(raw=raw):
                (self.root / LOCK).write_bytes(raw)
                with self.assertRaises(ContractLockError):
                    check_contract(self.root)
        (self.root / LOCK).unlink()
        with self.assertRaises(ContractLockError):
            check_contract(self.root)

    def test_missing_repeated_or_reversed_markers_rejected(self):
        for raw in (b"", b"start end start", b"end start"):
            with self.subTest(raw=raw), self.assertRaises(ContractLockError):
                section_bytes(raw, b"start", b"end")

    def test_rehashing_changed_text_proves_no_acceptance(self):
        # A maintainer can change both files. Only a reviewer-authenticated
        # immutable commit/signature binds acceptance, never this checksum tool.
        path = self.root / DOCUMENT
        path.write_bytes(path.read_bytes().replace(b"GM06 B:", b"GM06 A:", 1))
        lock = json.loads((self.root / LOCK).read_text())
        identity = lock["contract_id"].encode()
        changed = section_bytes(
            path.read_bytes(),
            b"<!-- BEGIN " + identity + b" -->",
            b"<!-- END " + identity + b" -->",
            include_end=True,
        )
        self.rewrite_lock(contract_sha256=hashlib.sha256(changed).hexdigest())
        self.assertEqual(check_contract(self.root), lock["contract_id"])

    def test_normalized_newlines_do_not_hide_byte_drift(self):
        path = self.root / DOCUMENT
        path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        with self.assertRaises(ContractLockError):
            check_contract(self.root)
