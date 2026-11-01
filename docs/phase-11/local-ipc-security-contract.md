# Phase 11 — Local IPC Security Contract

## Goal

Prepare a narrow, versioned request contract for future communication between the management console and the optional host diagnostics agent.

## Implemented in this phase

- Transport-neutral JSON envelope validator.
- Strict schema version, bounded message size, opaque request ID format, and method allowlist.
- Only `host.health.read` and `host.diagnostics.read` are accepted.
- Parameters must be an empty object; unknown fields are rejected.
- Client-supplied identity, role, ownership, consent, entitlement, authorization, device identifiers, commands, and shell fields are rejected.
- Unit tests cover valid messages and malformed, oversized, unknown, and authority-bearing requests.

## Not implemented

This is not an IPC server or authenticated channel. It does not open TCP sockets, named pipes, Unix sockets, launch services, enroll agents, issue credentials, validate peer identity, or grant authorization. A syntactically valid message is not trusted and must not be acted on until a separately reviewed authenticated transport and server-side authorization provider exist.

## Required transport controls before activation

1. Prefer OS-native local IPC with peer-credential verification (Windows named-pipe ACLs and client identity; Unix-domain socket ownership/permissions and peer credentials; macOS XPC where appropriate).
2. If loopback TCP is used for development, bind exclusively to loopback, use authenticated mutually bound sessions, reject remote interfaces, and avoid fixed-port assumptions.
3. Authenticate the peer independently of request fields. Never trust client-supplied user, role, device ownership, consent, or entitlement claims.
4. Use short-lived, revocable, audience-bound enrollment credentials from a trusted provider. No embedded static shared secrets.
5. Apply message size, schema, method, rate, timeout, and replay protections at the transport boundary.
6. Permit only read-only health/diagnostic methods. No arbitrary commands, shell, filesystem browsing, remote control, firmware changes, or security-control modifications.
7. Treat missing, expired, revoked, malformed, or unverifiable peer evidence as UNKNOWN/DENY.
8. Record only redacted audit metadata; never log credentials, raw device identifiers, or message bodies containing personal data.

## Security boundary

This phase does not inspect or alter Activation Lock, passcodes, Apple Account protections, MDM, or any other device security control. Device ownership and authorization remain independent of repository ownership, local account access, device possession, or IPC connectivity.

## Validation

The unit tests validate the message contract only. Actual OS IPC peer authentication, service installation, upgrade, rollback, and uninstall remain SKIPPED until transport/provider implementation and platform test runners are available.
