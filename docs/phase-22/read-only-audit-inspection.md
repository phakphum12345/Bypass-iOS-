# Phase 22 — Read-only Audit Database Inspection

## Purpose

Provide a local inspection entry point for the durable event ledger and
checkpoint history. It opens an existing SQLite database in read-only mode,
loads both evidence collections, and runs the Phase 21 consistency verifier.

## Usage

From the repository root:

```sh
python -m backend.audit_inspection_cli --database /path/to/audit.sqlite3
```

Use `--allow-stale-checkpoint` only when intentionally checking historical
checkpoint prefixes without requiring the latest checkpoint to cover the
current event-ledger head.

## Output and exit codes

The CLI emits one JSON summary containing status, evidence counts, the latest
checkpoint digest, a reason code, external anchor status, and storage trust.

- Exit 0: PASS — local ledger and checkpoint history are internally consistent.
- Exit 1: FAIL — conflicting or invalid local evidence was detected.
- Exit 2: UNKNOWN — evidence is missing, unreadable, or does not cover the
  current ledger head.

The report does not print event payloads, actor/device references, credentials,
or raw identifiers.

## Safety and trust boundary

- Opens only an existing database using SQLite `mode=ro`.
- Does not initialize tables, write, repair, delete, or mutate audit records.
- Does not invoke IPC, host diagnostics, network services, or device operations.
- External anchor status remains UNKNOWN.
- Storage trust remains UNVERIFIED_LOCAL_DATABASE: read-only access does not
  authenticate the file or protect it from replacement by a privileged actor.
- A PASS is a consistency result, not proof of trusted time, authorship,
  tamper-proof storage, authorization, or production readiness.

## Validation

Focused tests cover a consistent database, missing database, malformed schema,
read-only byte stability, JSON output, and CLI exit status. GitHub Actions is
the authoritative CI evidence; no local test run is claimed.
