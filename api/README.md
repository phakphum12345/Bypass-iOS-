# API Contracts

The API is the authoritative security boundary.

The Flutter external tool sends requests and displays authoritative results.
The client must not manufacture authorization, entitlement, or execution
permission.

## Decision

A workflow may proceed only when:

```
Authorization == ALLOWED
AND
Entitlement == ACTIVE
AND
Decision == ALLOWED
```

Otherwise the authoritative result is DENY. Missing, invalid, conflicting,
expired, or unknown security state must fail closed.

## Correlation

Every decision request and response must support correlation through a
correlation_id. The client rejects a response whose correlation_id does not
match the originating request.

## Evidence

Authoritative evidence is produced or validated by the server. Client-provided
evidence is not authoritative.

## Phase 1 implementation status

The development API scaffold is in `backend/decision_api`. It is loopback-only
and deny-only until trusted server-side identity, policy, authorization, and
entitlement providers exist. It does not execute device operations. See
`backend/README.md` for local startup and configuration.

## Phase 2 device diagnostics

`GET /v1/devices/{opaque-reference}/diagnostics` returns a versioned, read-only report. Until a trusted platform adapter is implemented, device attributes and connection status are `UNKNOWN`; passcode, Activation Lock, MDM enrollment, and device trust are `NOT_INSPECTED`. This report is not proof of ownership and does not authorize or execute an operation. See `docs/phase-2/device-intelligence.md`.
