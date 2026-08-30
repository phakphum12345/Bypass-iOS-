# Decision Pipeline

## Pipeline

1. Device identity
2. Capability detection
3. Policy evaluation
4. Authorization
5. Entitlement
6. Evidence generation
7. Execution eligibility

## Eligibility

A device is eligible only when all required policy conditions are satisfied.

## Denial

Authorization failure, unavailable service, unsupported capabilities, or
other policy failures must not be converted into an eligible state.

## Principle

The UI displays decisions. It does not create authorization.
