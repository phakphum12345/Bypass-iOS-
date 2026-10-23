# Release and installation guide

This repository is a defensive Flutter architecture reference. Release artifacts package the reference UI only; they do not unlock devices, remove Activation Lock, bypass passcodes or MDM, or grant authorization/entitlements.

## Supported CI release targets

- **Web:** a static Flutter web build in the `web-release` artifact.
- **Linux x64:** a Linux release bundle packaged as `research-os-linux-x64.tar.gz` in the `linux-release` artifact.

These artifacts are built and uploaded by the GitHub Actions **Final Gate** workflow for pull requests, pushes to `main`, and manual runs. Open the workflow run, then download the artifact from its **Artifacts** section. Artifacts are temporary CI outputs, not a signed/versioned GitHub Release.

## Run the Web build

1. Download and extract the `web-release` artifact.
2. Serve the extracted directory with a static HTTP server or deploy it to a static web host.
3. Configure the host's fallback routing if you later add client-side paths.

Do not open `index.html` directly from the filesystem; use an HTTP server.

## Run the Linux x64 build

1. Download and extract `linux-release`.
2. Extract `research-os-linux-x64.tar.gz`.
3. From the extracted `bundle` directory, run `./bypass_architecture_reference` (the executable name follows the Flutter package name).

The Linux bundle is built on Ubuntu x64. The target machine needs compatible Linux system libraries, including GTK 3. This is not a universal Linux package and is not currently distributed as a DEB, RPM, AppImage, or signed installer.

## Verification boundaries

A successful Final Gate means CI validated the required architecture/security contracts, Flutter analysis and tests, and the configured Web/Linux release builds. It does **not** prove installation on every real device or distribution. Perform a smoke test on the intended target OS before production use.

There is no iOS IPA or signed iOS app produced by this workflow. An iOS build requires macOS/Xcode signing and provisioning setup; do not treat Web/Linux artifacts as iOS install packages.
