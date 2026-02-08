"""Appointment tools — book, cancel, reschedule."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from hospital.data.hospital_data import APPOINTMENTS, DOCTORS
from hospital.enforcement.guardian import guardian_evaluate, format_trace


def appointment_book(
    doctor_id: str, department: str, date: str, time: str, reason: str, caller_id: str
) -> str:
    """Book an appointment with a doctor."""
    params = {"doctor_id": doctor_id, "department": department, "date": date, "time": time, "reason": reason}
    verdict = guardian_evaluate("appointment_book", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    doctor = DOCTORS.get(doctor_id)
    if not doctor:
        return json.dumps({"status": "ERROR", "reason": f"Doctor '{doctor_id}' not found"}, indent=2)

    if time not in doctor["available_slots"]:
        return json.dumps({
            "status": "ERROR",
            "reason": f"Time slot '{time}' not available for {doctor['name']}",
            "available_slots": doctor["available_slots"],
        }, indent=2)

    apt_id = f"APT{uuid.uuid4().hex[:3].upper()}"
    result = {
        "status": "APPOINTMENT_BOOKED",
        "appointment_id": apt_id,
        "doctor": doctor["name"],
        "department": doctor["department"],
        "date": date,
        "time": time,
        "reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def appointment_cancel(appointment_id: str, reason: str, caller_id: str) -> str:
    """Cancel an existing appointment."""
    params = {"appointment_id": appointment_id, "reason": reason}
    verdict = guardian_evaluate("appointment_cancel", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    apt = APPOINTMENTS.get(appointment_id)
    if not apt:
        return json.dumps({"status": "ERROR", "reason": f"Appointment '{appointment_id}' not found"}, indent=2)

    result = {
        "status": "APPOINTMENT_CANCELLED",
        "appointment_id": appointment_id,
        "doctor_id": apt["doctor_id"],
        "original_date": apt["date"],
        "original_time": apt["time"],
        "cancellation_reason": reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)


def appointment_reschedule(
    appointment_id: str, new_date: str, new_time: str, caller_id: str
) -> str:
    """Reschedule an existing appointment."""
    params = {"appointment_id": appointment_id, "new_date": new_date, "new_time": new_time}
    verdict = guardian_evaluate("appointment_reschedule", params, caller_id)

    if not verdict.allowed:
        return json.dumps({
            "status": "BLOCKED",
            "reason": verdict.reason,
            "suggestions": verdict.suggestions,
            "guardian_trace": format_trace(verdict),
        }, indent=2)

    apt = APPOINTMENTS.get(appointment_id)
    if not apt:
        return json.dumps({"status": "ERROR", "reason": f"Appointment '{appointment_id}' not found"}, indent=2)

    doctor = DOCTORS.get(apt["doctor_id"])
    if doctor and new_time not in doctor["available_slots"]:
        return json.dumps({
            "status": "ERROR",
            "reason": f"Time slot '{new_time}' not available for {doctor['name']}",
            "available_slots": doctor["available_slots"],
        }, indent=2)

    result = {
        "status": "APPOINTMENT_RESCHEDULED",
        "appointment_id": appointment_id,
        "doctor": doctor["name"] if doctor else apt["doctor_id"],
        "old_date": apt["date"],
        "old_time": apt["time"],
        "new_date": new_date,
        "new_time": new_time,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guardian_trace": format_trace(verdict),
    }
    return json.dumps(result, indent=2)
