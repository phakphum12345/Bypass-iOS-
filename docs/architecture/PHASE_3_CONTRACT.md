# Bypass-iOS — Phase 3 Architecture Contract

## Purpose

Phase 3 establishes the defensive architecture contract separating:

- Device identity
- Capability detection
- Policy evaluation
- Authorization
- Entitlement
- Evidence
- Execution eligibility
- Security boundaries

## Core Rule

The client UI is not an authorization authority.

Authorization and entitlement decisions must be evaluated through the
defined service boundaries.

## Decision Flow

Device
→ Identity
→ Capability
→ Policy
→ Authorization
→ Entitlement
→ Evidence
→ Execution Eligibility

## Security Boundary

The reference implementation does not bypass platform security controls.

Denied decisions must remain denied.

## Evidence

Architecture decisions must produce traceable evidence suitable for
audit and later validation.

## Phase Status

Implementation written.

Validation is intentionally deferred until FINAL GATE.
