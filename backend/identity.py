"""Fail-closed identity-provider contract for Phase 3.

This module does not authenticate users by itself. A future trusted server-side
adapter must validate bearer sessions and return verified, time-bounded evidence.
No client-supplied identity, role, ownership, or organization claims are trusted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class IdentityEvidence:
    """Provider result; identifiers must be opaque references, never credentials."""

    status: str
    issuer: str | None = None
    subject_ref: str | None = None
    session_ref: str | None = None
    issued_at: datetime | None = None
    expires_at: datetime | None = None
    auth_time: datetime | None = None
    assurance: str | None = None
    source: str | None = None


class IdentityProvider(Protocol):
    """Trusted server-side adapter contract. Never implemented by the client."""

    def resolve_bearer_session(
        self, bearer_token: str, *, now: datetime
    ) -> IdentityEvidence:
        """Validate token signature, issuer, audience, session and revocation."""


class UnavailableIdentityProvider:
    """Default provider: explicitly unavailable, so no identity is established."""

    def resolve_bearer_session(
        self, bearer_token: str, *, now: datetime
    ) -> IdentityEvidence:
        del bearer_token, now
        return IdentityEvidence(
            status="UNKNOWN",
            source="no_trusted_identity_provider",
        )


def _unknown(reason: str) -> IdentityEvidence:
    return IdentityEvidence(status="UNKNOWN", source=reason)


def resolve_identity(
    provider: IdentityProvider | None,
    authorization_header: str | None,
    *,
    now: datetime | None = None,
) -> IdentityEvidence:
    """Resolve a bearer session without accepting caller-supplied identity claims.

    Provider errors, malformed headers, missing providers, and incomplete or
    stale evidence all fail closed. The bearer token is never copied to output.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        return _unknown("invalid_evaluation_time")

    if not isinstance(authorization_header, str):
        return _unknown("missing_bearer_token")

    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        return _unknown("invalid_authorization_header")

    if provider is None:
        return _unknown("no_trusted_identity_provider")

    try:
        evidence = provider.resolve_bearer_session(parts[1], now=current)
    except Exception:
        return _unknown("identity_provider_error")

    if not isinstance(evidence, IdentityEvidence):
        return _unknown("invalid_identity_provider_response")

    if evidence.status in {"REVOKED", "EXPIRED"}:
        return IdentityEvidence(status=evidence.status, source=evidence.source)

    if evidence.status != "VERIFIED":
        return _unknown(evidence.source or "identity_not_verified")

    required_refs = (evidence.issuer, evidence.subject_ref, evidence.session_ref)
    if any(not isinstance(value, str) or not value.strip() for value in required_refs):
        return _unknown("incomplete_identity_evidence")

    times = (evidence.issued_at, evidence.expires_at, evidence.auth_time)
    if any(
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        for value in times
    ):
        return _unknown("incomplete_identity_timestamps")

    issued_at, expires_at, auth_time = times
    if issued_at > current or auth_time > current:
        return _unknown("identity_evidence_from_future")
    if expires_at <= current:
        return IdentityEvidence(status="EXPIRED", source=evidence.source)
    if expires_at <= issued_at or auth_time < issued_at:
        return _unknown("inconsistent_identity_timestamps")

    return evidence
