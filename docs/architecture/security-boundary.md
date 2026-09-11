# Security Boundary

## Authority

The server is the authoritative security boundary.

The client cannot override:

- Identity
- Policy
- Authorization
- Entitlement
- Security decisions

## Trust Boundary

UNTRUSTED CLIENT
      ↓ request
SERVER SECURITY BOUNDARY
      ↓
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
Permitted Workflow

## Deny by Default

Unknown, missing, expired, revoked, conflicting, or invalid security state
must resolve to DENY.

## Resource Conflict

A rejected update must not overwrite another valid state in the same version.

The affected operation must stop, resources must be released according to
policy, and delivery must be reconciled according to workflow policy.
