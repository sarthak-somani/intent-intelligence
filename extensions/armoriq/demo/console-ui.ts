/**
 * Guardian Console UI - Theatrical Output for Hackathon Video
 * 
 * Provides beautiful, colored terminal output to demonstrate
 * the Guardian Kernel's security features.
 */

// Use chalk for colors (v4 for CommonJS compatibility)
import chalk from "chalk";

// Delay helper for dramatic effect
export function delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Log user message (Cyan)
 */
export function logUser(text: string): void {
    console.log(chalk.cyan(`\n👤 User: "${text}"`));
}

/**
 * Log agent message (Yellow)
 */
export function logAgent(text: string): void {
    console.log(chalk.yellow(`🤖 Agent: ${text}`));
}

/**
 * Log Guardian scanning animation
 */
export async function logGuardianScanning(): Promise<void> {
    process.stdout.write(chalk.gray.dim("\n🛡️  Guardian Kernel analyzing request"));
    for (let i = 0; i < 3; i++) {
        await delay(300);
        process.stdout.write(chalk.gray.dim("."));
    }
    console.log("\n");
}

/**
 * Log a tier check result
 */
export function logTierCheck(
    tier: number,
    name: string,
    status: "PASS" | "FAIL" | "WARN"
): void {
    const tierLabel = `Tier ${tier}`;

    switch (status) {
        case "PASS":
            console.log(chalk.green(`   ✅ ${tierLabel} [${name}]: Passed`));
            break;
        case "FAIL":
            console.log(chalk.red.bold(`   🛑 ${tierLabel} [${name}]: BLOCKED`));
            break;
        case "WARN":
            console.log(chalk.yellow(`   ⚠️  ${tierLabel} [${name}]: Warning`));
            break;
    }
}

/**
 * Log a ledger hash (Magenta)
 */
export function logLedgerHash(hash: string): void {
    const shortHash = hash.substring(0, 16);
    console.log(chalk.magenta(`\n   🔗 Ledger Hash: ${shortHash}...`));
}

/**
 * Log success message
 */
export function logSuccess(text: string): void {
    console.log(chalk.green.bold(`\n✅ ${text}`));
}

/**
 * Log error/block message
 */
export function logBlocked(text: string): void {
    console.log(chalk.red.bold(`\n🛑 BLOCKED: ${text}`));
}

/**
 * Log info message
 */
export function logInfo(text: string): void {
    console.log(chalk.blue(`ℹ️  ${text}`));
}

/**
 * Log section header
 */
export function logSection(title: string): void {
    const line = "═".repeat(50);
    console.log(chalk.white.bold(`\n${line}`));
    console.log(chalk.white.bold(`  ${title}`));
    console.log(chalk.white.bold(`${line}`));
}

/**
 * Log scene header (for video)
 */
export function logScene(number: number, title: string): void {
    console.log(chalk.bgBlue.white.bold(`\n  📽️  SCENE ${number}: ${title}  `));
}

/**
 * Log subtle divider
 */
export function logDivider(): void {
    console.log(chalk.gray("─".repeat(50)));
}

/**
 * Print the Guardian ASCII art banner
 */
export function printBanner(): void {
    console.log(chalk.cyan(`
╔══════════════════════════════════════════════════════╗
║                                                      ║
║     █████╗ ██████╗ ███╗   ███╗ ██████╗ ██████╗       ║
║    ██╔══██╗██╔══██╗████╗ ████║██╔═══██╗██╔══██╗      ║
║    ███████║██████╔╝██╔████╔██║██║   ██║██████╔╝      ║
║    ██╔══██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗      ║
║    ██║  ██║██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║      ║
║    ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝      ║
║                                                      ║
║          🛡️  GUARDIAN KERNEL v1.0  🛡️                ║
║       Intent-Aware Agent Security Framework          ║
║                                                      ║
╚══════════════════════════════════════════════════════╝
  `));
}

/**
 * Print a ledger entry in visual format
 */
export function logLedgerEntry(
    index: number,
    hash: string,
    timestamp: number,
    action: string,
    actor: string
): void {
    const time = new Date(timestamp).toLocaleTimeString();
    const shortHash = hash.substring(0, 8);

    if (index > 0) {
        console.log(chalk.gray("        ▲"));
        console.log(chalk.gray("        │"));
    }

    console.log(
        chalk.magenta(`[🔗 ${shortHash}]`) +
        chalk.gray(` ← `) +
        chalk.blue(`[${time}]`) +
        chalk.white(` ${action}`) +
        chalk.gray(` (${actor})`)
    );
}
