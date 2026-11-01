# Phase 23 — Read-only Audit Inspection API

## Purpose

Expose the Phase 22 inspection report through the existing local development
HTTP API. The endpoint is read-only and never accepts a database path from the
HTTP caller.

## Configuration

Set `DECISION_API_AUDIT_DATABASE` in the local server environment to the path
of an existing SQLite audit database. If it is unset or blank, the endpoint
returns HTTP 503 with status UNKNOWN and a non-sensitive reason code. A missing
or invalid configured database is handled by the Phase 22 inspector and remains
UNKNOWN; the endpoint does not create or initialize a database.

## Endpoint

`GET /v1/audit/inspection`

The response is the Phase 22 non-sensitive report: status, event/checkpoint
counts, latest checkpoint digest, reason, external anchor status, and storage
trust. Event payloads, actor/device references, credentials, database paths,
and raw identifiers are not returned. The endpoint does not accept query
parameters or caller-supplied paths.

## Safety boundary

- Inherits the API server's loopback-only bind requirement.
- Uses the Phase 22 SQLite `mode=ro` inspector.
- Does not initialize, write, repair, delete, or export event records.
- Does not invoke IPC, host diagnostics, device operations, or network services.
- External anchor remains UNKNOWN and storage trust remains
  UNVERIFIED_LOCAL_DATABASE.
- No authentication, public hosting, CORS expansion, or production readiness
  is implied by this local development endpoint.
- A PASS means local consistency only, not authenticity or tamper-proof storage.

## Validation

Focused HTTP tests cover unconfigured inspection, a consistent database,
redaction of event identifiers, byte stability, and a missing database. GitHub
Actions is the authoritative CI evidence; no local test run is claimed.
