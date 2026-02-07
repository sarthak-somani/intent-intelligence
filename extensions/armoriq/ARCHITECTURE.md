# ArmorIQ Architecture Documentation

## Overview

ArmorIQ is an **intent-security integration layer** that provides a comprehensive security framework for AI agent tool execution. It implements a **5-tiered security architecture** that ensures every tool call is:
1. **Planned** - Captured in an explicit intent plan
2. **Policy-checked** - Evaluated against configurable rules
3. **Cryptographically verified** - Secured via CSRG Merkle proofs
4. **Guardian-protected** - Integrated security orchestration
5. **Audit-logged** - Recorded in an immutable ledger

---

## High-Level System Architecture

```mermaid
flowchart TB
    subgraph UserLayer["User Layer"]
        WA[WhatsApp]
        SL[Slack]
        TG[Telegram]
        HTTP["/tools/invoke"]
    end

    subgraph OpenClaw["OpenClaw Gateway"]
        GW[Gateway Server]
        RUNNER[PI Embedded Runner]
    end

    subgraph ArmorIQ["ArmorIQ Plugin"]
        direction TB
        T1["🎯 Tier 1: Intent Planning"]
        T2["📋 Tier 2: Policy Enforcement"]
        T3["🔐 Tier 3: CSRG Verification"]
        T4["🛡️ Tier 4: Guardian Integration"]
        T5["📜 Tier 5: Audit Ledger"]
    end

    subgraph Backend["ArmorIQ Backend"]
        IAP[IAP Service]
        CSRG[CSRG Server]
    end

    UserLayer --> GW
    GW --> RUNNER
    RUNNER --> ArmorIQ
    ArmorIQ --> Backend

    T1 --> T2 --> T3 --> T4 --> T5
```

---

## The 5-Tiered Security Architecture

ArmorIQ implements a **fail-closed, defense-in-depth** security model where each tier adds an additional layer of protection.

```mermaid
graph LR
    subgraph Tier1["Tier 1: Intent Planning"]
        IP[buildPlanFromPrompt]
        IC[capturePlan]
        IT[getIntentToken]
    end

    subgraph Tier2["Tier 2: Policy Enforcement"]
        PS[PolicyStore]
        PE[evaluatePolicy]
        DC[detectDataClasses]
    end

    subgraph Tier3["Tier 3: CSRG Verification"]
        CPS[CryptoPolicyService]
        IVS[IAPVerificationService]
        MP[Merkle Proofs]
    end

    subgraph Tier4["Tier 4: Guardian Integration"]
        AG[ArmorIQGuardian]
        IV[IntentVerifier]
        AA[AuthAuthority]
    end

    subgraph Tier5["Tier 5: Audit Ledger"]
        ML[MerkleLedger]
        WAL[Write-Ahead Log]
        INT[Integrity Verification]
    end

    Tier1 --> Tier2 --> Tier3 --> Tier4 --> Tier5
```

---

### Tier 1: Intent Planning Layer

**Purpose**: Capture the user's intent before any tool execution occurs.

```mermaid
sequenceDiagram
    participant User
    participant Agent
    participant Planner as Intent Planner
    participant SDK as ArmorIQ SDK
    participant IAP as IAP Backend

    User->>Agent: Send request
    Agent->>Planner: Build plan from prompt
    Planner->>Planner: Generate tool list
    Planner->>SDK: capturePlan(plan)
    SDK->>IAP: POST /intent
    IAP-->>SDK: Intent Token + Merkle Root
    SDK-->>Agent: Token cached for run
```

**Key Components**:

