# Permission Matrix

Legend: **Allow** means the role may request the workflow within its scope, not that an external platform will necessarily permit it. **No** means the role cannot perform that function. **Pending** means the trusted provider is not implemented and the runtime result must remain UNKNOWN/DENY.

| Capability | Project Owner | Device Owner | Organization Admin | Technician |
|---|---|---|---|---|
| Repository settings and source code | Allow | No | No | No |
| Approve and merge project PRs | Allow | No | No | No |
| Configure project backend | Allow | No | No | No |
| Register a device reference | Administer registry | Request own device | Within verified org scope | No |
| Read-only diagnostics | Request | Consent/request | Within verified org scope | Assigned cases |
| View device evidence | Project scope | Own device | Organization scope | Assigned cases |
| Grant device-owner consent | No, unless also verified owner | Allow | No, unless delegated | No |
| Set organization policy | No, unless also org admin | No | Allow within scope | No |
| Approve recovery workflow | No, unless separately authorized | Allow for own device | Allow within delegated scope | No |
| Execute supported recovery | Only with independent authorization | Only through supported flow | Only within delegated scope | Only assigned and approved |
| Override Activation Lock / passcode / MDM | No | No | No | No |
| Change own role or elevate privileges | No self-elevation | No | No self-elevation | No |

## Enforcement rules

1. Role checks are server-side and deny by default.
2. Scope checks bind every request to a verified user, device, and organization.
3. Consent is action-specific, time-bounded, and revocable.
4. High-impact actions require separation of requester and approver where feasible.
5. Unknown, missing, expired, revoked, or conflicting evidence produces UNKNOWN/DENY.
6. The client cannot submit or override role, ownership, authorization, or entitlement claims.
7. Project Owner authority over GitHub does not confer authority over device security or Apple services.

## Current status

This is a target policy matrix, not an implemented authorization provider. Until identity, ownership, organization, and consent providers exist, no protected action is authorized.
