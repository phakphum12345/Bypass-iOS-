# Bypass-iOS — Phase 6 Security Boundary Contract

## Purpose

Phase 6 formalizes the security boundary between client decisions and
server authorization.

## Rules

1. Client state cannot grant authorization.
2. Denied authorization remains denied.
3. Entitlement cannot exceed authorization.
4. Evidence cannot grant authorization.
5. UI state cannot override the security boundary.
6. Execution eligibility depends on the authoritative decision.

## Research Boundary

This project remains a defensive architecture reference.

No platform-security bypass behavior is implemented.

## Validation

Validation is performed during FINAL GATE.
