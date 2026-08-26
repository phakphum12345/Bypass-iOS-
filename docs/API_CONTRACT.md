# API Contract

## Purpose
Defensive API contract for authorized device-service workflows.

## Endpoint
POST /v1/device/eligibility

## Request
{
  "device_id": "device-identifier",
  "service_id": "service-identifier",
  "actor_id": "authenticated-actor"
}

## Response
{
  "decision": "ELIGIBLE",
  "authorization": "AUTHORIZED",
  "entitlement": "ACTIVE",
  "policy_version": "policy-version",
  "correlation_id": "correlation-id"
}

## Decision Values
- ELIGIBLE
- INELIGIBLE
- UNSUPPORTED
- REQUIRES_AUTHORIZATION
- REQUIRES_OWNER_ACTION
- REQUIRES_SUPPORT

## Security Requirements
- Authentication MUST be established before the request.
- Authorization MUST be evaluated server-side.
- Client input MUST NOT override policy or entitlement.
- Failed authorization decisions MUST be auditable.

## Research Boundary
This contract does not define security-control circumvention.
