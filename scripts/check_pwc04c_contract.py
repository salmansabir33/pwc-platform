"""Offline review-byte integrity only; never an approval or runtime gate.

No imports from Django/auth, no credentials, network, writes or privileged actions.
Reviewers must separately authenticate acceptance of the immutable Git commit.
"""

import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = Path("docs/reviews/PWC-04C-IMPLEMENTATION-AUTHORIZATION-PACKAGE-v1.0.md")
LOCK = Path("docs/reviews/PWC-04C-fixture-contract-lock.json")
BASELINE = "d7c5f977e0ca7c4f23d04a00ccb576fa1fb65a80"
FIXED_START = b"### 11.1 Settled constraints"
FIXED_END = b"### 11.2 Decision register"
FIELDS = {
    "contract_id",
    "baseline_commit",
    "document",
    "contract_sha256",
    "fixed_constraints_sha256",
}


class ContractLockError(ValueError):
    pass


def _fail():
    raise ContractLockError(
        "Fixture review contract integrity mismatch; not an approval check"
    ) from None


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            _fail()
        result[key] = value
    return result


def section_bytes(raw, start, end, *, include_end=False):
    """Exact bytes, not Markdown normalization; reject missing/ambiguous markers."""
    if raw.count(start) != 1 or raw.count(end) != 1:
        _fail()
    first, last = raw.index(start), raw.index(end)
    if first >= last:
        _fail()
    return raw[first : last + (len(end) if include_end else 0)]


def check_contract(root=ROOT):
    try:
        lock = json.loads(
            (root / LOCK).read_text(encoding="utf-8"), object_pairs_hook=_unique
        )
        if type(lock) is not dict or set(lock) != FIELDS:
            _fail()
        if (
            type(lock["contract_id"]) is not str
            or not re.fullmatch(r"C04C-FIXTURE-\d{8}\.[1-9]\d*", lock["contract_id"])
            or lock["baseline_commit"] != BASELINE
            or lock["document"] != DOCUMENT.as_posix()
        ):
            _fail()
        raw = (root / DOCUMENT).read_bytes()
        # Invalid encodings cannot masquerade as a reviewable UTF-8 document.
        raw.decode("utf-8")
        identity = lock["contract_id"].encode("ascii")
        contract = section_bytes(
            raw,
            b"<!-- BEGIN " + identity + b" -->",
            b"<!-- END " + identity + b" -->",
            include_end=True,
        )
        fixed = section_bytes(raw, FIXED_START, FIXED_END)
        for data, field in (
            (contract, "contract_sha256"),
            (fixed, "fixed_constraints_sha256"),
        ):
            digest = lock[field]
            if (
                type(digest) is not str
                or not re.fullmatch(r"[a-f0-9]{64}", digest)
                or hashlib.sha256(data).hexdigest() != digest
            ):
                _fail()
    except (OSError, UnicodeError, ValueError, TypeError, KeyError):
        _fail()
    return lock["contract_id"]


def main():
    try:
        identity = check_contract()
    except ContractLockError as error:
        print(str(error), file=sys.stderr)
        return 1
    print(
        f"{identity}: review bytes match; NOT technical acceptance or runtime authorization"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
