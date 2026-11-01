# Phase 8 — Cross-platform Authorized Device Management

## Goal

Define a safe cross-platform management foundation for authorized technicians using Windows, Linux, and macOS workstations. The first implementation target is a management console plus optional host-side diagnostic agent. A host agent reports facts about its own host only; it must not imply that it can inspect or control an attached iPhone/iPad unless a separately reviewed, documented, read-only adapter is available.

This phase does not implement device unlocking, security-control removal, or production authorization.

## Product surfaces

- **Management console:** Flutter desktop UI for Windows, Linux, and macOS. It presents registered opaque references, evidence provenance, diagnostic reports, authorization status, and official recovery guidance.
- **Host diagnostic agent:** optional least-privilege process for collecting a narrowly allowlisted set of host OS facts (OS version, app version, agent health, supported interface availability). No persistence of raw serial numbers, UDIDs, passcodes, Apple Account credentials, recovery keys, or private keys.
- **Shared contract layer:** versioned JSON schemas for agent health, host diagnostics, device diagnostic evidence, consent scope, and audit references.
- **Build/release pipeline:** reproducible per-OS CI builds, checksums, SBOM, provenance, and signing only through protected release environments.

## Trust and authorization model

- The server remains authoritative for identity, tenant, ownership, consent, policy, entitlement, and action scope.
- Local UI state, a connected cable, a device name, an opaque reference, or repository ownership is never proof of ownership or permission.
- Missing, stale, conflicting, expired, revoked, or untrusted evidence is UNKNOWN/DENY.
- Agents authenticate with short-lived, revocable, device-bound credentials provisioned through an approved enrollment flow. No static shared secret is embedded in binaries.
- The first agent release is read-only and has no general shell, arbitrary command, file browsing, remote-control, or firmware interfaces.
- Device adapters are disabled by default. Each adapter requires a documented supported interface, source provenance, platform/version matrix, explicit consent, and negative tests.
- Activation Lock, passcode, Apple Account, MDM, anti-theft, and other platform security controls are security boundaries, never bypass targets.

## Supported workstation targets

| Target | Initial package formats | Notes |
|---|---|---|
| Windows 10/11 x64 | ZIP portable; MSI later | Authenticode signing is a protected release prerequisite. |
| Linux x64 | AppImage; DEB; RPM later | Build on supported runner images; document distro/runtime compatibility. |
| macOS arm64 and x64 | unsigned development app bundle; PKG/DMG later | Developer ID signing and notarization are required before general distribution. |

Package format availability is a target, not a claim that packages currently exist. Do not publish unsigned or unverified artifacts as production installers.

## Implementation sequence

1. Freeze versioned contracts and threat model for console/agent communication.
2. Add host-only diagnostic collector with explicit allowlist and deterministic tests.
3. Add read-only agent service lifecycle, health endpoint, and safe uninstall behavior.
4. Integrate console with local agent over authenticated loopback IPC; reject non-loopback listeners.
5. Add CI matrix builds for Windows, Linux, and macOS; produce development artifacts with checksums and SBOM.
6. Add signing/notarization only after protected secrets, release approvals, provenance, and rollback are implemented.
7. Add a separately reviewed, read-only Apple-device adapter only if documented interfaces support the required facts.

## Non-goals

- Activation Lock bypass or removal.
- Passcode bypass, credential extraction, or brute force.
- MDM circumvention, unenrollment without authorized administrator workflow, or profile tampering.
- Exploit delivery, jailbreak-based access, security-control evasion, or unauthorized remote access.
- Arbitrary shell execution, remote desktop, file exfiltration, or unattended device changes.

## Phase 8 exit criteria

- Contract schemas validate and have compatibility tests.
- Host collector returns only allowlisted fields and has redaction tests.
- Agent binds only to loopback/local IPC and fails closed on invalid enrollment.
- Console displays UNKNOWN when agent or evidence is unavailable.
- Cross-platform CI builds complete for each declared target; each artifact has digest and SBOM.
- Installation, upgrade, rollback, and uninstall are tested on actual supported OS versions before claiming install support.
- Security review confirms no bypass or arbitrary command path.
- No production release claim until Phase 7 gates are independently satisfied.
