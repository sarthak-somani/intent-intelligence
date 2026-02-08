"""
Hospital Guardian — Enhanced Interactive Demo Dashboard
Run: python demo.py
Opens a web dashboard at http://localhost:5000

Features:
- 21 MCP tools with 9-step Guardian pipeline visualization
- ArmorIQ Intent Intelligence SDK integration
- Audit timeline, delegation panel, budget tracker
- Live charts and animated pipeline trace
"""

from __future__ import annotations

# ── Fix Windows encoding for ArmorIQ SDK emoji output ─────────────────
import os
import sys

os.environ["PYTHONIOENCODING"] = "utf-8"
if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import json
import time
import traceback
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
from dataclasses import asdict

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

from hospital.enforcement.guardian import guardian_evaluate, format_trace, _budgets
from hospital.enforcement.merkle_ledger import ledger
from hospital.enforcement.jwt_delegation import delegation_manager
from hospital.config import (
    CALLER_ROLES, DEFAULT_BUDGET_LIMITS, ROLE_ALLOWED_TOOLS,
    EMERGENCY_TOOLS, PHI_TOOLS, COST_TOOLS, ADMIN_ONLY_TOOLS,
)
from hospital.tools import emergency, appointments, records, laboratory, audit, negotiation
from hospital.tools import pharmacy as pharmacy_mod
from hospital.tools.delegation import delegation_grant, delegation_revoke

# ── ArmorIQ SDK (optional — graceful fallback) ───────────────────────
ARMORIQ_ENABLED = False
armoriq_client = None
armoriq_log: list[dict] = []  # log of all SDK interactions

ARMORIQ_API_KEY = "ak_live_0104000fd60af9ddfe4b1fd68aa547e54625a92c9155bae243a67c29160b8197"
ARMORIQ_MCP_NAME = "hospital"
ARMORIQ_USER_ID = "samarthbanodia1337@gmail.com"
ARMORIQ_AGENT_ID = "hospital_guardian_v1"

try:
    from armoriq_sdk import ArmorIQClient
    armoriq_client = ArmorIQClient(
        api_key=ARMORIQ_API_KEY,
        user_id=ARMORIQ_USER_ID,
        agent_id=ARMORIQ_AGENT_ID,
    )
    ARMORIQ_ENABLED = True
    print("[ArmorIQ] SDK initialized successfully")
except Exception as e:
    print(f"[ArmorIQ] SDK not available: {e}")
    print("[ArmorIQ] Dashboard will work without Intent Intelligence")

# ── Tool dispatcher ───────────────────────────────────────────────────
TOOL_DISPATCH = {
    "emergency_ambulance": lambda p: emergency.emergency_ambulance(p["location"], p["severity"], p["caller_id"]),
    "emergency_notify": lambda p: emergency.emergency_notify(p["message"], p["caller_id"]),
    "emergency_location": lambda p: emergency.emergency_location(p["caller_id"]),
    "pharmacy_order": lambda p: pharmacy_mod.pharmacy_order(p["medication"], int(p["quantity"]), p["pharmacy"], p["caller_id"]),
    "pharmacy_refill": lambda p: pharmacy_mod.pharmacy_refill(p["prescription_id"], p["pharmacy"], p["caller_id"]),
    "pharmacy_check_interactions": lambda p: pharmacy_mod.pharmacy_check_interactions(p["drug_a"], p["drug_b"], p["caller_id"]),
    "appointment_book": lambda p: appointments.appointment_book(p["doctor_id"], p["department"], p["date"], p["time"], p["reason"], p["caller_id"]),
    "appointment_cancel": lambda p: appointments.appointment_cancel(p["appointment_id"], p["reason"], p["caller_id"]),
    "appointment_reschedule": lambda p: appointments.appointment_reschedule(p["appointment_id"], p["new_date"], p["new_time"], p["caller_id"]),
    "records_view": lambda p: records.records_view(p["patient_id"], p["record_type"], p["caller_id"]),
    "records_share": lambda p: records.records_share(p["patient_id"], p["recipient_id"], p["record_type"], p["caller_id"]),
    "records_download": lambda p: records.records_download(p["patient_id"], p["record_type"], p["format"], p["caller_id"]),
    "lab_submit_sample": lambda p: laboratory.lab_submit_sample(p["test_type"], p["patient_id"], p["doctor_id"], p["urgency"], p["caller_id"]),
    "lab_get_results": lambda p: laboratory.lab_get_results(p["test_id"], p["patient_id"], p["caller_id"]),
    "lab_share_results": lambda p: laboratory.lab_share_results(p["test_id"], p["doctor_id"], p["caller_id"]),
    "delegation_grant": lambda p: delegation_grant(p["delegate_id"], p["role"], p["allowed_tools"], float(p["budget_limit"]), float(p["duration_days"]), p["caller_id"]),
    "delegation_revoke": lambda p: delegation_revoke(p["delegation_id"], p["caller_id"]),
    "audit_view": lambda p: audit.audit_view(int(p.get("count", 10)), p.get("filter_verdict", "all"), p["caller_id"]),
    "audit_verify": lambda p: audit.audit_verify(p["caller_id"]),
    "negotiation_request": lambda p: negotiation.negotiation_request(p["target_role"], p["tool_requested"], p["reason"], p["caller_id"]),
    "negotiation_respond": lambda p: negotiation.negotiation_respond(p["negotiation_id"], p["decision"], int(p["duration_minutes"]), p["caller_id"]),
}

TOOL_PARAMS = {
    "emergency_ambulance": ["location", "severity", "caller_id"],
    "emergency_notify": ["message", "caller_id"],
    "emergency_location": ["caller_id"],
    "pharmacy_order": ["medication", "quantity", "pharmacy", "caller_id"],
    "pharmacy_refill": ["prescription_id", "pharmacy", "caller_id"],
    "pharmacy_check_interactions": ["drug_a", "drug_b", "caller_id"],
    "appointment_book": ["doctor_id", "department", "date", "time", "reason", "caller_id"],
    "appointment_cancel": ["appointment_id", "reason", "caller_id"],
    "appointment_reschedule": ["appointment_id", "new_date", "new_time", "caller_id"],
    "records_view": ["patient_id", "record_type", "caller_id"],
    "records_share": ["patient_id", "recipient_id", "record_type", "caller_id"],
    "records_download": ["patient_id", "record_type", "format", "caller_id"],
    "lab_submit_sample": ["test_type", "patient_id", "doctor_id", "urgency", "caller_id"],
    "lab_get_results": ["test_id", "patient_id", "caller_id"],
    "lab_share_results": ["test_id", "doctor_id", "caller_id"],
    "delegation_grant": ["delegate_id", "role", "allowed_tools", "budget_limit", "duration_days", "caller_id"],
    "delegation_revoke": ["delegation_id", "caller_id"],
    "audit_view": ["count", "filter_verdict", "caller_id"],
    "audit_verify": ["caller_id"],
    "negotiation_request": ["target_role", "tool_requested", "reason", "caller_id"],
    "negotiation_respond": ["negotiation_id", "decision", "duration_minutes", "caller_id"],
}

