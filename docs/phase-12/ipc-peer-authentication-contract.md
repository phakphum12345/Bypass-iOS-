# Phase 12 — Local IPC Peer Authentication Contract

## Goal

Define the trusted server-side boundary that a future OS-native IPC adapter must satisfy before any local request can be considered authenticated.

## Implemented in this phase

- A transport-neutral `PeerAuthenticator` protocol.
- An explicit `UnavailablePeerAuthenticator` default that returns UNKNOWN.
- A resolver that accepts only verifier-produced evidence with:
  - a supported OS-native transport identifier;
  - opaque principal and channel-binding references;
  - an exact service audience;
  - timezone-aware authentication and expiry timestamps;
  - a non-expired, non-future authentication time.
- Provider exceptions, malformed responses, missing context, audience mismatch, unsupported transports, and incomplete evidence fail closed.
- Tests cover valid, unavailable, revoked, expired, malformed, mismatched, and time-invalid evidence.

## Critical trust boundary

The connection context must be an opaque, server-owned handle from a future transport implementation. It must never be built from JSON request fields, client-provided identity claims, device identifiers, or arbitrary strings.

The verifier must obtain peer identity from the operating system and cryptographically or OS-mechanism bind the result to the active channel. A caller cannot make itself trusted by constructing a `PeerEvidence` object or supplying a principal reference.

This module is only a provider contract. It does not implement OS peer authentication and must not be treated as doing so.

## Platform implementation gates

1. **Windows:** named pipe with restrictive ACLs; verify the connected client token/SID using supported OS APIs; protect against pipe squatting and remote named-pipe access; bind evidence to the actual pipe instance.
2. **Linux:** Unix-domain socket with restrictive directory/socket permissions; verify peer credentials using kernel-provided peer credentials; prevent symlink/path substitution and stale socket attacks.
3. **macOS:** prefer XPC with code-signing designated requirements and audit-token validation; do not substitute a client-supplied bundle identifier.
4. All platforms: exact service audience, short-lived evidence, revocation strategy, channel binding, rate/size/time limits, redacted logs, and explicit service lifecycle/rollback.
5. Platform-specific tests must run on native CI runners before a platform adapter can be enabled.

## Not implemented / SKIPPED

- No named pipe, Unix socket, XPC service, TCP listener, or other transport.
- No OS credential inspection, process launch, service registration, installer, or persistence.
- No trusted enrollment authority, credential issuance, revocation service, or production identity provider.
- No integration with the HTTP API or device-operation path.
- No device inspection or security-control changes.

## Safety boundary

A verified local host peer is not proof of a user's device ownership, consent, entitlement, or authority to alter a device. This phase does not permit arbitrary commands, shell access, file browsing, remote control, firmware changes, or security-control operations. Activation Lock, passcode, and MDM protections remain out of scope and must not be bypassed.

## Validation

The unit tests validate only the fail-closed evidence resolver. Real Windows, Linux, and macOS peer-authentication tests remain SKIPPED until native adapters exist.
