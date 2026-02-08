"""Guardian Pipeline — 9-step enforcement with full trace logging."""

from __future__ import annotations

from dataclasses import dataclass, field

from hospital.config import (
    ADMIN_ONLY_TOOLS,
    APPROVED_PHARMACIES,
    COST_TOOLS,
    DEFAULT_BUDGET_LIMITS,
    EMERGENCY_TOOLS,
    PHI_TOOLS,
    ROLE_ALLOWED_TOOLS,
)
from hospital.enforcement.jwt_delegation import Delegation, delegation_manager
from hospital.enforcement.merkle_ledger import TraceStep, ledger
from hospital.enforcement.policy_engine import Action, evaluate as policy_evaluate
from hospital.enforcement.roles import resolve_role


@dataclass
class GuardianVerdict:
    allowed: bool
    verdict: str          # ALLOW | BLOCK | EMERGENCY_BYPASS
    reason: str
    trace: list[TraceStep]
    suggestions: list[str]
    caller_role: str
    delegation_id: str | None = None
    budget_remaining: float | None = None


# ── Budget tracker (in-memory) ────────────────────────────────────────
_budgets: dict[str, float] = {}  # caller_id → amount spent


def _get_budget_remaining(caller_id: str, role: str, delegation: Delegation | None) -> float:
    if delegation:
        return delegation.budget - delegation.budget_spent
    limit = DEFAULT_BUDGET_LIMITS.get(role, 0.0)
    spent = _budgets.get(caller_id, 0.0)
    return max(0.0, limit - spent)


def _record_spend(caller_id: str, amount: float, delegation: Delegation | None) -> None:
    if delegation:
        delegation_manager.spend(delegation, amount)
    else:
        _budgets[caller_id] = _budgets.get(caller_id, 0.0) + amount


