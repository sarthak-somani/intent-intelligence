# Configuration Reference

> **Complete configuration options for the ArmorIQ plugin**

## Configuration Sources

ArmorIQ reads configuration from multiple sources (in priority order):

1. **Plugin config** in `openclaw.json` / `config.yml`
2. **Environment variables**
3. **Default values**

---

## Plugin Configuration Schema

```json
{
  "plugins": {
    "entries": {
      "armoriq": {
        "enabled": true,
        "apiKey": "string",
        "userId": "string",
        "agentId": "string",
        "contextId": "string",
        "userIdSource": "senderE164 | senderId | senderUsername | senderName | sessionKey | agentId",
        "agentIdSource": "agentId | sessionKey",
        "contextIdSource": "sessionKey | agentId | channel | accountId",
        "policy": {},
        "policyStorePath": "./armoriq.policy.json",
        "policyUpdateEnabled": false,
        "policyUpdateAllowList": [],
        "cryptoPolicyEnabled": false,
        "csrgEndpoint": "http://localhost:8000",
        "validitySeconds": 60,
        "useProduction": false,
        "iapEndpoint": "string",
        "proxyEndpoint": "string",
        "backendEndpoint": "string",
        "proxyEndpoints": {},
        "timeoutMs": 30000,
        "maxRetries": 3,
        "verifySsl": true,
        "maxParamChars": 2000,
        "maxParamDepth": 4,
        "maxParamKeys": 50,
        "maxParamItems": 50
      }
    }
  }
}
```

---

## Core Settings

### `enabled`
- **Type**: `boolean`
- **Default**: `false`
- **Description**: Enable/disable the ArmorIQ plugin

### `apiKey`
- **Type**: `string`
- **Env**: `ARMORIQ_API_KEY`
- **Required**: Yes
- **Description**: ArmorIQ API key for SDK authentication

### `userId`
- **Type**: `string`
- **Env**: `USER_ID`
- **Required**: Yes (or use `userIdSource`)
- **Description**: User identifier for intent tracking

### `agentId`
- **Type**: `string`
- **Env**: `AGENT_ID`
- **Required**: Yes (or use `agentIdSource`)
- **Description**: Agent identifier for intent tracking

### `contextId`
- **Type**: `string`
- **Env**: `CONTEXT_ID`
- **Default**: `"default"`
- **Description**: Context/session identifier

---

## Identity Resolution

When `userId`, `agentId`, or `contextId` are not explicitly set, ArmorIQ can derive them from the runtime context:

### `userIdSource`
- **Type**: `enum`
- **Options**: `senderE164`, `senderId`, `senderUsername`, `senderName`, `sessionKey`, `agentId`
- **Description**: Which context field to use as userId

### `agentIdSource`
- **Type**: `enum`
- **Options**: `agentId`, `sessionKey`
- **Description**: Which context field to use as agentId

### `contextIdSource`
- **Type**: `enum`
- **Options**: `sessionKey`, `agentId`, `channel`, `accountId`
- **Description**: Which context field to use as contextId

---

## Policy Settings

### `policy`
- **Type**: `object`
- **Description**: Inline policy definition

```json
{
  "policy": {
    "rules": [
      {
        "id": "block-pci",
        "action": "deny",
        "tool": "*",
        "dataClass": "PCI"
      }
    ]
  }
}
```

### `policyStorePath`
- **Type**: `string`
- **Env**: `ARMORIQ_POLICY_STORE_PATH`
- **Default**: `"armoriq.policy.json"`
- **Description**: Path to persistent policy store file

### `policyUpdateEnabled`
- **Type**: `boolean`
- **Env**: `ARMORIQ_POLICY_UPDATE_ENABLED`
- **Default**: `false`
- **Description**: Enable runtime policy updates via `policy_update` tool

### `policyUpdateAllowList`
- **Type**: `string[]`
- **Env**: `ARMORIQ_POLICY_UPDATE_ALLOWLIST`
- **Description**: User identifiers allowed to update policies
- **Special**: `["*"]` allows all users

```json
{
  "policyUpdateAllowList": ["+15550001111", "admin-user"]
}
```

---

## CSRG/Crypto Settings

### `cryptoPolicyEnabled`
- **Type**: `boolean`
- **Env**: `ARMORIQ_CRYPTO_POLICY_ENABLED`
- **Default**: `false`
- **Description**: Enable cryptographic policy binding via CSRG

### `csrgEndpoint`
- **Type**: `string`
- **Env**: `CSRG_URL`
- **Default**: `"http://localhost:8000"`
- **Description**: CSRG server endpoint

