# ArmorIQ Extension Documentation

> **Comprehensive documentation for the ArmorIQ Intent Security Framework**

## 📚 Documentation Index

| Document | Description |
|----------|-------------|
| [Getting Started](./getting-started.md) | Quick installation and configuration guide |
| [Architecture](./architecture.md) | 5-tier security architecture deep dive |
| [Configuration Reference](./configuration.md) | Complete configuration options |
| [Policy Engine](./policy-engine.md) | Policy rules, data classification, and enforcement |
| [API Reference](./api-reference.md) | Plugin hooks, tools, and HTTP endpoints |
| [Security Model](./security-model.md) | Cryptographic guarantees and threat model |
| [Demo & Testing](./demo-testing.md) | Demo scenarios and test commands |
| [Troubleshooting](./troubleshooting.md) | Common issues and debugging guide |

---

## What is ArmorIQ?

ArmorIQ is an **intent-security integration layer** for the OpenClaw agent runtime. It provides a comprehensive, defense-in-depth security framework that ensures every AI agent tool call is:

1. **Planned** – Captured in an explicit intent plan before execution
2. **Policy-checked** – Evaluated against configurable security rules
3. **Cryptographically verified** – Secured via CSRG Merkle proofs
4. **Guardian-protected** – Orchestrated through integrated security components
5. **Audit-logged** – Recorded in an immutable, tamper-evident ledger

---

## Key Features

### 🎯 Intent Planning & Enforcement
- Per-run planning with LLM-generated execution plans
- Fail-closed enforcement blocking unauthorized tool calls
- Intent drift detection for off-plan actions

### 📋 Policy Engine
- Flexible rule-based access control (allow/deny/require_approval)
- Automatic data classification (PCI, PAYMENT, PHI, PII)
- Runtime policy updates via natural language commands

### 🔐 Cryptographic Security
- CSRG Merkle tree tokens with Ed25519 signatures
- Policy digest verification at execution time
- Tamper-evident hash chains

### 📜 Immutable Audit
- Write-ahead logging (WAL) for crash recovery
- Cryptographic hash chain linking all entries
- Integrity verification on demand

---

## Quick Start

```yaml
# openclaw.json or config.yml
plugins:
  entries:
    armoriq:
      enabled: true
      apiKey: "your-api-key"
      userId: "user-123"
      agentId: "agent-456"
      policyUpdateEnabled: true
```

See [Getting Started](./getting-started.md) for complete setup instructions.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 1: Intent Planning                                        │
│  └─ buildPlanFromPrompt() → capturePlan() → getIntentToken()   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 2: Policy Enforcement                                     │
│  └─ PolicyStore → evaluatePolicy() → detectDataClasses()       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 3: CSRG Verification                                      │
│  └─ CryptoPolicyService → IAPVerificationService → Merkle      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 4: Guardian Integration                                   │
│  └─ ArmorIQGuardian → IntentVerifier → AuthAuthority           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tier 5: Audit Ledger                                           │
│  └─ MerkleLedger → Write-Ahead Log → Integrity Verification    │
└─────────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
extensions/armoriq/
├── index.ts                     # Main plugin entry (1944 lines)
├── index.test.ts               # Comprehensive test suite
├── README.md                   # Extension overview
├── ARCHITECTURE.md             # Technical architecture
├── openclaw.plugin.json        # Plugin manifest
├── package.json
├── docs/                       # 📁 This documentation
├── policies/
│   └── healthcare.json         # Example policy definitions
├── logs/
│   └── guardian_audit.log      # Persistent audit trail
├── demo/                       # Demo assets
└── src/
    ├── auth-authority.ts       # JWT token management
    ├── crypto-policy.service.ts # CSRG token issuance
    ├── guardian-integration.ts # Central orchestration
    ├── guardian-proxy.ts       # HTTP proxy layer
    ├── guardian-schemas.ts     # Type definitions
    ├── iap-verfication.service.ts # IAP verification
    ├── intent-verifier.ts      # Intent mismatch detection
    ├── ledger.ts               # Merkle ledger
    ├── policy-engine.ts        # Advanced rule engine
    └── policy.ts               # Policy store & evaluation
```

---

## Related Resources

- [OpenClaw Main Repository](../../README.md)
- [ArmorIQ Integration Guide](../../AIQREADME.md)
- [Plugin Configuration Schema](../openclaw.plugin.json)
- [Policy State File](../../armoriq.policy.json)

---

## Contributing

1. Read the [Architecture](./architecture.md) document
2. Run existing tests: `pnpm vitest extensions/armoriq/index.test.ts`
3. Add tests for new features
4. Update documentation

---

## License

MIT License - See [LICENSE](../../../LICENSE)
