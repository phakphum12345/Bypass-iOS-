# Decision API and Device Diagnostics (Phases 1–2)

This is a development-only, loopback-bound API scaffold. It is deliberately
**deny-only**: no identity, capability, policy, authorization, entitlement,
ownership, or execution provider is implemented. A valid request returns
`decision=DENY`, `authorization=DENY`, and `entitlement=UNKNOWN`. The server
does not perform or trigger device operations.

## Run

From the repository root:

```bash
python -m backend.decision_api.server
```

The server binds to loopback and selects an available port by default. Copy the
printed `DECISION_API_URL` into the Flutter build configuration:

```bash
cd flutter_app
flutter run -d chrome --dart-define=DECISION_API_BASE_URL=http://127.0.0.1:<printed-port>
```

Set `DECISION_API_PORT` to request a port, or `0` to let the OS select one.
The server rejects non-loopback bind addresses. For browser clients, set
`DECISION_API_ALLOWED_ORIGINS` to a comma-separated exact origin allowlist.
No wildcard CORS policy is enabled by default.

## Contract

- `GET /health`: reports service health and `deny_only` mode.
- `POST /v1/decisions`: accepts exactly the four request fields in
  `api/contracts/decision-request.json`.
- Client-supplied authorization or entitlement fields are rejected.
- `GET /v1/devices/{opaque-reference}/diagnostics`: returns a versioned, read-only diagnostic report. With no trusted platform adapter configured, all device and connection attributes remain `UNKNOWN`; passcode, Activation Lock, MDM, and device-trust states are `NOT_INSPECTED`.
- The diagnostics endpoint never establishes ownership, grants authorization, or performs a device operation.
- `GET /v1/execute` and other execution routes do not exist.

This scaffold is not production-ready and must not be exposed to the public
internet. A trusted read-only device adapter, production authorization provider, identity verification,
entitlement source, authentication, rate limiting, audit persistence, TLS,
deployment target, and threat-model review are separate required work.
Never send a device serial number, UDID, passcode, Apple Account credential,
or other secret as `device_id`; use a non-sensitive opaque reference.
