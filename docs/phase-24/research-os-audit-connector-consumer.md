# Phase 24 — Research OS Audit Connector (Consumer)

## Purpose

Add a dedicated connection page to the Bypass-iOS- Flutter application. The
application is an API consumer; Research OS remains a separate repository and
the intended API provider.

## UI

The Research OS Connector page provides:

- Research OS HTTPS API base URL input.
- Optional bearer credential input, held in screen memory only.
- A connection test that calls the audit inspection resource.
- PASS / FAIL / UNKNOWN result display and redacted summary fields.
- Last-checked timestamp and Disconnect action.

Disconnect clears the URL, credential, report, error, and timestamp from the
page state. No credential is persisted, logged, or placed in a URL.

## API contract expected from the provider

- Method: GET
- Path: /v1/audit/inspection
- Accept: application/json
- Optional authorization header: Authorization: Bearer <scoped-read-only-credential>
- Response status: HTTP 200 for an inspection report; HTTP 503 may return an
  UNKNOWN report when inspection is unavailable or not configured.
- Report fields: status (PASS / FAIL / UNKNOWN), reason,
  ledger_event_count, checkpoint_count, verified_checkpoint_count,
  latest_checkpoint_hash, external_anchor_status, and storage_trust.

Counts may be absent in an unavailable UNKNOWN response and are displayed as
zero only as a presentation fallback; the overall status remains UNKNOWN.

## Transport and security

- HTTPS is required for remote hosts.
- Plain HTTP is permitted only for localhost / loopback development.
- URL user information, query strings, and fragments are rejected.
- Credentials are sent only in the Authorization header and remain in memory
  for the lifetime of the page.
- The client performs GET only and has no write, repair, delete, device, unlock,
  activation, or bypass capability.
- PASS reflects the provider's reported local consistency result only.
  external_anchor_status=UNKNOWN and
  storage_trust=UNVERIFIED_LOCAL_DATABASE must not be presented as trusted.

## Integration status

This consumer implementation does not create or deploy the Research OS provider.
The Research OS endpoint, authentication contract, deployment URL, and real
cross-repository integration remain UNKNOWN until implemented and verified in
the separate Research OS repository. No live integration is claimed by this PR.

## Validation

GitHub Actions is the authoritative validation source for this repository.
The connector tests use an HTTP mock and do not claim that a live Research OS
service is available.
