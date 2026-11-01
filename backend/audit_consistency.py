"""Phase 21 independent consistency verification for local audit evidence.

This module compares a verified event hash-chain with its persisted checkpoint
history. It does not create trust, authenticate a store, or verify an external
anchor. A PASS means only that the supplied local records are internally
consistent at verification time.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import hashlib
import json

from backend.audit_anchor import GENESIS_HASH, AuditCheckpoint
from backend.audit_evidence import AuditLedger, verify_ledger


@dataclass(frozen=True, slots=True)
class AuditConsistencyReport:
    status: str
    ledger_event_count: int
    checkpoint_count: int
    verified_checkpoint_count: int
    latest_checkpoint_hash: str | None
    reason: str


def _canonical(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _checkpoint_is_valid(checkpoint: AuditCheckpoint) -> bool:
    if not isinstance(checkpoint, AuditCheckpoint):
        return False
    if type(checkpoint.schema_version) is not int or checkpoint.schema_version != 1:
        return False
    if type(checkpoint.event_count) is not int or checkpoint.event_count < 0:
        return False
    if not isinstance(checkpoint.head_hash, str) or len(checkpoint.head_hash) != 64:
        return False
    if any(char not in "0123456789abcdef" for char in checkpoint.head_hash):
        return False
    if not isinstance(checkpoint.checkpoint_hash, str) or len(checkpoint.checkpoint_hash) != 64:
        return False
    if any(char not in "0123456789abcdef" for char in checkpoint.checkpoint_hash):
        return False
    if not isinstance(checkpoint.created_at, str):
        return False
    try:
        created = datetime.fromisoformat(checkpoint.created_at.replace("Z", "+00:00"))
        if created.tzinfo is None or created.utcoffset() is None:
            return False
    except (TypeError, ValueError):
        return False
    payload = {
        "schema_version": checkpoint.schema_version,
        "event_count": checkpoint.event_count,
        "head_hash": checkpoint.head_hash,
        "created_at": checkpoint.created_at,
    }
    return hashlib.sha256(_canonical(payload)).hexdigest() == checkpoint.checkpoint_hash


def verify_checkpointed_audit(
    ledger: AuditLedger,
    checkpoints: tuple[AuditCheckpoint, ...],
    *,
    require_current_head: bool = True,
) -> AuditConsistencyReport:
    """Verify ledger integrity and every checkpoint's exact ledger prefix.

    Set require_current_head=False when validating historical checkpoints
    before appending the next checkpoint. A missing history is then acceptable
    as a migration/first-checkpoint state, but never proves external trust.
    """
    ledger_count = len(ledger.events) if isinstance(ledger, AuditLedger) else 0
    checkpoint_count = len(checkpoints) if isinstance(checkpoints, tuple) else 0

    if not isinstance(ledger, AuditLedger) or not verify_ledger(ledger):
        return AuditConsistencyReport(
            "FAIL", ledger_count, checkpoint_count, 0, None, "ledger_integrity_failed"
        )
    if not isinstance(checkpoints, tuple):
        return AuditConsistencyReport(
            "FAIL", ledger_count, 0, 0, None, "checkpoint_history_malformed"
        )
    if not checkpoints:
        if require_current_head:
            return AuditConsistencyReport(
                "UNKNOWN", ledger_count, 0, 0, None, "checkpoint_evidence_missing"
            )
        return AuditConsistencyReport(
            "PASS", ledger_count, 0, 0, None, "no_prior_checkpoints"
        )

    previous: AuditCheckpoint | None = None
    for checkpoint in checkpoints:
        if not _checkpoint_is_valid(checkpoint):
            return AuditConsistencyReport(
                "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_integrity_failed"
            )
        if checkpoint.event_count > ledger_count:
            return AuditConsistencyReport(
                "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_ahead_of_ledger"
            )
        expected_head = (
            ledger.events[checkpoint.event_count - 1].event_hash
            if checkpoint.event_count
            else GENESIS_HASH
        )
        if checkpoint.head_hash != expected_head:
            return AuditConsistencyReport(
                "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_prefix_mismatch"
            )
        if previous is not None:
            if checkpoint.event_count < previous.event_count:
                return AuditConsistencyReport(
                    "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_count_regressed"
                )
            if checkpoint.created_at < previous.created_at:
                return AuditConsistencyReport(
                    "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_time_regressed"
                )
            if (
                checkpoint.event_count == previous.event_count
                and checkpoint.head_hash != previous.head_hash
            ):
                return AuditConsistencyReport(
                    "FAIL", ledger_count, checkpoint_count, 0, None, "checkpoint_head_conflict"
                )
        previous = checkpoint

    latest = checkpoints[-1]
    if require_current_head and (
        latest.event_count != ledger_count
        or latest.head_hash != (ledger.events[-1].event_hash if ledger.events else GENESIS_HASH)
    ):
        return AuditConsistencyReport(
            "UNKNOWN",
            ledger_count,
            checkpoint_count,
            checkpoint_count,
            latest.checkpoint_hash,
            "latest_checkpoint_not_at_current_head",
        )

    return AuditConsistencyReport(
        "PASS",
        ledger_count,
        checkpoint_count,
        checkpoint_count,
        latest.checkpoint_hash,
        "ledger_and_checkpoint_history_consistent",
    )