def guardian_evaluate(tool_name: str, params: dict, caller_id: str, cost: float = 0.0) -> GuardianVerdict:
    """Run the 9-step Guardian pipeline. Returns a verdict with full trace."""
    trace: list[TraceStep] = []
    suggestions: list[str] = []
    delegation: Delegation | None = None
    delegation_id: str | None = None

    # ── Step 1: Emergency Check ───────────────────────────────────
    if tool_name in EMERGENCY_TOOLS:
        trace.append(TraceStep(1, "Emergency Check", "PASS", f"Tool '{tool_name}' is an emergency tool — bypassing all checks"))
        role = resolve_role(caller_id)
        budget_remaining = _get_budget_remaining(caller_id, role, None)

        ledger.log(
            caller_id=caller_id, caller_role=role, tool=tool_name,
            params=params, verdict="EMERGENCY_BYPASS",
            reason="Emergency tool — all checks bypassed",
            trace=trace, suggestions=[],
            budget_remaining=budget_remaining,
        )
        return GuardianVerdict(
            allowed=True, verdict="EMERGENCY_BYPASS",
            reason="Emergency tool — all checks bypassed",
            trace=trace, suggestions=[], caller_role=role,
            budget_remaining=budget_remaining,
        )
    trace.append(TraceStep(1, "Emergency Check", "N/A", "Not an emergency tool"))

    # ── Step 2: Role Resolution ───────────────────────────────────
    role = resolve_role(caller_id)
    trace.append(TraceStep(2, "Role Resolution", "PASS", f"Caller '{caller_id}' → role '{role}'"))

    # ── Step 3: Admin Gate ────────────────────────────────────────
    if role == "admin":
        trace.append(TraceStep(3, "Admin Gate", "PASS", "Admin role — full access granted, skipping remaining checks"))
        budget_remaining = _get_budget_remaining(caller_id, role, None)

        ledger.log(
            caller_id=caller_id, caller_role=role, tool=tool_name,
            params=params, verdict="ALLOW",
            reason="Admin — full access",
            trace=trace, suggestions=[],
            budget_remaining=budget_remaining,
        )
        return GuardianVerdict(
            allowed=True, verdict="ALLOW",
            reason="Admin — full access",
            trace=trace, suggestions=[], caller_role=role,
            budget_remaining=budget_remaining,
        )
    trace.append(TraceStep(3, "Admin Gate", "N/A", f"Role '{role}' is not admin — continuing checks"))

    # ── Step 4: Admin-Only Gate ───────────────────────────────────
    if tool_name in ADMIN_ONLY_TOOLS:
        trace.append(TraceStep(4, "Admin-Only Gate", "BLOCKED", f"Tool '{tool_name}' requires admin role"))
        suggestions.append(f"Ask an admin (e.g., dr_sharma) to perform '{tool_name}' on your behalf")
        suggestions.append(f"Request temporary admin access via negotiation_request")

        ledger.log(
            caller_id=caller_id, caller_role=role, tool=tool_name,
            params=params, verdict="BLOCK",
            reason=f"Tool '{tool_name}' is admin-only",
            trace=trace, suggestions=suggestions,
        )
        return GuardianVerdict(
            allowed=False, verdict="BLOCK",
            reason=f"Tool '{tool_name}' is admin-only",
            trace=trace, suggestions=suggestions, caller_role=role,
        )
    trace.append(TraceStep(4, "Admin-Only Gate", "PASS", "Tool is not admin-only"))

    # ── Step 5: Delegation Lookup ─────────────────────────────────
    delegation = delegation_manager.find_active(caller_id)
    if delegation:
        delegation_id = delegation.token_id
        trace.append(TraceStep(5, "Delegation Lookup", "FOUND", f"Active delegation '{delegation_id}' from '{delegation.grantor_id}'"))
    else:
        trace.append(TraceStep(5, "Delegation Lookup", "NOT_FOUND", "No active delegation"))

    # ── Step 6: Delegation Scope / Role Permission ────────────────
    allowed_by_role = tool_name in ROLE_ALLOWED_TOOLS.get(role, set())
    allowed_by_delegation = delegation is not None and tool_name in delegation.scope

    if allowed_by_role:
        trace.append(TraceStep(6, "Permission Check", "PASS", f"Tool '{tool_name}' is in {role}'s allowed set"))
    elif allowed_by_delegation:
        trace.append(TraceStep(6, "Permission Check", "PASS", f"Tool '{tool_name}' is in delegation scope {delegation.scope}"))
    else:
        detail = f"Tool '{tool_name}' is not in {role}'s allowed set"
        if delegation:
            detail += f" and not in delegation scope {delegation.scope}"
        trace.append(TraceStep(6, "Permission Check", "BLOCKED", detail))

        suggestions.append(f"Ask admin to grant delegation for '{tool_name}'")
        if not delegation:
            suggestions.append(f"Use negotiation_request to request access to '{tool_name}'")

        ledger.log(
            caller_id=caller_id, caller_role=role, tool=tool_name,
            params=params, verdict="BLOCK",
            reason=f"'{role}' does not have access to '{tool_name}'",
            trace=trace, suggestions=suggestions,
            delegation_id=delegation_id,
        )
        return GuardianVerdict(
            allowed=False, verdict="BLOCK",
            reason=f"'{role}' does not have access to '{tool_name}'",
            trace=trace, suggestions=suggestions, caller_role=role,
            delegation_id=delegation_id,
        )

    # ── Step 7: PHI Gate ──────────────────────────────────────────
    if tool_name in PHI_TOOLS:
        if role in ("admin", "doctor"):
            trace.append(TraceStep(7, "PHI Gate", "PASS", f"Role '{role}' has PHI access"))
        elif delegation and delegation.phi_access:
            trace.append(TraceStep(7, "PHI Gate", "PASS", "PHI access granted via delegation"))
        else:
            trace.append(TraceStep(7, "PHI Gate", "BLOCKED", f"Role '{role}' cannot access PHI data"))
            suggestions.append("Ask a doctor or admin to retrieve this information for you")
            suggestions.append("Request PHI access via delegation_grant (admin only)")

            ledger.log(
                caller_id=caller_id, caller_role=role, tool=tool_name,
                params=params, verdict="BLOCK",
                reason="PHI access denied",
                trace=trace, suggestions=suggestions,
                delegation_id=delegation_id,
            )
            return GuardianVerdict(
                allowed=False, verdict="BLOCK",
                reason="PHI access denied",
                trace=trace, suggestions=suggestions, caller_role=role,
                delegation_id=delegation_id,
            )
    else:
        trace.append(TraceStep(7, "PHI Gate", "N/A", "Tool does not access PHI"))

    # ── Step 8: Budget Check ──────────────────────────────────────
    if tool_name in COST_TOOLS and cost > 0:
        remaining = _get_budget_remaining(caller_id, role, delegation)
        if cost > remaining:
            trace.append(TraceStep(8, "Budget Check", "BLOCKED", f"Cost ₹{cost:.0f} exceeds remaining budget ₹{remaining:.0f}"))
            suggestions.append(f"Reduce order to ₹{remaining:.0f} or less")
            suggestions.append("Ask admin to increase budget via delegation_grant")

            ledger.log(
                caller_id=caller_id, caller_role=role, tool=tool_name,
                params=params, verdict="BLOCK",
                reason=f"Budget exceeded: ₹{cost:.0f} > ₹{remaining:.0f} remaining",
                trace=trace, suggestions=suggestions,
                delegation_id=delegation_id,
                budget_remaining=remaining,
            )
            return GuardianVerdict(
                allowed=False, verdict="BLOCK",
                reason=f"Budget exceeded: ₹{cost:.0f} > ₹{remaining:.0f} remaining",
                trace=trace, suggestions=suggestions, caller_role=role,
                delegation_id=delegation_id,
                budget_remaining=remaining,
            )
        trace.append(TraceStep(8, "Budget Check", "PASS", f"Cost ₹{cost:.0f} within budget (₹{remaining:.0f} remaining)"))
    else:
        trace.append(TraceStep(8, "Budget Check", "N/A", "No cost or not a cost-bearing tool"))

    # ── Step 9: Pharmacy Allowlist ────────────────────────────────
    pharmacy = params.get("pharmacy", "")
    if tool_name in ("pharmacy_order", "pharmacy_refill") and pharmacy:
        if pharmacy not in APPROVED_PHARMACIES:
            trace.append(TraceStep(9, "Pharmacy Allowlist", "BLOCKED", f"'{pharmacy}' is not an approved pharmacy"))
            suggestions.append(f"Use an approved pharmacy: {', '.join(APPROVED_PHARMACIES)}")

            ledger.log(
                caller_id=caller_id, caller_role=role, tool=tool_name,
                params=params, verdict="BLOCK",
                reason=f"Pharmacy '{pharmacy}' is not approved",
                trace=trace, suggestions=suggestions,
                delegation_id=delegation_id,
            )
            return GuardianVerdict(
                allowed=False, verdict="BLOCK",
                reason=f"Pharmacy '{pharmacy}' is not approved",
                trace=trace, suggestions=suggestions, caller_role=role,
                delegation_id=delegation_id,
            )
        trace.append(TraceStep(9, "Pharmacy Allowlist", "PASS", f"'{pharmacy}' is an approved pharmacy"))
    else:
        trace.append(TraceStep(9, "Pharmacy Allowlist", "N/A", "Not a pharmacy order or no pharmacy specified"))

    # ── All checks passed ─────────────────────────────────────────
    budget_remaining = _get_budget_remaining(caller_id, role, delegation)

    # Record spending if cost-bearing
    if tool_name in COST_TOOLS and cost > 0:
        _record_spend(caller_id, cost, delegation)
        budget_remaining = _get_budget_remaining(caller_id, role, delegation)

    ledger.log(
        caller_id=caller_id, caller_role=role, tool=tool_name,
        params=params, verdict="ALLOW",
        reason="All Guardian checks passed",
        trace=trace, suggestions=[],
        delegation_id=delegation_id,
        budget_remaining=budget_remaining,
    )
    return GuardianVerdict(
        allowed=True, verdict="ALLOW",
        reason="All Guardian checks passed",
        trace=trace, suggestions=[], caller_role=role,
        delegation_id=delegation_id,
        budget_remaining=budget_remaining,
    )


