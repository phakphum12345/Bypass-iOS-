# API Contracts

The API is the authoritative security boundary.

The Flutter external tool sends requests and displays authoritative results.

The client must not manufacture authorization, entitlement, or execution
permission.

## Decision

A workflow may proceed only when:

Authorization == ALLOWED
AND
Entitlement == ACTIVE

Otherwise the authoritative result is DENY.

## Correlation

Every decision request and response must support correlation through a
correlation_id.

## Evidence

Authoritative evidence is produced or validated by the server.
