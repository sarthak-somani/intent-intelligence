"""SHA-256 hash-chained audit ledger with Merkle tree batch verification."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


@dataclass
class TraceStep:
    step: int
    name: str
    result: str   # PASS, BLOCKED, SKIP, N/A
    detail: str


@dataclass
class AuditEntry:
    sequence: int
    timestamp: str
    entry_hash: str
    previous_hash: str
    merkle_root: str | None
    caller_id: str
    caller_role: str
    tool: str
    params: dict
    verdict: str          # ALLOW | BLOCK | EMERGENCY_BYPASS
    reason: str
    trace: list[dict]     # serialized TraceSteps
    suggestions: list[str]
    delegation_id: str | None = None
    budget_remaining: float | None = None


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def _redact_phi(params: dict) -> dict:
    """Redact PHI-sensitive fields from params before logging."""
    redacted = {}
    sensitive_keys = {"result", "results", "record", "records", "diagnosis", "medication_details"}
    for k, v in params.items():
        if k in sensitive_keys:
            redacted[k] = "[REDACTED]"
        else:
            redacted[k] = v
    return redacted


class MerkleLedger:
    """In-memory hash-chained audit ledger with Merkle tree roots."""

    MERKLE_BATCH_SIZE = 10

    def __init__(self) -> None:
        self._entries: list[AuditEntry] = []
        self._genesis_hash = _sha256("HOSPITAL_GUARDIAN_GENESIS_BLOCK")

    @property
    def entries(self) -> list[AuditEntry]:
        return self._entries

    def _compute_entry_hash(self, timestamp: str, tool: str, verdict: str, previous_hash: str) -> str:
        payload = f"{timestamp}|{tool}|{verdict}|{previous_hash}"
        return _sha256(payload)

    def _compute_merkle_root(self, hashes: list[str]) -> str:
        """Compute Merkle tree root from a list of hashes."""
        if not hashes:
            return _sha256("EMPTY")
        level = list(hashes)
        while len(level) > 1:
            next_level: list[str] = []
            for i in range(0, len(level), 2):
                left = level[i]
                right = level[i + 1] if i + 1 < len(level) else left
                next_level.append(_sha256(left + right))
            level = next_level
        return level[0]

    def log(
        self,
        caller_id: str,
        caller_role: str,
        tool: str,
        params: dict,
        verdict: str,
        reason: str,
        trace: list[TraceStep],
        suggestions: list[str] | None = None,
        delegation_id: str | None = None,
        budget_remaining: float | None = None,
    ) -> AuditEntry:
        """Log an action to the ledger and return the entry."""
        seq = len(self._entries)
        prev_hash = self._entries[-1].entry_hash if self._entries else self._genesis_hash
        ts = datetime.now(timezone.utc).isoformat()

        entry_hash = self._compute_entry_hash(ts, tool, verdict, prev_hash)

        # Compute Merkle root every MERKLE_BATCH_SIZE entries
        merkle_root: str | None = None
        if (seq + 1) % self.MERKLE_BATCH_SIZE == 0:
            start = seq + 1 - self.MERKLE_BATCH_SIZE
            batch_hashes = [self._entries[i].entry_hash for i in range(start, seq)]
            batch_hashes.append(entry_hash)
            merkle_root = self._compute_merkle_root(batch_hashes)

        serialized_trace = [
            {"step": t.step, "name": t.name, "result": t.result, "detail": t.detail}
            for t in trace
        ]

        entry = AuditEntry(
            sequence=seq,
            timestamp=ts,
            entry_hash=entry_hash,
            previous_hash=prev_hash,
            merkle_root=merkle_root,
            caller_id=caller_id,
            caller_role=caller_role,
            tool=tool,
            params=_redact_phi(params),
            verdict=verdict,
            reason=reason,
            trace=serialized_trace,
            suggestions=suggestions or [],
            delegation_id=delegation_id,
            budget_remaining=budget_remaining,
        )
        self._entries.append(entry)
        return entry

    def get_recent(self, count: int = 10, filter_verdict: str | None = None) -> list[dict]:
        """Return recent audit entries as dicts."""
        entries = self._entries
        if filter_verdict:
            entries = [e for e in entries if e.verdict == filter_verdict]
        selected = entries[-count:]
        return [asdict(e) for e in selected]

    def verify_chain(self) -> dict:
        """Verify the entire hash chain and all Merkle roots."""
        if not self._entries:
            return {"valid": True, "entries": 0, "chain": "EMPTY", "merkle_roots_checked": 0}

        errors: list[str] = []
        prev_hash = self._genesis_hash

        for entry in self._entries:
            expected = self._compute_entry_hash(entry.timestamp, entry.tool, entry.verdict, prev_hash)
            if entry.entry_hash != expected:
                errors.append(f"Seq {entry.sequence}: hash mismatch")
            if entry.previous_hash != prev_hash:
                errors.append(f"Seq {entry.sequence}: chain break")
            prev_hash = entry.entry_hash

        # Verify Merkle roots
        merkle_checked = 0
        for i, entry in enumerate(self._entries):
            if entry.merkle_root is not None:
                batch_end = i + 1
                batch_start = batch_end - self.MERKLE_BATCH_SIZE
                if batch_start >= 0:
                    batch_hashes = [self._entries[j].entry_hash for j in range(batch_start, batch_end)]
                    expected_root = self._compute_merkle_root(batch_hashes)
                    if entry.merkle_root != expected_root:
                        errors.append(f"Seq {entry.sequence}: Merkle root mismatch")
                    merkle_checked += 1

        return {
            "valid": len(errors) == 0,
            "entries": len(self._entries),
            "chain": "INTACT" if not errors else "BROKEN",
            "merkle_roots_checked": merkle_checked,
            "merkle_roots_valid": merkle_checked if not errors else 0,
            "errors": errors,
        }


# ── Singleton ─────────────────────────────────────────────────────────
ledger = MerkleLedger()
