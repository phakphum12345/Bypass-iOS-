# Phase 7 — Production & Enterprise Readiness

<badge>NOT PRODUCTION READY</badge>

## Current verified architecture boundary

The repository currently provides a defensive reference Flutter UI and a local loopback-only decision API. The decision API is deny-only. Identity, ownership, consent, policy, entitlement, and device capability providers are not production-integrated. Phase 6 audit evidence is an in-memory contract, not durable storage. CI artifacts are temporary build outputs; they are not signed releases or a production deployment.

A green CI run is not production authorization.

## Required production gates

Every gate below requires independently inspectable evidence. A checklist declaration alone is not proof. Missing, stale, conflicting, or untrusted evidence is UNKNOWN and blocks release.

### Security architecture
- [ ] Current threat model and data-flow diagrams reviewed by an independent security reviewer.
- [ ] Server-side authentication, session expiry, revocation, and MFA policy are implemented and tested.
- [ ] Ownership evidence is authoritative, scoped to the target device and organization, and revocable.
- [ ] Consent is explicit, purpose-bound, time-bound, and recorded before any permitted workflow.
- [ ] Policy and entitlement are evaluated server-side; clients cannot submit authority claims.
- [ ] No route or adapter can bypass the deny-only decision boundary.
- [ ] Activation Lock, passcode, Apple Account, and MDM protections remain outside the product's bypass scope.

### Deployment and network
- [ ] Production deployment uses a supported, patched runtime and pinned dependencies.
- [ ] TLS 1.2+ is enforced at the ingress; certificate renewal and expiry monitoring are tested.
- [ ] Backend is not exposed directly; ingress, network policy, firewall, and egress allowlists are reviewed.
- [ ] Development loopback server is not reused as a production server.
- [ ] Health/readiness endpoints reveal no identity, device, tenant, secret, or internal topology data.
- [ ] Rate limits, request size limits, abuse detection, and safe shutdown are configured.
- [ ] CORS is exact-origin allowlisted; no wildcard credentials policy.

### Secrets and identity
- [ ] Secrets are stored in a managed secret store and injected at runtime.
- [ ] No secrets, signing materials, tokens, or personal device identifiers are committed to source or CI logs.
- [ ] Key rotation, revocation, access review, and emergency credential rotation are tested.
- [ ] CI uses least-privilege permissions and protected environments for release actions.
- [ ] Production signing keys and provisioning profiles are protected and never included in artifacts.

### Data, audit, and privacy
- [ ] Durable append-only audit persistence is implemented with independently protected chain-head anchoring.
- [ ] Audit writes are authenticated, tenant-scoped, access-controlled, and monitored.
- [ ] Encryption at rest and in transit is verified.
- [ ] Retention, legal hold, export, deletion, and restore policies are approved and tested.
- [ ] Export authorization, redaction, and access logging are tested.
- [ ] Raw serial numbers, UDIDs, passcodes, Apple Account credentials, and recovery keys are not collected or logged.
- [ ] Data inventory, purpose limitation, user notice, and privacy review are approved.

### Enterprise isolation and operations
- [ ] Tenant isolation is enforced at storage, query, cache, queue, and audit layers.
- [ ] Cross-tenant negative tests are passing.
- [ ] Backup encryption, restore drills, RPO/RTO targets, and disaster recovery are verified.
- [ ] Monitoring, alerting, incident response, vulnerability disclosure, and escalation runbooks are approved.
- [ ] Dependency and container/image scanning, SBOM, artifact provenance, and release signing are configured.
- [ ] Rollback and safe-mode procedures are rehearsed.

### Device and platform validation
- [ ] Read-only adapters use documented, supported Apple or organization-approved interfaces.
- [ ] Device identity and state are reported only from trusted sources with provenance and timestamps.
- [ ] Unknown or inaccessible states remain UNKNOWN / NOT_INSPECTED.
- [ ] Physical-device tests are performed on explicitly authorized test devices.
- [ ] No test or release workflow attempts to bypass Activation Lock, passcodes, MDM, or other security controls.

## Release decision

Production approval requires all applicable gates to be PASS, named reviewers, evidence references, and a separately authorized release decision. Any FAIL or UNKNOWN blocks production release. This document does not enable deployment, authorize device operations, or assert that any production control exists.

## Current phase outcome

Phase 7 in this PR establishes the readiness criteria and CI documentation gate only. Production providers, hosting, TLS termination, durable storage, signing, tenant isolation, and deployment are NOT implemented by this PR.
