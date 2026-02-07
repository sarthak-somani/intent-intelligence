import jwt from "jsonwebtoken";

/**
 * Secret key for JWT signing - DO NOT USE IN PRODUCTION
 */
const SECRET_KEY = "HACKATHON_SECRET_DO_NOT_USE_IN_PROD";

/**
 * Payload structure for delegation tokens
 */
export interface TokenPayload {
    /** The role of the principal (e.g., 'caretaker', 'user', 'agent', 'automated_agent') */
    principal_role: string;
    /** Array of permission scopes (e.g., 'pharmacy:order', 'patient:records:read') */
    token_scopes: string[];
    /** Unix timestamp when the token was issued */
    issued_at: number;
}

/**
 * Input for signing a new token (issued_at is added automatically)
 */
export type TokenInput = Omit<TokenPayload, "issued_at">;

/**
 * AuthAuthority - Handles JWT token signing and verification for delegation.
 * Provides cryptographic proof of identity and permissions.
 */
export class AuthAuthority {
    private readonly secretKey: string;

    constructor(secretKey: string = SECRET_KEY) {
        this.secretKey = secretKey;
    }

    /**
     * Sign a new delegation token
     * @param payload - The token payload (role and scopes)
     * @returns Signed JWT string
     */
    public signToken(payload: TokenInput): string {
        const fullPayload: TokenPayload = {
            ...payload,
            issued_at: Date.now(),
        };

        return jwt.sign(fullPayload, this.secretKey, {
            expiresIn: "1h",
        });
    }

    /**
     * Verify and decode a token
     * @param token - The JWT string to verify
     * @returns Decoded TokenPayload if valid, null if invalid or expired
     */
    public verifyToken(token: string): TokenPayload | null {
        try {
            const decoded = jwt.verify(token, this.secretKey) as TokenPayload;
            return decoded;
        } catch (error) {
            // Token is invalid or expired
            console.warn("[AuthAuthority] Token verification failed:", (error as Error).message);
            return null;
        }
    }

    /**
     * Decode a token WITHOUT verification (for debugging only)
     * @param token - The JWT string to decode
     * @returns Decoded payload or null
     */
    public decodeWithoutVerify(token: string): TokenPayload | null {
        try {
            return jwt.decode(token) as TokenPayload;
        } catch {
            return null;
        }
    }
}
