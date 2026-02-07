import { z, ZodSchema } from "zod";

/**
 * Guardian Schemas - Tier 1 Egress Contracts
 * 
 * Rigorous Zod schemas to prevent:
 * - Tool Hijacking
 * - Malformed inputs
 * - Injection attacks (SQL, Command, etc.)
 * - Transaction limit violations
 */

/**
 * Common validation patterns
 */
const SafeString = z.string().regex(
    /^[a-zA-Z0-9_\-\s.]+$/,
    "Contains invalid characters"
);

const SafePatientId = z.string().regex(
    /^[a-zA-Z0-9_\-]+$/,
    "Invalid Patient ID format - alphanumeric, underscore, hyphen only"
);

const SafeEmail = z.string().email("Invalid email format");

const PositiveAmount = z.number().positive("Amount must be positive");

/**
 * Tool-specific contracts with strict validation
 */
export const ToolContracts: Record<string, ZodSchema> = {
    /**
     * Pharmacy tool - handles medication orders
     * - Strict item name validation
     * - Transaction limit of 100,000
     * - Positive quantity required
     */
    pharmacy: z.object({
        item: z.string().min(1, "Item name required").optional(),
        medication: z.string().min(1, "Medication name required").optional(),
        cost: PositiveAmount.max(100000, "Transaction limit exceeded (Max: 100,000)"),
        quantity: z.number().int().positive().default(1).optional(),
        patient_id: SafePatientId.optional(),
    }).passthrough(),

    /**
     * Records tool - handles patient data access
     * - Strict patient ID format (prevents injection)
     * - Allowed record types only
     */
    records: z.object({
        patient: SafePatientId.optional(),
        patient_id: SafePatientId.optional(),
        recordType: z.enum(["blood", "scan", "history", "medical_history", "prescription"]).optional(),
        record_type: z.string().optional(),
    }).passthrough(),

    /**
     * Payment tool - handles financial transactions
     * - Strict amount limits
     * - Currency validation
     */
    payment: z.object({
        amount: PositiveAmount.max(1000000, "Payment limit exceeded (Max: 1,000,000)"),
        currency: z.enum(["INR", "USD", "EUR", "GBP"]).default("INR").optional(),
        recipient: SafeString.optional(),
        description: z.string().max(500).optional(),
    }).passthrough(),

    /**
     * Payment Gateway - handles subscription and plan purchases
     */
    payment_gateway: z.object({
        amount: PositiveAmount.max(1000000, "Payment limit exceeded"),
        plan: z.string().optional(),
        subscription_id: z.string().optional(),
    }).passthrough(),

    /**
     * Emergency override - allows anything but logs heavily
     * Used only for critical situations
     */
    emergency: z.any(),

    /**
     * Weather tool - no sensitive data, lenient
     */
    weather: z.object({
        location: z.string(),
        units: z.enum(["celsius", "fahrenheit"]).optional(),
    }).passthrough(),

    /**
     * Search tool - basic validation
     */
    search: z.object({
        query: z.string().min(1).max(1000),
        limit: z.number().int().positive().max(100).optional(),
    }).passthrough(),
};

/**
 * Schema validation result
 */
export interface SchemaValidationResult {
    valid: boolean;
    errors?: string[];
    data?: any;
}

/**
 * Validate tool arguments against the contract
 * @param tool - Tool name
 * @param args - Arguments to validate
 * @returns Validation result with errors or parsed data
 */
export function validateToolContract(
    tool: string,
    args: any
): SchemaValidationResult {
    const schema = ToolContracts[tool.toLowerCase()];

    if (!schema) {
        // No schema defined - lenient mode
        return { valid: true, data: args };
    }

    const result = schema.safeParse(args);

    if (!result.success) {
        // Zod uses 'issues' not 'errors'
        const errors = result.error.issues.map(
            (e: any) => `${e.path?.join(".") || "root"}: ${e.message}`
        );
        return { valid: false, errors };
    }

    return { valid: true, data: result.data };
}

/**
 * Get list of tools with defined schemas
 */
export function getSchemaTools(): string[] {
    return Object.keys(ToolContracts);
}

/**
 * Check if a tool has a defined schema
 */
export function hasSchema(tool: string): boolean {
    return tool.toLowerCase() in ToolContracts;
}
