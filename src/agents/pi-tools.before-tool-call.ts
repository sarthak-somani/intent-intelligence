import type { AnyAgentTool } from "./tools/common.js";
import { createSubsystemLogger } from "../logging/subsystem.js";
import { getGlobalHookRunner } from "../plugins/hook-runner-global.js";
import { normalizeToolName } from "./tool-policy.js";
// ArmorIQ Guardian Integration
import { proxy as guardianProxy } from "../../extensions/armoriq/src/guardian-proxy.js";

type HookContext = {
  agentId?: string;
  sessionKey?: string;
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
  lastUserMessage?: string; // Added for intent verification
};

type HookOutcome = { blocked: true; reason: string } | { blocked: false; params: unknown };

const log = createSubsystemLogger("agents/tools");

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export async function runBeforeToolCallHook(args: {
  toolName: string;
  params: unknown;
  toolCallId?: string;
  ctx?: HookContext;
}): Promise<HookOutcome> {
  const hookRunner = getGlobalHookRunner();
  const toolName = normalizeToolName(args.toolName || "tool");
  const params = args.params;

  // ================================================================
  // ArmorIQ Guardian Validation (5-Tier Defense)
  // ================================================================
  try {
    const resolvedToken = args.ctx?.intentTokenRaw || "";
    const lastUserMessage = args.ctx?.lastUserMessage || "";

    // Only run Guardian validation if we have a token
    if (resolvedToken) {
      await guardianProxy.validateAndLog({
        token: resolvedToken,
        tool: toolName,
        args: isPlainObject(params) ? params : {},
        prompt: lastUserMessage,
      });
      log.info(`[ArmorIQ] Tool call validated: ${toolName}`);
    }
  } catch (guardianError) {
    // Guardian blocked the call - return blocked outcome
    log.warn(`[ArmorIQ] Tool call blocked: ${toolName} - ${String(guardianError)}`);
    return {
      blocked: true,
      reason: String(guardianError),
    };
  }

  // ================================================================
  // Original Plugin Hook Logic
  // ================================================================
  if (!hookRunner?.hasHooks("before_tool_call")) {
    return { blocked: false, params: args.params };
  }

  try {
    const normalizedParams = isPlainObject(params) ? params : {};
    const hookResult = await hookRunner.runBeforeToolCall(
      {
        toolName,
        params: normalizedParams,
      },
      {
        toolName,
        agentId: args.ctx?.agentId,
        sessionKey: args.ctx?.sessionKey,
        messageChannel: args.ctx?.messageChannel,
        accountId: args.ctx?.accountId,
        senderId: args.ctx?.senderId,
        senderName: args.ctx?.senderName,
        senderUsername: args.ctx?.senderUsername,
        senderE164: args.ctx?.senderE164,
        runId: args.ctx?.runId,
        intentTokenRaw: args.ctx?.intentTokenRaw,
        csrgPath: args.ctx?.csrgPath,
        csrgProofRaw: args.ctx?.csrgProofRaw,
        csrgValueDigest: args.ctx?.csrgValueDigest,
      },
    );

    if (hookResult?.block) {
      return {
        blocked: true,
        reason: hookResult.blockReason || "Tool call blocked by plugin hook",
      };
    }

    if (hookResult?.params && isPlainObject(hookResult.params)) {
      if (isPlainObject(params)) {
        return { blocked: false, params: { ...params, ...hookResult.params } };
      }
      return { blocked: false, params: hookResult.params };
    }
  } catch (err) {
    const toolCallId = args.toolCallId ? ` toolCallId=${args.toolCallId}` : "";
    log.warn(`before_tool_call hook failed: tool=${toolName}${toolCallId} error=${String(err)}`);
  }

  return { blocked: false, params };
}

export function wrapToolWithBeforeToolCallHook(
  tool: AnyAgentTool,
  ctx?: HookContext,
): AnyAgentTool {
  const execute = tool.execute;
  if (!execute) {
    return tool;
  }
  const toolName = tool.name || "tool";
  return {
    ...tool,
    execute: async (toolCallId, params, signal, onUpdate) => {
      const outcome = await runBeforeToolCallHook({
        toolName,
        params,
        toolCallId,
        ctx,
      });
      if (outcome.blocked) {
        throw new Error(outcome.reason);
      }
      return await execute(toolCallId, outcome.params, signal, onUpdate);
    },
  };
}

export const __testing = {
  runBeforeToolCallHook,
  isPlainObject,
};
