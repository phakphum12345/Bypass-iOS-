# Phase 20 — Checkpointed Durable Local IPC Audit

## Purpose

Connect the existing durable IPC event-audit wrapper (Phase 17) to the
checkpoint contract and local checkpoint-history store (Phases 18–19).

## Implemented

- Persist the metadata-only IPC outcome through the existing durable audit
  ledger wrapper.
- Reconcile every stored checkpoint against the exact event-ledger prefix it
  claims to represent.
- Create and append a checkpoint for the newly persisted ledger head.
- Return a successful read result only when both event persistence and
  checkpoint persistence succeed.
- Preserve denied outcomes in the event ledger and checkpoint history.
- If checkpoint loading, reconciliation, or append fails after the event was
  persisted, report AUDIT_CHECKPOINT_FAILED and suppress the read result.
- Keep the checkpoint hash as an evidence reference, not an authorization
  token or external trust assertion.

## Trust and safety boundary

This is an in-process orchestration function, not a transport listener. Both
SQLite stores remain local and in the same administrative trust domain.
A successful checkpoint means the local checkpoint record was persisted and
matched to a ledger prefix; it does not mean an external anchor is VERIFIED.
Phase 18's external anchor provider remains unconfigured and therefore
UNKNOWN by default. The wrapper grants no device authority and performs no
device operation.

## Not implemented / SKIPPED

- OS-native IPC transport, HTTP routes, Flutter integration, or remote calls.
- External timestamping, independent trust domain, signature verification,
  HSM/KMS, signing keys, remote replication, or tamper-proof storage.
- Production identity, tenant isolation, encryption-at-rest, or deployment.
- Device inspection, unlock, restore, Activation Lock, or MDM operations.

## Validation

GitHub Actions build, analysis, tests, iOS simulator, and final gate provide
the validation evidence for this PR. No local test run is claimed.
