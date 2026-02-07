import { createHash, randomUUID } from "node:crypto";

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
 * A cryptographically-linked immutable ledger using Merkle chain principles.
 * Each entry's hash depends on the previous entry, making tampering detectable.
 */
export class MerkleLedger {
    private chain: LedgerEntry[] = [];
    private readonly GENESIS_HASH = "00000000000000000000000000000000";

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
     * Appends a new entry to the ledger chain.
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
                console.error(`Chain broken at index ${i}: prevHash mismatch`);
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
                console.error(`Chain broken at index ${i}: hash mismatch`);
                return false;
            }
        }

        return true;
    }
}
