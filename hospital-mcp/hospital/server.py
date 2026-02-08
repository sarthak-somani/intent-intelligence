"""FastMCP server assembly — registers all 21 tools, resources, and prompts."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from hospital.data.hospital_data import (
    APPROVED_PHARMACIES,
    DOCTORS,
    EMERGENCY_CONTACTS,
    PATIENTS,
)
from hospital.config import CALLER_ROLES, ROLE_ALLOWED_TOOLS
from hospital.tools import emergency, appointments, records, laboratory, delegation, audit, negotiation
import hospital.tools.pharmacy as pharmacy_mod

# ── Create FastMCP instance ───────────────────────────────────────────
mcp = FastMCP(
    "Hospital Guardian",
    instructions=(
        "Hospital Guardian MCP Server — 21 tools across 8 categories with a 9-step "
        "Guardian safety pipeline, SHA-256 Merkle audit ledger, and HMAC-JWT delegation. "
        "Every tool call returns a full Guardian trace showing each enforcement step. "
        "Use caller_id to identify yourself (e.g., 'samarth banodia' for admin, 'samarth' for doctor, "
        "'fukishi seichi' for nurse, 'arinjay' for pharmacist, 'bot' for caretaker). "
        "Emergency tools bypass all checks. PHI tools require doctor/admin role."
    ),
    # Allow ArmorIQ platform to connect (disable DNS rebinding protection for cross-origin MCP)
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)

# ── Register Tools ────────────────────────────────────────────────────

# Emergency (3)
@mcp.tool()
def emergency_ambulance(location: str, severity: str, caller_id: str) -> str:
    """Dispatch an ambulance. Severity: critical/serious/moderate. EMERGENCY — bypasses all Guardian checks."""
    return emergency.emergency_ambulance(location, severity, caller_id)

@mcp.tool()
def emergency_notify(message: str, caller_id: str) -> str:
    """Send emergency notification to all contacts. EMERGENCY — bypasses all Guardian checks."""
    return emergency.emergency_notify(message, caller_id)

@mcp.tool()
def emergency_location(caller_id: str) -> str:
    """Share GPS location with emergency services. EMERGENCY — bypasses all Guardian checks."""
    return emergency.emergency_location(caller_id)

# Pharmacy (3)
@mcp.tool()
def pharmacy_order(medication: str, quantity: int, pharmacy: str, caller_id: str) -> str:
    """Order medication from an approved pharmacy. Cost tracked against budget. Approved pharmacies: MedPlus, Apollo Pharmacy, Wellness Forever, 1mg, PharmEasy."""
    return pharmacy_mod.pharmacy_order(medication, quantity, pharmacy, caller_id)

@mcp.tool()
def pharmacy_refill(prescription_id: str, pharmacy: str, caller_id: str) -> str:
    """Refill existing prescription. Prescriptions: RX001 (Metformin), RX002 (Amlodipine), RX003 (Ferrous Sulfate), RX004 (Warfarin)."""
    return pharmacy_mod.pharmacy_refill(prescription_id, pharmacy, caller_id)

@mcp.tool()
def pharmacy_check_interactions(drug_a: str, drug_b: str, caller_id: str) -> str:
    """Check drug interactions between two medications. Read-only, no cost."""
    return pharmacy_mod.pharmacy_check_interactions(drug_a, drug_b, caller_id)

# Appointments (3)
@mcp.tool()
def appointment_book(doctor_id: str, department: str, date: str, time: str, reason: str, caller_id: str) -> str:
    """Book appointment. Doctors: DOC001 (Cardiology), DOC002 (Ortho), DOC003 (Neuro), DOC004 (General), DOC005 (Pathology), DOC006 (Emergency)."""
    return appointments.appointment_book(doctor_id, department, date, time, reason, caller_id)

@mcp.tool()
def appointment_cancel(appointment_id: str, reason: str, caller_id: str) -> str:
    """Cancel an existing appointment."""
    return appointments.appointment_cancel(appointment_id, reason, caller_id)

@mcp.tool()
def appointment_reschedule(appointment_id: str, new_date: str, new_time: str, caller_id: str) -> str:
    """Reschedule an existing appointment."""
    return appointments.appointment_reschedule(appointment_id, new_date, new_time, caller_id)

# Records (3) [PHI]
@mcp.tool()
def records_view(patient_id: str, record_type: str, caller_id: str) -> str:
    """View patient records. PHI-protected. record_type: summary/medications/conditions/allergies. Patients: P001, P002, P003."""
    return records.records_view(patient_id, record_type, caller_id)

@mcp.tool()
def records_share(patient_id: str, recipient_id: str, record_type: str, caller_id: str) -> str:
    """Share patient records with another provider. PHI-protected."""
    return records.records_share(patient_id, recipient_id, record_type, caller_id)

@mcp.tool()
def records_download(patient_id: str, record_type: str, format: str, caller_id: str) -> str:
    """Download patient records. PHI-protected. format: pdf/csv/json."""
    return records.records_download(patient_id, record_type, format, caller_id)

# Laboratory (3)
@mcp.tool()
def lab_submit_sample(test_type: str, patient_id: str, doctor_id: str, urgency: str, caller_id: str) -> str:
    """Submit lab test order. urgency: routine/urgent/stat. Cost tracked. Tests: HbA1c, Complete Blood Count, Lipid Profile, etc."""
    return laboratory.lab_submit_sample(test_type, patient_id, doctor_id, urgency, caller_id)

@mcp.tool()
def lab_get_results(test_id: str, patient_id: str, caller_id: str) -> str:
    """Get lab results. PHI-protected. Reports: LAB001-LAB005."""
    return laboratory.lab_get_results(test_id, patient_id, caller_id)

@mcp.tool()
def lab_share_results(test_id: str, doctor_id: str, caller_id: str) -> str:
    """Share lab results with another doctor. PHI-protected."""
    return laboratory.lab_share_results(test_id, doctor_id, caller_id)

# Delegation (2) [admin only]
@mcp.tool()
def delegation_grant(delegate_id: str, role: str, allowed_tools: str, budget_limit: float, duration_days: float, caller_id: str) -> str:
    """Grant delegation token. Admin only. allowed_tools: comma-separated tool names. PHI access is never delegated."""
    return delegation.delegation_grant(delegate_id, role, allowed_tools, budget_limit, duration_days, caller_id)

@mcp.tool()
def delegation_revoke(delegation_id: str, caller_id: str) -> str:
    """Revoke a delegation token. Admin only."""
    return delegation.delegation_revoke(delegation_id, caller_id)

# Audit (2) [admin only]
@mcp.tool()
def audit_view(count: int, filter_verdict: str, caller_id: str) -> str:
    """View recent audit entries with Guardian traces. Admin only. filter_verdict: all/ALLOW/BLOCK/EMERGENCY_BYPASS."""
    return audit.audit_view(count, filter_verdict, caller_id)

@mcp.tool()
def audit_verify(caller_id: str) -> str:
    """Verify SHA-256 hash chain and Merkle tree integrity. Admin only."""
    return audit.audit_verify(caller_id)

# Negotiation (2) [inter-agent]
@mcp.tool()
def negotiation_request(target_role: str, tool_requested: str, reason: str, caller_id: str) -> str:
    """Request elevated permission from another role. Inter-agent negotiation."""
    return negotiation.negotiation_request(target_role, tool_requested, reason, caller_id)

@mcp.tool()
def negotiation_respond(negotiation_id: str, decision: str, duration_minutes: int, caller_id: str) -> str:
    """Respond to negotiation request. decision: approve/deny. Creates temporary delegation if approved."""
    return negotiation.negotiation_respond(negotiation_id, decision, duration_minutes, caller_id)


# ── Resources ─────────────────────────────────────────────────────────

@mcp.resource("hospital://info")
def hospital_info() -> str:
    """Hospital Guardian system information."""
    import json
    return json.dumps({
        "name": "Hospital Guardian MCP Server",
        "version": "1.0.0",
        "tools": 21,
        "categories": ["Emergency", "Pharmacy", "Appointments", "Records", "Laboratory", "Delegation", "Audit", "Negotiation"],
        "enforcement": "9-step Guardian Pipeline",
        "audit": "SHA-256 Hash Chain + Merkle Tree",
        "delegation": "HMAC-SHA256 JWT Tokens",
        "roles": ["admin", "doctor", "nurse", "pharmacist", "caretaker", "unknown"],
    }, indent=2)

@mcp.resource("hospital://patients")
def patient_list() -> str:
    """List of patients in the hospital system."""
    import json
    return json.dumps({
        pid: {"name": p["name"], "age": p["age"], "conditions": p["conditions"]}
        for pid, p in PATIENTS.items()
    }, indent=2)

@mcp.resource("hospital://doctors")
def doctor_list() -> str:
    """List of doctors and their departments."""
    import json
    return json.dumps({
        did: {"name": d["name"], "department": d["department"], "available_slots": d["available_slots"]}
        for did, d in DOCTORS.items()
    }, indent=2)

@mcp.resource("hospital://roles")
def role_info() -> str:
    """Role hierarchy and permissions."""
    import json
    return json.dumps({
        "caller_roles": CALLER_ROLES,
        "role_permissions": {role: sorted(tools) for role, tools in ROLE_ALLOWED_TOOLS.items()},
    }, indent=2)


# ── Prompts ───────────────────────────────────────────────────────────

@mcp.prompt()
def hospital_system_prompt(caller_id: str = "unknown") -> str:
    """System prompt for the Hospital Guardian assistant."""
    from hospital.enforcement.roles import resolve_role
    role = resolve_role(caller_id)
    allowed = sorted(ROLE_ALLOWED_TOOLS.get(role, set()))

    return f"""You are the Hospital Guardian AI Assistant, operating within a secure MCP server.

Current caller: {caller_id} (role: {role})
Allowed tools for this role: {', '.join(allowed) if allowed else 'Emergency tools only'}

Key rules:
- Every tool call passes through a 9-step Guardian safety pipeline
- Emergency tools (ambulance, notify, location) bypass all checks — use in genuine emergencies
- PHI (Protected Health Information) is restricted to doctors and admins
- Budget is tracked for cost-bearing tools (pharmacy orders, lab tests)
- Delegation tokens allow scoped, time-limited access sharing
- All actions are logged to a SHA-256 hash-chained Merkle audit ledger
- If a tool is blocked, the response includes suggestions for alternative actions

Available patients: P001 (Rajesh Kumar), P002 (Anita Desai), P003 (Mohammed Hussain)
Available doctors: DOC001-DOC006
Approved pharmacies: {', '.join(APPROVED_PHARMACIES)}

Always include the caller_id parameter in every tool call."""


# ── Stdio entry point ────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run(transport="stdio")
