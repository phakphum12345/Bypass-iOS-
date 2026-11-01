# Phase 5 — Authorized Recovery Workflows

## Scope

Phase 5 provides structured, informational recovery plans for common iPhone/iPad support scenarios. Plans point users to official Apple support or the verified organization's administrator. They do not connect to devices, inspect device state, execute commands, alter settings, or grant authorization.

## Supported guidance scenarios

- Forgotten screen passcode: Apple-supported recovery-mode guidance, explicit local-data-loss warning, and backup reminder.
- iPhone/iPad unavailable: stop guessing passcodes; use Apple's supported reset or recovery instructions.
- Activation Lock: stop and direct the owner to the previously linked Apple Account, Apple's account recovery, the previous owner, or Apple Support with proof of purchase. No bypass or removal workflow exists.
- Organization-managed / Remote Management: contact the verified organization's administrator for any authorized release through its official management service. No MDM removal or evasion exists.
- Unknown issue: record the exact on-screen message and consult Apple Support.

## Safety invariants

- All plans are guidance-only. authorization_granted and operation_performed are always false.
- The planner accepts a scenario category only; it does not accept client-supplied identity, ownership, consent, policy, entitlement, device identifiers, credentials, or security-state claims.
- Restore paths explicitly warn that local data is erased. Backup availability is never inferred.
- Activation Lock and organization management are security stops, not executable recovery actions.
- A repository role, device possession, USB connection, or an opaque device reference is not proof of device ownership.
- Never request or log passcodes, Apple Account passwords, verification codes, recovery keys, serial numbers, or UDIDs.

## Implementation

backend.recovery_workflow.build_recovery_plan is a pure planner with fixed official support URLs. It is not exposed as an HTTP route and is not connected to a device execution layer. The Flutter Official Recovery Assistant remains informational; CI tests cover its existing user-facing safety warnings, while backend tests cover structured plan invariants.

## Remaining work

Human-reviewed confirmation UX, trusted ownership/consent/policy/entitlement providers, append-only audit, verified device/organization adapters, Apple-supported operational integrations, and security review remain separate gates. No sensitive operation is enabled by this phase.
