"""Role resolution: caller_id → role."""

from __future__ import annotations

from hospital.config import CALLER_ROLES


def resolve_role(caller_id: str) -> str:
    """Resolve a caller_id to its role. Defaults to 'unknown'."""
    return CALLER_ROLES.get(caller_id.lower().strip(), "unknown")
