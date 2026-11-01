# Security Boundary

## Authority domains

The Project Owner governs this software repository. Device owners and verified organizations govern their own devices within applicable delegated authority. Apple-controlled security services remain governed by Apple and the applicable account/device recovery process.

## Non-negotiable boundaries

This project must not implement or facilitate:
- Activation Lock or Apple Account lock bypass;
- passcode bypass, credential extraction, or recovery-key collection;
- MDM circumvention or unauthorized unenrollment;
- exploit delivery, unauthorized pairing, or security-control evasion;
- silent device modification, data extraction, or execution.

## Diagnostic boundary

Diagnostics are read-only. A USB connection, device name, model string, or user-provided reference is not proof of ownership, trust, Activation Lock state, passcode state, or MDM authorization.

Security-sensitive states that are not inspected by an approved trusted provider must be reported as NOT_INSPECTED. Missing or failed observations must be UNKNOWN, never PASS or CLEAR.

## Authorization boundary

Only a server-side provider may establish identity, ownership, consent, policy, and entitlement. The Flutter app is an untrusted presentation client. Any missing, stale, revoked, conflicting, or unverifiable prerequisite denies protected operations.

## Evidence and privacy

Use opaque references. Do not store or log serial numbers, UDIDs, passcodes, Apple Account credentials, recovery keys, or unnecessary personal data. Record source, observation time, correlation identifier, and integrity metadata for future trusted evidence. Do not fabricate timestamps or evidence.

## Current implementation status

Phase 1 is a loopback-only deny-only API. Phase 2 diagnostic reports are explicitly UNKNOWN until a trusted read-only adapter is implemented and reviewed. No device operation is executed.
