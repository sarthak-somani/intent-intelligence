# Troubleshooting

> **Common issues and debugging guide**

## Quick Diagnostics

### Check Plugin Status

```bash
# Look for ArmorIQ logs at startup
pnpm start 2>&1 | grep -i armoriq
```

**Expected output (enabled)**:
```
armoriq: plugin enabled
```

**Expected output (disabled)**:
```
armoriq: plugin disabled (set plugins.entries.armoriq.enabled=true)
```

---

## Common Issues

### 1. Plugin Not Loading

**Symptom**: No ArmorIQ log messages at startup.

**Causes & Solutions**:

| Cause | Solution |
|-------|----------|
| Plugin not enabled | Set `enabled: true` in config |
| Config file not found | Check path to `openclaw.json` |
| Syntax error in config | Validate JSON/YAML syntax |

```yaml
# Ensure plugin is enabled
plugins:
  entries:
    armoriq:
      enabled: true  # Must be true
```

---

### 2. "ArmorIQ API key missing"

**Symptom**: All tool calls blocked with this message.

**Solution**: Set the API key:

```yaml
# In config
plugins:
  entries:
    armoriq:
      apiKey: "ak_live_xxx"
```

```bash
# Or via environment
export ARMORIQ_API_KEY="ak_live_xxx"
```

---

### 3. "ArmorIQ identity missing (userId/agentId)"

**Symptom**: Tool calls blocked due to missing identity.

**Solution**: Set user and agent IDs:

```yaml
plugins:
  entries:
    armoriq:
      userId: "user-123"
      agentId: "agent-456"
```

**Or use identity sources** (for channel contexts):

```yaml
plugins:
  entries:
    armoriq:
      userIdSource: "senderE164"   # Use phone number
      agentIdSource: "agentId"
```

---

### 4. "ArmorIQ intent plan missing for this run"

**Symptom**: Tool calls blocked because no plan was cached.

**Causes**:

1. Planning failed at run start
2. `/tools/invoke` called without intent token
3. Plan cache expired or cleared

**Solutions**:

- Check logs for planning errors
- For `/tools/invoke`, pass `x-armoriq-intent-token` header
- Increase `validitySeconds` if plans expire too fast

---

### 5. "ArmorIQ intent drift: tool not in plan"

**Symptom**: Specific tool blocked but others work.

**Explanation**: The tool is not in the planned action list.

**Causes**:

1. LLM planner didn't include the tool
2. Tool name mismatch (case sensitivity)
3. Dynamic tool call not anticipated

**Solutions**:

- Review the plan in logs
- Check tool name matches exactly
- Adjust user prompt to be more explicit

---

### 6. "ArmorIQ intent token expired"

**Symptom**: Tool calls blocked after some time.

**Solution**: Increase token validity:

```yaml
plugins:
  entries:
    armoriq:
      validitySeconds: 120  # Default: 60
```

---

### 7. "ArmorIQ policy denied"

**Symptom**: Tool blocked by policy rule.

**Debugging**:

1. Check current policy rules:
   ```
   User: Policy list
   ```

2. Look for matching rule in logs:
   ```
   armoriq: policy block tool=send_email rule=policy1 action=deny dataClasses=["PCI"]
   ```

3. Modify or delete the rule:
   ```
   User: Policy delete policy1
   ```

---

### 8. "ArmorIQ policy update denied"

**Symptom**: Cannot update policies via chat.

**Causes**:

1. `policyUpdateEnabled` is `false`
2. User not in `policyUpdateAllowList`

**Solution**:

```yaml
plugins:
  entries:
    armoriq:
      policyUpdateEnabled: true
      policyUpdateAllowList:
        - "+15550001111"  # Your phone number
        - "*"             # Or allow everyone
```

---

### 9. CSRG Verification Failures

**Symptom**: Tool blocked with CSRG-related errors.

**Common errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| CSRG proof header missing | Missing `x-csrg-proof` | Include required headers |
| CSRG path header missing | Missing `x-csrg-path` | Include path header |
| Crypto policy mismatch | Policy changed after token | Re-issue intent token |

**Disable CSRG** (for debugging):

```bash
export REQUIRE_CSRG_PROOFS=false
export CSRG_VERIFY_ENABLED=false
```

---

### 10. Planning Failures

**Symptom**: All tool calls blocked with planning error.

**Check logs**:
```
armoriq: planning with model gemini/gemini-2.0-flash
armoriq: ArmorIQ planning failed: <error message>
```

**Common causes**:

| Cause | Solution |
|-------|----------|
| No API key for model | Configure model provider |
| Model quota exceeded | Switch model or wait |
| Network timeout | Increase `timeoutMs` |
| Invalid model response | Check model configuration |

---

## Debugging Mode

### Enable Debug Logging

Check your logging configuration supports debug level, then look for detailed ArmorIQ logs:

```
armoriq: verify-step request tool=web_search proofs=present proofCount=1
armoriq: verify-step result tool=web_search allowed=true
armoriq: plan check tool=web_search steps=3 status=ok
```

### Inspect Plan Cache

The plan is cached per run. Key format: `{sessionKey}::{runId}` or just `{runId}`.

---

## Testing Commands

### Run ArmorIQ Tests

```bash
# All ArmorIQ tests
pnpm vitest extensions/armoriq/index.test.ts

# Specific test file
pnpm vitest extensions/armoriq/src/test-policy-engine.ts
```

### Check Build

```bash
pnpm check
pnpm build
```

---

## Log Messages Reference

### Info Messages

| Message | Meaning |
|---------|---------|
| `armoriq: plugin enabled` | Plugin loaded successfully |
| `armoriq: planning with model X` | Plan generation starting |
| `armoriq: plan check tool=X status=ok` | Tool allowed by plan |
| `armoriq: verify-step result allowed=true` | IAP verification passed |

### Warning Messages

| Message | Meaning |
|---------|---------|
| `armoriq: plugin disabled` | Plugin not enabled in config |
| `armoriq: policy block tool=X` | Policy denied tool call |
| `armoriq: ArmorIQ planning failed` | Plan generation error |
| `armoriq: policy_update denied` | Unauthorized policy update |
| `armoriq: crypto policy verification failed` | Policy digest mismatch |

---

## Getting Help

1. **Review logs** for specific error messages
2. **Check configuration** against [Configuration Reference](./configuration.md)
3. **Test with minimal config** to isolate issues
4. **Run tests** to verify installation

---

## Related Documentation

- [Getting Started](./getting-started.md) - Initial setup
- [Configuration Reference](./configuration.md) - All options
- [Policy Engine](./policy-engine.md) - Policy rules
