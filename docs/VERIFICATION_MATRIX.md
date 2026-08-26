# Verification Matrix

| Control | Test | Expected Result |
|---|---|---|
| Authentication | Invalid credential | DENY |
| Authorization | Missing permission | DENY |
| Eligibility | Unsupported device | UNSUPPORTED |
| Entitlement | Missing entitlement | DENY |
| Replay Protection | Replayed request | DENY |
| Policy | Expired policy | DENY |
| Audit | Successful operation | Evidence created |
| Audit | Failed operation | Evidence created |
| Input Validation | Malformed request | DENY |
| Least Privilege | Excess permission | DENY |

## Acceptance Gate
Architecture changes are ready for review when all required
verification checks pass.
