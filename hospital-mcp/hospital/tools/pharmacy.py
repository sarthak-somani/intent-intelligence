"""Pharmacy tools — order, refill, interaction check."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from hospital.data.hospital_data import (
    APPROVED_PHARMACIES,
    DRUG_INTERACTIONS,
    MEDICATION_CATALOG,
    PRESCRIPTIONS,
)
from hospital.enforcement.guardian import guardian_evaluate, format_trace


def pharmacy_order(medication: str, quantity: int, pharmacy: str, caller_id: str) -> str:
    """Order medication from an approved pharmacy. Cost is tracked against caller's budget."""
    med_info = MEDICATION_CATALOG.get(medication)
    cost = med_info["unit_price"] * quantity if med_info else quantity * 10.0

    params = {"medication": medication, "quantity": quantity, "pharmacy": pharmacy}
    verdict = guardian_evaluate("pharmacy_order", params, caller_id, cost=cost)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    order_id = f"ORD-{uuid.uuid4().hex[:6].upper()}"
    result = {
        "status": "ORDER_PLACED",
        "order_id": order_id,
        "medication": medication,
        "quantity": quantity,
        "pharmacy": pharmacy,
        "unit_price": med_info["unit_price"] if med_info else 10.0,
        "total_cost": cost,
        "category": med_info["category"] if med_info else "Unknown",
        "controlled": med_info["controlled"] if med_info else False,
        "budget_remaining": verdict.budget_remaining,
        "estimated_delivery": "2-4 hours",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def pharmacy_refill(prescription_id: str, pharmacy: str, caller_id: str) -> str:
    """Refill an existing prescription at an approved pharmacy."""
    rx = PRESCRIPTIONS.get(prescription_id)
    if not rx:
        return json.dumps({"status": "ERROR", "reason": f"Prescription '{prescription_id}' not found"}, indent=2)

    cost = rx["cost_per_refill"]
    params = {"prescription_id": prescription_id, "pharmacy": pharmacy}
    verdict = guardian_evaluate("pharmacy_refill", params, caller_id, cost=cost)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    if rx["refills_remaining"] <= 0:
        return json.dumps({
            "status": "ERROR",
            "reason": f"No refills remaining for {rx['medication']}. Contact prescribing doctor.",
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    result = {
        "status": "REFILL_ORDERED",
        "prescription_id": prescription_id,
        "medication": rx["medication"],
        "dosage": rx["dosage"],
        "quantity": rx["quantity"],
        "pharmacy": pharmacy,
        "cost": cost,
        "refills_remaining": rx["refills_remaining"] - 1,
        "budget_remaining": verdict.budget_remaining,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def pharmacy_check_interactions(drug_a: str, drug_b: str, caller_id: str) -> str:
    """Check for drug interactions between two medications. Read-only — no cost."""
    params = {"drug_a": drug_a, "drug_b": drug_b}
    verdict = guardian_evaluate("pharmacy_check_interactions", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    # Search interactions (case-insensitive, bidirectional)
    da, db = drug_a.lower(), drug_b.lower()
    found = []
    for interaction in DRUG_INTERACTIONS:
        ia, ib = interaction["drug_a"].lower(), interaction["drug_b"].lower()
        if (da in ia or ia in da) and (db in ib or ib in db):
            found.append(interaction)
        elif (da in ib or ib in da) and (db in ia or ia in db):
            found.append(interaction)

    result = {
        "status": "INTERACTION_CHECK_COMPLETE",
        "drug_a": drug_a,
        "drug_b": drug_b,
        "interactions_found": len(found),
        "interactions": found,
        "recommendation": found[0]["description"] if found else "No known interactions found",
        "severity": found[0]["severity"] if found else "NONE",
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
