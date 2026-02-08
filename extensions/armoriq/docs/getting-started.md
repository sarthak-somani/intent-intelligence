# Getting Started with ArmorIQ

> **Quick start guide for enabling ArmorIQ in OpenClaw**

## Prerequisites

- **Node.js 22+** (required for OpenClaw)
- **pnpm** package manager
- OpenClaw repository cloned and dependencies installed
- ArmorIQ API key (contact ArmorIQ team)

---

## Installation

ArmorIQ comes bundled with OpenClaw at `extensions/armoriq/`. No separate installation required.

If using a local SDK:

```bash
# Update extensions/armoriq/package.json
"@armoriq/sdk": "file:../../../armoriq-sdk-customer-ts"

# Reinstall dependencies
pnpm install
```

---

## Basic Configuration

### Method 1: YAML Configuration

Edit your `openclaw.json` or `config.yml`:

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
      apiKey: "ak_live_xxx"           # Required
      userId: "user-123"               # Required
      agentId: "agent-456"             # Required
      contextId: "default"             # Optional
      validitySeconds: 60              # Token validity
```

### Method 2: Environment Variables

```bash
export ARMORIQ_API_KEY="ak_live_xxx"
export USER_ID="user-123"
export AGENT_ID="agent-456"
export CONTEXT_ID="default"
```

Then enable the plugin:

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
```

---

## Minimal Configuration Examples

### JSON Format

```json
{
  "plugins": {
    "entries": {
      "armoriq": {
        "enabled": true,
        "apiKey": "ak_live_xxx",
        "userId": "user-123",
        "agentId": "agent-456"
      }
    }
  }
}
```

### YAML Format

```yaml
plugins:
  entries:
    armoriq:
      enabled: true
      apiKey: "ak_live_xxx"
      userId: "user-123"
      agentId: "agent-456"
```

---

## Verification

Start OpenClaw and look for ArmorIQ log messages:

```bash
pnpm start
# or
npx tsx openclaw.mjs
```

Expected logs:

```
armoriq: plugin enabled
armoriq: planning with model gemini/gemini-2.0-flash
armoriq: plan check tool=web_search steps=3 status=ok
```

If disabled:

```
armoriq: plugin disabled (set plugins.entries.armoriq.enabled=true)
```

---

## How ArmorIQ Integrates with OpenClaw

ArmorIQ uses OpenClaw's plugin system to intercept and control agent execution:

### Plugin Hooks Used

| Hook | Purpose |
|------|---------|
| `before_agent_start` | Build intent plan from user prompt |
| `before_tool_call` | Enforce plan, policy, and CSRG verification |
| `agent_end` | Clean up plan cache |

### Integration Points

```
User Request
     │
     ▼
┌─────────────────────────────────────────┐
│  OpenClaw Gateway                       │
│  ├─ Channels: WhatsApp, Slack, Telegram │
│  └─ /tools/invoke HTTP endpoint         │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  PI Embedded Runner                     │
│  └─ Calls ArmorIQ before_agent_start    │
│     → Builds plan from prompt           │
│     → Captures plan with SDK            │
│     → Obtains intent token              │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│  Tool Execution Loop                    │
│  └─ pi-tools.before-tool-call.ts        │
│     → Guardian validation (5-tier)      │
│     → ArmorIQ plugin hook               │
│     → Policy enforcement                │
│     → CSRG verification (if enabled)    │
└────────────────┬────────────────────────┘
                 │
                 ▼
           Tool executes or is blocked
```

### Key Source Files

| File | Purpose |
|------|---------|
| `src/agents/pi-tools.before-tool-call.ts` | Entry point for tool validation |
| `src/plugins/hooks.ts` | Plugin hook runner |
| `src/plugins/types.ts` | Hook type definitions |
| `src/gateway/tools-invoke-http.ts` | HTTP `/tools/invoke` handler |

---

## Fail-Closed Behavior

ArmorIQ enforces **fail-closed** security:

| Condition | Result |
|-----------|--------|
| API key missing | ❌ Block |
| User/Agent ID missing | ❌ Block |
| Plan missing for run | ❌ Block |
| Tool not in plan | ❌ Block |
| Token expired | ❌ Block |
| Policy denies | ❌ Block |
| CSRG verification fails | ❌ Block |

---

## Next Steps

- [Configuration Reference](./configuration.md) - All configuration options
- [Policy Engine](./policy-engine.md) - Configure security rules
- [Demo & Testing](./demo-testing.md) - Run the demo scenarios
- [Troubleshooting](./troubleshooting.md) - Common issues

---

## Quick Test

Send a message via any channel:

```
Use web_search to find 3 Boston attractions. Write results to demo/attractions.md.
```

Check logs for:
- `armoriq: planning with model...`
- `armoriq: plan check tool=web_search status=ok`
- `armoriq: plan check tool=write status=ok`
