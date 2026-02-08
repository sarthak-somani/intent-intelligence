"""Audit tools — view logs and verify chain integrity [admin only]."""

from __future__ import annotations

import json

from hospital.enforcement.guardian import guardian_evaluate, format_trace
from hospital.enforcement.merkle_ledger import ledger


def audit_view(count: int, filter_verdict: str, caller_id: str) -> str:
    """View recent audit entries with Guardian trace. Admin only.
    filter_verdict: 'all', 'ALLOW', 'BLOCK', or 'EMERGENCY_BYPASS'."""
    params = {"count": count, "filter_verdict": filter_verdict}
    verdict = guardian_evaluate("audit_view", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    fv = None if filter_verdict == "all" else filter_verdict
    entries = ledger.get_recent(count=count, filter_verdict=fv)

    result = {
        "status": "AUDIT_RETRIEVED",
        "total_entries": len(ledger.entries),
        "returned": len(entries),
        "filter": filter_verdict,
        "entries": entries,
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2, default=str)


def audit_verify(caller_id: str) -> str:
    """Verify the integrity of the SHA-256 hash chain and Merkle tree. Admin only."""
    params = {}
    verdict = guardian_evaluate("audit_verify", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    verification = ledger.verify_chain()

    result = {
        "status": "VERIFICATION_COMPLETE",
        "entries_verified": verification["entries"],
        "hash_chain": verification["chain"],
        "merkle_roots_checked": verification["merkle_roots_checked"],
        "merkle_roots_valid": verification.get("merkle_roots_valid", 0),
        "integrity": "INTACT" if verification["valid"] else "COMPROMISED",
        "errors": verification.get("errors", []),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
