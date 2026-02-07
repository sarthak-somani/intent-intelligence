import { z, ZodSchema } from "zod";
import { ArmorIQGuardian } from "./guardian-integration";
import { ToolContracts, validateToolContract, SchemaValidationResult } from "./guardian-schemas";

/**
 * Intent Packet - The standardized input for protected calls
 */
export interface IntentPacket {
    /** JWT authentication token */
    token: string;
    /** The tool being called */
    tool: string;
    /** Arguments passed to the tool */
    args: any;
    /** The user's original prompt */
    prompt: string;
}

/**
 * Result of a protected call
 */
export interface ProtectedCallResult {
    success: boolean;
    sanitizedPrompt: string;
    validatedArgs?: any;
    error?: string;
}

/**
 * PII patterns for sanitization
 */
const PII_PATTERNS = {
    email: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g,
    phone: /(\+?\d{1,3}[-.\s]?)?(\(?\d{3}\)?[-.\s]?)?\d{3}[-.\s]?\d{4}/g,
    ssn: /\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b/g,
    creditCard: /\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b/g,
    aadhaar: /\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b/g, // Indian ID
};

/**
 * GuardianProxy - The 5-Tier Defense-in-Depth Interceptor
 * 
 * Orchestrates all security layers:
 * - Tier 1: Ingress Sanitization (PII redaction)
 * - Tier 1: Egress Validation (Zod schema contracts)
 * - Tier 2: Intent Verification
 * - Tier 3: Policy Engine
 * - Tier 4: Delegation Authority (JWT)
 * - Tier 5: Merkle Ledger (Forensic Audit)
 */
export class GuardianProxy {
    private guardian: ArmorIQGuardian;

    constructor(guardian?: ArmorIQGuardian) {
        this.guardian = guardian || new ArmorIQGuardian();
    }

    /**
     * Sanitize PII from text (Tier 1 - Ingress)
     * Masks sensitive information to protect user privacy
     * @param text - The text to sanitize
     * @returns Sanitized text with PII replaced by [REDACTED]
     */
    private sanitize(text: string): string {
        let sanitized = text;

        // Redact emails
        sanitized = sanitized.replace(PII_PATTERNS.email, "[EMAIL_REDACTED]");

        // Redact phone numbers
        sanitized = sanitized.replace(PII_PATTERNS.phone, "[PHONE_REDACTED]");

        // Redact SSNs
        sanitized = sanitized.replace(PII_PATTERNS.ssn, "[SSN_REDACTED]");

        // Redact credit cards
        sanitized = sanitized.replace(PII_PATTERNS.creditCard, "[CARD_REDACTED]");

        // Redact Aadhaar numbers
        sanitized = sanitized.replace(PII_PATTERNS.aadhaar, "[AADHAAR_REDACTED]");

        return sanitized;
    }

    /**
     * Detect what types of PII were found
     */
    private detectPIITypes(original: string, sanitized: string): string[] {
        const types: string[] = [];
        if (sanitized.includes("[EMAIL_REDACTED]")) types.push("email");
        if (sanitized.includes("[PHONE_REDACTED]")) types.push("phone");
        if (sanitized.includes("[SSN_REDACTED]")) types.push("ssn");
        if (sanitized.includes("[CARD_REDACTED]")) types.push("credit_card");
        if (sanitized.includes("[AADHAAR_REDACTED]")) types.push("aadhaar");
        return types;
    }

    /**
     * Validate and Log - The main orchestration method
     * 
     * Executes all 5 tiers of defense:
     * 1. Ingress Sanitization
     * 2. Egress Validation (Schema)
     * 3. Intent Verification
     * 4. Policy + Delegation
     * 5. Audit Logging
     * 
     * @param packet - The intent packet to validate
     * @throws Error if any security layer fails
     */
    public async validateAndLog(packet: IntentPacket): Promise<void> {
        const { token, tool, args, prompt } = packet;
        const ledger = this.guardian.getComponents().ledger;

        // ================================================================
        // TIER 1: INGRESS SANITIZATION (PII Redaction)
        // ================================================================
        const safePrompt = this.sanitize(prompt);
        const piiWasRedacted = safePrompt !== prompt;

        if (piiWasRedacted) {
            ledger.append("SYSTEM", "PII_SANITIZATION", {
                tool,
                redactedTypes: this.detectPIITypes(prompt, safePrompt),
                originalLength: prompt.length,
                sanitizedLength: safePrompt.length,
            });
        }

        // ================================================================
        // TIER 1: EGRESS VALIDATION (Zod Schema Contracts)
        // ================================================================
        const schemaResult = validateToolContract(tool, args);

        if (!schemaResult.valid) {
            // Log schema violation to the forensic ledger
            ledger.append("SYSTEM", "SCHEMA_VIOLATION", {
                tool,
                args,
                errors: schemaResult.errors,
                timestamp: new Date().toISOString(),
            });

            throw new Error(
                `[Guardian] 🛡️ Egress Contract Violation: Invalid Arguments for '${tool}'. ` +
                `Errors: ${schemaResult.errors?.join(", ")}`
            );
        }

        // ================================================================
        // TIER 2, 3, 4, 5: Intent + Policy + Auth + Audit
        // (Delegated to GuardianService.validateRequest)
        // ================================================================
        await this.guardian.validateRequest(token, tool, args, safePrompt);
    }

    /**
     * Execute a protected call and return result instead of throwing
     * @param packet - The intent packet
     * @returns ProtectedCallResult with success status
     */
    public async executeProtectedCall(packet: IntentPacket): Promise<ProtectedCallResult> {
        const safePrompt = this.sanitize(packet.prompt);

        try {
            await this.validateAndLog(packet);
            return {
                success: true,
                sanitizedPrompt: safePrompt,
                validatedArgs: packet.args,
            };
        } catch (error) {
            return {
                success: false,
                sanitizedPrompt: safePrompt,
                error: (error as Error).message,
            };
        }
    }

    /**
     * Get the underlying guardian instance
     */
    public getGuardian(): ArmorIQGuardian {
        return this.guardian;
    }

    /**
     * Get the audit history
     */
    public getAuditHistory() {
        return this.guardian.getAuditHistory();
    }

    /**
     * Verify audit chain integrity
     */
    public verifyAuditIntegrity(): boolean {
        return this.guardian.verifyAuditIntegrity();
    }

    /**
     * Get the log file path (for forensic analysis)
     */
    public getLogFilePath(): string {
        return this.guardian.getComponents().ledger.getLogFilePath();
    }
}

// Export singleton instance
export const proxy = new GuardianProxy();