| Component | File | Description |
|-----------|------|-------------|
| `buildPlanFromPrompt` | [index.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/index.ts#L1050-L1157) | Uses LLM to generate a JSON plan from user prompt |
| `ArmorIQClient` | SDK | Captures plan and obtains intent tokens from IAP |
| `planCache` | [index.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/index.ts#L119) | Per-run cache for plan/token pairs |

**Plan Schema**:
```json
{
  "steps": [
    {
      "action": "tool_name",
      "mcp": "openclaw",
      "description": "optional",
      "metadata": { "inputs": {} }
    }
  ],
  "metadata": { "goal": "user's goal" }
}
```

---

### Tier 2: Policy Enforcement Layer

**Purpose**: Evaluate tool calls against configurable security rules with data classification.

```mermaid
flowchart TD
    subgraph Input["Tool Call Input"]
        TN[Tool Name]
        TP[Tool Parameters]
    end

    subgraph Detection["Data Classification"]
        PCI["💳 PCI (Credit Cards)"]
        PAY["💰 PAYMENT"]
        PHI["🏥 PHI (Health)"]
        PII["👤 PII (Personal)"]
    end

    subgraph PolicyEval["Policy Evaluation"]
        PS[(PolicyStore)]
        RULES[Policy Rules]
        MATCH{Rule Match?}
    end

    subgraph Outcomes["Decision"]
        ALLOW[✅ Allow]
        DENY[❌ Deny]
        APPROVE[⏳ Require Approval]
    end

    Input --> Detection
    Detection --> PolicyEval
    PS --> RULES
    RULES --> MATCH
    MATCH -->|allow| ALLOW
    MATCH -->|deny| DENY
    MATCH -->|require_approval| APPROVE
```

**Key Components**:

| Component | File | Description |
|-----------|------|-------------|
| `PolicyStore` | [policy.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/policy.ts#L305-L492) | Persistent policy storage with versioning and history |
| `evaluatePolicy` | [policy.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/policy.ts#L232-L284) | Evaluates tool calls against policy rules |
| `detectDataClasses` | [policy.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/policy.ts#L215-L230) | Automatically classifies sensitive data |
| `PolicyEngine` | [policy-engine.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/policy-engine.ts#L74-L266) | Advanced rule engine with conditions |

**Policy Rule Actions**:
- `allow` - Permit tool execution
- `deny` - Block tool execution
- `require_approval` - Pause for user approval

**Data Classes**:
- **PCI** - Credit card numbers (Luhn-validated)
- **PAYMENT** - Financial/billing terms
- **PHI** - Health/medical information
- **PII** - Personal identifiable information

---

### Tier 3: CSRG Cryptographic Verification Layer

**Purpose**: Provide cryptographic guarantees through Merkle tree proofs.

```mermaid
flowchart TB
    subgraph TokenGeneration["Token Issuance"]
        POLICY[Policy State]
        PLAN[Intent Plan]
        MERKLE[Build Merkle Tree]
        SIGN["🔑 Ed25519 Signature"]
        TOKEN[CSRG Token]
    end

    subgraph Verification["Execution Verification"]
        TOOL[Tool Call]
        PROOF[Extract Proof]
        VERIFY["Verify Merkle Path"]
        HASH["Validate Hash Chain"]
    end

    POLICY --> MERKLE
    PLAN --> MERKLE
    MERKLE --> SIGN --> TOKEN

    TOKEN --> VERIFICATION
    TOOL --> PROOF --> VERIFY --> HASH

    subgraph Result["Result"]
        VALID[✅ Cryptographically Valid]
        INVALID[❌ Tamper Detected]
    end

    HASH -->|Valid| VALID
    HASH -->|Invalid| INVALID
```

**Key Components**:

| Component | File | Description |
|-----------|------|-------------|
| `CryptoPolicyService` | [crypto-policy.service.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/crypto-policy.service.ts#L149-L355) | Issues CSRG tokens with embedded policy |
| `IAPVerificationService` | [iap-verfication.service.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/iap-verfication.service.ts#L164-L342) | Verifies steps against IAP backend |
| `computePolicyDigest` | [crypto-policy.service.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/crypto-policy.service.ts#L133-L147) | SHA-256 hash of policy rules |

**CSRG Verification Flow**:
1. Policy embedded in Merkle tree at token issuance
2. Each tool step gets a cryptographic proof
3. At execution, proof is validated against Merkle root
4. Tampering detected if hash chain broken

---

### Tier 4: Guardian Integration Layer

**Purpose**: Central orchestration of all security components.

```mermaid
flowchart TD
    subgraph Guardian["ArmorIQGuardian"]
        AA[AuthAuthority<br/>JWT Management]
        IV[IntentVerifier<br/>Risk Detection]
        PE[PolicyEngine<br/>Rule Evaluation]
        ML[MerkleLedger<br/>Audit Trail]
    end

    subgraph Request["Incoming Request"]
        TOKEN[JWT Token]
        TOOL[Tool + Args]
        PROMPT[User Prompt]
    end

    subgraph Validation["Validation Pipeline"]
        V1["1️⃣ Token Verification"]
        V2["2️⃣ Intent Verification"]
        V3["3️⃣ Policy Check"]
        V4["4️⃣ Audit Log"]
    end

    Request --> Guardian
    TOKEN --> AA --> V1
    PROMPT --> IV --> V2
    TOOL --> PE --> V3
    V3 --> ML --> V4

    V1 -->|Invalid| BLOCK[❌ Block]
    V2 -->|High Risk| BLOCK
    V3 -->|Denied| BLOCK
    V4 --> ALLOW[✅ Execute]
```

**Key Components**:

| Component | File | Description |
|-----------|------|-------------|
| `ArmorIQGuardian` | [guardian-integration.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/guardian-integration.ts#L30-L233) | Main orchestration class |
| `IntentVerifier` | [intent-verifier.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/intent-verifier.ts#L19-L145) | Detects intent mismatches |
| `AuthAuthority` | [auth-authority.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/auth-authority.ts) | JWT token signing/verification |

**Intent Verification Heuristics**:
- **Financial Risk Detection**: Flags financial tools without explicit user authorization
- **Dangerous Phrase Detection**: Catches override/bypass attempts
- **High-Risk Verbs**: buy, purchase, pay, transfer, delete, etc.

---

### Tier 5: Audit Ledger Layer

**Purpose**: Immutable, tamper-evident logging with cryptographic integrity.

```mermaid
flowchart LR
    subgraph Chain["Merkle Ledger Chain"]
        E1["Entry 1<br/>hash: abc123"]
        E2["Entry 2<br/>prevHash: abc123<br/>hash: def456"]
        E3["Entry 3<br/>prevHash: def456<br/>hash: ghi789"]
        EN["Entry N<br/>..."]
    end

    E1 --> E2 --> E3 --> EN

    subgraph Entry["Ledger Entry"]
        ID[UUID]
        PREV[Previous Hash]
        TS[Timestamp]
        ACTOR[Actor]
        ACTION[Action Type]
        PAYLOAD[Payload Data]
        HASH[Entry Hash]
    end

    subgraph Actions["Action Types"]
        TC[TOOL_CALL]
        AF[AUTH_FAILURE]
        PV[POLICY_VIOLATION]
        IW[INTENT_WARNING]
    end
```

**Key Components**:

| Component | File | Description |
|-----------|------|-------------|
| `MerkleLedger` | [ledger.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/ledger.ts#L56-L274) | Cryptographic ledger implementation |
| Write-Ahead Log | [ledger.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/ledger.ts#L114-L127) | Crash recovery mechanism |
| Integrity Verification | [ledger.ts](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/src/ledger.ts#L209-L243) | Detects chain tampering |

**Features**:
- **Write-Ahead Logging**: Persists to disk before acknowledgment
- **Hash Chain**: Each entry hash includes previous entry hash
- **Integrity Check**: Re-compute all hashes to detect tampering
- **Query Support**: Filter by action, actor, or time range

---

## Complete Request Flow

```mermaid
sequenceDiagram
    participant User
    participant Channel as WhatsApp/Slack/Telegram
    participant Gateway as OpenClaw Gateway
    participant Plugin as ArmorIQ Plugin
    participant Policy as PolicyStore
    participant CSRG as CSRG Service
    participant Tool
    participant Ledger as MerkleLedger

    User->>Channel: "Find flights to Boston"
    Channel->>Gateway: Message

    rect rgb(230, 245, 255)
        Note over Gateway,Plugin: Phase 1: Intent Planning
        Gateway->>Plugin: on_run_start(prompt)
        Plugin->>Plugin: buildPlanFromPrompt()
        Plugin->>CSRG: capturePlan + getIntentToken
        CSRG-->>Plugin: Token + Merkle Root
    end

    rect rgb(255, 245, 230)
        Note over Plugin,Tool: Phase 2: Tool Execution
        Gateway->>Plugin: before_tool_call(web_search)
        Plugin->>Plugin: Check plan contains tool
        Plugin->>Policy: evaluatePolicy(tool, params)
        Policy-->>Plugin: allowed=true
        Plugin->>CSRG: verifyStep (if CSRG enabled)
        CSRG-->>Plugin: verified=true
        Plugin->>Tool: Execute tool
        Tool-->>Plugin: Result
        Plugin->>Ledger: append(TOOL_CALL)
    end

    rect rgb(230, 255, 230)
        Note over Plugin,User: Phase 3: Response
        Plugin-->>Gateway: Tool result
        Gateway-->>Channel: Response
        Channel-->>User: "Found 5 flights..."
    end
```

---

## Component Interaction Map

```mermaid
graph TB
    subgraph Core["Core Plugin (index.ts)"]
        REG[register]
        HOOKS[before_tool_call<br/>on_run_start<br/>on_run_end]
        TOOLS[policy_update tool]
    end

    subgraph Services["Service Layer"]
        PS[PolicyStore]
        CPS[CryptoPolicyService]
        IVS[IAPVerificationService]
    end

    subgraph Guardian["Guardian Layer"]
        AG[ArmorIQGuardian]
        IV[IntentVerifier]
        AA[AuthAuthority]
        PEN[PolicyEngine]
    end

    subgraph Audit["Audit Layer"]
        ML[MerkleLedger]
    end

    subgraph External["External"]
        SDK[ArmorIQ SDK]
        IAP[IAP Backend]
        CSRG[CSRG Server]
    end

    REG --> HOOKS
    REG --> TOOLS
    HOOKS --> PS
    HOOKS --> CPS
    HOOKS --> SDK

    PS --> CPS
    CPS --> CSRG
    SDK --> IAP
    IVS --> IAP
    IVS --> CSRG

    AG --> IV
    AG --> AA
    AG --> PEN
    AG --> ML
```

---

## Security Guarantees

| Guarantee | Mechanism | Tier |
|-----------|-----------|------|
| **Intent Drift Prevention** | Plan allowlist enforcement | Tier 1 |
| **Fail-Closed Enforcement** | Block on missing plan/token | Tier 1 |
| **Data Classification** | Automatic PCI/PII/PHI detection | Tier 2 |
| **Policy Versioning** | History with audit trail | Tier 2 |
| **Cryptographic Proof** | Merkle tree + Ed25519 | Tier 3 |
| **Tamper Detection** | Hash chain verification | Tier 3, 5 |
| **Financial Protection** | High-risk intent detection | Tier 4 |
| **Immutable Audit** | Write-ahead ledger | Tier 5 |

---

## Configuration Reference

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
      
      # Tier 1: Intent Planning
      validitySeconds: 60
      
      # Tier 2: Policy Enforcement  
      policyStorePath: "./armoriq.policy.json"
      policyUpdateEnabled: true
      policyUpdateAllowList: ["+15550001111"]
      
      # Tier 3: CSRG Verification
      cryptoPolicyEnabled: true
      csrgEndpoint: "http://localhost:8000"
      
      # Tier 4: Guardian
      iapEndpoint: "https://customer-iap.armoriq.ai"
      proxyEndpoint: "https://customer-proxy.armoriq.ai"
      backendEndpoint: "https://customer-api.armoriq.ai"
```

---

## File Structure

```
extensions/armoriq/
├── index.ts                    # Main plugin (1944 lines)
├── index.test.ts              # Plugin tests
├── ARCHITECTURE.md            # This document
├── README.md                  # Quick start guide
├── openclaw.plugin.json       # Plugin manifest
├── package.json
├── policies/
│   └── healthcare.json        # Example policies
├── logs/
│   └── guardian_audit.log     # Audit log output
└── src/
    ├── auth-authority.ts      # JWT management
    ├── crypto-policy.service.ts # CSRG token issuance
    ├── guardian-integration.ts  # Central orchestration
    ├── guardian-proxy.ts       # HTTP proxy layer
    ├── guardian-schemas.ts     # Type definitions
    ├── iap-verfication.service.ts # IAP verification
    ├── intent-verifier.ts      # Intent mismatch detection
    ├── ledger.ts               # Merkle ledger
    ├── policy-engine.ts        # Advanced rule engine
    ├── policy.ts               # Policy store & evaluation
    └── test-*.ts               # Test files
```

---

## Related Documentation

- [AIQREADME.md](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/AIQREADME.md) - Integration guide and demo runbook
- [armoriq.policy.json](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/armoriq.policy.json) - Current policy state
- [openclaw.plugin.json](file:///c:/Users/soman/OneDrive/Coding/ArmorIQ/aiq-openclaw/extensions/armoriq/openclaw.plugin.json) - Plugin configuration schema
