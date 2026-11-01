# Phase 8 — Cross-platform Artifact and Installer Plan

## Status

**PLANNED — no Phase 8 installer or signed release artifact is produced by this document.**

## Build matrix

| OS | CI runner target | Development artifact target | Installer target | Required release proof |
|---|---|---|---|---|
| Windows 10/11 x64 | windows-latest | ZIP portable | MSI | Authenticode signature, SHA-256, SBOM, provenance, install/upgrade/uninstall test |
| Ubuntu Linux x64 | ubuntu-latest | AppImage | DEB and RPM | SHA-256, SBOM, provenance, package install/remove tests on declared distros |
| macOS arm64/x64 | macos runners | app bundle archive | PKG and DMG | Developer ID signature, notarization, SHA-256, SBOM, provenance, install/uninstall test |

Runner labels and architecture availability must be verified in workflow execution; do not assume a runner label guarantees a particular CPU architecture.

## Artifact naming

Use deterministic names containing product, semantic version, OS, architecture, and package type, for example:

- `device-management_<version>_windows_x64.zip`
- `device-management_<version>_linux_x64.AppImage`
- `device-management_<version>_macos_arm64.dmg`

Each release must include a machine-readable manifest with source commit SHA, workflow run ID, build target, artifact filename, SHA-256 digest, SBOM reference, and signing/notarization status.

## Security requirements

- Build from reviewed commits only; pin third-party actions to immutable commit SHAs.
- Use least-privilege workflow permissions and protected release environments.
- Never expose signing keys, certificates, provisioning profiles, or notarization credentials to pull-request workflows.
- Do not embed API keys, bearer tokens, tenant secrets, or device identifiers in artifacts.
- Generate SBOM and provenance for every distributable package.
- Verify signatures and digests after packaging.
- Treat unsigned development artifacts as test-only and label them clearly.
- No installer may add a public network listener, firewall exception, privileged remote shell, or startup persistence without a separate reviewed requirement and explicit opt-in.
- Installer must support clean uninstall and document files intentionally retained; never delete user data silently.

## Test gates

- Static analysis and unit/contract tests.
- Package content inspection and malware/dependency scanning.
- Fresh install, upgrade, downgrade policy, repair, and uninstall tests on supported OS images.
- Least-privilege execution and no unexpected services/listeners.
- Local IPC is loopback-only and authenticated.
- Redaction checks ensure logs contain no secrets or raw device identifiers.
- Reproducibility/digest verification and SBOM presence.
- macOS signing/notarization and Windows signing checks before public distribution.

## Release labels

- `development`: unsigned, test-only, non-production.
- `candidate`: signed where supported, not yet approved for general distribution.
- `stable`: only after all applicable Phase 7 production gates pass and a named release approver authorizes publication.

CI success alone never promotes an artifact to stable.
