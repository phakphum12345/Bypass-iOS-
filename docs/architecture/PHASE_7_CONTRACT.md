# Bypass-iOS — Phase 7 UI Contract

## Purpose

Phase 7 defines the boundary between Flutter UI and the core decision
architecture.

## UI Responsibilities

The UI may:

- display device state
- display capabilities
- display policy state
- display authorization state
- display entitlement state
- display evidence
- display execution eligibility

## UI Restrictions

The UI must not:

- manufacture authorization
- override denied decisions
- manufacture entitlement
- act as the server authorization authority

## Validation

Validation is performed during FINAL GATE.
