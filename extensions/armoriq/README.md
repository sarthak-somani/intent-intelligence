# 🛡️ ArmorIQ Guardian Kernel
> **Intent-Aware Security Framework for Autonomous Agents**

The **Guardian Kernel** is a "Defense-in-Depth" security overlay for the OpenClaw agent runtime. It transforms a standard AI agent into a verifiable, secure, and policy-compliant system suitable for high-risk environments (e.g., healthcare, finance).

## 🚀 Key Improvements & Features

We have upgraded the original `aiq-openclaw` with a **5-Tier Security Architecture**:

### 1. Tier 1: The "Sidecar Proxy" (Isolation Layer)
- **Ingress Sanitization:** Automatically detects and redacts PII (Emails, Phone Numbers, SSNs, Credit Cards) *before* the LLM ever sees the user prompt.
- **Egress Validation (Zod Contracts):** Prevents "Tool Hijacking" and injection attacks by enforcing strict schema validation on all tool arguments.
- **Components:** `GuardianProxy`, `GuardianSidecar`, `ToolContracts`.

### 2. Tier 2: Intent Verification
- **Heuristic Analysis:** Analyzes the user's natural language prompt against the attempted tool action.
- **Risk Detection:** Blocks high-risk actions (e.g., financial spend) if they aren't explicitly authorized in the prompt.
- **Override Protection:** Detects and blocks "Jailbreak" attempts (e.g., "Ignore safety protocols").
- **Components:** `IntentVerifier`.

### 3. Tier 3: Policy Engine
- **Granular Control:** Enforces logic-based rules (e.g., "Max spend < $2000", "No access after 5 PM").
- **Deny-by-Default:** Actions are blocked unless explicitly allowed by a policy.
- **JSON Rules:** Policies are defined in human-readable JSON files (e.g., `healthcare.json`).
- **Components:** `PolicyEngine`.

### 4. Tier 4: Delegation Authority (JWT)
- **Cryptographic Identity:** Every action requires a signed Checkpoint (JWT) proving the agent's role (e.g., `Caretaker`, `Auditor`).
- **Scope Enforcement:** Tokens carry specific scopes (e.g., `pharmacy:order`, `records:read`). Missing scopes result in immediate blocks.
- **Components:** `AuthAuthority`.

### 5. Tier 5: Immutable Forensic Audit (Merkle Ledger)
- **Tamper-Proof Logging:** Every action (allowed or blocked) is hashed and cryptographically linked to the previous entry.
- **Persistent Storage:** Uses Write-Ahead Logging (WAL) to persist audit trails to disk (`guardian_audit.log`).
- **Crash Recovery:** Automatically rebuilds state from disk on startup.
- **Chain Verification:** `verifyIntegrity()` ensures no log entry has been altered or deleted.
- **Components:** `MerkleLedger`.

---

## 📂 Project Structure

```
extensions/armoriq/
├── src/
│   ├── guardian-proxy.ts       # 🛡️ The 5-Tier Interceptor (Main Entry)
│   ├── guardian-integration.ts # 🧠 Core Integration Service
│   ├── guardian-schemas.ts     # 📜 Zod Validation Contracts
│   ├── intent-verifier.ts      # 🕵️ Intent Analysis Logic
│   ├── policy-engine.ts        # ⚖️ Rule Enforcement Engine
│   ├── auth-authority.ts       # 🔑 JWT Delegation System
│   └── ledger.ts               # 🔗 Immutable Merkle Ledger
├── policies/
│   └── healthcare.json         # 🏥 Example Policy Definitions
├── demo/
│   ├── run-scenario.ts         # 🎬 "Hero's Journey" Demo Script
│   ├── console-ui.ts           # 🎨 Theatrical Terminal Output
│   └── visualize-ledger.ts     # 📊 Merkle Chain Visualizer
└── logs/
    └── guardian_audit.log      # 📝 Persistent Audit Trail
```

---

## 🕹️ Running the Demo

We have included a comprehensive "Visualizer Suite" to demonstrate the security features in action.

### 1. The "Hero's Journey" Scenario
Simulates 4 distinct scenes:
1.  **Happy Path:** Legitimate delegation and action (Allowed).
2.  **Privacy Breach:** Unauthorized access attempt (Blocked by Tier 4).
3.  **Rogue Agent:** Dangerous override attempt (Blocked by Tier 2).
4.  **Injection Attack:** SQL Injection attempt (Blocked by Tier 1).

```bash
# Run the demo
npx tsx extensions/armoriq/demo/run-scenario.ts
```

### 2. Ledger Visualization
After running the demo, visualize the cryptographic audit trail:

```bash
# Visualize the Merkle Chain
npx tsx extensions/armoriq/demo/visualize-ledger.ts
```

---

## 🔧 Integration Details

The Guardian Kernel is wired directly into the agent's runtime via `src/agents/pi-tools.before-tool-call.ts`. This ensures **zero-bypass security** — no tool can be executed without passing through the Guardian Proxy.

```typescript
// Integration Hook
await guardianProxy.validateAndLog({
  token: resolvedToken,
  tool: toolName,
  args: params,
  prompt: userPrompt
});
```
