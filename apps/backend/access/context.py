"""Typed context identifiers; an identifier is never authority."""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class ResolvedContext:
    kind: str
    subject_uuid: UUID


def resolve_context(kind, identifier, *, personal_user_id=None):
    if kind not in ("personal", "ngo"):
        raise ValueError("unsupported context")
    value = UUID(str(identifier))
    if kind == "personal" and value != personal_user_id:
        raise ValueError("personal owner mismatch")
    return ResolvedContext(kind, value)
