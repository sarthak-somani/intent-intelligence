import { MerkleLedger } from "./ledger";

/**
 * Test script to verify the MerkleLedger implementation.
 * Creates sample entries and validates chain integrity.
 */
function testMerkleLedger(): void {
    console.log("=".repeat(60));
    console.log("🔐 Merkle Ledger Test Script");
    console.log("=".repeat(60));
    console.log();

    // Instantiate the ledger
    const ledger = new MerkleLedger();

    // Add 3 dummy entries
    console.log("📝 Adding entries to the ledger...\n");

    const entry1 = ledger.append("user-123", "USER_LOGIN", {
        ip: "192.168.1.100",
        userAgent: "Mozilla/5.0",
        loginMethod: "password",
    });
    console.log(`✅ Entry 1 added: ${entry1.action}`);

    const entry2 = ledger.append("user-123", "VIEW_RECORDS", {
        recordType: "patient_data",
        recordIds: ["rec-001", "rec-002", "rec-003"],
        accessLevel: "read-only",
    });
    console.log(`✅ Entry 2 added: ${entry2.action}`);

    const entry3 = ledger.append("user-123", "USER_LOGOUT", {
        sessionDuration: 3600,
        actionsPerformed: 15,
    });
    console.log(`✅ Entry 3 added: ${entry3.action}`);

    // Display the full chain
    console.log("\n" + "=".repeat(60));
    console.log("📜 Full Ledger Chain:");
    console.log("=".repeat(60) + "\n");

    const history = ledger.getHistory();
    history.forEach((entry, index) => {
        console.log(`--- Entry ${index + 1} ---`);
        console.log(`  ID:        ${entry.id}`);
        console.log(`  Actor:     ${entry.actor}`);
        console.log(`  Action:    ${entry.action}`);
        console.log(`  Timestamp: ${new Date(entry.timestamp).toISOString()}`);
        console.log(`  PrevHash:  ${entry.prevHash.substring(0, 16)}...`);
        console.log(`  Hash:      ${entry.hash.substring(0, 16)}...`);
        console.log(`  Payload:   ${JSON.stringify(entry.payload)}`);
        console.log();
    });

    // Verify integrity
    console.log("=".repeat(60));
    console.log("🔍 Verifying Chain Integrity...");
    console.log("=".repeat(60) + "\n");

    const isValid = ledger.verifyIntegrity();
    if (isValid) {
        console.log("✅ Chain integrity verified! All hashes are valid.");
    } else {
        console.log("❌ Chain integrity check FAILED! Tampering detected.");
    }

    console.log("\n" + "=".repeat(60));
    console.log("🏁 Test Complete");
    console.log("=".repeat(60));
}

// Run the test
testMerkleLedger();
