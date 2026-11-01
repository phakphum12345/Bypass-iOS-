# Phase 10 — Host Agent Lifecycle Contract

## Goal

Define a deterministic, fail-closed lifecycle model for the optional read-only host diagnostics agent introduced in Phase 9.

## States and transitions

- STOPPED → STARTING
- STARTING → RUNNING, STOPPING, or FAILED
- RUNNING → STOPPING or FAILED
- STOPPING → STOPPED or FAILED
- FAILED → STOPPED (explicit reset required)

All other transitions are rejected. A FAILED state is never ready. Health output never implies authentication, ownership, consent, entitlement, or authorization.

## Implementation in this phase

- Adds an in-memory Python state machine with deterministic transitions.
- Adds health snapshot fields and negative tests for invalid transitions.
- Failure codes are bounded and restricted to simple alphanumeric/underscore identifiers.
- No host identifiers, user data, paths, credentials, or environment variables are included.

## Explicitly not implemented

This is a lifecycle contract, not a running service manager. It does not spawn or terminate processes, install OS services, configure launch agents/systemd/Windows services, bind a socket, persist state, enroll an agent, authenticate IPC, or execute device operations. It does not grant authorization.

## Security requirements for later IPC/service work

- Bind only to loopback or an OS-native local IPC mechanism with peer authentication.
- Never expose an unauthenticated network listener.
- Use short-lived, revocable credentials from a trusted enrollment provider; never embed shared secrets in the app.
- Treat missing, expired, invalid, or revoked enrollment as UNKNOWN/DENY.
- Keep diagnostics read-only and keep device adapters disabled until separately reviewed.
- Provide explicit stop/uninstall behavior and test upgrade/rollback on actual supported OS versions.

## Validation

Unit tests cover legal transitions, invalid transition rejection, failure handling, readiness semantics, and the invariant that health never grants authorization or claims an operation.
