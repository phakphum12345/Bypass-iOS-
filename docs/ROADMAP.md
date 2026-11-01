# Bypass-iOS- Roadmap

## Product direction

Build a defensive iOS/iPadOS Device Diagnostics, Ownership, Authorized Recovery, and Enterprise Device Management platform. The product does not bypass Activation Lock, passcodes, MDM controls, Apple Account protections, or other security boundaries.

## Phase plan

| Phase | Scope | Exit criteria |
|---|---|---|
| 1. Decision API Spine | Loopback-only deny-only API, Flutter client, strict contracts | API and Flutter tests pass; no client-supplied authorization; CI green |
| 2. Device Intelligence | Opaque device registry references, read-only diagnostic report contract, evidence provenance, conservative UNKNOWN/NOT_INSPECTED states | Unit/API tests; no device writes; no sensitive identifiers; platform/security states never inferred |
| 3. Identity & Ownership | Trusted authentication provider contract, verified device-owner relationship, delegated organization scope, technician identities | Production-grade trusted provider, secure sessions, revocation, ownership evidence, negative tests, audit evidence |
| 4. Consent, Policy & Entitlement | Scoped consent, policy evaluation, entitlement lifecycle, separation of duties | Server-only decisions; expiry/revocation tests; deny-by-default |
| 5. Authorized Recovery | Guided Apple-supported recovery and organization-authorized management workflows | Official supported procedures only; explicit confirmation; data-loss warnings; tested rollback/stop conditions |
| 6. Audit & Evidence | Append-only audit events, evidence integrity, retention/export, privacy controls | Tamper-evidence tests, access controls, retention and export validation |
| 7. Production & Enterprise | Hardened deployment, TLS, secrets, backups, tenant isolation, monitoring, incident response | Threat model, security review, restore drill, operational runbooks, production acceptance |

## Delivery status

- Phase 1: merged to main via PR #11 (merge commit ae5a79b2ee26a11d16e4d2033ff72a11b6811afc).
- Phase 2: merged to main via PR #12 (merge commit 45b53ec7d3d6f2da4578c9599f234f6b2b86afa4).
- Phase 3: merged to main via PR #13 (merge commit ae5a79b2ee26a11d16e4d2033ff72a11b6811afc). It adds a fail-closed identity-provider contract only; no production authentication or ownership provider is enabled.
- Phase 4: in progress on a separate PR. It adds a pure evidence evaluator and negative tests; no trusted providers or live authorization route are enabled.

## Dependency order

Phase 3 must not grant authority based on device connection, an opaque reference, repository ownership, or client-supplied claims. The default identity provider is unavailable, so identity remains UNKNOWN. Phase 4 must not return ALLOW in the live API until identity, ownership, consent, policy, and entitlement providers are independently verified. Phase 5 is limited to documented, authorized platform recovery and management paths.

## Release gates

- Preserve the base SHA, branch SHA, test output, and CI run identifiers.
- Run Python unit/API tests, Flutter tests/analyze/build, iOS Simulator build, and Final Gate.
- Treat PASS, FAIL, SKIPPED, and UNKNOWN distinctly.
- No merge or deployment without explicit Project Owner approval.
- Never report a device security state without a trusted source and timestamp.
