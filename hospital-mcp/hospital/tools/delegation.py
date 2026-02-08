"""Delegation tools — grant and revoke HMAC-JWT delegation tokens [admin only]."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from hospital.enforcement.guardian import guardian_evaluate, format_trace
from hospital.enforcement.jwt_delegation import delegation_manager


def delegation_grant(
    delegate_id: str,
    role: str,
    allowed_tools: str,
    budget_limit: float,
    duration_days: float,
    caller_id: str,
) -> str:
    """Grant a delegation token to a user. Admin only.
    allowed_tools is a comma-separated list of tool names."""
    params = {
        "delegate_id": delegate_id,
        "role": role,
        "allowed_tools": allowed_tools,
        "budget_limit": budget_limit,
        "duration_days": duration_days,
    }
    verdict = guardian_evaluate("delegation_grant", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    tools_list = [t.strip() for t in allowed_tools.split(",")]
    delegation = delegation_manager.grant(
        delegate_id=delegate_id,
        grantor_id=caller_id,
        scope=tools_list,
        budget=budget_limit,
        duration_days=duration_days,
        phi_access=False,  # Never delegate PHI by default
    )

    result = {
        "status": "DELEGATION_GRANTED",
        "token_id": delegation.token_id,
        "delegate_id": delegate_id,
        "grantor_id": caller_id,
        "scope": tools_list,
        "budget_limit": budget_limit,
        "duration_days": duration_days,
        "phi_access": False,
        "jwt_token": delegation.token,
        "note": "Token is HMAC-SHA256 signed. PHI access is never delegated.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def delegation_revoke(delegation_id: str, caller_id: str) -> str:
    """Revoke an active delegation token. Admin only."""
    params = {"delegation_id": delegation_id}
    verdict = guardian_evaluate("delegation_revoke", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    revoked = delegation_manager.revoke(delegation_id)

    if not revoked:
        return json.dumps({
            "status": "ERROR",
            "reason": f"Delegation '{delegation_id}' not found",
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    result = {
        "status": "DELEGATION_REVOKED",
        "delegation_id": delegation_id,
        "revoked_by": caller_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
