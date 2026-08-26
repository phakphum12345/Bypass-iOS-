# Threat Model

## Threat Categories
- Credential compromise
- Token replay
- Request tampering
- Authorization confusion
- Entitlement abuse
- Device identity spoofing
- Privilege escalation
- API abuse
- Audit manipulation
- Insider misuse

## Security Requirements
- Server-side authorization
- Short-lived credentials
- Replay protection
- Request integrity
- Rate limiting
- Least privilege
- Immutable audit evidence
- Separation of duties
- Anomaly detection
- Data minimization

## Trust Boundary

USER
↓
CLIENT
↓
API GATEWAY
↓
AUTHORIZED SERVICES
↓
DEVICE / REGISTRY
↓
AUDIT / EVIDENCE

## Defensive Principle
Security controls MUST fail closed when required evidence is unavailable.

## Research Boundary
This document is defensive threat modeling only and does not provide
exploit implementation or security-control evasion procedures.
