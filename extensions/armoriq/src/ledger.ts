import { createHash, randomUUID } from "node:crypto";
import { appendFileSync, existsSync, readFileSync, mkdirSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

// Get current directory for ESM modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Default log file location
 */
const LOG_DIR = join(__dirname, "..", "logs");
const LOG_FILE = join(LOG_DIR, "guardian_audit.log");

/**
 * Represents a single entry in the Merkle Ledger.
 * Each entry is cryptographically linked to the previous entry via prevHash.
 */
export interface LedgerEntry {
    /** Unique identifier for this entry */
    id: string;
    /** The hash of the previous entry in the chain */
    prevHash: string;
    /** Unix timestamp when the entry was created */
    timestamp: number;
    /** The agent or user who performed the action */
    actor: string;
    /** The type of action (e.g., "TOOL_CALL", "POLICY_CHECK") */
    action: string;
    /** The data associated with this action */
    payload: any;
    /** SHA-256 hash of this entire entry */
    hash: string;
}

/**
 * Configuration for the MerkleLedger
 */
export interface LedgerConfig {
    /** Path to the log file for persistent storage */
    logFile?: string;
    /** Whether to persist to disk (default: true) */
    persistToDisk?: boolean;
}

/**
 * A cryptographically-linked immutable ledger using Merkle chain principles.
 * Each entry's hash depends on the previous entry, making tampering detectable.
 * 
 * Features:
 * - Write-Ahead Logging (WAL) for crash recovery
 * - Persistent forensic audit trail
 * - Integrity verification via hash chain
 */
export class MerkleLedger {
    private chain: LedgerEntry[] = [];
    private readonly GENESIS_HASH = "00000000000000000000000000000000";
    private readonly logFile: string;
    private readonly persistToDisk: boolean;

    constructor(config: LedgerConfig = {}) {
        this.logFile = config.logFile || LOG_FILE;
        this.persistToDisk = config.persistToDisk !== false;

        // Ensure log directory exists
        if (this.persistToDisk) {
            this.ensureLogDirectory();
            this.loadFromDisk();
        }
    }

    /**
     * Ensure the log directory exists
     */
    private ensureLogDirectory(): void {
        const logDir = dirname(this.logFile);
        try {
            if (!existsSync(logDir)) {
                mkdirSync(logDir, { recursive: true });
            }
        } catch (error) {
            console.warn(`[MerkleLedger] Could not create log directory: ${(error as Error).message}`);
        }
    }

    /**
     * Load existing entries from disk for recovery
     */
    private loadFromDisk(): void {
        try {
            if (existsSync(this.logFile)) {
                const content = readFileSync(this.logFile, "utf-8");
                const lines = content.trim().split("\n").filter(line => line.length > 0);

                for (const line of lines) {
                    try {
                        const entry = JSON.parse(line) as LedgerEntry;
                        this.chain.push(entry);
                    } catch (parseError) {
                        console.warn(`[MerkleLedger] Skipping malformed log line`);
                    }
                }

                if (this.chain.length > 0) {
                    console.log(`[MerkleLedger] Recovered ${this.chain.length} entries from disk`);
                }
            }
        } catch (error) {
            console.warn(`[MerkleLedger] Could not load from disk: ${(error as Error).message}`);
        }
    }

    /**
     * Write entry to disk immediately (Write-Ahead Logging)
     */
    private persistEntry(entry: LedgerEntry): void {
        if (!this.persistToDisk) return;

        try {
            const line = JSON.stringify(entry) + "\n";
            appendFileSync(this.logFile, line, "utf-8");
        } catch (error) {
            console.error(`[MerkleLedger] CRITICAL: Failed to persist entry: ${(error as Error).message}`);
            // Don't throw - allow in-memory operation to continue
        }
    }

    /**
     * Generates a SHA-256 hash of the provided data string.
     * @param data - The string to hash
     * @returns The hexadecimal representation of the hash
     */
    private generateHash(data: string): string {
        return createHash("sha256").update(data).digest("hex");
    }

    /**
     * Gets the hash of the last entry in the chain.
     * @returns The last entry's hash, or GENESIS_HASH if the chain is empty
     */
    public getLastHash(): string {
        if (this.chain.length === 0) {
            return this.GENESIS_HASH;
        }
        return this.chain[this.chain.length - 1].hash;
    }

    /**
     * Appends a new entry to the ledger chain with Write-Ahead Logging.
     * @param actor - The agent or user performing the action
     * @param action - The type of action being recorded
     * @param payload - The data associated with the action
     * @returns The newly created and appended LedgerEntry
     */
    public append(actor: string, action: string, payload: any): LedgerEntry {
        const prevHash = this.getLastHash();

        // Create the entry without the hash first
        const entryWithoutHash = {
            id: randomUUID(),
            prevHash,
            timestamp: Date.now(),
            actor,
            action,
            payload,
        };

        // Calculate the hash by stringifying the entry
        const hash = this.generateHash(JSON.stringify(entryWithoutHash));

        // Create the complete entry with the hash
        const entry: LedgerEntry = {
            ...entryWithoutHash,
            hash,
        };

        // WRITE-AHEAD: Persist to disk BEFORE adding to memory
        this.persistEntry(entry);

        // Add to in-memory chain
        this.chain.push(entry);

        return entry;
    }

    /**
     * Returns a copy of the entire chain history.
     * @returns A shallow copy of the ledger chain array
     */
    public getHistory(): LedgerEntry[] {
        return [...this.chain];
    }

    /**
     * Get the log file path
     */
    public getLogFilePath(): string {
        return this.logFile;
    }

    /**
     * Get the number of entries in the chain
     */
    public getLength(): number {
        return this.chain.length;
    }

    /**
     * Verifies the integrity of the entire chain.
     * Re-calculates hashes for every entry to ensure no tampering has occurred.
     * @returns true if the chain is valid, false if any entry has been tampered with
     */
    public verifyIntegrity(): boolean {
        for (let i = 0; i < this.chain.length; i++) {
            const entry = this.chain[i];

            // Verify the prevHash points to the correct previous entry
            const expectedPrevHash = i === 0 ? this.GENESIS_HASH : this.chain[i - 1].hash;
            if (entry.prevHash !== expectedPrevHash) {
                console.error(`[MerkleLedger] Chain broken at index ${i}: prevHash mismatch`);
                return false;
            }

            // Reconstruct the entry without hash and verify the hash matches
            const entryWithoutHash = {
                id: entry.id,
                prevHash: entry.prevHash,
                timestamp: entry.timestamp,
                actor: entry.actor,
                action: entry.action,
                payload: entry.payload,
            };

            const calculatedHash = this.generateHash(JSON.stringify(entryWithoutHash));
            if (calculatedHash !== entry.hash) {
                console.error(`[MerkleLedger] Chain broken at index ${i}: hash mismatch`);
                return false;
            }
        }

        return true;
    }

    /**
     * Export the chain to JSON format
     */
    public exportToJSON(): string {
        return JSON.stringify(this.chain, null, 2);
    }

    /**
     * Get entries filtered by action type
     */
    public getByAction(action: string): LedgerEntry[] {
        return this.chain.filter(entry => entry.action === action);
    }

    /**
     * Get entries filtered by actor
     */
    public getByActor(actor: string): LedgerEntry[] {
        return this.chain.filter(entry => entry.actor === actor);
    }

    /**
     * Get entries within a time range
     */
    public getByTimeRange(startTime: number, endTime: number): LedgerEntry[] {
        return this.chain.filter(
            entry => entry.timestamp >= startTime && entry.timestamp <= endTime
        );
    }
}
