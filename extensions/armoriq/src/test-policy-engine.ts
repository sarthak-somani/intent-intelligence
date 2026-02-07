import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import { PolicyEngine, EvaluationContext } from "./policy-engine";

// Get current directory for ESM modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Test script for the Policy Engine
 */
function testPolicyEngine(): void {
    console.log("=".repeat(60));
    console.log("🛡️  Policy Engine Test Script");
    console.log("=".repeat(60));
    console.log();

    // Initialize the engine and load policies
    const engine = new PolicyEngine();
    const policiesPath = join(__dirname, "..", "policies", "healthcare.json");
    engine.loadPolicies(policiesPath);
    console.log();

    // Test Case 1: Automated agent tries to spend > 2000 INR (should DENY)
    console.log("--- Test 1: Budget Check (Automated Agent, 5000 INR) ---");
    const result1 = engine.evaluate(
        "pharmacy",
        { cost: 5000, medication: "Insulin" },
        { principal_role: "automated_agent" }
    );
    console.log(`  Tool: pharmacy`);
    console.log(`  Cost: 5000 INR`);
    console.log(`  Role: automated_agent`);
    console.log(`  ✅ Allowed: ${result1.allowed}`);
    console.log(`  📋 Reason: ${result1.reason}`);
    console.log();

    // Test Case 2: Automated agent spends <= 2000 INR (should ALLOW)
    console.log("--- Test 2: Budget Check (Automated Agent, 1500 INR) ---");
    const result2 = engine.evaluate(
        "pharmacy",
        { cost: 1500, medication: "Aspirin" },
        { principal_role: "automated_agent" }
    );
    console.log(`  Tool: pharmacy`);
    console.log(`  Cost: 1500 INR`);
    console.log(`  Role: automated_agent`);
    console.log(`  ✅ Allowed: ${result2.allowed}`);
    console.log(`  📋 Reason: ${result2.reason}`);
    console.log();

    // Test Case 3: Human user spends > 2000 INR (should ALLOW - rule only applies to agents)
    console.log("--- Test 3: Budget Check (Human User, 5000 INR) ---");
    const result3 = engine.evaluate(
        "pharmacy",
        { cost: 5000, medication: "Insulin" },
        { principal_role: "human_user" }
    );
    console.log(`  Tool: pharmacy`);
    console.log(`  Cost: 5000 INR`);
    console.log(`  Role: human_user`);
    console.log(`  ✅ Allowed: ${result3.allowed}`);
    console.log(`  📋 Reason: ${result3.reason}`);
    console.log();

    // Test Case 4: Caretaker WITHOUT required scope tries to access records (should DENY)
    console.log("--- Test 4: Delegation Privacy (Caretaker, NO Scope) ---");
    const result4 = engine.evaluate(
        "records",
        { patient_id: "P-12345", record_type: "medical_history" },
        { principal_role: "caretaker", token_scopes: ["patient:basic:read"] }
    );
    console.log(`  Tool: records`);
    console.log(`  Role: caretaker`);
    console.log(`  Scopes: ["patient:basic:read"]`);
    console.log(`  ✅ Allowed: ${result4.allowed}`);
    console.log(`  📋 Reason: ${result4.reason}`);
    console.log();

    // Test Case 5: Caretaker WITH required scope accesses records (should ALLOW)
    console.log("--- Test 5: Delegation Privacy (Caretaker, WITH Scope) ---");
    const result5 = engine.evaluate(
        "records",
        { patient_id: "P-12345", record_type: "medical_history" },
        { principal_role: "caretaker", token_scopes: ["patient:basic:read", "patient:records:read"] }
    );
    console.log(`  Tool: records`);
    console.log(`  Role: caretaker`);
    console.log(`  Scopes: ["patient:basic:read", "patient:records:read"]`);
    console.log(`  ✅ Allowed: ${result5.allowed}`);
    console.log(`  📋 Reason: ${result5.reason}`);
    console.log();

    // Test Case 6: Patient (not caretaker) accesses their own records (should ALLOW)
    console.log("--- Test 6: Delegation Privacy (Patient, Own Records) ---");
    const result6 = engine.evaluate(
        "records",
        { patient_id: "P-12345", record_type: "medical_history" },
        { principal_role: "patient", token_scopes: [] }
    );
    console.log(`  Tool: records`);
    console.log(`  Role: patient`);
    console.log(`  Scopes: []`);
    console.log(`  ✅ Allowed: ${result6.allowed}`);
    console.log(`  📋 Reason: ${result6.reason}`);
    console.log();

    // Summary
    console.log("=".repeat(60));
    console.log("📊 Test Summary");
    console.log("=".repeat(60));
    console.log(`  Test 1 (Agent > 2000): ${!result1.allowed ? "✅ DENIED as expected" : "❌ UNEXPECTED ALLOW"}`);
    console.log(`  Test 2 (Agent <= 2000): ${result2.allowed ? "✅ ALLOWED as expected" : "❌ UNEXPECTED DENY"}`);
    console.log(`  Test 3 (Human > 2000): ${result3.allowed ? "✅ ALLOWED as expected" : "❌ UNEXPECTED DENY"}`);
    console.log(`  Test 4 (Caretaker NO scope): ${!result4.allowed ? "✅ DENIED as expected" : "❌ UNEXPECTED ALLOW"}`);
    console.log(`  Test 5 (Caretaker WITH scope): ${result5.allowed ? "✅ ALLOWED as expected" : "❌ UNEXPECTED DENY"}`);
    console.log(`  Test 6 (Patient, own records): ${result6.allowed ? "✅ ALLOWED as expected" : "❌ UNEXPECTED DENY"}`);
    console.log();
    console.log("=".repeat(60));
    console.log("🏁 Policy Engine Test Complete");
    console.log("=".repeat(60));
}

// Run the test
testPolicyEngine();
