# Phase 14 — Local IPC Audit Evidence Mapping

## Goal

Define a narrow adapter from Phase 13 IPC outcomes to the existing Phase 6 immutable audit evidence contract. Preserve evidence without recording request bodies or diagnostic payloads.

## Implemented in this phase

- Map the two allowlisted IPC methods to fixed audit action names.
- Map dispatcher outcomes to audit results:
  - OK → SUCCEEDED
  - ERROR → FAILED
  - DENIED and INVALID_REQUEST → NOT_RUN
- Use the verified peer's opaque principal reference only when the supplied evidence is marked VERIFIED; otherwise use a fixed peer_unknown sentinel.
- Use a fixed not_applicable host-scope reference because these events describe host IPC, not a target device.
- Preserve a valid request ID as the correlation reference; malformed or absent IDs fall back to the server-generated event ID.
- Always set audit decision=UNKNOWN. A verified local process is not device ownership, consent, entitlement, or authority to change a device.
- Return a new immutable ledger and preserve existing hash-chain verification.

## Privacy and trust boundaries

- The adapter accepts no request body, diagnostics report, exception text, credentials, serial, UDID, or other raw device identifier.
- The peer evidence must come from the server-side Phase 12 resolver, not from client JSON.
- Opaque references are metadata, not credentials.
- Audit records do not grant authorization or trigger operations.

## Not implemented / SKIPPED

- No automatic integration into the Phase 13 dispatcher.
- No durable database, append-only remote store, tenant isolation, authenticated audit API, encryption-at-rest, or independently protected chain-head anchor.
- No OS-native IPC transport or peer-authentication implementation.
- No device inspection, device writes, shell, remote control, or security-control changes.

## Validation

Unit tests verify mapping, immutable append behavior, hash-chain validity, unknown actor handling, result mapping, fixed action allowlist, and absence of request/diagnostic payload inputs. This validates only the in-memory adapter contract; durable audit persistence remains SKIPPED.
