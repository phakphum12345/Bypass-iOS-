# Phase 9 — Host Diagnostics Agent (read-only)

## Scope

Phase 9 introduces a minimal Python standard-library collector for workstation facts on Windows, Linux, and macOS. It is a library/API diagnostic endpoint, not yet a background service, installer, enrollment system, or production agent.

## Endpoint

- `GET /v1/host/diagnostics`
- Served only by the existing development API, which binds to loopback.
- Returns OS family/release, CPU architecture, Python runtime, agent version, capability declarations, source, and limitations.
- Does not return hostname, username, serial number, hardware UUID, MAC/IP address, filesystem paths, environment variables, installed software, or attached-device identifiers.
- Reports attached-device inspection as NOT_CONFIGURED and security-control changes as NOT_SUPPORTED.
- Never grants authorization or performs an operation.

## Security properties

- Standard-library only; no subprocess, shell, network scan, USB enumeration, filesystem crawl, privilege escalation, or persistence.
- The endpoint does not establish identity, tenant, ownership, consent, policy, or entitlement.
- Existing API remains development-only, loopback-bound, and deny-only. This endpoint is diagnostic metadata and is not an authorization route.
- Activation Lock, passcode, and MDM are not inspected or changed.
- Missing or unsupported platform information is reported as UNKNOWN/OTHER, never inferred.

## Validation

Backend unit tests cover allowlisted fields, excluded sensitive identifiers, no authorization/execution claims, and unknown OS handling. Cross-platform runtime verification and installation tests remain pending until the CI matrix and actual target hosts are available.

## Not included

No service manager integration, authenticated enrollment, signed binaries, MSI/DEB/RPM/PKG/DMG installers, remote management, device adapters, or production deployment.
