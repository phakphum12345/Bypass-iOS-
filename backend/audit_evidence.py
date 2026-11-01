"""Phase 6 immutable, in-memory audit evidence primitives.

This module is deliberately storage- and transport-free. It never receives
raw device identifiers or credentials, persists records, or triggers actions.
A future durable adapter must provide authenticated append-only storage.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Iterable

GENESIS_HASH = "0" * 64
_REFERENCE = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
_ALLOWED_DECISIONS = {"ALLOW", "DENY", "UNKNOWN"}
_ALLOWED_RESULTS = {"SUCCEEDED", "FAILED", "NOT_RUN", "UNKNOWN"}


class AuditValidationError(ValueError):
    """Raised when an audit event is malformed or violates the contract."""


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: str
    actor_ref: str
    device_ref: str
    service_id: str
    action: str
    decision: str
    result: str
    occurred_at: str
    correlation_ref: str
    previous_hash: str
    event_hash: str
    schema_version: int = 1


@dataclass(frozen=True, slots=True)
class AuditLedger:
    """An immutable sequence; append returns a new ledger, never mutates this one."""

    events: tuple[AuditEvent, ...] = ()


def _reference(name: str, value: str) -> str:
    if not isinstance(value, str) or not _REFERENCE.fullmatch(value):
        raise AuditValidationError(f"invalid_{name}")
    return value


def _timestamp(value: datetime) -> str:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise AuditValidationError("timestamp_must_be_timezone_aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds").replace(
        "+00:00", "Z"
    )


def _canonical(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _digest(payload: dict) -> str:
    return hashlib.sha256(_canonical(payload)).hexdigest()


def _event_payload(event: AuditEvent) -> dict:
    values = asdict(event)
    values.pop("event_hash")
    return values


def verify_ledger(ledger: AuditLedger) -> bool:
    """Verify sequence links, event hashes, schema, and event uniqueness."""
    if not isinstance(ledger, AuditLedger) or not isinstance(ledger.events, tuple):
        return False
    previous = GENESIS_HASH
    seen: set[str] = set()
    for event in ledger.events:
        if not isinstance(event, AuditEvent) or event.schema_version != 1:
            return False
        if event.event_id in seen or event.previous_hash != previous:
            return False
        try:
            _reference("event_id", event.event_id)
            _reference("actor_ref", event.actor_ref)
            _reference("device_ref", event.device_ref)
            _reference("service_id", event.service_id)
            _reference("action", event.action)
            _reference("correlation_ref", event.correlation_ref)
            parsed = datetime.fromisoformat(event.occurred_at.replace("Z", "+00:00"))
            if parsed.tzinfo is None or event.decision not in _ALLOWED_DECISIONS:
                return False
            if event.result not in _ALLOWED_RESULTS:
                return False
            if _digest(_event_payload(event)) != event.event_hash:
                return False
        except (AuditValidationError, TypeError, ValueError):
            return False
        seen.add(event.event_id)
        previous = event.event_hash
    return True


def append_event(
    ledger: AuditLedger,
    *,
    event_id: str,
    actor_ref: str,
    device_ref: str,
    service_id: str,
    action: str,
    decision: str,
    result: str,
    occurred_at: datetime,
    correlation_ref: str,
) -> AuditLedger:
    """Append one validated event by returning a new immutable ledger."""
    if not verify_ledger(ledger):
        raise AuditValidationError("existing_ledger_integrity_failed")
    if decision not in _ALLOWED_DECISIONS:
        raise AuditValidationError("invalid_decision")
    if result not in _ALLOWED_RESULTS:
        raise AuditValidationError("invalid_result")
    values = {
        "event_id": _reference("event_id", event_id),
        "actor_ref": _reference("actor_ref", actor_ref),
        "device_ref": _reference("device_ref", device_ref),
        "service_id": _reference("service_id", service_id),
        "action": _reference("action", action),
        "decision": decision,
        "result": result,
        "occurred_at": _timestamp(occurred_at),
        "correlation_ref": _reference("correlation_ref", correlation_ref),
        "previous_hash": ledger.events[-1].event_hash if ledger.events else GENESIS_HASH,
        "schema_version": 1,
    }
    event = AuditEvent(**values, event_hash=_digest(values))
    updated = AuditLedger(events=ledger.events + (event,))
    if not verify_ledger(updated):
        raise AuditValidationError("new_event_integrity_failed")
    return updated


def retention_candidates(
    ledger: AuditLedger, *, before: datetime
) -> tuple[str, ...]:
    """List expired-by-policy candidates; never deletes or mutates evidence."""
    if not verify_ledger(ledger):
        raise AuditValidationError("ledger_integrity_failed")
    cutoff = _timestamp(before)
    return tuple(
        event.event_id for event in ledger.events if event.occurred_at < cutoff
    )


def export_ledger(
    ledger: AuditLedger, *, include_opaque_references: bool = False
) -> str:
    """Export verified JSON; reference fields are redacted by default."""
    if not verify_ledger(ledger):
        raise AuditValidationError("ledger_integrity_failed")
    records = []
    for event in ledger.events:
        record = asdict(event)
        if not include_opaque_references:
            for field in ("actor_ref", "device_ref", "correlation_ref"):
                record[field] = "[REDACTED]"
        records.append(record)
    return json.dumps(
        {"schema_version": 1, "events": records},
        sort_keys=True,
        separators=(",", ":"),
    )
