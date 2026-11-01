# Phase 17 — Durable audit dispatch integration

## Purpose

Connect the Phase 15 audited Local IPC dispatcher to the Phase 16 file-backed
SQLite audit store. The integration makes the durable ledger the source of
truth for each dispatch instead of asking each caller to manually carry an
in-memory ledger between requests.

## Flow

1. The caller initializes the SQLite schema before using this integration.
2. The dispatcher loads and verifies the persisted ledger.
3. If loading fails, it does not authenticate or dispatch the request and
   returns `AUDIT_UNAVAILABLE`.
4. It dispatches through the existing fail-closed Local IPC path and maps the
   outcome to a metadata-only audit event.
5. It appends and verifies the updated ledger transactionally.
6. Only after persistence succeeds does the response include
   `audit_recorded: true`. If persistence fails, the response is
   `AUDIT_PERSISTENCE_FAILED`, the read result is suppressed, and
   `audit_recorded` is false.

## Security and failure boundaries

- The only supported IPC methods remain `host.health.read` and
  `host.diagnostics.read`.
- Unknown, denied, invalid, and provider-error outcomes are also audited.
- Audit records contain metadata only; request bodies, diagnostics payloads,
  credentials, serials, UDIDs, and raw device identifiers are not persisted.
- Peer verification remains distinct from device-operation authorization.
  Responses always keep `authorization_granted=false` and
  `device_operation_performed=false`.
- The store must be initialized explicitly by its owner. This function does
  not create directories, initialize schema, select a storage path, or manage
  database lifecycle.
- A failure to load the ledger prevents dispatch. A failure to append cannot
  roll back a read-only provider call that has already happened; instead the
  response suppresses its result and explicitly reports audit persistence
  failure. No durable audit success is claimed.
- SQLite triggers and hash-chain verification do not prevent a privileged
  actor from replacing or rewriting the database. There is still no
  independent chain-head anchor, encryption-at-rest, authenticated store
  access, tenant isolation, remote replication, native IPC transport,
  service installation, or production deployment.

## Validation

The test suite covers successful persistence and reload, sequential ledger
extension, durable denied and invalid outcomes, fail-closed behavior when
loading fails, and result suppression when append fails.
