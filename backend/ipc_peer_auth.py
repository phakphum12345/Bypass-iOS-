"""Fail-closed contract for authenticating local IPC peers.

This module defines a provider boundary only. It does not inspect OS handles,
validate operating-system credentials, open transports, or establish trust.
The default provider is unavailable, so peer identity remains UNKNOWN.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


SUPPORTED_TRANSPORTS = {"windows_named_pipe", "unix_domain_socket", "macos_xpc"}


@dataclass(frozen=True)
class PeerEvidence:
    """Trusted verifier output; references are opaque and never credentials."""

    status: str
    transport: str | None = None
    principal_ref: str | None = None
    audience: str | None = None
    channel_binding_ref: str | None = None
    authenticated_at: datetime | None = None
    expires_at: datetime | None = None
    source: str | None = None


class PeerAuthenticator(Protocol):
    """Server-side OS adapter; input must be a server-owned connection handle."""

    def verify_peer(
        self, connection_context: object, *, audience: str, now: datetime
    ) -> PeerEvidence:
        """Verify OS peer credentials and bind evidence to this channel."""


class UnavailablePeerAuthenticator:
    """Default implementation: no platform peer authentication is configured."""

    def verify_peer(
        self, connection_context: object, *, audience: str, now: datetime
    ) -> PeerEvidence:
        del connection_context, audience, now
        return PeerEvidence(status="UNKNOWN", source="no_peer_authenticator")


def _unknown(reason: str) -> PeerEvidence:
    return PeerEvidence(status="UNKNOWN", source=reason)


def resolve_peer(
    authenticator: PeerAuthenticator | None,
    connection_context: object,
    *,
    audience: str,
    now: datetime | None = None,
) -> PeerEvidence:
    """Resolve independently verified peer evidence; fail closed on all errors.

    Never pass request-envelope fields as connection_context. It must be an
    opaque server-owned handle supplied by a future authenticated transport.
    """
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        return _unknown("invalid_evaluation_time")
    if not isinstance(audience, str) or not audience.strip():
        return _unknown("invalid_expected_audience")
    if connection_context is None:
        return _unknown("missing_connection_context")
    if authenticator is None:
        return _unknown("no_peer_authenticator")

    try:
        evidence = authenticator.verify_peer(
            connection_context, audience=audience, now=current
        )
    except Exception:
        return _unknown("peer_authenticator_error")

    if not isinstance(evidence, PeerEvidence):
        return _unknown("invalid_peer_authenticator_response")
    if evidence.status in {"REVOKED", "EXPIRED"}:
        return PeerEvidence(status=evidence.status, source=evidence.source)
    if evidence.status != "VERIFIED":
        return _unknown(evidence.source or "peer_not_verified")

    if evidence.transport not in SUPPORTED_TRANSPORTS:
        return _unknown("unsupported_peer_transport")
    refs = (evidence.principal_ref, evidence.channel_binding_ref)
    if any(not isinstance(value, str) or not value.strip() for value in refs):
        return _unknown("incomplete_peer_references")
    if evidence.audience != audience:
        return _unknown("peer_audience_mismatch")

    authenticated_at, expires_at = evidence.authenticated_at, evidence.expires_at
    if any(
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
        for value in (authenticated_at, expires_at)
    ):
        return _unknown("incomplete_peer_timestamps")
    if authenticated_at > current:
        return _unknown("peer_evidence_from_future")
    if expires_at <= current:
        return PeerEvidence(status="EXPIRED", source=evidence.source)
    if expires_at <= authenticated_at:
        return _unknown("inconsistent_peer_timestamps")

    return evidence
