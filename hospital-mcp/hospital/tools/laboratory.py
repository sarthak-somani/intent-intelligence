"""Laboratory tools — submit sample, get results, share results."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from hospital.data.hospital_data import LABS, LAB_REPORTS, DOCTORS
from hospital.enforcement.guardian import guardian_evaluate, format_trace


LAB_TEST_COSTS: dict[str, float] = {
    "HbA1c": 600.0,
    "Serum Creatinine": 350.0,
    "Complete Blood Count": 450.0,
    "INR / PT": 500.0,
    "Lipid Profile": 800.0,
    "Thyroid Panel": 900.0,
    "Liver Function Test": 700.0,
    "Kidney Function Test": 650.0,
    "Blood Glucose Fasting": 200.0,
    "Urine Routine": 150.0,
}


def lab_submit_sample(
    test_type: str, patient_id: str, doctor_id: str, urgency: str, caller_id: str
) -> str:
    """Submit a lab test order. Cost is tracked against budget. Delegatable."""
    cost = LAB_TEST_COSTS.get(test_type, 500.0)
    params = {"test_type": test_type, "patient_id": patient_id, "doctor_id": doctor_id, "urgency": urgency}
    verdict = guardian_evaluate("lab_submit_sample", params, caller_id, cost=cost)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    doctor = DOCTORS.get(doctor_id)
    lab_id = f"LAB{uuid.uuid4().hex[:3].upper()}"

    # Choose lab based on urgency
    lab = "SRL Diagnostics"
    turnaround = "24 hours"
    if urgency == "urgent":
        lab = "Metropolis Healthcare"
        turnaround = "12 hours"
    elif urgency == "stat":
        lab = "Metropolis Healthcare"
        turnaround = "4 hours"

    result = {
        "status": "SAMPLE_SUBMITTED",
        "lab_order_id": lab_id,
        "test_type": test_type,
        "patient_id": patient_id,
        "ordering_doctor": doctor["name"] if doctor else doctor_id,
        "lab": lab,
        "urgency": urgency,
        "estimated_turnaround": turnaround,
        "cost": cost,
        "budget_remaining": verdict.budget_remaining,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def lab_get_results(test_id: str, patient_id: str, caller_id: str) -> str:
    """Get lab test results. PHI-protected — requires doctor or admin role."""
    params = {"test_id": test_id, "patient_id": patient_id}
    verdict = guardian_evaluate("lab_get_results", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    report = LAB_REPORTS.get(test_id)
    if not report:
        return json.dumps({"status": "ERROR", "reason": f"Lab report '{test_id}' not found"}, indent=2)

    if report["patient_id"] != patient_id:
        return json.dumps({"status": "ERROR", "reason": "Patient ID does not match lab report"}, indent=2)

    result = {
        "status": "RESULTS_RETRIEVED",
        "test_id": test_id,
        "test_type": report["test_type"],
        "patient_id": patient_id,
        "result": report["result"],
        "normal_range": report["normal_range"],
        "interpretation": report["interpretation"],
        "lab": report["lab"],
        "report_date": report["date"],
        "report_status": report["status"],
        "accessed_by": caller_id,
        "access_role": verdict.caller_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def lab_share_results(test_id: str, doctor_id: str, caller_id: str) -> str:
    """Share lab results with another doctor. PHI-protected."""
    params = {"test_id": test_id, "doctor_id": doctor_id}
    verdict = guardian_evaluate("lab_share_results", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    report = LAB_REPORTS.get(test_id)
    if not report:
        return json.dumps({"status": "ERROR", "reason": f"Lab report '{test_id}' not found"}, indent=2)

    doctor = DOCTORS.get(doctor_id)

    result = {
        "status": "RESULTS_SHARED",
        "test_id": test_id,
        "test_type": report["test_type"],
        "shared_with": doctor["name"] if doctor else doctor_id,
        "shared_with_department": doctor["department"] if doctor else "Unknown",
        "shared_by": caller_id,
        "share_role": verdict.caller_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
