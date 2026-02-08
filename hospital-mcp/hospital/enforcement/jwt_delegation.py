"""HMAC-SHA256 signed JWT delegation tokens — hand-rolled for demo clarity."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field

from hospital.config import SERVER_SECRET


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(header_b64: str, payload_b64: str, secret: str) -> str:
    msg = f"{header_b64}.{payload_b64}".encode()
    sig = hmac.new(secret.encode(), msg, hashlib.sha256).digest()
    return _b64url_encode(sig)


def create_token(payload: dict, secret: str = SERVER_SECRET) -> str:
    """Create a JWT token with HMAC-SHA256 signature."""
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signature = _sign(header_b64, payload_b64, secret)
    return f"{header_b64}.{payload_b64}.{signature}"


def verify_token(token: str, secret: str = SERVER_SECRET) -> dict | None:
    """Verify a JWT token. Returns claims dict or None if invalid/expired."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        expected_sig = _sign(header_b64, payload_b64, secret)
        if not hmac.compare_digest(sig_b64, expected_sig):
            return None
        claims = json.loads(_b64url_decode(payload_b64))
        if "exp" in claims and claims["exp"] < time.time():
            return None
        return claims
    except Exception:
        return None


@dataclass
class Delegation:
    token_id: str
    token: str
    delegate_id: str
    grantor_id: str
    scope: list[str]
    budget: float
    budget_spent: float = 0.0
    phi_access: bool = False
    expires_at: float = 0.0
    revoked: bool = False


class DelegationManager:
    """Manages delegation tokens: grant, revoke, lookup."""

    def __init__(self) -> None:
        self._delegations: dict[str, Delegation] = {}

    def grant(
        self,
        delegate_id: str,
        grantor_id: str,
        scope: list[str],
        budget: float,
        duration_days: float = 7.0,
        phi_access: bool = False,
    ) -> Delegation:
        """Create and store a delegation token."""
        now = time.time()
        token_id = f"del_{uuid.uuid4().hex[:8]}"
        payload = {
            "sub": delegate_id,
            "iss": grantor_id,
            "iat": int(now),
            "exp": int(now + duration_days * 86400),
            "jti": token_id,
            "scope": scope,
            "budget": budget,
            "phi_access": phi_access,
        }
        token = create_token(payload)
        delegation = Delegation(
            token_id=token_id,
            token=token,
            delegate_id=delegate_id,
            grantor_id=grantor_id,
            scope=scope,
            budget=budget,
            phi_access=phi_access,
            expires_at=now + duration_days * 86400,
        )
        self._delegations[token_id] = delegation
        return delegation

    def revoke(self, token_id: str) -> bool:
        """Revoke a delegation token."""
        if token_id in self._delegations:
            self._delegations[token_id].revoked = True
            return True
        return False

    def find_active(self, delegate_id: str) -> Delegation | None:
        """Find an active (non-revoked, non-expired) delegation for a delegate."""
        now = time.time()
        for d in self._delegations.values():
            if (
                d.delegate_id == delegate_id
                and not d.revoked
                and d.expires_at > now
            ):
                return d
        return None

    def find_by_id(self, token_id: str) -> Delegation | None:
        """Find a delegation by its token ID."""
        return self._delegations.get(token_id)

    def list_active(self) -> list[dict]:
        """List all active delegations."""
        now = time.time()
        return [
            {
                "token_id": d.token_id,
                "delegate_id": d.delegate_id,
                "grantor_id": d.grantor_id,
                "scope": d.scope,
                "budget": d.budget,
                "budget_spent": d.budget_spent,
                "budget_remaining": d.budget - d.budget_spent,
                "phi_access": d.phi_access,
                "expires_at": d.expires_at,
                "revoked": d.revoked,
                "active": not d.revoked and d.expires_at > now,
            }
            for d in self._delegations.values()
        ]

    def spend(self, delegation: Delegation, amount: float) -> bool:
        """Record spending against a delegation's budget. Returns True if within budget."""
        if delegation.budget_spent + amount > delegation.budget:
            return False
        delegation.budget_spent += amount
        return True


# ── Singleton ─────────────────────────────────────────────────────────
delegation_manager = DelegationManager()
