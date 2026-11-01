# Phase 4 — Consent, Policy & Entitlement

## Scope

Phase 4 introduces a pure server-side evidence evaluator for one exact request. It requires independently verified identity, device ownership, explicit consent, applicable policy, and service entitlement. It does not add a login flow, provider integration, authorization HTTP route, device operation, or production grant path.

## Evidence requirements

- **Identity:** a current, non-revoked session from the trusted Phase 3 identity provider.
- **Ownership:** a current trusted relationship binding the authenticated subject to the exact opaque device reference. Possession, USB connection, repository ownership, and client claims are not evidence.
- **Consent:** explicit owner consent bound to subject, device, and exact action; time-bounded and revocable.
- **Policy:** an active trusted policy bound to the device and explicitly permitting the exact action.
- **Entitlement:** an active trusted service entitlement bound to the subject and exact service.

All timestamps must be timezone-aware and current. Scope mismatches, expired or revoked consent, denying policy, inactive/revoked/expired entitlement, and other explicit negative evidence deny the request. Missing, unavailable, malformed, stale, or incomplete evidence remains UNKNOWN and cannot grant authority.

## Runtime boundary

The backend.authorization.evaluate_authorization function is a pure evaluator over server-side evidence objects. It is not wired into backend.decision_api.server; the existing HTTP decision API remains deny-only. No evidence provider is configured, no route accepts these objects, and no device operation is available. ALLOW from this isolated evaluator means only that supplied trusted evidence is eligible for a separate review/confirmation stage; operation_performed remains false.

## Separation of duties

A technician cannot grant owner consent, self-approve a high-impact action, elevate their own role, or override organization policy. Project Owner authority over this GitHub repository is not device ownership. Any future provider must be independently authenticated, audited, revocable, and tested against cross-subject/cross-device replay.

## Exit criteria still outstanding

- Trusted ownership, consent, policy, and entitlement provider integrations.
- Provider authentication, integrity, revocation, and lifecycle tests.
- Persistent append-only audit and evidence provenance.
- Human confirmation and separation-of-duties workflow for any future high-impact operation.
- Security review and explicit Project Owner acceptance.

Until those exist, protected actions remain DENY in the live API.
