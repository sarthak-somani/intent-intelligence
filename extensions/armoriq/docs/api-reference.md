# API Reference

> **Plugin hooks, tools, and HTTP endpoints**

## Plugin Hooks

ArmorIQ registers handlers for the following OpenClaw plugin hooks:

### `before_agent_start`

**Triggered**: At the start of each agent run, before any tool calls.

**Purpose**: Build intent plan from user prompt.

```typescript
api.on("before_agent_start", async (event, ctx) => {
  // event.prompt - User's request
  // event.tools - Available tools
  // ctx.model - LLM model
  // ctx.sessionKey - Session identifier
  
  // 1. Build plan from prompt using LLM
  // 2. Capture plan with ArmorIQ SDK
  // 3. Obtain intent token from IAP
  // 4. Cache plan for run duration
  
  return { prependContext: POLICY_UPDATE_INSTRUCTIONS };
});
```

**Event Type**:
```typescript
interface PluginHookBeforeAgentStartEvent {
  prompt: string;
  messages?: unknown[];
  tools?: Array<{
    name: string;
    description?: string;
    parameters?: Record<string, unknown>;
  }>;
}
```

---

### `before_tool_call`

**Triggered**: Before each tool execution.

**Purpose**: Enforce intent plan, policies, and CSRG verification.

```typescript
api.on("before_tool_call", async (event, ctx) => {
  // event.toolName - Tool being called
  // event.params - Tool parameters
  // ctx.intentTokenRaw - Intent token (if present)
  // ctx.senderId - User identifier
  
  // 1. Check tool is in plan
  // 2. Evaluate policy rules
  // 3. Verify CSRG proofs (if enabled)
  // 4. Allow or block execution
  
  return { block: true, blockReason: "..." };
  // or
  return { params: modifiedParams };
});
```

**Event Type**:
```typescript
interface PluginHookBeforeToolCallEvent {
  toolName: string;
  params: Record<string, unknown>;
}
```

**Result Type**:
```typescript
interface PluginHookBeforeToolCallResult {
  params?: Record<string, unknown>;  // Modified params
  block?: boolean;                   // Block execution
  blockReason?: string;              // Reason for blocking
}
```

---

### `agent_end`

**Triggered**: At the end of each agent run.

**Purpose**: Clean up plan cache.

```typescript
api.on("agent_end", async (event, ctx) => {
  // Clean up cached plan/token for this run
  planCache.delete(runKey);
});
```

---

## Registered Tool

### `policy_update`

**Purpose**: Runtime policy management via natural language commands.

**Registered when**: `policyUpdateEnabled: true`

```typescript
api.registerTool({
  name: "policy_update",
  label: "Policy Update",
  description: "Manage ArmorIQ policy rules",
  parameters: PolicyUpdateToolSchema,
  execute: async (toolCallId, params) => { ... }
});
```

**Parameters**:

```typescript
interface PolicyUpdateParams {
  text?: string;  // Natural language command
  update?: {
    reason: string;
    rules: PolicyRule[];
    mode?: "replace" | "merge";
    scope?: "org" | "project" | "run";
    expiresAt?: number;
    actor?: string;
  };
}
```

**Example Invocations**:

```json
// Natural language
{ "text": "Policy list" }
{ "text": "Policy new: block send_email for PCI data" }
{ "text": "Policy delete policy1" }

// Structured update
{
  "update": {
    "reason": "Block credit card data",
    "rules": [{
      "id": "policy1",
      "action": "deny",
      "tool": "*",
      "dataClass": "PCI"
    }],
    "mode": "merge"
  }
}
```

**Response Examples**:

```json
// List
{
  "content": [{ "type": "text", "text": "Policy version 3:\n1. id=policy1 action=deny..." }],
  "details": { "action": "list", "version": 3 }
}

// Update
{
  "content": [{ "type": "text", "text": "Policy updated to version 4." }],
  "details": { "version": 4, "updatedAt": "...", "policyHash": "sha256..." }
}
```

---

## HTTP Endpoints

### `/tools/invoke` Integration

ArmorIQ intercepts calls to OpenClaw's `/tools/invoke` endpoint.

**Headers Recognized**:

| Header | Purpose |
|--------|---------|
| `x-armoriq-intent-token` | Intent token (JSON or CSRG JWT) |
| `x-csrg-path` | Merkle path for step verification |
| `x-csrg-proof` | JSON array of proof items |
| `x-csrg-value-digest` | SHA256 of leaf value |

**Example Request**:

```bash
curl -X POST http://localhost:18789/tools/invoke \
  -H "Authorization: Bearer <gateway-token>" \
  -H "Content-Type: application/json" \
  -H "x-armoriq-intent-token: <token>" \
  -d '{
    "tool": "web_fetch",
    "args": { "url": "https://example.com" }
  }'
```

**With CSRG Proofs**:

