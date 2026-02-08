# Policy Engine

> **Configure security rules, data classification, and enforcement**

## Overview

The ArmorIQ Policy Engine provides granular control over tool execution. Policies are evaluated against every tool call, with automatic data classification to detect sensitive information.

---

## Policy Structure

```json
{
  "version": 1,
  "updatedAt": "2024-01-01T00:00:00Z",
  "updatedBy": "admin",
  "policy": {
    "rules": [
      {
        "id": "policy1",
        "action": "deny",
        "tool": "*",
        "dataClass": "PCI"
      }
    ]
  },
  "history": []
}
```

---

## Policy Rules

### Rule Schema

```typescript
interface PolicyRule {
  id: string;           // Unique identifier (e.g., "policy1")
  action: PolicyAction; // "allow" | "deny" | "require_approval"
  tool: string;         // Tool name or "*" for all
  dataClass?: DataClass; // Optional data classification
  params?: object;      // Optional parameter constraints
  scope?: PolicyScope;  // "org" | "project" | "run"
}
```

### Actions

| Action | Behavior |
|--------|----------|
| `allow` | Permit tool execution |
| `deny` | Block tool execution |
| `require_approval` | Pause for user approval |

### Rule Evaluation Order

Rules are evaluated **top-to-bottom**. First matching rule wins.

```
Rule 1: deny  tool=send_email dataClass=PCI
Rule 2: allow tool=send_email
Rule 3: deny  tool=*

→ send_email with PCI data → BLOCKED (Rule 1)
→ send_email without PCI → ALLOWED (Rule 2)
→ web_search → BLOCKED (Rule 3)
```

---

## Data Classification

ArmorIQ automatically detects sensitive data in tool parameters:

### Classes

| Class | Description | Detection |
|-------|-------------|-----------|
| `PCI` | Payment Card Industry data | Credit card numbers (Luhn check) |
| `PAYMENT` | Financial data | bank, invoice, payment, routing |
| `PHI` | Protected Health Info | patient, diagnosis, medical |
| `PII` | Personal Identifiable Info | SSN patterns, email detection |

### Detection Logic

```typescript
// Credit card detection with Luhn validation
function hasCardNumber(texts: string[]): boolean {
  const pattern = /\b\d{13,19}\b/;
  // Plus Luhn checksum validation
}

// Keyword-based detection
function hasPaymentKeywords(texts: string[]): boolean {
  const keywords = ["bank", "invoice", "payment", "billing"];
  return texts.some(text => keywords.some(kw => text.includes(kw)));
}
```

---

## Runtime Policy Updates

When `policyUpdateEnabled: true`, authorized users can update policies via natural language:

### Policy Commands

| Command | Description |
|---------|-------------|
| `Policy list` | Show all rules |
| `Policy get policy1` | Show one rule |
| `Policy delete policy1` | Remove a rule |
| `Policy reset` | Clear all rules |
| `Policy update policy1: allow send_email` | Update existing |
| `Policy new: block upload_file for PII` | Create new rule |
| `Policy prioritize policy2 1` | Move rule to position |

### Examples

```
User: Policy new: block send_email for credit card data

→ Creates:
{
  "id": "policy1",
  "action": "deny",
  "tool": "send_email",
  "dataClass": "PCI"
}
```

```
User: Policy update policy1: allow send_email

→ Updates policy1 action to "allow"
```

```
User: Policy list

→ Policy version 3:
  1. id=policy1 action=deny tool=send_email dataClass=PCI
  2. id=policy2 action=allow tool=*
```

### Authorization

Only users in `policyUpdateAllowList` can modify policies:

```yaml
policyUpdateAllowList:
  - "+15550001111"
  - "admin@company.com"
  - "*"  # Allow all users
```

---

## Policy File Format

### `armoriq.policy.json`

```json
{
  "version": 5,
  "updatedAt": "2024-01-15T10:30:00Z",
  "updatedBy": "+15550001111",
  "policy": {
    "rules": [
      {
        "id": "block-pci-all",
        "action": "deny",
        "tool": "*",
        "dataClass": "PCI"
      },
      {
        "id": "block-phi-external",
        "action": "deny",
        "tool": "send_email",
        "dataClass": "PHI"
      },
      {
        "id": "require-approval-payments",
        "action": "require_approval",
        "tool": "make_payment",
        "dataClass": "PAYMENT"
      },
      {
        "id": "allow-read",
        "action": "allow",
        "tool": "read"
      }
    ]
  },
  "history": [
    {
      "version": 4,
      "updatedAt": "2024-01-14T15:00:00Z",
      "updatedBy": "+15550001111",
      "reason": "Added PHI protection",
      "policy": { "rules": [...] }
    }
  ]
}
```

---

## Policy Configuration

### Inline Policy

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
      policy:
        rules:
          - id: "block-pci"
            action: "deny"
            tool: "*"
            dataClass: "PCI"
```

### External File

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
      policyStorePath: "./policies/production.json"
```

---

## Advanced: PolicyEngine

For more complex scenarios, `PolicyEngine` (in `src/policy-engine.ts`) provides:

### Condition Evaluation

```typescript
interface PolicyCondition {
  type: "time_range" | "amount_limit" | "role_check";
  params: Record<string, unknown>;
}
```

Example rule with conditions:

```json
{
  "id": "after-hours-block",
  "action": "deny",
  "tool": "make_payment",
  "conditions": [
    {
      "type": "time_range",
      "params": { "after": "17:00", "before": "09:00" }
    }
  ]
}
```

### Amount Limits

```json
{
  "id": "high-value-approval",
  "action": "require_approval",
  "tool": "make_payment",
  "conditions": [
    {
      "type": "amount_limit",
      "params": { "max": 2000, "currency": "USD" }
    }
  ]
}
```

---

## Healthcare Example

```json
// policies/healthcare.json
{
  "version": 1,
  "policy": {
    "rules": [
      {
        "id": "block-phi-external",
        "action": "deny",
        "tool": "send_email",
        "dataClass": "PHI"
      },
      {
        "id": "block-phi-upload",
        "action": "deny",
        "tool": "upload_file",
        "dataClass": "PHI"
      },
      {
        "id": "require-approval-records",
        "action": "require_approval",
        "tool": "access_patient_records"
      },
      {
        "id": "allow-internal",
        "action": "allow",
        "tool": "*",
        "scope": "project"
      }
    ]
  }
}
```

---

## Crypto-Bound Policies

When `cryptoPolicyEnabled: true`:

1. Policy hash embedded in CSRG token at issuance
2. At execution, policy digest verified against token
3. Tampering detected if digests mismatch

```typescript
// Compute policy digest
const digest = computePolicyDigest(policy.rules);
// SHA-256 of canonicalized rules
```

---

## Related Documentation

- [Configuration Reference](./configuration.md) - Enable policy updates
- [Architecture](./architecture.md) - Tier 2 details
- [API Reference](./api-reference.md) - `policy_update` tool