**Related environment variables:**
- `REQUIRE_CSRG_PROOFS` - Require CSRG proofs for tool calls
- `CSRG_VERIFY_ENABLED` - Enable CSRG verification

---

## Token Settings

### `validitySeconds`
- **Type**: `number`
- **Default**: `60`
- **Description**: Intent token validity duration in seconds

---

## Endpoint Settings

### `useProduction`
- **Type**: `boolean`
- **Default**: `false`
- **Description**: Use production ArmorIQ endpoints

### `iapEndpoint`
- **Type**: `string`
- **Env**: `IAP_ENDPOINT`
- **Description**: IAP (Intent Access Protocol) service endpoint

### `proxyEndpoint`
- **Type**: `string`
- **Env**: `PROXY_ENDPOINT`
- **Description**: ArmorIQ proxy endpoint

### `backendEndpoint`
- **Type**: `string`
- **Env**: `BACKEND_ENDPOINT`
- **Description**: ArmorIQ backend API endpoint

### `proxyEndpoints`
- **Type**: `object`
- **Description**: Map of named proxy endpoints

```json
{
  "proxyEndpoints": {
    "primary": "https://proxy1.armoriq.ai",
    "secondary": "https://proxy2.armoriq.ai"
  }
}
```

---

## Network Settings

### `timeoutMs`
- **Type**: `number`
- **Default**: `30000`
- **Description**: HTTP request timeout in milliseconds

### `maxRetries`
- **Type**: `number`
- **Default**: `3`
- **Description**: Maximum retry attempts for failed requests

### `verifySsl`
- **Type**: `boolean`
- **Default**: `true`
- **Description**: Verify SSL certificates

---

## Parameter Sanitization

Control how tool parameters are sanitized before policy evaluation:

### `maxParamChars`
- **Type**: `number`
- **Default**: `2000`
- **Description**: Maximum characters per string parameter

### `maxParamDepth`
- **Type**: `number`
- **Default**: `4`
- **Description**: Maximum nesting depth for objects

### `maxParamKeys`
- **Type**: `number`
- **Default**: `50`
- **Description**: Maximum keys per object

### `maxParamItems`
- **Type**: `number`
- **Default**: `50`
- **Description**: Maximum items per array

---

## Environment Variables Summary

| Variable | Config Key | Description |
|----------|------------|-------------|
| `ARMORIQ_API_KEY` | `apiKey` | API key |
| `USER_ID` | `userId` | User identifier |
| `AGENT_ID` | `agentId` | Agent identifier |
| `CONTEXT_ID` | `contextId` | Context identifier |
| `ARMORIQ_POLICY_STORE_PATH` | `policyStorePath` | Policy file path |
| `ARMORIQ_POLICY_UPDATE_ENABLED` | `policyUpdateEnabled` | Enable updates |
| `ARMORIQ_POLICY_UPDATE_ALLOWLIST` | `policyUpdateAllowList` | Allowed users |
| `ARMORIQ_CRYPTO_POLICY_ENABLED` | `cryptoPolicyEnabled` | Enable CSRG |
| `CSRG_URL` | `csrgEndpoint` | CSRG server |
| `REQUIRE_CSRG_PROOFS` | - | Require proofs |
| `CSRG_VERIFY_ENABLED` | - | Enable verification |
| `IAP_ENDPOINT` | `iapEndpoint` | IAP service |
| `PROXY_ENDPOINT` | `proxyEndpoint` | Proxy service |
| `BACKEND_ENDPOINT` | `backendEndpoint` | Backend API |

---

## Complete Example

```yaml
plugins:
  entries:
    armoriq:
      # Core
      enabled: true
      apiKey: "${ARMORIQ_API_KEY}"
      userId: "user-123"
      agentId: "openclaw-agent"
      contextId: "production"
      
      # Identity resolution (for channels)
      userIdSource: "senderE164"
      agentIdSource: "agentId"
      contextIdSource: "sessionKey"
      
      # Policy
      policyStorePath: "./armoriq.policy.json"
      policyUpdateEnabled: true
      policyUpdateAllowList:
        - "+15550001111"
        - "admin@company.com"
      
      # Security
      cryptoPolicyEnabled: true
      csrgEndpoint: "http://localhost:8000"
      validitySeconds: 120
      
      # Endpoints
      useProduction: true
      backendEndpoint: "https://api.armoriq.ai"
      
      # Network
      timeoutMs: 30000
      maxRetries: 3
      verifySsl: true
```

---

## Related Documentation

- [Getting Started](./getting-started.md)
- [Policy Engine](./policy-engine.md)
- [Security Model](./security-model.md)
