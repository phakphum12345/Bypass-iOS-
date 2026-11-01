# Phase 7 — Threat Model

## Assets

- User and technician identity/session evidence.
- Device ownership and organization authorization evidence.
- Consent, policy, and entitlement decisions.
- Opaque device and correlation references.
- Diagnostic reports and audit evidence.
- Build artifacts, signing credentials, deployment configuration, and tenant data.

## Trust boundaries

1. Flutter client to API: client input is untrusted; the client cannot assert identity, ownership, consent, policy, entitlement, or execution authority.
2. API to identity/ownership providers: only authenticated, server-side provider responses may contribute trusted evidence.
3. Tenant boundary: every request, record, cache key, audit event, export, and background job must be scoped to the authenticated tenant.
4. API to device adapter: adapters must be read-only by default and limited to documented, authorized interfaces.
5. CI to release environment: build outputs are untrusted until provenance, review, signing, and protected-environment approvals are verified.
6. Audit storage: the in-memory hash chain is not a production trust anchor; durable storage needs independently protected chain-head anchoring.

## Threats and required controls

| Threat | Required control | Fail-closed behavior |
|---|---|---|
| Forged client role or ownership claim | Server-side identity and ownership verification | DENY / UNKNOWN |
| Stolen or replayed session | Short-lived sessions, revocation, audience/scope checks, MFA where appropriate | DENY |
| Consent replay or scope expansion | Purpose, device, tenant, action, expiry, and revocation binding | DENY |
| Cross-tenant data access | Tenant scoping at every data access layer and negative tests | DENY |
| Malicious or malformed request | Strict schema, size limits, rate limiting, safe parsing | Reject request |
| Audit record tampering | Durable append-only store and independently protected chain anchor | Stop audit-dependent workflow |
| Secret leakage | Managed secret store, redaction, log scanning, rotation | Revoke and investigate |
| Compromised build/dependency | Pinned dependencies, scanning, SBOM, provenance, protected release | Block release |
| Insecure transport or ingress | TLS, network policy, restricted egress, security review | Block deployment |
| Unsafe device command path | Read-only adapter contract, allowlisted operations, independent authorization | No operation |
| Misleading device status | Provenance, timestamp, source health, UNKNOWN when unavailable | Do not infer state |
| Data loss or ransomware | Encrypted backups, restore drills, retention and incident procedures | Suspend affected workflow |

## Abuse cases explicitly out of scope

The system must not provide Activation Lock bypass, passcode bypass, Apple Account credential collection, MDM circumvention, exploit delivery, unauthorized access, or security-control evasion. Ownership of this source repository is not evidence of ownership of a connected device.

## Residual risks and current limitations

- The API is a development-only loopback service and remains deny-only.
- No production identity, ownership, consent, policy, entitlement, or device provider is configured.
- No production TLS ingress, managed secrets, tenant-isolated persistence, or durable audit store exists.
- Phase 6 hash chaining is tamper-evident within the in-memory data structure, not tamper-proof against full ledger replacement.
- CI builds do not produce a signed physical-device iOS package or attest a production deployment.

## Review triggers

Re-review after changes to identity, ownership, authorization, device adapters, persistence, tenancy, external network exposure, signing, data retention, or deployment topology.
