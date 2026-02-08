"""Negotiation tools — inter-agent permission requests and responses."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timezone

from hospital.enforcement.guardian import guardian_evaluate, format_trace
from hospital.enforcement.jwt_delegation import delegation_manager


# In-memory negotiation requests
_negotiations: dict[str, dict] = {}


def negotiation_request(
    target_role: str, tool_requested: str, reason: str, caller_id: str
) -> str:
    """Request elevated permission from another role. Used for inter-agent negotiation."""
    params = {"target_role": target_role, "tool_requested": tool_requested, "reason": reason}
    verdict = guardian_evaluate("negotiation_request", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    neg_id = f"NEG-{uuid.uuid4().hex[:6].upper()}"
    negotiation = {
        "negotiation_id": neg_id,
        "requester_id": caller_id,
        "requester_role": verdict.caller_role,
        "target_role": target_role,
        "tool_requested": tool_requested,
        "reason": reason,
        "status": "PENDING",
        "created_at": time.time(),
        "expires_at": time.time() + 300,  # 5-minute window to respond
    }
    _negotiations[neg_id] = negotiation

    result = {
        "status": "NEGOTIATION_REQUESTED",
        "negotiation_id": neg_id,
        "requester": caller_id,
        "requester_role": verdict.caller_role,
        "target_role": target_role,
        "tool_requested": tool_requested,
        "reason": reason,
        "response_deadline": "5 minutes",
        "note": f"An agent with '{target_role}' role must call negotiation_respond to approve/deny",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def negotiation_respond(
    negotiation_id: str, decision: str, duration_minutes: int, caller_id: str
) -> str:
    """Respond to a negotiation request. Grant or deny temporary access.
    decision: 'approve' or 'deny'. duration_minutes: how long the temporary delegation lasts."""
    params = {"negotiation_id": negotiation_id, "decision": decision, "duration_minutes": duration_minutes}
    verdict = guardian_evaluate("negotiation_respond", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    neg = _negotiations.get(negotiation_id)
    if not neg:
        return json.dumps({"status": "ERROR", "reason": f"Negotiation '{negotiation_id}' not found"}, indent=2)

    if neg["status"] != "PENDING":
        return json.dumps({"status": "ERROR", "reason": f"Negotiation already {neg['status']}"}, indent=2)

    if time.time() > neg["expires_at"]:
        neg["status"] = "EXPIRED"
        return json.dumps({"status": "ERROR", "reason": "Negotiation request has expired"}, indent=2)

    if decision == "approve":
        neg["status"] = "APPROVED"
        # Create temporary delegation
        duration_days = duration_minutes / (60 * 24)
        delegation = delegation_manager.grant(
            delegate_id=neg["requester_id"],
            grantor_id=caller_id,
            scope=[neg["tool_requested"]],
            budget=1000.0,  # Default budget for negotiated access
            duration_days=duration_days,
            phi_access=False,
        )

        result = {
            "status": "NEGOTIATION_APPROVED",
            "negotiation_id": negotiation_id,
            "approved_by": caller_id,
            "requester": neg["requester_id"],
            "tool_granted": neg["tool_requested"],
            "duration_minutes": duration_minutes,
            "delegation_token_id": delegation.token_id,
            "note": f"Temporary access granted for {duration_minutes} minutes",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "guardian_trace": format_trace(verdict),
        }
    else:
        neg["status"] = "DENIED"
        result = {
            "status": "NEGOTIATION_DENIED",
            "negotiation_id": negotiation_id,
            "denied_by": caller_id,
            "requester": neg["requester_id"],
            "tool_requested": neg["tool_requested"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "guardian_trace": format_trace(verdict),
        }

    return json.dumps(result, indent=2)
