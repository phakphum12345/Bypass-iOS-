# Phase 15 — Dispatcher and Audit Evidence Integration

## Goal

Provide one in-process entry point that dispatches the existing authenticated, read-only local IPC request and appends the matching Phase 14 metadata-only audit event.

## Implemented in this phase

- Add `dispatch_local_ipc_request_with_audit` alongside the existing dispatcher API.
- Preserve the original `dispatch_local_ipc_request` behavior for callers that do not opt into audit integration.
- Capture the validated server-side peer evidence through a proxy; the underlying authenticator is invoked at most once.
- Append one Phase 14 audit event for each returned dispatcher outcome, including malformed requests.
- Return the immutable updated `AuditLedger` to the caller; the caller owns and must retain that value between calls.
- Keep audit decision UNKNOWN, use opaque references only, and never include request or diagnostics payloads or exception details.
- Add tests for successful reads, denied/unknown peers, malformed requests, provider failures, authenticator failures, and immutable ledger handling.

## Trust and privacy boundary

A VERIFIED local process remains insufficient to establish human identity, device ownership, consent, entitlement, or authority to modify a device. Audit integration is evidence recording only. The dispatcher continues to allow only host health and host diagnostics reads.

## Not implemented / SKIPPED

- No automatic durable storage or cross-process ledger coordination.
- No HTTP or Flutter integration, native IPC transport, OS peer-authentication provider, service installation, or production deployment.
- No device inspection or modification, Activation Lock/passcode/MDM changes, shell, or remote command execution.
- No authenticated audit query/export endpoint, tenant isolation, encryption-at-rest, or independently protected chain-head anchor.

## Validation

CI runs the repository build, test, analysis, iOS simulator, and final-gate workflows. These tests validate the in-process integration only; native transport and durable persistence remain SKIPPED.
