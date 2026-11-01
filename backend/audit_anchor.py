"""Phase 18 audit checkpoint and external-anchor verification contract.

This module creates deterministic checkpoints from a verified local ledger
and validates evidence returned by a separately trusted anchor provider.
It does not contact a remote service or provide cryptographic signature
verification itself. The default provider is unavailable and resolves UNKNOWN.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Protocol

from backend.audit_evidence import AuditLedger, verify_ledger

GENESIS_HASH = "0" * 64
_REFERENCE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_HASH = re.compile(r"^[a-f0-9]{64}$")


@dataclass(frozen=True, slots=True)
class AuditCheckpoint:
    schema_version: int
    event_count: int
    head_hash: str
    created_at: str
    checkpoint_hash: str


@dataclass(frozen=True, slots=True)
class AnchorEvidence:
    """Provider-validated evidence; refs must be opaque and non-secret."""

    status: str
    provider_ref: str
    anchor_ref: str
    checkpoint_hash: str
    verified_at: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class AnchorVerification:
    status: str
    provider_ref: str | None = None
    anchor_ref: str | None = None
    checkpoint_hash: str | None = None
    verified_at: str | None = None
    reason: str = "anchor_unavailable"


class AuditAnchorProvider(Protocol):
    def verify_checkpoint(
        self, checkpoint: AuditCheckpoint, *, now: datetime
    ) -> AnchorEvidence:
        """Verify a checkpoint against an independent, trusted anchor."""


class UnavailableAuditAnchorProvider:
    """Safe default until a real independently trusted provider is configured."""

    def verify_checkpoint(
        self, checkpoint: AuditCheckpoint, *, now: datetime
    ) -> AnchorEvidence:
        raise RuntimeError("audit_anchor_provider_unavailable")


def _utc(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timezone_aware_datetime_required")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _parse_utc(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timezone_aware_timestamp_required")
    return parsed.astimezone(timezone.utc)


def _canonical(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def create_audit_checkpoint(
    ledger: AuditLedger, *, created_at: datetime
) -> AuditCheckpoint:
    """Create a stable checkpoint binding event count and current chain head."""
    if not verify_ledger(ledger):
        raise ValueError("audit_ledger_integrity_failed")
    timestamp = _utc(created_at)
    payload = {
        "schema_version": 1,
        "event_count": len(ledger.events),
        "head_hash": ledger.events[-1].event_hash if ledger.events else GENESIS_HASH,
        "created_at": timestamp,
    }
    digest = hashlib.sha256(_canonical(payload)).hexdigest()
    return AuditCheckpoint(**payload, checkpoint_hash=digest)


def verify_anchor_evidence(
    checkpoint: AuditCheckpoint,
    evidence: AnchorEvidence,
    *,
    now: datetime,
) -> AnchorVerification:
    """Validate provider-returned evidence against the exact checkpoint.

    Cryptographic signature and trust-root verification are the responsibility
    of the configured provider adapter. This function validates its normalized
    result, matching hash, opaque references, and validity window.
    """
    try:
        current = _parse_utc(_utc(now))
        if not isinstance(checkpoint, AuditCheckpoint) or not isinstance(evidence, AnchorEvidence):
            raise ValueError("malformed_anchor_evidence")
        if checkpoint.schema_version != 1 or checkpoint.event_count < 0:
            raise ValueError("invalid_checkpoint")
        if not _HASH.fullmatch(checkpoint.head_hash):
            raise ValueError("invalid_checkpoint_head")
        if not _HASH.fullmatch(checkpoint.checkpoint_hash):
            raise ValueError("invalid_checkpoint_hash")
        checkpoint_payload = {
            "schema_version": checkpoint.schema_version,
            "event_count": checkpoint.event_count,
            "head_hash": checkpoint.head_hash,
            "created_at": checkpoint.created_at,
        }
        if hashlib.sha256(_canonical(checkpoint_payload)).hexdigest() != checkpoint.checkpoint_hash:
            raise ValueError("checkpoint_digest_mismatch")
        if evidence.status != "VERIFIED":
            raise ValueError("anchor_not_verified")
        if not _REFERENCE.fullmatch(evidence.provider_ref):
            raise ValueError("invalid_provider_ref")
        if not _REFERENCE.fullmatch(evidence.anchor_ref):
            raise ValueError("invalid_anchor_ref")
        if evidence.checkpoint_hash != checkpoint.checkpoint_hash:
            raise ValueError("anchor_checkpoint_mismatch")
        verified_at = _parse_utc(evidence.verified_at)
        expires_at = _parse_utc(evidence.expires_at)
        if verified_at > current or expires_at <= current or expires_at <= verified_at:
            raise ValueError("anchor_evidence_outside_validity_window")
        if verified_at < _parse_utc(checkpoint.created_at):
            raise ValueError("anchor_predates_checkpoint")
        return AnchorVerification(
            status="VERIFIED",
            provider_ref=evidence.provider_ref,
            anchor_ref=evidence.anchor_ref,
            checkpoint_hash=evidence.checkpoint_hash,
            verified_at=evidence.verified_at,
            reason="verified",
        )
    except (AttributeError, TypeError, ValueError):
        return AnchorVerification(status="UNKNOWN", reason="anchor_evidence_invalid")


def resolve_audit_anchor(
    checkpoint: AuditCheckpoint,
    *,
    provider: AuditAnchorProvider | None,
    now: datetime,
) -> AnchorVerification:
    """Resolve external anchor status; absent, failing, or malformed is UNKNOWN."""
    if provider is None:
        provider = UnavailableAuditAnchorProvider()
    try:
        evidence = provider.verify_checkpoint(checkpoint, now=now)
    except Exception:
        return AnchorVerification(status="UNKNOWN", reason="anchor_provider_unavailable")
    return verify_anchor_evidence(checkpoint, evidence, now=now)
