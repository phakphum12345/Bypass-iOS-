# Phase 18 — Independent Audit Checkpoint Verification Contract

## Purpose

Define a deterministic checkpoint for the durable audit ledger and a narrow
provider contract for verifying that checkpoint against an independent trust
domain. This is a contract and validation layer, not a deployed anchor service.

## Implemented

- Create a checkpoint binding schema version, event count, current hash-chain
  head, and timezone-aware creation timestamp.
- Hash the canonical checkpoint payload with SHA-256.
- Validate provider evidence against the exact checkpoint digest.
- Require opaque provider and anchor references and a bounded validity window.
- Return `UNKNOWN` when the provider is absent, unavailable, malformed,
  expired, future-dated, or returns evidence for another checkpoint.
- Include a default unavailable provider that fails closed.

## Trust boundary

The provider adapter is responsible for authenticating the external service,
validating its signature or authenticated response, enforcing trust roots,
and ensuring the anchor is held outside the SQLite database's administrative
trust boundary. This module cannot establish that trust itself. A provider
that simply echoes values from the local database is not an independent
anchor and must not be marked VERIFIED.

The checkpoint hash is not a signature. It detects a mismatch only when
compared with independently authenticated evidence.

## Not implemented / SKIPPED

- No external anchor provider, signing key, HSM, KMS, remote service, or
  network request is configured.
- No automatic checkpoint schedule or dispatcher integration.
- No claim of tamper-proof storage or production-grade audit immutability.
- No encryption-at-rest, tenant isolation, native IPC transport, device
  operation, or production deployment.

## Validation

Tests cover deterministic checkpoint structure, empty-ledger genesis state,
valid normalized evidence, missing provider, provider exception, digest
mismatch, expired/future evidence, and checkpoint tampering.
