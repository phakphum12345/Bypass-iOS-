# Decision API, Device Diagnostics, Identity, and Authorization Foundation (Phases 1–4)

This is a development-only, loopback-bound API scaffold. The live decision API is deliberately **deny-only**: no production identity, ownership, consent, capability, policy, authorization, entitlement, or execution provider is enabled. A valid decision request returns decision=DENY, authorization=DENY, and entitlement=UNKNOWN. The server does not perform or trigger device operations.

Phase 3 adds backend.identity, a server-side identity-provider interface and fail-closed bearer-session evidence resolver. The default provider is unavailable, so the resolver returns UNKNOWN. It does not issue tokens, authenticate accounts, create sessions, or establish device ownership. A future adapter must independently validate signature, issuer, audience, session status, and revocation before returning verified evidence. Never log or persist bearer tokens.

Phase 4 adds backend.authorization, a pure evaluator requiring current, scope-matched identity, ownership, consent, policy, and entitlement evidence. Missing or untrusted evidence remains UNKNOWN; explicit denials, revocation, expiry, and scope mismatches deny the request. This evaluator is not wired into an HTTP route, has no configured providers, and never executes an operation. Its ALLOW result is only an eligibility result for a separate future review/confirmation workflow. The live decision API remains deny-only.

## Run

From the repository root, run: python -m backend.decision_api.server

The server binds to loopback and selects an available port by default. Copy the printed DECISION_API_URL into the Flutter build configuration. Set DECISION_API_PORT to request a port, or 0 to let the OS select one. The server rejects non-loopback bind addresses. For browser clients, set DECISION_API_ALLOWED_ORIGINS to a comma-separated exact origin allowlist. No wildcard CORS policy is enabled by default.

## Contract

- GET /health: reports service health and deny_only mode.
- POST /v1/decisions: accepts exactly the four request fields in api/contracts/decision-request.json.
- Client-supplied authorization or entitlement fields are rejected.
- GET /v1/devices/{opaque-reference}/diagnostics: returns a versioned, read-only diagnostic report. With no trusted platform adapter configured, all device and connection attributes remain UNKNOWN; passcode, Activation Lock, MDM, and device-trust states are NOT_INSPECTED.
- The diagnostics endpoint never establishes ownership, grants authorization, or performs a device operation.
- Phase 3 identity evidence is resolved only by a trusted server-side provider; client-supplied role, ownership, or organization claims are not accepted by the resolver.
- Phase 4 evidence evaluation is an isolated Python contract; it is not exposed over HTTP and accepts no client-submitted evidence fields.
- The default identity provider is unavailable; identity remains UNKNOWN.
- GET /v1/execute and other execution routes do not exist.

This scaffold is not production-ready and must not be exposed to the public internet. A trusted read-only device adapter, production identity and ownership providers, consent/policy/entitlement sources, authentication integration, rate limiting, audit persistence, TLS, deployment target, and threat-model review are separate required work. Never send a device serial number, UDID, passcode, Apple Account credential, or other secret as device_id; use a non-sensitive opaque reference.
