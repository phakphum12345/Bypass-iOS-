# Bypass-iOS — Phase 3 Architecture Contract

## Purpose

Phase 3 establishes explicit architectural boundaries for the defensive
device-service reference implementation.

This project does not implement platform-security bypass behavior.

## Canonical Pipeline

Device
→ Identity
→ Capability
→ Policy
→ Server Authorization
→ Entitlement
→ Execution Eligibility
→ Evidence

## Policy

Policy determines whether authorization is required.

The baseline policy is deny-by-default.

Client-side authorization override is prohibited.

## Authorization

Authorization is an independent server-side domain concept.

Supported states include:

- unknown
- pending
- authorized
- denied
- expired

Only an authorized state may satisfy the authorization boundary.

## Entitlement

Entitlement is derived from authorization.

Unauthorized subjects cannot receive an active entitlement.

## Evidence

Evidence records decision stages for auditability and traceability.

Relevant stages include:

- identity
- capability
- policy
- authorization
- entitlement
- execution

## Security Boundary

A denied authorization result cannot be converted into an authorized
result by the client.

The UI is not an authorization authority.

## Research Boundary

This implementation is defensive and architectural.

It does not bypass:

- platform security
- authentication
- authorization
- licensing
- entitlement controls

## Validation

Implementation validation is intentionally deferred until FINAL GATE.
