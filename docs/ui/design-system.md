# Design System

## Visual Direction

The desktop client uses:

- dark interface
- glassmorphism surfaces
- purple-to-blue visual accents
- clear security-state indicators
- strong information hierarchy
- responsive cards

## Dashboard

Primary sections:

- Device Status
- Security Gates
- Decision
- Evidence
- Audit

## Interaction

Primary action:

Evaluate Decision

Secondary action:

View Evidence

There is no client-side bypass action.

## Security States

- UNKNOWN
- PENDING
- ALLOWED
- DENIED
- EXPIRED
- REVOKED

The UI must never visually imply permission when the authoritative state is
unknown.
