# Phase 3 — Identity & Ownership Foundation

## Scope of this PR

This PR introduces a server-side identity-provider contract and fail-closed session-evidence resolver. It is a foundation, not a production authentication system.

- Only a trusted server-side adapter may validate bearer sessions.
- The adapter is responsible for signature, issuer, audience, session, and revocation checks.
- A verified result must include opaque issuer, subject, and session references plus timezone-aware issue, authentication, and expiry timestamps.
- Missing, malformed, expired, revoked, future-dated, inconsistent, incomplete, or provider-error results never become VERIFIED.
- Bearer credentials are not returned in evidence and must never be logged.
- Client-supplied roles, ownership claims, organization membership, and authorization decisions are not accepted.
- The default provider is unavailable; therefore the current runtime cannot authenticate users.

## Deliberate non-goals

No OAuth/OIDC provider, login UI, token issuance, refresh-token storage, database, organization directory, ownership registry, device binding, authorization grant, or protected operation is implemented here. No identity is inferred from a device reference, USB connection, repository ownership, or device diagnostics.

## Next integration gates

Before enabling a real provider, independently review:
1. OIDC issuer and audience allowlists, signature/JWKS rotation, algorithm restrictions, nonce/state/PKCE and redirect URI handling.
2. Secure session issuance, short expiry, refresh rotation, logout, revocation propagation, and replay protections.
3. Account linking and verified ownership evidence, including conflict resolution and recovery paths.
4. Tenant/organization membership provenance and scope checks.
5. Rate limiting, CSRF/CORS policy, secret management, TLS, privacy-safe logs, and security review.

Until those gates pass, identity is UNKNOWN and all protected actions remain DENY.
