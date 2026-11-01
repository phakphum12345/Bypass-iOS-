# Phase 19 — Durable Audit Checkpoint Store

## Purpose

Persist deterministic Phase 18 checkpoints and verify the checkpoint history
when it is loaded. This is a local durability layer, not an external anchor.

## Implemented

- A separate SQLite checkpoint table, independent of the audit event table.
- Transactional append and reload verification of checkpoint digests.
- Exact retry idempotency.
- Monotonic event-count and timestamp checks.
- Rejection when a checkpoint at the same event count changes the chain head.
- Ordinary SQL UPDATE and DELETE guards.
- Tests for reload, retries, invalid digests, ordering conflicts, and tampering.

## Trust boundary

The checkpoint table resides in the same SQLite database and administrative
trust domain as the local audit ledger. Triggers and digest checks do not
prevent a privileged actor from replacing the database, changing its schema,
or rewriting all records and hashes. This store does not authenticate an
external service, verify digital signatures, or establish an independent
anchor. Phase 18's external provider remains unconfigured and therefore
resolves to UNKNOWN.

## Not implemented / SKIPPED

- External timestamping or independent anchor service.
- HSM/KMS, signing keys, remote replication, or automatic scheduling.
- Encryption-at-rest, tenant isolation, or production deployment.
- HTTP/Flutter/native IPC integration or device operations.

## Validation

CI is the source of build, analysis, test, iOS simulator, and final-gate
evidence. No local test run is claimed by this change.
