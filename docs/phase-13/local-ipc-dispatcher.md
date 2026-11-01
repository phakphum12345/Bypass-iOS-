# Phase 13 — Authenticated Local IPC Dispatcher

## Goal

Connect the Phase 11 message-envelope validator and Phase 12 peer-authentication contract through a small in-process dispatcher. The dispatcher must authenticate a server-owned connection context before returning any host diagnostics.

## Implemented in this phase

- A transport-neutral `dispatch_local_ipc_request` function.
- Strict request validation through the Phase 11 envelope contract.
- Peer verification through the Phase 12 `resolve_peer` contract before dispatch.
- Default unavailable authentication remains fail-closed: UNKNOWN peers are denied.
- A second server-side method allowlist permits only:
  - `host.health.read`
  - `host.diagnostics.read`
- Provider failures return redacted error codes; exception details are not exposed.
- Responses preserve the request ID and explicitly state that authorization was not granted and no device operation was performed.
- Tests cover denied peers, revoked/expired evidence, provider exceptions, request validation, request correlation, and the two read-only methods.

## Trust and authorization boundary

A VERIFIED local IPC peer is not proof of a human identity, device ownership, consent, entitlement, or authority to modify a device. This dispatcher exposes only host health and allowlisted workstation diagnostics. It does not grant device-operation authorization.

The connection context must be an opaque server-owned object obtained from a future OS-native transport. Never construct it from JSON fields, caller-provided strings, device identifiers, or claimed identity.

## Not implemented / SKIPPED

- No TCP listener, named pipe, Unix-domain socket, XPC service, or other transport.
- No OS credential inspection or production peer-authentication provider.
- No service installation, process launch, persistence, enrollment, or credential issuance.
- No HTTP route or Flutter integration.
- No device inspection, device writes, remote command execution, shell, filesystem browsing, or security-control changes.
- No production authorization, tenant isolation, or durable audit service.

## Validation

Unit tests exercise the in-process dispatcher with a test verifier. The production default remains unavailable and denies requests. Native Windows, Linux, and macOS transport/authentication tests remain SKIPPED until platform adapters exist.
