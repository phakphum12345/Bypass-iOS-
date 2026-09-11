# Bypass-iOS- — Defensive Architecture Reference

## Purpose

This repository defines a defensive device-service architecture.

The client is an external tool and is not a security authority.

## Security Rule

All security-sensitive decisions are server authoritative.

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

Authorization == ALLOWED
AND
Entitlement == ACTIVE
→ permitted workflow execution

Otherwise
→ DENY

## Prohibited Operations

- Activation Lock bypass
- Passcode bypass
- MDM circumvention
- Credential theft
- Exploit delivery
- Unauthorized device access
- Security-control evasion

## Client Boundary

Flutter may display device information, capabilities, policy state,
authorization state, entitlement state, decisions, evidence and audit data.

Flutter must not manufacture authorization, manufacture entitlement,
override policy, override server decisions, or perform unauthorized
device operations.

## Final Gate

All implementation changes must pass architecture, security-boundary,
API contract, code, Flutter, test, build, evidence and Final Gate
validation.

The main branch is updated only through the approved branch and PR workflow.
