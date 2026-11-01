# Production Release Gate

**Current status: NOT PRODUCTION READY.**

A successful build or green pull-request workflow is necessary but insufficient for production release.

## Mandatory evidence packet

- Exact source commit SHA and reviewed pull request.
- Complete CI run URLs and successful conclusions for all required jobs.
- Dependency inventory and software bill of materials (SBOM).
- Artifact digest, provenance/attestation, and release signature verification.
- Security review and current threat-model approval.
- Production environment configuration review with secret values withheld.
- TLS, ingress, network, rate-limit, and CORS verification.
- Identity, ownership, consent, policy, entitlement, and revocation negative-test results.
- Tenant-isolation tests and independent access-control review.
- Durable audit persistence, integrity-anchor, export, retention, and restore evidence.
- Backup/restore drill, incident response, monitoring, and rollback evidence.
- Authorized physical-device smoke-test evidence for the supported device/OS matrix.
- Named release approver and explicit release authorization.

## Decision rules

- PASS: evidence is current, independently verifiable, and meets the stated control.
- FAIL: evidence demonstrates a control is absent or violated.
- SKIPPED: a test or review was not run; it is not a pass.
- UNKNOWN: evidence is missing, stale, conflicting, or cannot be verified.

Any applicable FAIL, SKIPPED, or UNKNOWN blocks production release. Do not convert a documentation checklist into a claim that the control is implemented. Never include credentials, signing keys, serial numbers, UDIDs, passcodes, or recovery keys in the evidence packet.

## Current release limitations

The repository's local API is loopback-only and deny-only. Current CI artifacts are temporary Web/Linux/iOS Simulator build artifacts, not signed production releases. No production hosting, identity provider, tenant isolation, durable audit service, or physical iOS signing workflow is established by this repository state.