TOOL_CATEGORIES = {
    "Emergency": ["emergency_ambulance", "emergency_notify", "emergency_location"],
    "Pharmacy": ["pharmacy_order", "pharmacy_refill", "pharmacy_check_interactions"],
    "Appointments": ["appointment_book", "appointment_cancel", "appointment_reschedule"],
    "Records [PHI]": ["records_view", "records_share", "records_download"],
    "Laboratory": ["lab_submit_sample", "lab_get_results", "lab_share_results"],
    "Delegation [Admin]": ["delegation_grant", "delegation_revoke"],
    "Audit [Admin]": ["audit_view", "audit_verify"],
    "Negotiation": ["negotiation_request", "negotiation_respond"],
}

PRESET_DEMOS = [
    {"name": "1. Admin Views Records", "tool": "records_view", "params": {"patient_id": "P001", "record_type": "summary", "caller_id": "samarth banodia"}, "expect": "ALLOWED", "desc": "Admin has full access to all tools including PHI"},
    {"name": "2. Doctor Views Lab", "tool": "lab_get_results", "params": {"test_id": "LAB001", "patient_id": "P001", "caller_id": "samarth"}, "expect": "ALLOWED", "desc": "Doctors can access PHI data (lab results)"},
    {"name": "3. Nurse Blocked PHI", "tool": "records_view", "params": {"patient_id": "P001", "record_type": "summary", "caller_id": "fukishi seichi"}, "expect": "BLOCKED", "desc": "Nurses cannot access Protected Health Information"},
    {"name": "4. Doctor Blocked Admin", "tool": "delegation_grant", "params": {"delegate_id": "arinjay", "role": "pharmacist", "allowed_tools": "pharmacy_order", "budget_limit": "5000", "duration_days": "7", "caller_id": "samarth"}, "expect": "BLOCKED", "desc": "Delegation is admin-only tool"},
    {"name": "5. Grant Delegation", "tool": "delegation_grant", "params": {"delegate_id": "arinjay", "role": "pharmacist", "allowed_tools": "appointment_book,lab_submit_sample", "budget_limit": "5000", "duration_days": "7", "caller_id": "samarth banodia"}, "expect": "ALLOWED", "desc": "Admin grants JWT delegation token"},
    {"name": "6. Budget Exceeded", "tool": "pharmacy_order", "params": {"medication": "Paracetamol 500mg", "quantity": "10000", "pharmacy": "MedPlus", "caller_id": "arinjay"}, "expect": "BLOCKED", "desc": "Cost exceeds budget limit"},
    {"name": "7. Emergency Bypass", "tool": "emergency_ambulance", "params": {"location": "Mumbai Central", "severity": "critical", "caller_id": "stranger"}, "expect": "ALLOWED", "desc": "Emergency tools bypass ALL checks for ANY caller"},
    {"name": "8. Drug Interaction", "tool": "pharmacy_check_interactions", "params": {"drug_a": "Warfarin", "drug_b": "Aspirin", "caller_id": "fukishi seichi"}, "expect": "ALLOWED", "desc": "Read-only drug check allowed for nurses"},
    {"name": "9. Audit Verify", "tool": "audit_verify", "params": {"caller_id": "samarth banodia"}, "expect": "ALLOWED", "desc": "Admin verifies SHA-256 hash chain integrity"},
]

# ── ArmorIQ SDK helper ───────────────────────────────────────────────

def armoriq_invoke(tool_name: str, params: dict) -> dict | None:
    """Send tool call through ArmorIQ Intent Intelligence pipeline."""
    if not ARMORIQ_ENABLED or armoriq_client is None:
        return None

    try:
        # Step 1: Capture plan
        plan = armoriq_client.capture_plan(
            llm="hospital-guardian",
            prompt=f"Execute {tool_name} with params {json.dumps(params)}",
            plan={
                "goal": f"Execute {tool_name}",
                "steps": [
                    {
                        "action": tool_name,
                        "mcp": ARMORIQ_MCP_NAME,
                        "params": {k: str(v) for k, v in params.items()},
                    }
                ],
            },
        )

        # Step 2: Get intent token
        token = armoriq_client.get_intent_token(plan, validity_seconds=120)

        sdk_entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "tool": tool_name,
            "step": "intent_token",
            "token_id": token.token_id,
            "plan_hash": token.plan_hash[:16] + "..." if token.plan_hash else "N/A",
            "status": "OK",
        }
        armoriq_log.append(sdk_entry)

        # Step 3: Invoke through proxy
        try:
            result = armoriq_client.invoke(
                mcp=ARMORIQ_MCP_NAME,
                action=tool_name,
                intent_token=token,
                params={k: str(v) for k, v in params.items()},
                user_email=ARMORIQ_USER_ID,
            )
            sdk_entry_invoke = {
                "timestamp": time.strftime("%H:%M:%S"),
                "tool": tool_name,
                "step": "invoke",
                "status": result.status,
                "verified": result.verified,
                "execution_time": f"{result.execution_time:.2f}s",
            }
            armoriq_log.append(sdk_entry_invoke)
            return {"status": "OK", "token_id": token.token_id, "verified": result.verified}
        except Exception as e:
            sdk_entry_err = {
                "timestamp": time.strftime("%H:%M:%S"),
                "tool": tool_name,
                "step": "invoke",
                "status": "ERROR",
                "error": str(e)[:100],
            }
            armoriq_log.append(sdk_entry_err)
            return {"status": "TOKEN_OK", "token_id": token.token_id, "invoke_error": str(e)[:100]}

    except Exception as e:
        sdk_entry_fail = {
            "timestamp": time.strftime("%H:%M:%S"),
            "tool": tool_name,
            "step": "capture/token",
            "status": "ERROR",
            "error": str(e)[:100],
        }
        armoriq_log.append(sdk_entry_fail)
        return {"status": "ERROR", "error": str(e)[:100]}


# ── HTML Dashboard ────────────────────────────────────────────────────

