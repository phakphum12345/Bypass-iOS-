# Decision Pipeline

## Canonical Pipeline

1. Device identity
2. Capability detection
3. Policy evaluation
4. Server-side authorization
5. Entitlement evaluation
6. Execution eligibility
7. Evidence generation

## Eligibility

A device is eligible only when all required policy, authorization, and
entitlement conditions are satisfied.

## Denial

Authorization failure, unavailable service, unsupported capabilities, or
other policy failures must not be converted into an eligible state.

## Principle

The UI displays decisions. It does not create authorization.