```bash
curl -X POST http://localhost:18789/tools/invoke \
  -H "Authorization: Bearer <gateway-token>" \
  -H "Content-Type: application/json" \
  -H "x-armoriq-intent-token: <csrg-jwt>" \
  -H "x-csrg-path: /steps/[0]/action" \
  -H 'x-csrg-proof: [{"position":"left","sibling_hash":"..."}]' \
  -H "x-csrg-value-digest: <sha256>" \
  -d '{
    "tool": "web_fetch",
    "args": { "url": "https://example.com" }
  }'
```

---

## Internal Services

### IAPVerificationService

**Location**: `src/iap-verfication.service.ts`

**Purpose**: Verify intent tokens against IAP backend.

```typescript
const verificationService = new IAPVerificationService({
  iapBaseUrl: "https://customer-iap.armoriq.ai",
  timeoutMs: 30000,
  logger: api.logger,
});

const result = await verificationService.verifyStep(
  jwtToken,
  csrgProofs,
  toolName
);
// result: { allowed: boolean; reason?: string }
```

**Methods**:

| Method | Purpose |
|--------|---------|
| `verifyStep()` | Verify a tool step against IAP |
| `csrgProofsRequired()` | Check if proofs are required |
| `csrgVerifyIsEnabled()` | Check if verification is enabled |

---

### CryptoPolicyService

**Location**: `src/crypto-policy.service.ts`

**Purpose**: Issue and verify crypto-bound policy tokens.

```typescript
const cryptoService = new CryptoPolicyService({
  csrgBaseUrl: "http://localhost:8000",
  timeoutMs: 30000,
  logger: api.logger,
});

const token = await cryptoService.issuePolicyToken(
  policyState,
  identity,
  validitySeconds
);
// token: CsrgPolicyToken

const result = cryptoService.verifyPolicyDigest(
  currentDigest,
  tokenDigest
);
// result: { valid: boolean; reason: string }
```

---

### PolicyStore

**Location**: `src/policy.ts`

**Purpose**: Persistent policy storage with versioning.

```typescript
const policyStore = new PolicyStore({
  filePath: "./armoriq.policy.json",
  basePolicy: { rules: [] },
  logger: api.logger,
  onPolicyChange: handleCryptoPolicyUpdate,
});

await policyStore.load();

const decision = evaluatePolicy({
  policy: policyStore.getPolicy(),
  toolName: "send_email",
  toolParams: { to: "...", body: "..." },
});
// decision: { allowed: boolean; reason?: string; matchedRule?: PolicyRule; dataClasses: string[] }

await policyStore.applyUpdate(update, actor);
```

---

### ArmorIQGuardian

**Location**: `src/guardian-integration.ts`

**Purpose**: Central security orchestration.

```typescript
import { guardian } from "./guardian-integration.js";

// Sign delegation token
const token = guardian.signToken({
  role: "Caretaker",
  scopes: ["pharmacy:order", "records:read"],
});

// Validate request
const allowed = await guardian.validateRequest(
  token,
  "order_medication",
  { medication: "aspirin" },
  "Order aspirin for patient"
);

// Get audit history
const history = guardian.getAuditHistory();

// Verify ledger integrity
const valid = guardian.verifyAuditIntegrity();
```

---

### MerkleLedger

**Location**: `src/ledger.ts`

**Purpose**: Immutable audit logging.

```typescript
const ledger = new MerkleLedger();

// Append entry
const entry = ledger.append("Caretaker", "TOOL_CALL", {
  tool: "order_medication",
  args: { medication: "aspirin" },
});

// Get history
const entries = ledger.getHistory();

// Filter by action
const violations = ledger.query({ action: "POLICY_VIOLATION" });

// Verify integrity
const valid = ledger.verifyIntegrity();
```

---

## Type Definitions

### Tool Context

```typescript
interface PluginHookToolContext {
  agentId?: string;
  sessionKey?: string;
  toolName: string;
  messageChannel?: string;
  accountId?: string;
  senderId?: string;
  senderName?: string;
  senderUsername?: string;
  senderE164?: string;
  runId?: string;
  intentTokenRaw?: string;
  csrgPath?: string;
  csrgProofRaw?: string;
  csrgValueDigest?: string;
}
```

### Policy Types

```typescript
type PolicyRuleAction = "allow" | "deny" | "require_approval";
type PolicyScope = "org" | "project" | "run";
type PolicyDataClass = "PCI" | "PAYMENT" | "PHI" | "PII";

interface PolicyRule {
  id: string;
  action: PolicyRuleAction;
  tool: string;
  dataClass?: PolicyDataClass;
  params?: Record<string, unknown>;
  scope?: PolicyScope;
}

interface PolicyDefinition {
  rules: PolicyRule[];
}

interface PolicyState {
  version: number;
  updatedAt: string;
  updatedBy?: string;
  policy: PolicyDefinition;
  history: PolicyHistoryEntry[];
}
```

---

## Related Documentation

- [Architecture](./architecture.md) - System design
- [Policy Engine](./policy-engine.md) - Rule configuration
- [Demo & Testing](./demo-testing.md) - Test the APIs
