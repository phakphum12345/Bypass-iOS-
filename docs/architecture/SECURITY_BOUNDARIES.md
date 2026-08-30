# Security Boundaries

## Server-Side Authorization

Authorization must remain outside the presentation layer.

## Client Boundary

The Flutter application may display authorization state but must not
manufacture an authorization result.

## Decision Boundary

Denied authorization remains denied.

Entitlement cannot exceed authorization.

Execution eligibility depends on the authoritative decision.

## Research Boundary

This project is a defensive architecture reference.

It does not provide mechanisms for bypassing operating-system security,
entitlements, signing, access controls, or platform protections.

## Evidence Boundary

Evidence records must describe what was evaluated and what decision was
returned without claiming capabilities that were not actually verified.
