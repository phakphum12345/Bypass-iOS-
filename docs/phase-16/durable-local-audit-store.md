# Phase 16 — Durable Local Audit Store

## Goal

Add an opt-in, file-backed SQLite adapter for the existing immutable SHA-256 audit ledger. The store persists only already-validated audit events and verifies the complete chain whenever it is read or extended.

## Implemented in this phase

- Add `SQLiteAuditStore` with explicit initialization, load, and append operations.
- Use SQLite transactions and `BEGIN IMMEDIATE` to serialize append attempts.
- Permit only append of a ledger whose existing prefix exactly matches persisted evidence.
- Treat replay of the same ledger as idempotent.
- Add database triggers that reject ordinary SQL UPDATE and DELETE statements.
- Reconstruct typed audit events and verify the complete hash chain on every load and after append.
- Fail closed on malformed records, chain mismatch, conflicting history, or database errors.
- Add tests for empty state, persistence/reload, append conflict, idempotency, update/delete rejection, and tamper detection.

## Security and privacy boundary

The store accepts only the existing `AuditLedger` model. It does not accept request bodies, diagnostics payloads, credentials, serials, UDIDs, or raw device identifiers. It does not grant authorization or trigger device operations.

SQLite triggers are an application-level guard, not a security boundary against an administrator or attacker who can replace the database, drop triggers, alter the schema, or rewrite the file. A hash chain detects modifications only when a trusted prior chain head is available; this phase does not provide an independently protected anchor.

## Not implemented / SKIPPED

- No automatic wiring into the IPC dispatcher or HTTP API; callers must explicitly persist the returned ledger.
- No encryption-at-rest, key management, authenticated access control, tenant isolation, remote replication, backup/restore policy, or trusted timestamp.
- No cross-process identity or OS-native IPC transport.
- No device inspection, device writes, shell, remote control, or security-control changes.
- No production deployment or production readiness claim.

## Validation

CI runs the repository build, tests, analysis, iOS simulator, and final gate. Unit tests cover the SQLite adapter contract. Filesystem permissions, platform-specific database locking behavior, backup/restore, and hostile administrator-level tampering remain outside this phase.