def format_trace(verdict: GuardianVerdict) -> str:
    """Format a Guardian verdict into a human-readable trace string."""
    lines = [
        f"╔══ Guardian Pipeline ═══════════════════════════",
        f"║ Caller: {verdict.caller_role} | Verdict: {verdict.verdict}",
        f"║ Reason: {verdict.reason}",
        f"╠══ Trace ═════════════════════════════════════",
    ]
    for step in verdict.trace:
        icon = {"PASS": "✅", "BLOCKED": "🚫", "N/A": "⬜", "FOUND": "🔍", "NOT_FOUND": "⬜", "SKIP": "⏭️"}.get(step.result, "❓")
        lines.append(f"║ {icon} Step {step.step}: {step.name} → {step.result}")
        lines.append(f"║    {step.detail}")
    if verdict.suggestions:
        lines.append(f"╠══ Suggestions ═══════════════════════════════")
        for s in verdict.suggestions:
            lines.append(f"║ 💡 {s}")
    if verdict.budget_remaining is not None:
        lines.append(f"╠══ Budget ════════════════════════════════════")
        lines.append(f"║ 💰 Remaining: ₹{verdict.budget_remaining:,.0f}")
    if verdict.delegation_id:
        lines.append(f"╠══ Delegation ════════════════════════════════")
        lines.append(f"║ 🔑 Token: {verdict.delegation_id}")
    lines.append(f"╚══════════════════════════════════════════════")
    return "\n".join(lines)
