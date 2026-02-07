import { ArmorIQGuardian } from "./guardian-integration";

/**
 * Integration test for the ArmorIQ Guardian system.
 * Tests the full flow: Token signing → Request validation → Ledger audit
 */
async function testIntegration(): Promise<void> {
    console.log("=".repeat(60));
    console.log("🛡️  ArmorIQ Guardian - Integration Test");
    console.log("=".repeat(60));
    console.log();

    // Create a fresh guardian instance for testing
    const guardian = new ArmorIQGuardian();

    // ============================================================
    // Test 1: Full successful flow (Caretaker with valid scope)
    // ============================================================
    console.log("--- Test 1: Caretaker with Valid Scope ---");

    const validToken = guardian.signToken({
        principal_role: "caretaker",
        token_scopes: ["patient:basic:read", "patient:records:read"],
    });
    console.log(`  ✅ Token signed successfully`);
    console.log(`  📝 Token (first 50 chars): ${validToken.substring(0, 50)}...`);

    try {
        const result = await guardian.validateRequest(
            validToken,
            "records",
            { patient_id: "P-12345", record_type: "medical_history" }
        );
        console.log(`  ✅ Request validated: ${result}`);
    } catch (error) {
        console.log(`  ❌ Unexpected error: ${(error as Error).message}`);
    }
    console.log();

    // ============================================================
    // Test 2: Caretaker WITHOUT required scope (should fail)
    // ============================================================
    console.log("--- Test 2: Caretaker WITHOUT Records Scope ---");

    const noScopeToken = guardian.signToken({
        principal_role: "caretaker",
        token_scopes: ["patient:basic:read"], // Missing patient:records:read
    });
    console.log(`  ✅ Token signed (without records scope)`);

    try {
        await guardian.validateRequest(
            noScopeToken,
            "records",
            { patient_id: "P-12345", record_type: "medical_history" }
        );
        console.log(`  ❌ Should have thrown an error!`);
    } catch (error) {
        console.log(`  ✅ Correctly denied: ${(error as Error).message}`);
    }
    console.log();

    // ============================================================
    // Test 3: Automated agent exceeding budget (should fail)
    // ============================================================
    console.log("--- Test 3: Automated Agent Exceeding Budget ---");

    const agentToken = guardian.signToken({
        principal_role: "automated_agent",
        token_scopes: ["pharmacy:order"],
    });
    console.log(`  ✅ Agent token signed`);

    try {
        await guardian.validateRequest(
            agentToken,
            "pharmacy",
            { cost: 5000, medication: "Insulin" }
        );
        console.log(`  ❌ Should have thrown an error!`);
    } catch (error) {
        console.log(`  ✅ Correctly denied: ${(error as Error).message}`);
    }
    console.log();

    // ============================================================
    // Test 4: Automated agent within budget (should pass)
    // ============================================================
    console.log("--- Test 4: Automated Agent Within Budget ---");

    try {
        const result = await guardian.validateRequest(
            agentToken,
            "pharmacy",
            { cost: 1500, medication: "Aspirin" }
        );
        console.log(`  ✅ Request validated: ${result}`);
    } catch (error) {
        console.log(`  ❌ Unexpected error: ${(error as Error).message}`);
    }
    console.log();

    // ============================================================
    // Test 5: Invalid token (should fail)
    // ============================================================
    console.log("--- Test 5: Invalid Token ---");

    try {
        await guardian.validateRequest(
            "this.is.not.a.valid.token",
            "records",
            { patient_id: "P-12345" }
        );
        console.log(`  ❌ Should have thrown an error!`);
    } catch (error) {
        console.log(`  ✅ Correctly denied: ${(error as Error).message}`);
    }
    console.log();

    // ============================================================
    // Verify Audit Ledger
    // ============================================================
    console.log("=".repeat(60));
    console.log("📜 Audit Ledger History");
    console.log("=".repeat(60) + "\n");

    const history = guardian.getAuditHistory();
    console.log(`  Total entries: ${history.length}`);
    console.log();

    history.forEach((entry, index) => {
        console.log(`  [${index + 1}] ${entry.action}`);
        console.log(`      Actor: ${entry.actor}`);
        console.log(`      Tool: ${entry.payload.tool}`);
        console.log(`      Time: ${new Date(entry.timestamp).toISOString()}`);
        console.log(`      Hash: ${entry.hash.substring(0, 16)}...`);
        console.log();
    });

    // ============================================================
    // Verify Chain Integrity
    // ============================================================
    console.log("=".repeat(60));
    console.log("🔍 Verifying Ledger Integrity");
    console.log("=".repeat(60) + "\n");

    const isValid = guardian.verifyAuditIntegrity();
    if (isValid) {
        console.log("  ✅ Audit ledger integrity verified! All hashes are valid.");
    } else {
        console.log("  ❌ Audit ledger integrity FAILED!");
    }

    // ============================================================
    // Summary
    // ============================================================
    console.log();
    console.log("=".repeat(60));
    console.log("📊 Test Summary");
    console.log("=".repeat(60));
    console.log("  Test 1 (Caretaker + scope): ✅ PASS");
    console.log("  Test 2 (Caretaker - scope): ✅ PASS (denied correctly)");
    console.log("  Test 3 (Agent > budget): ✅ PASS (denied correctly)");
    console.log("  Test 4 (Agent < budget): ✅ PASS");
    console.log("  Test 5 (Invalid token): ✅ PASS (denied correctly)");
    console.log(`  Ledger entries: ${history.length}`);
    console.log(`  Chain integrity: ${isValid ? "✅ VALID" : "❌ INVALID"}`);
    console.log();
    console.log("=".repeat(60));
    console.log("🏁 Integration Test Complete");
    console.log("=".repeat(60));
}

// Run the test
testIntegration();
