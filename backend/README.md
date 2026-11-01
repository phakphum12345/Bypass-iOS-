# Decision API, Device Diagnostics, Identity, Authorization, Recovery, and Audit Foundation (Phases 1–7)

This is a development-only, loopback-bound API scaffold. The live decision API is deliberately **deny-only**: no production identity, ownership, consent, capability, policy, authorization, entitlement, or execution provider is enabled. A valid decision request returns decision=DENY, authorization=DENY, and entitlement=UNKNOWN. The server does not perform or trigger device operations.

Phase 3 adds backend.identity, a server-side identity-provider interface and fail-closed bearer-session evidence resolver. The default provider is unavailable, so the resolver returns UNKNOWN. It does not issue tokens, authenticate accounts, create sessions, or establish device ownership. A future adapter must independently validate signature, issuer, audience, session status, and revocation before returning verified evidence. Never log or persist bearer tokens.

Phase 4 adds backend.authorization, a pure evaluator requiring current, scope-matched identity, ownership, consent, policy, and entitlement evidence. Missing or untrusted evidence remains UNKNOWN; explicit denials, revocation, expiry, and scope mismatches deny the request. This evaluator is not wired into an HTTP route, has no configured providers, and never executes an operation. Its ALLOW result is only an eligibility result for a separate future review/confirmation workflow. The live decision API remains deny-only.

Phase 5 adds backend.recovery_workflow, a pure informational planner for official Apple and organization-authorized recovery guidance. It does not connect to devices, inspect device state, execute commands, or grant authorization. Restore guidance warns about local data loss and unverified backup availability. Activation Lock and MDM are explicit security stops; no bypass/removal workflow exists.

Phase 6 adds backend.audit_evidence, an immutable in-memory ledger contract with SHA-256 hash chaining, verification, redacted JSON export, and non-destructive retention candidate reporting. It is not connected to the HTTP API and has no database, durable append-only store, authenticated access control, tenant isolation, encryption-at-rest, or independently protected chain-head anchor. The hash chain is tamper-evident, not tamper-proof. Phase 16 adds an opt-in SQLiteAuditStore adapter with transactional append, prefix-conflict detection, reload verification, and ordinary SQL UPDATE/DELETE guards. It is not automatically wired into the dispatcher or HTTP API; callers must explicitly persist returned ledgers. SQLite triggers do not protect against database-file replacement or an administrator who can alter the schema. There is no independent chain-head anchor, encryption-at-rest, authenticated access control, tenant isolation, or remote replication. Audit evidence never grants authorization or triggers an operation.

Phase 7 documents production and enterprise readiness gates, a threat model, and evidence-based release requirements. It does not configure hosting, TLS termination, managed secrets, production identity, tenant isolation, durable audit persistence, signing, or deployment. The service remains development-only, loopback-bound, and deny-only. A green CI workflow is not production approval.

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
- Phase 5 recovery planning is an isolated Python contract; it is not exposed over HTTP and cannot execute device operations.
- Phase 6 audit evidence is an isolated in-memory contract; it is not exposed over HTTP and cannot grant authorization.
- The default identity provider is unavailable; identity remains UNKNOWN.
- GET /v1/execute and other execution routes do not exist.

This scaffold is not production-ready and must not be exposed to the public internet. A trusted read-only device adapter, production identity and ownership providers, consent/policy/entitlement sources, authentication integration, rate limiting, durable append-only audit persistence, TLS, deployment target, and threat-model review are separate required work. Never send a device serial number, UDID, passcode, Apple Account credential, or other secret as device_id; use a non-sensitive opaque reference.
