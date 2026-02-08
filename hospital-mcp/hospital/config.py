"""Configuration: roles, budgets, policies, constants."""

from __future__ import annotations

import os

# ── Server secret for JWT signing ─────────────────────────────────────
SERVER_SECRET = os.environ.get("HOSPITAL_JWT_SECRET", "hospital-guardian-secret-key-2025")

# ── Role Hierarchy ────────────────────────────────────────────────────
ROLES = ["admin", "doctor", "nurse", "pharmacist", "caretaker", "unknown"]

# caller_id → role mapping
# Team members (ArmorIQ platform accounts)
# Also includes hospital persona aliases for demo flexibility
CALLER_ROLES: dict[str, str] = {
    # ── Team members ──
    "samarth banodia": "admin",
    "samarth_banodia": "admin",
    "samarth banodia (admin)": "admin",
    "samarth": "doctor",
    "samarth (doctor)": "doctor",
    "fukishi seichi": "nurse",
    "fukishi_seichi": "nurse",
    "fukishi": "nurse",
    "arinjay": "pharmacist",
    "bot": "caretaker",
    # ── Hospital persona aliases (for demo narration) ──
    "dr_sharma": "admin",
    "dr_patel": "doctor",
    "nurse_priya": "nurse",
    "pharmacist_ravi": "pharmacist",
    "caretaker_amit": "caretaker",
}

# ── Budget Limits (INR) ──────────────────────────────────────────────
DEFAULT_BUDGET_LIMITS: dict[str, float] = {
    "admin": float("inf"),
    "doctor": 50000.0,
    "nurse": 5000.0,
    "pharmacist": 20000.0,
    "caretaker": 2000.0,
    "unknown": 0.0,
}

# ── Tool Classifications ─────────────────────────────────────────────
EMERGENCY_TOOLS = {"emergency_ambulance", "emergency_notify", "emergency_location"}

PHARMACY_TOOLS = {"pharmacy_order", "pharmacy_refill", "pharmacy_check_interactions"}

APPOINTMENT_TOOLS = {"appointment_book", "appointment_cancel", "appointment_reschedule"}

RECORDS_TOOLS = {"records_view", "records_share", "records_download"}

LAB_TOOLS = {"lab_submit_sample", "lab_get_results", "lab_share_results"}

DELEGATION_TOOLS = {"delegation_grant", "delegation_revoke"}

AUDIT_TOOLS = {"audit_view", "audit_verify"}

NEGOTIATION_TOOLS = {"negotiation_request", "negotiation_respond"}

# Tools that access Protected Health Information
PHI_TOOLS = {"records_view", "records_share", "records_download", "lab_get_results", "lab_share_results"}

# Tools that incur cost
COST_TOOLS = {"pharmacy_order", "pharmacy_refill", "lab_submit_sample"}

# Admin-only tools
ADMIN_ONLY_TOOLS = DELEGATION_TOOLS | AUDIT_TOOLS

ALL_TOOLS = (
    EMERGENCY_TOOLS | PHARMACY_TOOLS | APPOINTMENT_TOOLS |
    RECORDS_TOOLS | LAB_TOOLS | DELEGATION_TOOLS |
    AUDIT_TOOLS | NEGOTIATION_TOOLS
)

# ── Role → Allowed Tools ─────────────────────────────────────────────
ROLE_ALLOWED_TOOLS: dict[str, set[str]] = {
    "admin": ALL_TOOLS,
    "doctor": RECORDS_TOOLS | LAB_TOOLS | PHARMACY_TOOLS | APPOINTMENT_TOOLS | NEGOTIATION_TOOLS | EMERGENCY_TOOLS,
    "nurse": {"records_view", "pharmacy_check_interactions"} | APPOINTMENT_TOOLS | NEGOTIATION_TOOLS | EMERGENCY_TOOLS,
    "pharmacist": PHARMACY_TOOLS | NEGOTIATION_TOOLS | EMERGENCY_TOOLS,
    "caretaker": {"pharmacy_order", "pharmacy_refill", "appointment_book", "appointment_reschedule"} | NEGOTIATION_TOOLS | EMERGENCY_TOOLS,
    "unknown": EMERGENCY_TOOLS,
}

# ── Approved Pharmacy Names ──────────────────────────────────────────
from hospital.data.hospital_data import APPROVED_PHARMACIES  # noqa: E402
