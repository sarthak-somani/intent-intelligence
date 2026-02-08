"""Medical records tools — view, share, download [PHI protected]."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from hospital.data.hospital_data import PATIENTS
from hospital.enforcement.guardian import guardian_evaluate, format_trace


def records_view(patient_id: str, record_type: str, caller_id: str) -> str:
    """View patient medical records. PHI-protected — requires doctor or admin role."""
    params = {"patient_id": patient_id, "record_type": record_type}
    verdict = guardian_evaluate("records_view", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    patient = PATIENTS.get(patient_id)
    if not patient:
        return json.dumps({"status": "ERROR", "reason": f"Patient '{patient_id}' not found"}, indent=2)

    # Build record based on type
    record: dict = {"patient_id": patient_id, "patient_name": patient["name"]}
    if record_type == "summary":
        record.update({
            "age": patient["age"],
            "gender": patient["gender"],
            "blood_type": patient["blood_type"],
            "conditions": patient["conditions"],
            "medications": patient["medications"],
            "allergies": patient["allergies"],
            "primary_doctor": patient["doctor_id"],
        })
    elif record_type == "medications":
        record["medications"] = patient["medications"]
        record["allergies"] = patient["allergies"]
    elif record_type == "conditions":
        record["conditions"] = patient["conditions"]
    elif record_type == "allergies":
        record["allergies"] = patient["allergies"]
    else:
        record.update({
            "age": patient["age"],
            "gender": patient["gender"],
            "blood_type": patient["blood_type"],
            "conditions": patient["conditions"],
            "medications": patient["medications"],
            "allergies": patient["allergies"],
        })

    result = {
        "status": "RECORDS_RETRIEVED",
        "record_type": record_type,
        "record": record,
        "accessed_by": caller_id,
        "access_role": verdict.caller_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def records_share(patient_id: str, recipient_id: str, record_type: str, caller_id: str) -> str:
    """Share patient records with another healthcare provider. PHI-protected."""
    params = {"patient_id": patient_id, "recipient_id": recipient_id, "record_type": record_type}
    verdict = guardian_evaluate("records_share", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    patient = PATIENTS.get(patient_id)
    if not patient:
        return json.dumps({"status": "ERROR", "reason": f"Patient '{patient_id}' not found"}, indent=2)

    result = {
        "status": "RECORDS_SHARED",
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "record_type": record_type,
        "shared_with": recipient_id,
        "shared_by": caller_id,
        "share_role": verdict.caller_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def records_download(patient_id: str, record_type: str, format: str, caller_id: str) -> str:
    """Download patient records in specified format (pdf/csv/json). PHI-protected."""
    params = {"patient_id": patient_id, "record_type": record_type, "format": format}
    verdict = guardian_evaluate("records_download", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    patient = PATIENTS.get(patient_id)
    if not patient:
        return json.dumps({"status": "ERROR", "reason": f"Patient '{patient_id}' not found"}, indent=2)

    result = {
        "status": "DOWNLOAD_READY",
        "patient_id": patient_id,
        "patient_name": patient["name"],
        "record_type": record_type,
        "format": format,
        "file_name": f"{patient_id}_{record_type}.{format}",
        "file_size": "2.3 MB",
        "download_url": f"/api/records/{patient_id}/{record_type}.{format}",
        "expires_in": "30 minutes",
        "downloaded_by": caller_id,
        "download_role": verdict.caller_role,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
