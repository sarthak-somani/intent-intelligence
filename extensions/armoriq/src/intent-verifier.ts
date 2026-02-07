/**
 * Intent Verification Service
 * Analyzes user prompts against tool actions to detect intent mismatches.
 * Helps prevent unauthorized high-risk actions like spending money.
 */

/**
 * Result of intent verification
 */
export interface IntentVerificationResult {
    riskLevel: "LOW" | "HIGH";
    warning?: string;
}

/**
 * IntentVerifier - Detects mismatches between user intent and tool actions.
 * Uses heuristics to identify when a tool action doesn't align with user's stated intent.
 */
export class IntentVerifier {
    /**
     * High-risk verbs that indicate financial or destructive intent
     */
    private readonly highRiskVerbs = [
        "buy",
        "purchase",
        "order",
        "pay",
        "transfer",
        "delete",
        "remove",
        "spend",
        "charge",
        "subscribe",
    ];

    /**
     * Financial-related tool names
     */
    private readonly financialTools = [
        "pharmacy",
        "payment",
        "checkout",
        "billing",
        "order",
        "purchase",
    ];

    /**
     * Financial-related argument keys
     */
    private readonly financialArgKeys = [
        "cost",
        "price",
        "amount",
        "total",
        "payment",
        "fee",
    ];

    /**
     * Dangerous override phrases that should be flagged
     */
    private readonly dangerousPhrases = [
        "ignore safety",
        "override",
        "bypass security",
        "skip verification",
        "force approve",
        "ignore policy",
        "disable check",
    ];

    /**
     * Validate user intent against a tool action
     * @param userPrompt - The user's original prompt/request
     * @param toolName - The name of the tool being called
     * @param toolArgs - Arguments passed to the tool
     * @returns IntentVerificationResult with risk level and optional warning
     */
    public validate(
        userPrompt: string,
        toolName: string,
        toolArgs: any
    ): IntentVerificationResult {
        const normalizedPrompt = userPrompt.toLowerCase();
        const normalizedToolName = toolName.toLowerCase();

        // Heuristic 2: Check for explicit override attempts (highest priority)
        for (const phrase of this.dangerousPhrases) {
            if (normalizedPrompt.includes(phrase)) {
                return {
                    riskLevel: "HIGH",
                    warning: `Dangerous override phrase detected: "${phrase}"`,
                };
            }
        }

        // Heuristic 1: Financial Risk Detection
        const isFinancialTool = this.financialTools.some(
            (ft) => normalizedToolName.includes(ft)
        );

        const hasFinancialArgs = toolArgs && typeof toolArgs === "object" &&
            Object.keys(toolArgs).some((key) =>
                this.financialArgKeys.includes(key.toLowerCase())
            );

        // If this is a financial action...
        if (isFinancialTool || hasFinancialArgs) {
            // Check if user's prompt contains any high-risk verbs
            const hasIntentVerb = this.highRiskVerbs.some((verb) =>
                normalizedPrompt.includes(verb)
            );

            if (!hasIntentVerb) {
                // Financial action without explicit user intent = HIGH RISK
                return {
                    riskLevel: "HIGH",
                    warning: `Financial action "${toolName}" not explicitly authorized in user prompt`,
                };
            }
        }

        // Default: LOW risk
        return {
            riskLevel: "LOW",
        };
    }

    /**
     * Check if a prompt contains any high-risk verbs
     */
    public hasHighRiskIntent(userPrompt: string): boolean {
        const normalized = userPrompt.toLowerCase();
        return this.highRiskVerbs.some((verb) => normalized.includes(verb));
    }

    /**
     * Extract detected intents from a prompt
     */
    public extractIntents(userPrompt: string): string[] {
        const normalized = userPrompt.toLowerCase();
        return this.highRiskVerbs.filter((verb) => normalized.includes(verb));
    }
}
