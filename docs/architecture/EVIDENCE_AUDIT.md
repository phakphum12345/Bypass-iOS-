# Evidence and Audit Contract

## Objective

Every important architecture decision should be explainable from evidence.

## Evidence Categories

- Device identity
- Platform
- Model
- OS version
- Firmware version
- Capabilities
- Authorization state
- Service state
- Policy result
- Entitlement result
- Final decision

## Audit Principle

Evidence is descriptive.

Evidence must not be used to fabricate authorization or entitlement.

## Security

Evidence cannot grant authorization.

Evidence cannot convert a denied state into an allowed state.

## Validation

Automated validation is performed during the final project gate.
