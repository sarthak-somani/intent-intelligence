import { readFileSync } from "node:fs";
import { join } from "node:path";

/**
 * Supported comparison operations for policy conditions
 */
export type ConditionOp = "eq" | "neq" | "gt" | "lt" | "gte" | "lte" | "contains" | "missing_scope";

/**
 * A single condition check in a policy rule
 */
export interface ConditionClause {
    op: ConditionOp;
    var: string;  // Dot-notation path like "args.cost" or "context.principal_role"
    val: string | number | boolean;
}

/**
 * Compound condition with logical AND
 */
export interface AndCondition {
    and: ConditionClause[];
}

/**
 * Compound condition with logical OR
 */
export interface OrCondition {
    or: ConditionClause[];
}

/**
 * A policy rule definition
 */
export interface PolicyRule {
    id: string;
    description: string;
    target_tool: string;
    condition: AndCondition | OrCondition | ConditionClause;
    effect: "ALLOW" | "DENY";
    reason: string;
}

/**
 * Context provided during policy evaluation
 */
export interface EvaluationContext {
    principal_role: string;
    token_scopes?: string[];
    user_id?: string;
    [key: string]: any;
}

/**
 * Arguments passed to the tool being evaluated
 */
export interface ToolArgs {
    [key: string]: any;
}

/**
 * Result of a policy evaluation
 */
export interface PolicyDecision {
    allowed: boolean;
    matchedRule: PolicyRule | null;
    reason: string;
}

/**
 * Policy Engine - Evaluates tool calls against defined policy rules.
 * Implements a "deny by default" pattern where any matching DENY rule blocks the action.
 */
export class PolicyEngine {
    private policies: PolicyRule[] = [];

    constructor() { }

    /**
     * Load policies from a JSON file
     * @param filePath - Path to the policy JSON file
     */
    public loadPolicies(filePath: string): void {
        const content = readFileSync(filePath, "utf-8");
        const parsed = JSON.parse(content);

        if (!Array.isArray(parsed)) {
            throw new Error("Policy file must contain an array of rules");
        }

        this.policies = parsed as PolicyRule[];
        console.log(`[PolicyEngine] Loaded ${this.policies.length} policies from ${filePath}`);
    }

    /**
     * Add policies directly (useful for testing)
     * @param rules - Array of policy rules
     */
    public addPolicies(rules: PolicyRule[]): void {
        this.policies.push(...rules);
    }

    /**
     * Get a value from a nested object using dot notation
     * @param obj - The object to traverse
     * @param path - Dot-notation path (e.g., "args.cost")
     */
    private getValueByPath(obj: Record<string, any>, path: string): any {
        const parts = path.split(".");
        let current: any = obj;

        for (const part of parts) {
            if (current === undefined || current === null) {
                return undefined;
            }
            current = current[part];
        }

        return current;
    }

    /**
     * Evaluate a single condition clause
     */
    private evaluateClause(
        clause: ConditionClause,
        data: Record<string, any>
    ): boolean {
        const actualValue = this.getValueByPath(data, clause.var);
        const expectedValue = clause.val;

        switch (clause.op) {
            case "eq":
                return actualValue === expectedValue;

            case "neq":
                return actualValue !== expectedValue;

            case "gt":
                return typeof actualValue === "number" && actualValue > (expectedValue as number);

            case "lt":
                return typeof actualValue === "number" && actualValue < (expectedValue as number);

            case "gte":
                return typeof actualValue === "number" && actualValue >= (expectedValue as number);

            case "lte":
                return typeof actualValue === "number" && actualValue <= (expectedValue as number);

            case "contains":
                if (Array.isArray(actualValue)) {
                    return actualValue.includes(expectedValue);
                }
                if (typeof actualValue === "string") {
                    return actualValue.includes(expectedValue as string);
                }
                return false;

            case "missing_scope":
                // Check if the scope array does NOT contain the required scope
                if (Array.isArray(actualValue)) {
                    return !actualValue.includes(expectedValue as string);
                }
                // If no scopes provided, the scope is definitely missing
                return true;

            default:
                console.warn(`[PolicyEngine] Unknown operator: ${clause.op}`);
                return false;
        }
    }

    /**
     * Evaluate a compound or single condition
     */
    private evaluateCondition(
        condition: AndCondition | OrCondition | ConditionClause,
        data: Record<string, any>
    ): boolean {
        // Check for AND condition
        if ("and" in condition) {
            return (condition as AndCondition).and.every(clause =>
                this.evaluateClause(clause, data)
            );
        }

        // Check for OR condition
        if ("or" in condition) {
            return (condition as OrCondition).or.some(clause =>
                this.evaluateClause(clause, data)
            );
        }

        // Single clause
        return this.evaluateClause(condition as ConditionClause, data);
    }

    /**
     * Evaluate a tool call against all loaded policies
     * @param toolName - The name of the tool being called
     * @param args - Arguments passed to the tool
     * @param context - Evaluation context (user role, scopes, etc.)
     * @returns PolicyDecision indicating if the action is allowed
     */
    public evaluate(
        toolName: string,
        args: ToolArgs,
        context: EvaluationContext
    ): PolicyDecision {
        // Build the data object for condition evaluation
        const data = {
            args,
            context,
            tool: toolName,
        };

        // Find all policies that apply to this tool
        const applicablePolicies = this.policies.filter(
            policy => policy.target_tool === toolName || policy.target_tool === "*"
        );

        if (applicablePolicies.length === 0) {
            // No policies for this tool - default ALLOW
            return {
                allowed: true,
                matchedRule: null,
                reason: "No applicable policies - default allow",
            };
        }

        // Check each policy - first matching DENY wins
        for (const policy of applicablePolicies) {
            const conditionMet = this.evaluateCondition(policy.condition, data);

            if (conditionMet && policy.effect === "DENY") {
                return {
                    allowed: false,
                    matchedRule: policy,
                    reason: policy.reason,
                };
            }
        }

        // No DENY policies matched - allow the action
        return {
            allowed: true,
            matchedRule: null,
            reason: "All policy checks passed",
        };
    }

    /**
     * Get all loaded policies
     */
    public getPolicies(): PolicyRule[] {
        return [...this.policies];
    }

    /**
     * Clear all loaded policies
     */
    public clearPolicies(): void {
        this.policies = [];
    }
}
