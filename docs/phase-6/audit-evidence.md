# Phase 6 — Audit & Evidence Integrity

## Scope delivered in this phase

- An immutable, in-memory event sequence: append returns a new ledger and does not mutate the prior value.
- SHA-256 hash chaining over canonical JSON event payloads.
- Verification detects altered payloads, broken links, duplicate event IDs, and unsupported schema versions.
- Strict event fields use opaque references only; arbitrary fields and raw identifiers are not accepted.
- JSON export redacts actor, device, and correlation references by default.
- Retention evaluation reports candidate event IDs only. It does not delete, rewrite, or compact evidence.

## Explicit limitations

This is a pure Python contract, not a durable audit service. It has no HTTP endpoint, database, encryption-at-rest, authenticated append permissions, tenant isolation, key management, trusted clock, export authorization, or background retention job. The in-memory hash chain is tamper-evident for accidental or detectable mutation, not tamper-proof against an attacker able to rewrite the entire ledger and its hashes. A production adapter must anchor chain heads in independently protected storage and enforce server-side access control.

No device operation is authorized or performed. A decision value of ALLOW is evidence metadata only; the existing live decision API remains deny-only. Never record serial numbers, UDIDs, passcodes, Apple Account credentials, recovery keys, or other secrets. Use server-issued opaque references.

## Validation

Tests cover append immutability, chain linkage, payload/link tampering, duplicate IDs, malformed references, timestamp and enum validation, non-destructive retention candidates, and privacy-redacted export.
