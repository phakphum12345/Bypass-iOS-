# Phase 2 — Device Intelligence

## Objective

Introduce a conservative, read-only diagnostic report contract and API endpoint. Phase 2 does not prove ownership, authorize recovery, or inspect protected Apple security states.

## Initial scope

- Accept only a non-sensitive opaque device reference.
- Return a versioned report with provenance-aware statuses.
- Use UNKNOWN when no trusted platform adapter is configured or an observation cannot be obtained.
- Use NOT_INSPECTED for passcode, Activation Lock, MDM enrollment, and device trust.
- Explicitly state that no device operation was performed.
- Keep the existing local API loopback-only and deny-only.

## Status vocabulary

- DETECTED / NOT_DETECTED: only for a specific supported observation from a trusted adapter.
- UNKNOWN: observation unavailable, failed, stale, or unsupported.
- NOT_INSPECTED: deliberately outside this phase's inspection scope.

These states are not authorization decisions.

## Adapter requirements for future work

A future adapter must be read-only, documented, platform-supported, independently tested, and explicit about data provenance and observation time. It must not pair silently, change services, install drivers, enter recovery/DFU, restore, unlock, or write device data.

## Acceptance criteria

- Valid opaque references return a schema-valid UNKNOWN report when no adapter exists.
- Invalid references are rejected.
- Security-sensitive states remain NOT_INSPECTED.
- Reports say operation_performed=false and authorization_granted=false.
- Tests verify no serial/UDID/credential collection and no unsupported security-state inference.
- CI includes all backend tests.
