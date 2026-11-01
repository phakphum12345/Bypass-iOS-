# Phase 21 — Independent Audit Consistency Verification

## Purpose

Provide a reusable verifier that checks a verified event hash-chain against
the exact ledger prefixes represented by the stored checkpoint history. This
separates verification/reporting from the Phase 20 dispatch orchestration.

## Implemented

- Verify the event ledger with the existing hash-chain verifier.
- Recompute every checkpoint digest from its canonical payload.
- Check each checkpoint's event count and head hash against the exact ledger
  prefix it claims to represent.
- Check checkpoint count and timestamp ordering.
- Optionally require the latest checkpoint to match the current ledger head.
- Return a structured PASS / FAIL / UNKNOWN report with counts, latest hash,
  and a non-sensitive reason code.
- Keep the pre-append migration state explicit: no prior checkpoints can be
  accepted only when current-head coverage is not required.

## Result semantics

- PASS: supplied local records are internally consistent for the requested
  verification mode.
- FAIL: malformed or conflicting local evidence was detected.
- UNKNOWN: evidence is missing or the latest checkpoint does not cover the
  current ledger head.

A PASS does not authenticate the database, prove who created the records,
establish trusted time, or imply an independent/external anchor.

## Trust and safety boundary

The verifier is a pure in-process consistency check over caller-supplied
objects. It does not open files, access a network, invoke an anchor provider,
or grant authorization. It performs no device inspection or device operation.
The external anchor remains UNKNOWN unless a separately trusted provider is
configured and independently validates signatures and trust roots.

## Not implemented / SKIPPED

- External timestamping, signature verification, HSM/KMS, remote replication,
  independent administrative trust domain, or tamper-proof storage.
- HTTP/IPC transport, Flutter integration, production identity, or deployment.
- Any device-management, unlock, restore, Activation Lock, or MDM operation.

## Validation

GitHub Actions build, analysis, tests, iOS simulator, and final gate are the
validation evidence for this PR. No local test run is claimed.
