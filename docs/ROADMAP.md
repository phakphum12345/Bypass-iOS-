# Bypass-iOS- Roadmap

## Product direction

Build a defensive iOS/iPadOS Device Diagnostics, Ownership, Authorized Recovery, and Enterprise Device Management platform. The product does not bypass Activation Lock, passcodes, MDM controls, Apple Account protections, or other security boundaries.

## Phase plan

| Phase | Scope | Exit criteria |
|---|---|---|
| 1. Decision API Spine | Loopback-only deny-only API, Flutter client, strict contracts | API and Flutter tests pass; no client-supplied authorization; CI green |
| 2. Device Intelligence | Opaque device registry references, read-only diagnostic report contract, evidence provenance, conservative UNKNOWN/NOT_INSPECTED states | Unit/API tests; no device writes; no sensitive identifiers; platform/security states never inferred |
| 3. Identity & Ownership | Authentication, verified device-owner relationship, delegated organization scope, technician identities | Trusted provider, session security, revocation, negative tests, audit evidence |
| 4. Consent, Policy & Entitlement | Scoped consent, policy evaluation, entitlement lifecycle, separation of duties | Server-only decisions; expiry/revocation tests; deny-by-default |
| 5. Authorized Recovery | Guided Apple-supported recovery and organization-authorized management workflows | Official supported procedures only; explicit confirmation; data-loss warnings; tested rollback/stop conditions |
| 6. Audit & Evidence | Append-only audit events, evidence integrity, retention/export, privacy controls | Tamper-evidence tests, access controls, retention and export validation |
| 7. Production & Enterprise | Hardened deployment, TLS, secrets, backups, tenant isolation, monitoring, incident response | Threat model, security review, restore drill, operational runbooks, production acceptance |

## Dependency order

Phase 2 is stacked on the unmerged Phase 1 PR. It does not target main directly because the decision API foundation is not merged yet. Merge Phase 1 first, then retarget/rebase Phase 2 onto main after review.

Phase 3 must not grant authority based on device connection or an opaque reference. Phase 4 must not return ALLOW until identity, ownership, consent, policy, and entitlement providers are independently verified. Phase 5 is limited to documented, authorized platform recovery and management paths.

## Release gates

- Preserve the base SHA, branch SHA, test output, and CI run identifiers.
- Run Python unit/API tests, Flutter tests/analyze/build, iOS Simulator build, and Final Gate.
- Treat PASS, FAIL, SKIPPED, and UNKNOWN distinctly.
- No merge or deployment without explicit Project Owner approval.
- Never report a device security state without a trusted source and timestamp.
