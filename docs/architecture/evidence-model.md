# Evidence Model

Evidence records are immutable after creation.

## Required Fields

- event_id
- actor
- device_id
- service_id
- action
- policy_id
- policy_version
- policy_decision
- authorization_result
- timestamp
- correlation_id
- result

## Rules

Evidence must identify the actor and target device.

Evidence must identify the policy version and authorization result.

Evidence must be correlated with the originating request.

Client-generated information must not be treated as authoritative security
evidence unless validated by the server.

## Audit Reconstruction

Audit data must support reconstruction of:

request
→ decision
→ workflow
→ result
