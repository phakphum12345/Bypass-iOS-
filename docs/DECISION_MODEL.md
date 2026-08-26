# Decision Model

## Canonical Flow

Identity
↓
Capability
↓
Policy
↓
Authorization
↓
Entitlement
↓
Decision
↓
Execution
↓
Evidence

## Decision Properties
Every decision MUST be deterministic, auditable, attributable,
policy-versioned, and correlation-traceable.

## Rules

- Invalid identity → REQUIRES_SUPPORT
- Unsupported capability → UNSUPPORTED
- Policy denial → INELIGIBLE
- Missing authorization → REQUIRES_AUTHORIZATION
- Missing entitlement → REQUIRES_OWNER_ACTION
- All conditions satisfied → ELIGIBLE

## Security Boundary
A client MUST NOT transform a denied decision into an allowed decision.
Final authorization remains server-side.
