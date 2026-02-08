"""Emergency tools — bypass all Guardian checks."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from hospital.data.hospital_data import EMERGENCY_CONTACTS
from hospital.enforcement.guardian import guardian_evaluate, format_trace


def emergency_ambulance(location: str, severity: str, caller_id: str) -> str:
    """Dispatch an ambulance to the specified location. Severity: critical/serious/moderate.
    This is an EMERGENCY tool — bypasses all Guardian safety checks."""
    params = {"location": location, "severity": severity}
    verdict = guardian_evaluate("emergency_ambulance", params, caller_id)

    dispatch_id = f"AMB-{uuid.uuid4().hex[:6].upper()}"
    ambulance_info = next((c for c in EMERGENCY_CONTACTS if c["service"] == "Ambulance"), {})

    result = {
        "status": "DISPATCHED",
        "dispatch_id": dispatch_id,
        "location": location,
        "severity": severity,
        "ambulance_number": ambulance_info.get("number", "108"),
        "estimated_response": ambulance_info.get("response_time", "8-12 minutes"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def emergency_notify(message: str, caller_id: str) -> str:
    """Send emergency notification to all emergency contacts.
    This is an EMERGENCY tool — bypasses all Guardian safety checks."""
    params = {"message": message}
    verdict = guardian_evaluate("emergency_notify", params, caller_id)

    result = {
        "status": "NOTIFICATIONS_SENT",
        "message": message,
        "contacts_notified": [
            {"service": c["service"], "number": c["number"]}
            for c in EMERGENCY_CONTACTS
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def emergency_location(caller_id: str) -> str:
    """Share caller's GPS location with emergency services.
    This is an EMERGENCY tool — bypasses all Guardian safety checks."""
    params = {}
    verdict = guardian_evaluate("emergency_location", params, caller_id)

    result = {
        "status": "LOCATION_SHARED",
        "shared_with": ["Ambulance Dispatch (108)", "Hospital Emergency"],
        "gps_coordinates": "19.0760° N, 72.8777° E",  # Mumbai coordinates (mock)
        "accuracy": "±10 meters",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
