import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import { MerkleLedger, LedgerEntry } from "./ledger";
import { PolicyEngine, PolicyDecision, EvaluationContext } from "./policy-engine";
import { AuthAuthority, TokenPayload, TokenInput } from "./auth-authority";
import { IntentVerifier, IntentVerificationResult } from "./intent-verifier";

// Get current directory for ESM modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Result of a validation request
 */
export interface ValidationResult {
    allowed: boolean;
    tokenPayload: TokenPayload | null;
    policyDecision: PolicyDecision | null;
    ledgerEntry: LedgerEntry | null;
    error?: string;
}

/**
 * ArmorIQGuardian - The central integration service that wires together:
 * - MerkleLedger for immutable audit logging
 * - PolicyEngine for rule-based access control
 * - AuthAuthority for JWT token management
 */
export class ArmorIQGuardian {
    private ledger: MerkleLedger;
    private policy: PolicyEngine;
    private auth: AuthAuthority;
    private intentVerifier: IntentVerifier;

    constructor() {
        this.ledger = new MerkleLedger();
        this.policy = new PolicyEngine();
        this.auth = new AuthAuthority();
        this.intentVerifier = new IntentVerifier();

        // Load default healthcare policies
        const policiesPath = join(__dirname, "..", "policies", "healthcare.json");
        try {
            this.policy.loadPolicies(policiesPath);
        } catch (error) {
            console.warn("[ArmorIQGuardian] Could not load default policies:", (error as Error).message);
        }
    }

    /**
     * Sign a new delegation token
     * @param input - Token input with role and scopes
     * @returns Signed JWT string
     */
    public signToken(input: TokenInput): string {
        return this.auth.signToken(input);
    }

    /**
     * Validate a request against authentication, intent, policy, and audit requirements
     * @param token - JWT token string
     * @param tool - The tool being called
     * @param args - Arguments passed to the tool
     * @param userPrompt - The user's original prompt for intent verification
     * @returns true if allowed
     * @throws Error if token is invalid, intent mismatch, or policy denies
     */
    public async validateRequest(
        token: string,
        tool: string,
        args: any,
        userPrompt: string = ""
    ): Promise<boolean> {
        // Step 1: Verify Token
        const tokenPayload = this.auth.verifyToken(token);
        if (!tokenPayload) {
            // Log the failed attempt
            this.ledger.append("UNKNOWN", "AUTH_FAILURE", {
                tool,
                args,
                reason: "Invalid or expired token",
            });
            throw new Error("Unauthorized: Invalid or expired token");
        }

        // Step 2: Intent Verification (NEW)
        const intentResult = this.intentVerifier.validate(userPrompt, tool, args);
        if (intentResult.riskLevel === "HIGH") {
            // Log the intent warning
            this.ledger.append(tokenPayload.principal_role, "INTENT_WARNING", {
                tool,
                args,
                userPrompt: userPrompt.substring(0, 100), // Truncate for logging
                risk: "HIGH",
                warning: intentResult.warning,
            });
            throw new Error(
                `[Guardian] 🧠 Intent Mismatch: User did not authorize high-risk action '${tool}'. ${intentResult.warning || ""}`
            );
        }

        // Step 3: Build evaluation context from token
        const context: EvaluationContext = {
            principal_role: tokenPayload.principal_role,
            token_scopes: tokenPayload.token_scopes,
        };

        // Step 4: Check Policy
        const policyDecision = this.policy.evaluate(tool, args, context);
        if (!policyDecision.allowed) {
            // Log the policy violation
            this.ledger.append(tokenPayload.principal_role, "POLICY_VIOLATION", {
                tool,
                args,
                rule_id: policyDecision.matchedRule?.id,
                reason: policyDecision.reason,
            });
            throw new Error(`Policy Violation: ${policyDecision.reason}`);
        }

        // Step 5: Log successful request to Ledger
        this.ledger.append(tokenPayload.principal_role, "TOOL_CALL", {
            tool,
            args,
            userPrompt: userPrompt.substring(0, 100),
            decision: "ALLOWED",
        });

        return true;
    }

    /**
     * Get the full validation result without throwing
     * @param token - JWT token string
     * @param tool - The tool being called
     * @param args - Arguments passed to the tool
     * @returns ValidationResult with all details
     */
    public validateRequestSafe(
        token: string,
        tool: string,
        args: any
    ): ValidationResult {
        // Step 1: Verify Token
        const tokenPayload = this.auth.verifyToken(token);
        if (!tokenPayload) {
            this.ledger.append("UNKNOWN", "AUTH_FAILURE", {
                tool,
                args,
                reason: "Invalid or expired token",
            });
            return {
                allowed: false,
                tokenPayload: null,
                policyDecision: null,
                ledgerEntry: null,
                error: "Unauthorized: Invalid or expired token",
            };
        }

        // Step 2: Build evaluation context from token
        const context: EvaluationContext = {
            principal_role: tokenPayload.principal_role,
            token_scopes: tokenPayload.token_scopes,
        };

        // Step 3: Check Policy
        const policyDecision = this.policy.evaluate(tool, args, context);
        if (!policyDecision.allowed) {
            const entry = this.ledger.append(tokenPayload.principal_role, "POLICY_VIOLATION", {
                tool,
                args,
                rule_id: policyDecision.matchedRule?.id,
                reason: policyDecision.reason,
            });
            return {
                allowed: false,
                tokenPayload,
                policyDecision,
                ledgerEntry: entry,
                error: `Policy Violation: ${policyDecision.reason}`,
            };
        }

        // Step 4: Log successful request
        const entry = this.ledger.append(tokenPayload.principal_role, "TOOL_CALL", {
            tool,
            args,
            decision: "ALLOWED",
        });

        return {
            allowed: true,
            tokenPayload,
            policyDecision,
            ledgerEntry: entry,
        };
    }

    /**
     * Get the audit ledger history
     */
    public getAuditHistory(): LedgerEntry[] {
        return this.ledger.getHistory();
    }

    /**
     * Verify the integrity of the audit ledger
     */
    public verifyAuditIntegrity(): boolean {
        return this.ledger.verifyIntegrity();
    }

    /**
     * Get the underlying components (for advanced use)
     */
    public getComponents() {
        return {
            ledger: this.ledger,
            policy: this.policy,
            auth: this.auth,
            intentVerifier: this.intentVerifier,
        };
    }

    /**
     * Verify intent only (without full validation)
     */
    public verifyIntent(userPrompt: string, tool: string, args: any): IntentVerificationResult {
        return this.intentVerifier.validate(userPrompt, tool, args);
    }
}

// Export singleton instance
export const guardian = new ArmorIQGuardian();
