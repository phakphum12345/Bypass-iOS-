# Data Model

## Device
- device_id
- platform
- model
- hardware_class
- os_version
- firmware_version
- capabilities
- status

## Actor
- actor_id
- authentication_state
- roles
- permissions

## Policy
- policy_id
- policy_version
- rules
- effective_from
- effective_until

## Entitlement
- entitlement_id
- actor_id
- device_id
- service_id
- status
- issued_at
- expires_at

## Evidence
- event_id
- correlation_id
- actor_id
- device_id
- action
- decision
- timestamp
- result

## Data Protection
Protected identity and authorization data MUST be minimized and
protected in transit and at rest where applicable.
