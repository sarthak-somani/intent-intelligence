# Hospital Guardian MCP Server

Enterprise-grade hospital safety system built as a **Model Context Protocol (MCP) server** with a 9-step Guardian enforcement pipeline, SHA-256 Merkle audit ledger, and HMAC-JWT delegation tokens.

## Quick Start

```bash
pip install -r requirements.txt

# Local (stdio transport)
python -m hospital.server

# Local (HTTP transport)
uvicorn api.index:app --port 8000

# Deploy to Vercel
vercel --prod
```

## Architecture

- **21 tools** across 8 categories (Emergency, Pharmacy, Appointments, Records, Laboratory, Delegation, Audit, Negotiation)
- **9-step Guardian Pipeline** — deterministic enforcement with full trace on every call
- **SHA-256 Hash Chain + Merkle Tree** — cryptographic audit integrity
- **HMAC-SHA256 JWT Delegation** — scoped, time-limited, budget-capped access sharing
- **6 roles**: admin, doctor, nurse, pharmacist, caretaker, unknown

## Roles

| Role | Caller ID | Access |
|------|-----------|--------|
| Admin | `dr_sharma` | Full access to all 21 tools |
| Doctor | `dr_patel` | Records, labs, pharmacy, appointments |
| Nurse | `nurse_priya` | View records, appointments, interaction checks |
| Pharmacist | `pharmacist_ravi` | Pharmacy tools only |
| Caretaker | `caretaker_amit` | Limited pharmacy + appointments (via delegation) |
| Unknown | any other | Emergency tools only |

## Guardian Pipeline (9 Steps)

Every tool call passes through:

1. **Emergency Check** — Emergency tools bypass all checks
2. **Role Resolution** — Map caller_id to role
3. **Admin Gate** — Admins skip remaining checks
4. **Admin-Only Gate** — Block delegation/audit for non-admins
5. **Delegation Lookup** — Check for active JWT delegation
6. **Permission Check** — Verify role or delegation scope
7. **PHI Gate** — Block PHI access for unauthorized roles
8. **Budget Check** — Verify spending limits
9. **Pharmacy Allowlist** — Only approved pharmacies

Each blocked step returns actionable **suggestions** for the user.

## Connect to ArmorIQ Platform

Add the deployed Vercel URL as an MCP server on [platform.armoriq.ai](https://platform.armoriq.ai).
