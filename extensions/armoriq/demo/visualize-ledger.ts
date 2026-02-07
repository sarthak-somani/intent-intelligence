/**
 * Guardian Ledger Visualizer
 * 
 * Reads the persistent audit log and displays
 * a visual Merkle Chain for forensic analysis.
 */

import { existsSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import chalk from "chalk";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Log file path
const LOG_FILE = join(__dirname, "..", "logs", "guardian_audit.log");

interface LedgerEntry {
    id: string;
    prevHash: string;
    timestamp: number;
    actor: string;
    action: string;
    payload: any;
    hash: string;
}

function printBanner(): void {
    console.log(chalk.magenta(`
╔══════════════════════════════════════════════════════╗
║                                                      ║
║      🔗 MERKLE LEDGER VISUALIZER 🔗                  ║
║         Immutable Audit Trail Analysis               ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
  `));
}

function formatTimestamp(ts: number): string {
    const date = new Date(ts);
    return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
    });
}

function formatHash(hash: string): string {
    return hash.substring(0, 8) + "..." + hash.substring(hash.length - 4);
}

function getActionColor(action: string): typeof chalk {
    switch (action) {
        case "TOOL_CALL":
            return chalk.green;
        case "POLICY_VIOLATION":
            return chalk.red;
        case "INTENT_WARNING":
            return chalk.yellow;
        case "SCHEMA_VIOLATION":
            return chalk.red;
        case "PII_SANITIZATION":
            return chalk.cyan;
        case "AUTH_FAILURE":
            return chalk.red.bold;
        default:
            return chalk.white;
    }
}

function visualizeLedger(): void {
    printBanner();

    if (!existsSync(LOG_FILE)) {
        console.log(chalk.yellow(`\n⚠️  Log file not found: ${LOG_FILE}`));
        console.log(chalk.gray("Run the demo scenario first to generate audit entries."));
        return;
    }

    const content = readFileSync(LOG_FILE, "utf-8");
    const lines = content.trim().split("\n").filter(l => l.length > 0);

    if (lines.length === 0) {
        console.log(chalk.yellow("\n⚠️  Log file is empty."));
        return;
    }

    console.log(chalk.white.bold(`\n  📜 Audit Log: ${LOG_FILE}`));
    console.log(chalk.white.bold(`  📊 Total Entries: ${lines.length}\n`));

    // Parse entries
    const entries: LedgerEntry[] = [];
    for (const line of lines) {
        try {
            entries.push(JSON.parse(line));
        } catch (e) {
            console.log(chalk.red(`  ⚠️  Malformed entry skipped`));
        }
    }

    // Display chain visualization
    console.log(chalk.gray("  ┌" + "─".repeat(70) + "┐"));
    console.log(chalk.gray("  │") + chalk.white.bold("  MERKLE CHAIN VISUALIZATION") + " ".repeat(41) + chalk.gray("│"));
    console.log(chalk.gray("  └" + "─".repeat(70) + "┘\n"));

    entries.forEach((entry, index) => {
        const actionColor = getActionColor(entry.action);
        const time = formatTimestamp(entry.timestamp);
        const hash = formatHash(entry.hash);
        const prevHash = formatHash(entry.prevHash);

        // Chain link arrow
        if (index > 0) {
            console.log(chalk.gray("           ▲"));
            console.log(chalk.gray("           │"));
            console.log(chalk.gray("           │") + chalk.dim.gray(` prevHash: ${prevHash}`));
            console.log(chalk.gray("           │"));
        }

        // Entry block
        console.log(chalk.gray("  ┌────────┴" + "─".repeat(61) + "┐"));
        console.log(
            chalk.gray("  │ ") +
            chalk.magenta(`🔗 ${hash}`) +
            chalk.gray(" │ ") +
            chalk.blue(`🕒 ${time}`) +
            chalk.gray(" │ ") +
            actionColor(entry.action.padEnd(18)) +
            chalk.gray(" │")
        );
        console.log(
            chalk.gray("  │ ") +
            chalk.gray(`Actor: ${entry.actor.padEnd(15)}`) +
            chalk.gray(" │ ") +
            chalk.gray(`Tool: ${(entry.payload?.tool || "N/A").toString().padEnd(15)}`) +
            chalk.gray(" ".repeat(16)) +
            chalk.gray("│")
        );
        console.log(chalk.gray("  └" + "─".repeat(70) + "┘"));
    });

    // Chain integrity check
    console.log(chalk.gray("\n  " + "═".repeat(70)));

    // Verify chain
    let isValid = true;
    const genesisHash = "00000000000000000000000000000000";

    for (let i = 0; i < entries.length; i++) {
        const expectedPrev = i === 0 ? genesisHash : entries[i - 1].hash;
        if (entries[i].prevHash !== expectedPrev) {
            isValid = false;
            break;
        }
    }

    if (isValid) {
        console.log(chalk.green.bold("\n  ✅ CHAIN INTEGRITY: VERIFIED"));
        console.log(chalk.green("     All hashes are correctly linked.\n"));
    } else {
        console.log(chalk.red.bold("\n  ❌ CHAIN INTEGRITY: COMPROMISED"));
        console.log(chalk.red("     Tampering detected in the audit trail!\n"));
    }

    // Statistics
    console.log(chalk.white.bold("  📊 STATISTICS"));
    console.log(chalk.gray("  ─".repeat(35)));

    const actionCounts: Record<string, number> = {};
    entries.forEach(e => {
        actionCounts[e.action] = (actionCounts[e.action] || 0) + 1;
    });

    Object.entries(actionCounts).forEach(([action, count]) => {
        const color = getActionColor(action);
        console.log(`     ${color(action.padEnd(20))} ${chalk.white(count.toString())}`);
    });

    console.log();
}

// Run visualizer
visualizeLedger();
