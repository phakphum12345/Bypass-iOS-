# Evidence Model

Evidence records are immutable after creation. Audit events are appended as new records and linked using a cryptographic hash chain.

## Required audit event fields

- event_id
- actor_ref (server-issued opaque reference)
- device_ref (server-issued opaque reference)
- service_id
- action
- decision (ALLOW, DENY, UNKNOWN)
- result (SUCCEEDED, FAILED, NOT_RUN, UNKNOWN)
- occurred_at (timezone-aware UTC timestamp)
- correlation_ref (opaque request correlation reference)
- previous_hash
- event_hash
- schema_version

## Rules

Evidence must identify the actor and target device through opaque references only. Never store serial numbers, UDIDs, passcodes, Apple Account credentials, recovery keys, or other secrets.

Evidence must identify the policy/decision context and result where applicable. Client-generated information must not be treated as authoritative security evidence unless validated by the server.

Each event hash is SHA-256 over canonical JSON of the event payload excluding event_hash. Each event links to the preceding event hash; the first event links to the all-zero genesis hash. Verification must reject altered payloads, broken links, duplicate event IDs, and unsupported schema versions.

## Privacy, retention, and export

Exports redact actor_ref, device_ref, and correlation_ref by default. Including opaque references requires an explicit caller choice and future server-side export authorization. Retention evaluation may identify records older than a configured cutoff but must not silently delete or rewrite evidence. Destructive retention requires a separately approved, auditable policy and protected archive process.

## Audit reconstruction

Audit data must support reconstruction of:

request
→ decision
→ workflow
→ result

## Limitations

An in-memory hash chain is tamper-evident, not tamper-proof. Production use requires durable append-only storage, authenticated append/read/export access, tenant isolation, encryption at rest, independently protected chain-head anchoring, trusted timestamps, backup/restore validation, and an incident response process. Audit records never grant authorization or cause device operations.
