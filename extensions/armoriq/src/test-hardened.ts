import { GuardianProxy } from "./guardian-proxy";
import { ArmorIQGuardian } from "./guardian-integration";
import { validateToolContract } from "./guardian-schemas";
import { existsSync, unlinkSync, readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Test script for the Hardened Guardian (Phase 5).
 * Tests persistent logging, strict schemas, and full integration.
 */
async function testHardenedGuardian(): Promise<void> {
    console.log("=".repeat(60));
    console.log("🛡️  Hardened Guardian Test (Phase 5)");
    console.log("=".repeat(60));
    console.log();

    // Clean up previous log file for fresh test
    const logDir = join(__dirname, "..", "logs");
    const logFile = join(logDir, "guardian_audit.log");
    if (existsSync(logFile)) {
        try {
            unlinkSync(logFile);
            console.log("✅ Cleaned previous log file\n");
        } catch (e) {
            console.log("⚠️  Could not clean log file\n");
        }
    }

    // Create fresh instances
    const proxy = new GuardianProxy();
    const guardian = proxy.getGuardian();

    // Sign a valid token
    const validToken = guardian.signToken({
        principal_role: "user",
        token_scopes: ["pharmacy:order", "patient:records:read"],
    });
    console.log("✅ Token signed for testing\n");

    // ============================================================
    // Test 1: Schema Validation - Invalid cost type
    // ============================================================
    console.log("--- Test 1: Schema Violation (Invalid Type) ---");
    console.log("  Tool: pharmacy");
    console.log("  Args: { cost: 'expensive' }");

    const schema1 = validateToolContract("pharmacy", { cost: "expensive" });
    console.log(`  Valid: ${schema1.valid}`);
    if (schema1.errors) {
        console.log(`  Errors: ${schema1.errors.join(", ")}`);
    }
    console.log();

    // ============================================================
    // Test 2: Schema Validation - Cost exceeds limit
    // ============================================================
    console.log("--- Test 2: Schema Violation (Limit Exceeded) ---");
    console.log("  Tool: pharmacy");
    console.log("  Args: { cost: 999999 }");

    const schema2 = validateToolContract("pharmacy", { cost: 999999 });
    console.log(`  Valid: ${schema2.valid}`);
    if (schema2.errors) {
        console.log(`  Errors: ${schema2.errors.join(", ")}`);
    }
    console.log();

    // ============================================================
    // Test 3: Schema Validation - Invalid patient ID (injection attempt)
    // ============================================================
    console.log("--- Test 3: Schema Violation (Injection Attempt) ---");
    console.log("  Tool: records");
    console.log("  Args: { patient: \"'; DROP TABLE users;--\" }");

    const schema3 = validateToolContract("records", { patient: "'; DROP TABLE users;--" });
    console.log(`  Valid: ${schema3.valid}`);
    if (schema3.errors) {
        console.log(`  Errors: ${schema3.errors.join(", ")}`);
    }
    console.log();

    // ============================================================
    // Test 4: Full Proxy Flow with PII Sanitization
    // ============================================================
    console.log("--- Test 4: Full Proxy Flow (PII + Schema + Policy) ---");
    console.log("  Prompt: 'Order vitamins, email: test@mail.com, phone: 123-456-7890'");
    console.log("  Tool: pharmacy");
    console.log("  Args: { cost: 500, medication: 'Vitamins' }");

    const result4 = await proxy.executeProtectedCall({
        token: validToken,
        tool: "pharmacy",
        args: { cost: 500, medication: "Vitamins" },
        prompt: "Order vitamins, email: test@mail.com, phone: 123-456-7890",
    });
    console.log(`  Success: ${result4.success}`);
    console.log(`  Sanitized: "${result4.sanitizedPrompt}"`);
    if (result4.error) {
        console.log(`  Error: ${result4.error}`);
    }
    console.log();

    // ============================================================
    // Test 5: Valid records access
    // ============================================================
    console.log("--- Test 5: Valid Records Access ---");
    console.log("  Patient ID: P12345 (valid format)");

    const schema5 = validateToolContract("records", { patient: "P12345", recordType: "blood" });
    console.log(`  Valid: ${schema5.valid}`);
    console.log();

    // ============================================================
    // Test 6: Emergency override
    // ============================================================
    console.log("--- Test 6: Emergency Override (Lenient) ---");
    console.log("  Tool: emergency");
    console.log("  Args: { anything: 'goes', here: true }");

    const schema6 = validateToolContract("emergency", { anything: "goes", here: true, nested: { deep: "value" } });
    console.log(`  Valid: ${schema6.valid}`);
    console.log();

    // ============================================================
    // Verify Persistent Logging
    // ============================================================
    console.log("=".repeat(60));
    console.log("📜 Persistent Audit Log");
    console.log("=".repeat(60) + "\n");

    const logPath = proxy.getLogFilePath();
    console.log(`  Log file: ${logPath}`);

    if (existsSync(logPath)) {
        const logContent = readFileSync(logPath, "utf-8");
        const lines = logContent.trim().split("\n").filter(l => l.length > 0);
        console.log(`  Entries persisted: ${lines.length}`);
        console.log("\n  Recent entries:");
        lines.slice(-3).forEach((line, i) => {
            try {
                const entry = JSON.parse(line);
                console.log(`    [${i + 1}] ${entry.action} - ${entry.actor}`);
            } catch (e) {
                console.log(`    [${i + 1}] (parse error)`);
            }
        });
    } else {
        console.log("  Log file not yet created");
    }

    // ============================================================
    // Verify Chain Integrity
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("🔍 Chain Integrity Check");
    console.log("=".repeat(60) + "\n");

    const isValid = proxy.verifyAuditIntegrity();
    console.log(`  Integrity: ${isValid ? "✅ VALID" : "❌ INVALID"}`);

    const history = proxy.getAuditHistory();
    console.log(`  In-memory entries: ${history.length}`);

    // ============================================================
    // Summary
    // ============================================================
    console.log("\n" + "=".repeat(60));
    console.log("📊 Test Summary");
    console.log("=".repeat(60));
    console.log("  Test 1 (Invalid type): " + (!schema1.valid ? "✅ BLOCKED" : "❌ ALLOWED"));
    console.log("  Test 2 (Limit exceeded): " + (!schema2.valid ? "✅ BLOCKED" : "❌ ALLOWED"));
    console.log("  Test 3 (Injection): " + (!schema3.valid ? "✅ BLOCKED" : "❌ ALLOWED"));
    console.log("  Test 4 (Full flow): " + (result4.success ? "✅ PASSED" : "⚠️ " + result4.error));
    console.log("  Test 5 (Valid access): " + (schema5.valid ? "✅ ALLOWED" : "❌ BLOCKED"));
    console.log("  Test 6 (Emergency): " + (schema6.valid ? "✅ LENIENT" : "❌ BLOCKED"));
    console.log(`  Persistent logging: ${existsSync(logPath) ? "✅ ACTIVE" : "❌ INACTIVE"}`);
    console.log(`  Chain integrity: ${isValid ? "✅ VALID" : "❌ INVALID"}`);
    console.log();
    console.log("=".repeat(60));
    console.log("🏁 Hardened Guardian Test Complete");
    console.log("=".repeat(60));
}

// Run the test
testHardenedGuardian();
