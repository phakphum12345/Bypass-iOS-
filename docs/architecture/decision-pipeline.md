# Decision Pipeline

## Canonical Pipeline

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
Execution
  ↓
Evidence

## Execution Rule

Authorization == ALLOWED
AND
Entitlement == ACTIVE

→ permitted workflow execution

Otherwise:

→ DENY

## Client Rule

The client sends inputs and displays authoritative results.

The client must never calculate a local result and present it as the
authoritative security decision.

## Evidence

Every security-sensitive decision must be correlated with the originating
request and recorded with the applicable policy version.