def build_html() -> str:
    # Build sidebar tool list
    sidebar_tools = ""
    for cat, tools in TOOL_CATEGORIES.items():
        icon = {"Emergency": "🚨", "Pharmacy": "💊", "Appointments": "📅", "Records [PHI]": "🔒", "Laboratory": "🔬", "Delegation [Admin]": "🔑", "Audit [Admin]": "📋", "Negotiation": "🤝"}.get(cat, "📌")
        sidebar_tools += f'<div class="cat"><div class="cat-title">{icon} {cat}</div>'
        for t in tools:
            sidebar_tools += f'<button class="tool-btn" onclick="selectTool(\'{t}\')">{t}</button>'
        sidebar_tools += '</div>'

    # Build preset buttons
    preset_btns = ""
    for d in PRESET_DEMOS:
        cls = "expect-blocked" if d["expect"] == "BLOCKED" else "expect-allowed"
        preset_btns += f'<button class="btn btn-preset {cls}" onclick=\'runPreset({json.dumps(d)})\' title="{d["desc"]}">{d["name"]}</button>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Hospital Guardian - ArmorIQ Demo</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0a0e17; color: #e0e0e0; overflow: hidden; height: 100vh; }}

/* Header */
.header {{ background: linear-gradient(135deg, #1a1f35 0%, #0d1117 100%); padding: 12px 20px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 10px; }}
.header h1 {{ font-size: 18px; color: #58a6ff; white-space: nowrap; }}
.badge {{ display: inline-block; background: #238636; color: white; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; white-space: nowrap; }}
.header .subtitle {{ color: #8b949e; font-size: 12px; margin-left: auto; white-space: nowrap; }}
.armoriq-status {{ display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
.armoriq-on {{ background: #1f6feb33; color: #58a6ff; border: 1px solid #1f6feb; }}
.armoriq-off {{ background: #30363d; color: #8b949e; border: 1px solid #30363d; }}

/* Main layout */
.main {{ display: grid; grid-template-columns: 220px 1fr; height: calc(100vh - 48px); }}
.sidebar {{ background: #0d1117; border-right: 1px solid #30363d; overflow-y: auto; padding: 6px 0; }}
.sidebar h3 {{ padding: 6px 12px; color: #8b949e; font-size: 10px; text-transform: uppercase; letter-spacing: 1px; }}
.cat {{ margin-bottom: 2px; }}
.cat-title {{ padding: 4px 12px; color: #c9d1d9; font-size: 12px; font-weight: 600; cursor: pointer; }}
.cat-title:hover {{ background: #161b22; }}
.tool-btn {{ display: block; width: 100%; text-align: left; padding: 3px 12px 3px 24px; background: none; border: none; color: #8b949e; font-size: 11px; cursor: pointer; font-family: 'Consolas', 'Courier New', monospace; }}
.tool-btn:hover {{ background: #161b22; color: #58a6ff; }}
.tool-btn.active {{ background: #1f2937; color: #58a6ff; border-left: 2px solid #58a6ff; }}

/* Content area */
.content {{ display: grid; grid-template-rows: auto 1fr auto; overflow: hidden; }}

/* Top bar: stats + presets */
.topbar {{ display: flex; border-bottom: 1px solid #30363d; background: #0d1117; }}
.stats {{ display: flex; gap: 6px; padding: 6px 10px; flex-shrink: 0; }}
.stat-card {{ background: #161b22; border: 1px solid #30363d; border-radius: 6px; padding: 4px 10px; text-align: center; min-width: 60px; }}
.stat-card .num {{ font-size: 18px; font-weight: 700; color: #58a6ff; }}
.stat-card .label {{ font-size: 9px; color: #8b949e; text-transform: uppercase; }}
.presets {{ padding: 4px 10px; overflow-x: auto; white-space: nowrap; display: flex; align-items: center; gap: 4px; flex: 1; }}
.presets h4 {{ color: #8b949e; font-size: 10px; text-transform: uppercase; margin-right: 6px; white-space: nowrap; }}
.btn-preset {{ background: #1f2937; color: #58a6ff; border: 1px solid #30363d; font-size: 10px; padding: 3px 8px; border-radius: 4px; cursor: pointer; white-space: nowrap; }}
.btn-preset:hover {{ background: #30363d; }}
.btn-preset.expect-blocked {{ border-color: #f8514966; color: #f85149; }}
.btn-preset.expect-allowed {{ border-color: #3fb95066; color: #3fb950; }}

/* Middle: split into tool form + result */
.workspace {{ display: grid; grid-template-columns: 320px 1fr; overflow: hidden; }}
.form-panel {{ border-right: 1px solid #30363d; display: flex; flex-direction: column; overflow: hidden; }}
.form-panel h3 {{ padding: 8px 12px; border-bottom: 1px solid #30363d; color: #c9d1d9; font-size: 13px; background: #0d1117; flex-shrink: 0; }}
.form-area {{ padding: 10px; overflow-y: auto; flex: 1; }}
.form-group {{ margin-bottom: 8px; }}
.form-group label {{ display: block; color: #8b949e; font-size: 11px; margin-bottom: 2px; }}
.form-group input, .form-group select {{ width: 100%; padding: 6px 8px; background: #0d1117; border: 1px solid #30363d; border-radius: 4px; color: #e0e0e0; font-size: 12px; font-family: 'Consolas', monospace; }}
.form-group input:focus, .form-group select:focus {{ border-color: #58a6ff; outline: none; }}
.btn {{ padding: 8px 16px; border: none; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; }}
.btn-primary {{ background: #238636; color: white; width: 100%; margin-top: 8px; }}
.btn-primary:hover {{ background: #2ea043; }}

/* Result panel with tabs */
.result-panel {{ display: flex; flex-direction: column; overflow: hidden; }}
.tab-bar {{ display: flex; background: #0d1117; border-bottom: 1px solid #30363d; flex-shrink: 0; }}
.tab {{ padding: 6px 14px; font-size: 11px; color: #8b949e; cursor: pointer; border-bottom: 2px solid transparent; font-weight: 600; }}
.tab:hover {{ color: #c9d1d9; background: #161b22; }}
.tab.active {{ color: #58a6ff; border-bottom-color: #58a6ff; }}
.tab-content {{ flex: 1; overflow-y: auto; padding: 12px; display: none; }}
.tab-content.active {{ display: block; }}

/* Trace visualization */
.trace-step {{ padding: 6px 10px; border-left: 3px solid #30363d; margin: 4px 0; font-size: 11px; font-family: 'Consolas', monospace; border-radius: 0 4px 4px 0; transition: all 0.3s; }}
.trace-step.pass {{ border-color: #3fb950; background: #3fb95010; }}
.trace-step.blocked {{ border-color: #f85149; background: #f8514910; }}
.trace-step.na {{ border-color: #30363d; background: #161b22; }}
.trace-step.found {{ border-color: #d29922; background: #d2992210; }}
.trace-step .step-num {{ display: inline-block; width: 20px; color: #8b949e; }}
.trace-step .step-name {{ color: #c9d1d9; font-weight: 600; }}
.trace-step .step-result {{ float: right; font-weight: 700; }}
.trace-step .step-detail {{ display: block; color: #8b949e; margin-top: 2px; font-size: 10px; }}

.verdict-banner {{ padding: 10px; margin: 8px 0; border-radius: 6px; font-weight: 700; font-size: 15px; text-align: center; animation: fadeIn 0.3s; }}
.verdict-allow {{ background: #23863633; color: #3fb950; border: 1px solid #238636; }}
.verdict-block {{ background: #f8514933; color: #f85149; border: 1px solid #f85149; }}
.verdict-emergency {{ background: #1f6feb33; color: #58a6ff; border: 1px solid #1f6feb; }}

.suggestion {{ padding: 5px 10px; background: #d2992215; border-left: 3px solid #d29922; margin: 3px 0; font-size: 11px; color: #d29922; }}
.json-block {{ background: #0d1117; border: 1px solid #30363d; border-radius: 4px; padding: 8px; font-size: 10px; font-family: 'Consolas', monospace; overflow-x: auto; white-space: pre-wrap; word-break: break-all; color: #8b949e; max-height: 250px; overflow-y: auto; margin-top: 6px; }}

/* Bottom bar */
.bottombar {{ border-top: 1px solid #30363d; background: #0d1117; display: grid; grid-template-columns: 1fr 1fr 1fr; max-height: 180px; overflow: hidden; }}
.bottom-section {{ border-right: 1px solid #30363d; overflow-y: auto; }}
.bottom-section:last-child {{ border-right: none; }}
.bottom-section h4 {{ padding: 4px 10px; font-size: 10px; color: #8b949e; text-transform: uppercase; border-bottom: 1px solid #30363d; position: sticky; top: 0; background: #0d1117; z-index: 1; }}

/* History items */
.history-item {{ padding: 3px 10px; border-bottom: 1px solid #30363d10; font-size: 10px; display: flex; gap: 6px; align-items: center; }}
.h-verdict {{ font-weight: 700; width: 50px; flex-shrink: 0; }}
.h-tool {{ color: #58a6ff; font-family: monospace; flex: 1; }}
.h-caller {{ color: #8b949e; flex-shrink: 0; }}
.h-time {{ color: #484f58; flex-shrink: 0; font-size: 9px; }}

/* Delegation items */
.del-item {{ padding: 4px 10px; font-size: 10px; border-bottom: 1px solid #30363d20; }}
.del-item .del-id {{ color: #a371f7; font-family: monospace; }}
.del-item .del-scope {{ color: #d29922; }}

/* ArmorIQ log */
.aiq-item {{ padding: 3px 10px; font-size: 10px; border-bottom: 1px solid #30363d10; display: flex; gap: 6px; }}
.aiq-item .aiq-time {{ color: #484f58; width: 50px; }}
.aiq-item .aiq-step {{ color: #a371f7; width: 80px; }}
.aiq-item .aiq-tool {{ color: #58a6ff; font-family: monospace; flex: 1; }}
.aiq-item .aiq-status {{ font-weight: 600; }}

/* Role indicators */
.role-badge {{ display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 10px; font-weight: 600; }}
.role-admin {{ background: #1f6feb33; color: #58a6ff; }}
.role-doctor {{ background: #23863633; color: #3fb950; }}
.role-nurse {{ background: #d2992233; color: #d29922; }}
.role-pharmacist {{ background: #a371f733; color: #a371f7; }}
.role-caretaker {{ background: #f8514933; color: #f85149; }}
.role-unknown {{ background: #30363d; color: #8b949e; }}

/* Charts */
.chart-container {{ height: 120px; margin: 8px 0; }}

/* Animations */
@keyframes fadeIn {{ from {{ opacity: 0; transform: translateY(-5px); }} to {{ opacity: 1; transform: translateY(0); }} }}
@keyframes slideIn {{ from {{ opacity: 0; transform: translateX(-10px); }} to {{ opacity: 1; transform: translateX(0); }} }}
.trace-step {{ animation: slideIn 0.2s ease-out; }}
.trace-step:nth-child(1) {{ animation-delay: 0.0s; }}
.trace-step:nth-child(2) {{ animation-delay: 0.05s; }}
.trace-step:nth-child(3) {{ animation-delay: 0.1s; }}
.trace-step:nth-child(4) {{ animation-delay: 0.15s; }}
.trace-step:nth-child(5) {{ animation-delay: 0.2s; }}
.trace-step:nth-child(6) {{ animation-delay: 0.25s; }}
.trace-step:nth-child(7) {{ animation-delay: 0.3s; }}
.trace-step:nth-child(8) {{ animation-delay: 0.35s; }}
.trace-step:nth-child(9) {{ animation-delay: 0.4s; }}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: #0d1117; }}
::-webkit-scrollbar-thumb {{ background: #30363d; border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: #484f58; }}

/* Roles sidebar section */
.roles-section {{ padding: 6px 12px; }}
.role-row {{ display: flex; align-items: center; gap: 6px; margin: 2px 0; font-size: 10px; }}
.role-row .name {{ color: #c9d1d9; }}
.role-row .eq {{ color: #484f58; }}
</style>
</head>
<body>

<div class="header">
  <h1>Hospital Guardian</h1>
  <span class="badge">21 Tools</span>
  <span class="badge" style="background:#1f6feb">9-Step Pipeline</span>
  <span class="badge" style="background:#a371f7">Merkle Audit</span>
  <span class="badge" style="background:#d29922">JWT Delegation</span>
  <span class="armoriq-status {'armoriq-on' if ARMORIQ_ENABLED else 'armoriq-off'}" id="aiqStatus">
    {'ON' if ARMORIQ_ENABLED else 'OFF'} ArmorIQ SDK
  </span>
  <span class="subtitle">IITB ArmorIQ Hackathon | MCP Enforcement Demo</span>
</div>

<div class="main">
  <!-- Sidebar -->
  <div class="sidebar">
    <h3>Tools (21)</h3>
    {sidebar_tools}
    <h3 style="margin-top:8px">Role Hierarchy</h3>
    <div class="roles-section">
      <div class="role-row"><span class="role-badge role-admin">admin</span> <span class="eq">=</span> <span class="name">samarth banodia</span></div>
      <div class="role-row"><span class="role-badge role-doctor">doctor</span> <span class="eq">=</span> <span class="name">samarth</span></div>
      <div class="role-row"><span class="role-badge role-nurse">nurse</span> <span class="eq">=</span> <span class="name">fukishi seichi</span></div>
      <div class="role-row"><span class="role-badge role-pharmacist">pharmacist</span> <span class="eq">=</span> <span class="name">arinjay</span></div>
      <div class="role-row"><span class="role-badge role-caretaker">caretaker</span> <span class="eq">=</span> <span class="name">bot</span></div>
      <div class="role-row"><span class="role-badge role-unknown">unknown</span> <span class="eq">=</span> <span class="name">anyone else</span></div>
    </div>
  </div>

  <!-- Content -->
  <div class="content">
    <!-- Top bar -->
    <div class="topbar">
      <div class="stats">
        <div class="stat-card"><div class="num" id="stat-total">0</div><div class="label">Calls</div></div>
        <div class="stat-card"><div class="num" id="stat-allow" style="color:#3fb950">0</div><div class="label">Allow</div></div>
        <div class="stat-card"><div class="num" id="stat-block" style="color:#f85149">0</div><div class="label">Block</div></div>
        <div class="stat-card"><div class="num" id="stat-emg" style="color:#58a6ff">0</div><div class="label">Emerg</div></div>
        <div class="stat-card"><div class="num" id="stat-merkle" style="color:#a371f7">0</div><div class="label">Merkle</div></div>
      </div>
      <div class="presets">
        <h4>Demos:</h4>
        {preset_btns}
      </div>
    </div>

    <!-- Workspace -->
    <div class="workspace">
      <!-- Form panel -->
      <div class="form-panel">
        <h3 id="tool-title">Select a tool</h3>
        <div class="form-area" id="form-area">
          <p style="color:#8b949e;padding:20px;text-align:center;font-size:12px">Click a tool from the sidebar or a preset demo scenario above</p>
        </div>
      </div>

      <!-- Result panel with tabs -->
      <div class="result-panel">
        <div class="tab-bar">
          <div class="tab active" onclick="switchTab('trace')">Guardian Trace</div>
          <div class="tab" onclick="switchTab('audit')">Audit Timeline</div>
          <div class="tab" onclick="switchTab('budget')">Budget</div>
          <div class="tab" onclick="switchTab('permissions')">Permissions</div>
          <div class="tab" onclick="switchTab('json')">Raw JSON</div>
        </div>
        <div class="tab-content active" id="tab-trace">
          <p style="color:#8b949e;text-align:center;padding:30px;font-size:12px">Run a tool to see the 9-step Guardian pipeline trace</p>
        </div>
        <div class="tab-content" id="tab-audit">
          <canvas id="auditChart" style="width:100%;height:140px"></canvas>
          <div id="auditTimeline" style="margin-top:10px"></div>
        </div>
        <div class="tab-content" id="tab-budget">
          <canvas id="budgetChart" style="width:100%;height:160px"></canvas>
          <div id="budgetDetails" style="margin-top:10px"></div>
        </div>
        <div class="tab-content" id="tab-permissions">
          <div id="permMatrix"></div>
        </div>
        <div class="tab-content" id="tab-json">
          <div class="json-block" id="rawJson">No data yet</div>
        </div>
      </div>
    </div>

    <!-- Bottom bar -->
    <div class="bottombar">
      <div class="bottom-section">
        <h4>Call History</h4>
        <div id="history"></div>
      </div>
      <div class="bottom-section">
        <h4>Active Delegations</h4>
        <div id="delegations"><p style="padding:8px 10px;color:#484f58;font-size:10px">No delegations yet</p></div>
      </div>
      <div class="bottom-section">
        <h4>ArmorIQ Intent Intelligence</h4>
        <div id="armoriqLog"><p style="padding:8px 10px;color:#484f58;font-size:10px">{'SDK connected - calls will appear on platform.armoriq.ai' if ARMORIQ_ENABLED else 'SDK not connected'}</p></div>
      </div>
    </div>
  </div>
</div>

<script>
const TOOL_PARAMS = {json.dumps(TOOL_PARAMS)};
const ROLE_TOOLS = {json.dumps({role: sorted(list(tools)) for role, tools in ROLE_ALLOWED_TOOLS.items()})};
let callCount = 0, allowCount = 0, blockCount = 0, emgCount = 0;
let auditData = {{ labels: [], allow: [], block: [], emg: [] }};
let auditChart = null, budgetChart = null;

// Tab switching
function switchTab(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');

  if (name === 'audit') refreshAuditChart();
  if (name === 'budget') refreshBudgetChart();
  if (name === 'permissions') refreshPermMatrix();
}}

// Tool selection
function selectTool(name) {{
  document.querySelectorAll('.tool-btn').forEach(b => b.classList.remove('active'));
  if (event && event.target) event.target.classList.add('active');
  document.getElementById('tool-title').textContent = name;
  const params = TOOL_PARAMS[name] || [];
  let html = '<form id="toolForm" onsubmit="callTool(event)">';
  html += '<input type="hidden" name="tool" value="' + name + '">';
  params.forEach(p => {{
    html += '<div class="form-group"><label>' + p + '</label>';
    if (p === 'caller_id') {{
      html += '<select name="' + p + '">';
      html += '<option value="samarth banodia">samarth banodia (Admin)</option>';
      html += '<option value="samarth">samarth (Doctor)</option>';
      html += '<option value="fukishi seichi">fukishi seichi (Nurse)</option>';
      html += '<option value="arinjay">arinjay (Pharmacist)</option>';
      html += '<option value="bot">bot (Caretaker)</option>';
      html += '<option value="stranger">stranger (Unknown)</option>';
      html += '</select>';
    }} else if (p === 'severity') {{
      html += '<select name="' + p + '"><option value="critical">critical</option><option value="serious">serious</option><option value="moderate">moderate</option></select>';
    }} else if (p === 'record_type') {{
      html += '<select name="' + p + '"><option value="summary">summary</option><option value="medications">medications</option><option value="conditions">conditions</option><option value="allergies">allergies</option></select>';
    }} else if (p === 'filter_verdict') {{
      html += '<select name="' + p + '"><option value="all">all</option><option value="ALLOW">ALLOW</option><option value="BLOCK">BLOCK</option><option value="EMERGENCY_BYPASS">EMERGENCY_BYPASS</option></select>';
    }} else if (p === 'urgency') {{
      html += '<select name="' + p + '"><option value="routine">routine</option><option value="urgent">urgent</option><option value="stat">stat</option></select>';
    }} else if (p === 'decision') {{
      html += '<select name="' + p + '"><option value="approve">approve</option><option value="deny">deny</option></select>';
    }} else if (p === 'format') {{
      html += '<select name="' + p + '"><option value="pdf">pdf</option><option value="csv">csv</option><option value="json">json</option></select>';
    }} else {{
      html += '<input type="text" name="' + p + '" placeholder="' + p + '">';
    }}
    html += '</div>';
  }});
  html += '<button type="submit" class="btn btn-primary">Execute Tool</button>';
  html += '<label style="display:flex;align-items:center;gap:6px;margin-top:6px;font-size:11px;color:#8b949e"><input type="checkbox" id="aiqToggle" checked> Send to ArmorIQ</label>';
  html += '</form>';
  document.getElementById('form-area').innerHTML = html;
}}

function runPreset(demo) {{
  selectTool(demo.tool);
  setTimeout(() => {{
    const form = document.getElementById('toolForm');
    Object.entries(demo.params).forEach(([k, v]) => {{
      const el = form.querySelector('[name="' + k + '"]');
      if (el) el.value = v;
    }});
    form.dispatchEvent(new Event('submit'));
  }}, 100);
}}

// Tool execution
async function callTool(e) {{
  e.preventDefault();
  const fd = new FormData(e.target);
  const params = {{}};
  fd.forEach((v, k) => params[k] = v);
  const tool = params.tool;
  delete params.tool;
  const sendAiq = document.getElementById('aiqToggle')?.checked ?? false;

  // Show loading
  document.getElementById('tab-trace').innerHTML = '<p style="color:#58a6ff;text-align:center;padding:20px;font-size:12px">Running ' + tool + '...</p>';
  switchTabDirect('trace');

  const resp = await fetch('/api/call', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{tool, params, send_armoriq: sendAiq}})
  }});
  const data = await resp.json();
  displayResult(tool, params, data);
}}

function switchTabDirect(name) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
  document.querySelector('.tab-bar .tab:first-child').classList.add('active');
  document.getElementById('tab-' + name).classList.add('active');
}}

function displayResult(tool, params, data) {{
  callCount++;
  let result;
  try {{ result = typeof data.result === 'string' ? JSON.parse(data.result) : data.result; }}
  catch {{ result = data.result || data; }}

  const status = result.status || 'UNKNOWN';
  const isBlock = status === 'BLOCKED';
  const isEmergency = (result.guardian_trace || '').includes('EMERGENCY_BYPASS');
  const verdict = isBlock ? 'BLOCK' : isEmergency ? 'EMERGENCY_BYPASS' : 'ALLOW';
  const ts = new Date().toLocaleTimeString();

  if (isBlock) blockCount++;
  else if (isEmergency) emgCount++;
  else allowCount++;

  // Update audit data
  auditData.labels.push(callCount);
  auditData.allow.push(allowCount);
  auditData.block.push(blockCount);
  auditData.emg.push(emgCount);

  // ── Trace tab ──
  const trace = result.guardian_trace || '';
  const traceLines = trace.split('\\n').filter(l => l.includes('Step'));
  let html = '';

  const vc = isBlock ? 'verdict-block' : isEmergency ? 'verdict-emergency' : 'verdict-allow';
  html += '<div class="verdict-banner ' + vc + '">' + verdict + '</div>';
  html += '<div style="color:#8b949e;font-size:11px;margin-bottom:8px;text-align:center">' + (result.reason || '') + '</div>';

  traceLines.forEach((line, i) => {{
    let cls = 'na';
    if (line.includes('PASS')) cls = 'pass';
    else if (line.includes('BLOCKED')) cls = 'blocked';
    else if (line.includes('FOUND')) cls = 'found';

    // Parse step number, name, result, detail
    const stepMatch = line.match(/Step\\s*(\\d+):\\s*([\\w\\s/]+?)\\s*[→>]+\\s*(\\w+)/);
    const detailMatch = line.match(/^[║│]\\s+(.+)/);

    if (stepMatch) {{
      const [_, num, name, res] = stepMatch;
      html += '<div class="trace-step ' + cls + '" style="animation-delay:' + (i*0.05) + 's">';
      html += '<span class="step-num">' + num + '</span>';
      html += '<span class="step-name">' + name.trim() + '</span>';
      html += '<span class="step-result" style="color:' + (cls==='pass'?'#3fb950':cls==='blocked'?'#f85149':'#8b949e') + '">' + res + '</span>';
      html += '</div>';
    }} else {{
      const clean = line.replace(/^[║│]\\s*/, '').replace(/[✅🚫⬜🔍⏭️❓💡💰🔑]/g, '').trim();
      if (clean && clean.length > 2) {{
        html += '<div class="trace-step ' + cls + '" style="animation-delay:' + (i*0.05) + 's"><span class="step-detail">' + clean + '</span></div>';
      }}
    }}
  }});

  // Suggestions
  if (result.suggestions && result.suggestions.length > 0) {{
    html += '<div style="margin-top:8px"><h4 style="color:#d29922;font-size:11px;margin-bottom:4px">Suggestions</h4>';
    result.suggestions.forEach(s => {{ html += '<div class="suggestion">' + s + '</div>'; }});
    html += '</div>';
  }}

  // Budget
  if (result.budget_remaining != null) {{
    html += '<div style="margin:6px 0;padding:5px 10px;background:#23863620;border-radius:4px;font-size:11px;color:#3fb950">Budget remaining: Rs. ' + Number(result.budget_remaining).toLocaleString('en-IN') + '</div>';
  }}

  // ArmorIQ status
  if (data.armoriq) {{
    const aiq = data.armoriq;
    const aiqColor = aiq.status === 'OK' ? '#3fb950' : aiq.status === 'TOKEN_OK' ? '#d29922' : '#f85149';
    html += '<div style="margin:6px 0;padding:5px 10px;background:' + aiqColor + '20;border-left:3px solid ' + aiqColor + ';border-radius:0 4px 4px 0;font-size:11px;color:' + aiqColor + '">';
    html += 'ArmorIQ: ' + aiq.status;
    if (aiq.token_id) html += ' | Token: ' + aiq.token_id;
    if (aiq.invoke_error) html += ' | Invoke: ' + aiq.invoke_error;
    html += '</div>';
  }}

  document.getElementById('tab-trace').innerHTML = html;

  // ── Raw JSON tab ──
  const cleanResult = {{...result}};
  delete cleanResult.guardian_trace;
  document.getElementById('rawJson').textContent = JSON.stringify(cleanResult, null, 2);

  // ── Update stats ──
  document.getElementById('stat-total').textContent = callCount;
  document.getElementById('stat-allow').textContent = allowCount;
  document.getElementById('stat-block').textContent = blockCount;
  document.getElementById('stat-emg').textContent = emgCount;

  // ── History ──
  const hist = document.getElementById('history');
  const verdictColor = isBlock ? '#f85149' : isEmergency ? '#58a6ff' : '#3fb950';
  hist.innerHTML = '<div class="history-item"><span class="h-time">' + ts + '</span><span class="h-verdict" style="color:' + verdictColor + '">' + verdict + '</span><span class="h-tool">' + tool + '</span><span class="h-caller">' + params.caller_id + '</span></div>' + hist.innerHTML;

  // ── Refresh bottom panels ──
  refreshDelegations();
  refreshArmoriqLog();
  fetch('/api/stats').then(r => r.json()).then(s => {{
    document.getElementById('stat-merkle').textContent = s.merkle_roots;
  }});
}}

// ── Charts ──
function refreshAuditChart() {{
  const ctx = document.getElementById('auditChart');
  if (!ctx) return;

  if (auditChart) auditChart.destroy();
  auditChart = new Chart(ctx, {{
    type: 'line',
    data: {{
      labels: auditData.labels,
      datasets: [
        {{ label: 'Allowed', data: auditData.allow, borderColor: '#3fb950', backgroundColor: '#3fb95020', fill: true, tension: 0.3, borderWidth: 2, pointRadius: 2 }},
        {{ label: 'Blocked', data: auditData.block, borderColor: '#f85149', backgroundColor: '#f8514920', fill: true, tension: 0.3, borderWidth: 2, pointRadius: 2 }},
        {{ label: 'Emergency', data: auditData.emg, borderColor: '#58a6ff', backgroundColor: '#58a6ff20', fill: true, tension: 0.3, borderWidth: 2, pointRadius: 2 }}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 10 }} }} }} }},
      scales: {{
        x: {{ ticks: {{ color: '#484f58', font: {{ size: 9 }} }}, grid: {{ color: '#30363d20' }} }},
        y: {{ ticks: {{ color: '#484f58', font: {{ size: 9 }} }}, grid: {{ color: '#30363d20' }}, beginAtZero: true }}
      }}
    }}
  }});

  // Audit timeline
  fetch('/api/audit?count=10').then(r => r.json()).then(entries => {{
    let tl = '';
    entries.forEach(e => {{
      const vc = e.verdict === 'BLOCK' ? '#f85149' : e.verdict === 'EMERGENCY_BYPASS' ? '#58a6ff' : '#3fb950';
      tl += '<div class="history-item"><span class="h-time">' + e.timestamp.split('T')[1].split('.')[0] + '</span><span class="h-verdict" style="color:' + vc + '">' + e.verdict + '</span><span class="h-tool">' + e.tool + '</span><span class="h-caller">' + e.caller_id + '</span></div>';
    }});
    document.getElementById('auditTimeline').innerHTML = tl || '<p style="color:#484f58;font-size:10px;padding:8px">No audit entries yet</p>';
  }});
}}

function refreshBudgetChart() {{
  fetch('/api/budgets').then(r => r.json()).then(data => {{
    const ctx = document.getElementById('budgetChart');
    if (!ctx) return;

    if (budgetChart) budgetChart.destroy();
    const labels = data.map(b => b.caller_id);
    const remaining = data.map(b => b.remaining);
    const spent = data.map(b => b.spent);
    const colors = data.map(b => {{
      const r = b.role;
      return r === 'admin' ? '#58a6ff' : r === 'doctor' ? '#3fb950' : r === 'nurse' ? '#d29922' : r === 'pharmacist' ? '#a371f7' : r === 'caretaker' ? '#f85149' : '#8b949e';
    }});

    budgetChart = new Chart(ctx, {{
      type: 'bar',
      data: {{
        labels,
        datasets: [
          {{ label: 'Spent', data: spent, backgroundColor: colors.map(c => c + '80'), borderColor: colors, borderWidth: 1 }},
          {{ label: 'Remaining', data: remaining, backgroundColor: colors.map(c => c + '30'), borderColor: colors, borderWidth: 1 }}
        ]
      }},
      options: {{
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {{ legend: {{ labels: {{ color: '#8b949e', font: {{ size: 10 }} }} }} }},
        scales: {{
          x: {{ stacked: true, ticks: {{ color: '#484f58', font: {{ size: 9 }}, callback: v => 'Rs.' + v.toLocaleString() }}, grid: {{ color: '#30363d20' }} }},
          y: {{ stacked: true, ticks: {{ color: '#c9d1d9', font: {{ size: 10 }} }}, grid: {{ display: false }} }}
        }}
      }}
    }});

    let details = '<div style="margin-top:8px">';
    data.forEach(b => {{
      const pct = b.limit > 0 && b.limit < 1e10 ? Math.round((b.spent / b.limit) * 100) : 0;
      details += '<div style="font-size:10px;padding:2px 0;color:#8b949e">' + b.caller_id + ' (' + b.role + '): Rs.' + b.spent.toLocaleString() + ' / Rs.' + (b.limit > 1e10 ? 'Unlimited' : b.limit.toLocaleString()) + ' (' + pct + '%)</div>';
    }});
    details += '</div>';
    document.getElementById('budgetDetails').innerHTML = details;
  }});
}}

function refreshPermMatrix() {{
  const roles = ['admin', 'doctor', 'nurse', 'pharmacist', 'caretaker', 'unknown'];
  const categories = {json.dumps({cat: tools for cat, tools in TOOL_CATEGORIES.items()})};
  const roleColors = {{admin:'#58a6ff',doctor:'#3fb950',nurse:'#d29922',pharmacist:'#a371f7',caretaker:'#f85149',unknown:'#8b949e'}};

  let html = '<table style="width:100%;font-size:10px;border-collapse:collapse">';
  html += '<tr><th style="text-align:left;padding:4px;color:#8b949e;border-bottom:1px solid #30363d">Tool</th>';
  roles.forEach(r => {{ html += '<th style="padding:4px;color:' + roleColors[r] + ';border-bottom:1px solid #30363d;font-size:9px">' + r + '</th>'; }});
  html += '</tr>';

  Object.entries(categories).forEach(([cat, tools]) => {{
    html += '<tr><td colspan="' + (roles.length + 1) + '" style="padding:4px 4px 2px;color:#484f58;font-weight:600;font-size:9px;border-top:1px solid #30363d20">' + cat + '</td></tr>';
    tools.forEach(tool => {{
      html += '<tr><td style="padding:2px 4px;color:#c9d1d9;font-family:monospace">' + tool + '</td>';
      roles.forEach(r => {{
        const has = ROLE_TOOLS[r] && ROLE_TOOLS[r].includes(tool);
        html += '<td style="text-align:center;padding:2px;color:' + (has ? '#3fb950' : '#f85149') + '">' + (has ? 'Y' : '-') + '</td>';
      }});
      html += '</tr>';
    }});
  }});
  html += '</table>';
  document.getElementById('permMatrix').innerHTML = html;
}}

function refreshDelegations() {{
  fetch('/api/delegations').then(r => r.json()).then(dels => {{
    if (dels.length === 0) {{
      document.getElementById('delegations').innerHTML = '<p style="padding:8px 10px;color:#484f58;font-size:10px">No delegations</p>';
      return;
    }}
    let html = '';
    dels.forEach(d => {{
      const active = d.active ? '#3fb950' : '#f85149';
      html += '<div class="del-item">';
      html += '<span class="del-id">' + d.token_id + '</span> ';
      html += '<span style="color:' + active + ';font-size:9px">' + (d.active ? 'ACTIVE' : 'EXPIRED') + '</span><br>';
      html += '<span style="color:#8b949e;font-size:9px">' + d.grantor_id + ' -> ' + d.delegate_id + ' | </span>';
      html += '<span class="del-scope">' + d.scope.join(', ') + '</span>';
      html += '<span style="color:#8b949e;font-size:9px"> | Rs.' + d.budget_remaining.toLocaleString() + ' left</span>';
      html += '</div>';
    }});
    document.getElementById('delegations').innerHTML = html;
  }});
}}

function refreshArmoriqLog() {{
  fetch('/api/armoriq-log').then(r => r.json()).then(entries => {{
    if (entries.length === 0) return;
    let html = '';
    entries.slice(-20).reverse().forEach(e => {{
      const sc = e.status === 'OK' ? '#3fb950' : e.status === 'TOKEN_OK' ? '#d29922' : '#f85149';
      html += '<div class="aiq-item">';
      html += '<span class="aiq-time">' + e.timestamp + '</span>';
      html += '<span class="aiq-step">' + e.step + '</span>';
      html += '<span class="aiq-tool">' + e.tool + '</span>';
      html += '<span class="aiq-status" style="color:' + sc + '">' + e.status + '</span>';
      html += '</div>';
    }});
    document.getElementById('armoriqLog').innerHTML = html;
  }});
}}

// Initialize permission matrix on load
setTimeout(refreshPermMatrix, 100);
</script>
</body>
</html>"""


# ── Cache the HTML ────────────────────────────────────────────────────
HTML_PAGE = build_html()


# ── Request handler ──────────────────────────────────────────────────

class DemoHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self._json_or_html(HTML_PAGE, 'text/html')
        elif path == '/api/stats':
            verification = ledger.verify_chain()
            stats = {
                "total_entries": len(ledger.entries),
                "merkle_roots": verification["merkle_roots_checked"],
                "chain_intact": verification["valid"],
            }
            self._json_response(stats)
        elif path == '/api/audit':
            qs = parse_qs(urlparse(self.path).query)
            count = int(qs.get("count", [10])[0])
            filt = qs.get("filter", [None])[0]
            entries = ledger.get_recent(count, filt)
            self._json_response(entries)
        elif path == '/api/delegations':
            self._json_response(delegation_manager.list_active())
        elif path == '/api/budgets':
            budgets = []
            seen = set()
            for caller_id, role in CALLER_ROLES.items():
                if role in seen or caller_id in ("samarth_banodia", "samarth banodia (admin)", "samarth (doctor)", "fukishi_seichi", "fukishi"):
                    continue
                seen.add(role)
                limit = DEFAULT_BUDGET_LIMITS.get(role, 0.0)
                spent = _budgets.get(caller_id, 0.0)
                budgets.append({
                    "caller_id": caller_id,
                    "role": role,
                    "limit": limit,
                    "spent": spent,
                    "remaining": max(0, limit - spent) if limit < float('inf') else 999999,
                })
            self._json_response(budgets)
        elif path == '/api/armoriq-log':
            self._json_response(armoriq_log[-50:])
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/api/call':
            length = int(self.headers.get('Content-Length', 0))
            body = json.loads(self.rfile.read(length))
            tool = body.get("tool", "")
            params = body.get("params", {})
            send_armoriq = body.get("send_armoriq", False)

            handler = TOOL_DISPATCH.get(tool)
            if not handler:
                self._json_response({"error": f"Unknown tool: {tool}"}, 400)
                return

            try:
                result = handler(params)
                response = {"result": result}

                # ArmorIQ SDK integration (run in background to not block)
                if send_armoriq and ARMORIQ_ENABLED:
                    try:
                        aiq_result = armoriq_invoke(tool, params)
                        response["armoriq"] = aiq_result
                    except Exception as e:
                        response["armoriq"] = {"status": "ERROR", "error": str(e)[:100]}

                self._json_response(response)
            except Exception as e:
                self._json_response({"error": str(e), "traceback": traceback.format_exc()[-300:]}, 500)
        else:
            self.send_response(404)
            self.end_headers()

    def _json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, default=str).encode())

    def _json_or_html(self, content, content_type):
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        self.wfile.write(content.encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        pass


def main():
    port = 5000
    server = HTTPServer(('127.0.0.1', port), DemoHandler)
    print()
    print("  Hospital Guardian - Enhanced Demo Dashboard")
    print("  ============================================")
    print(f"  Open: http://localhost:{port}")
    print()
    print("  Features:")
    print("  - 21 MCP tools with 9-step Guardian pipeline")
    print("  - SHA-256 Merkle audit ledger visualization")
    print("  - HMAC-JWT delegation management")
    print("  - Budget tracking with live charts")
    print("  - Role permission matrix")
    print(f"  - ArmorIQ Intent Intelligence: {'ENABLED' if ARMORIQ_ENABLED else 'DISABLED'}")
    print()
    print("  Press Ctrl+C to stop")
    print()

    import webbrowser
    webbrowser.open(f"http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
