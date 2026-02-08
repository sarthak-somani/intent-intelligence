"""Deterministic policy engine — priority-ordered rules, no LLM in safety path."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from fnmatch import fnmatch

from hospital.config import (
    ADMIN_ONLY_TOOLS,
    COST_TOOLS,
    EMERGENCY_TOOLS,
    PHI_TOOLS,
    ROLE_ALLOWED_TOOLS,
)


class Action(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    CHECK_BUDGET = "check_budget"
    CHECK_ALLOWLIST = "check_allowlist"


@dataclass
class PolicyRule:
    name: str
    priority: int
    action: Action
    tools: set[str] | None = None          # None = all tools
    tool_patterns: list[str] | None = None  # fnmatch patterns
    roles: set[str] | None = None           # None = all roles
    data_class: str | None = None           # e.g. "PHI"
    description: str = ""


@dataclass
class PolicyResult:
    action: Action
    rule_name: str
    description: str
    matched: bool = True


# ── Built-in rules ───────────────────────────────────────────────────
RULES: list[PolicyRule] = sorted(
    [
        PolicyRule(
            name="emergency-bypass",
            priority=0,
            action=Action.ALLOW,
            tools=EMERGENCY_TOOLS,
            description="Emergency tools bypass all checks",
        ),
        PolicyRule(
            name="admin-full-access",
            priority=10,
            action=Action.ALLOW,
            roles={"admin"},
            description="Admin has unrestricted access to all tools",
        ),
        PolicyRule(
            name="admin-only-gate",
            priority=20,
            action=Action.DENY,
            tools=ADMIN_ONLY_TOOLS,
            description="Delegation and audit tools are admin-only",
        ),
        PolicyRule(
            name="phi-restrict",
            priority=30,
            action=Action.DENY,
            tools=PHI_TOOLS,
            roles={"nurse", "pharmacist", "caretaker", "unknown"},
            data_class="PHI",
            description="PHI access restricted to admin and doctor roles",
        ),
        PolicyRule(
            name="role-tool-allow",
            priority=40,
            action=Action.ALLOW,
            description="Allow tools in the role's allowed set",
        ),
        PolicyRule(
            name="budget-enforce",
            priority=50,
            action=Action.CHECK_BUDGET,
            tools=COST_TOOLS,
            description="Cost-bearing tools require budget check",
        ),
        PolicyRule(
            name="pharmacy-allowlist",
            priority=60,
            action=Action.CHECK_ALLOWLIST,
            tools={"pharmacy_order", "pharmacy_refill"},
            description="Pharmacy orders must use approved pharmacies",
        ),
    ],
    key=lambda r: r.priority,
)


def _tool_matches(rule: PolicyRule, tool_name: str) -> bool:
    """Check if a rule applies to the given tool."""
    if rule.tools is None and rule.tool_patterns is None:
        return True
    if rule.tools and tool_name in rule.tools:
        return True
    if rule.tool_patterns:
        return any(fnmatch(tool_name, p) for p in rule.tool_patterns)
    return False


def _role_matches(rule: PolicyRule, caller_role: str) -> bool:
    """Check if a rule applies to the given role."""
    if rule.roles is None:
        return True
    return caller_role in rule.roles


def evaluate(tool_name: str, caller_role: str) -> PolicyResult:
    """Evaluate the policy for a tool call. Returns the first matching rule result."""
    for rule in RULES:
        if not _tool_matches(rule, tool_name):
            continue
        if not _role_matches(rule, caller_role):
            continue

        # Special handling for the generic role-tool-allow rule
        if rule.name == "role-tool-allow":
            allowed = ROLE_ALLOWED_TOOLS.get(caller_role, set())
            if tool_name in allowed:
                return PolicyResult(
                    action=Action.ALLOW,
                    rule_name=rule.name,
                    description=f"Tool '{tool_name}' is in {caller_role}'s allowed set",
                )
            # Not in allowed set — continue to next rule (or fall through to deny)
            continue

        return PolicyResult(
            action=rule.action,
            rule_name=rule.name,
            description=rule.description,
        )

    # Default deny
    return PolicyResult(
        action=Action.DENY,
        rule_name="default-deny",
        description=f"No rule grants '{caller_role}' access to '{tool_name}'",
    )
