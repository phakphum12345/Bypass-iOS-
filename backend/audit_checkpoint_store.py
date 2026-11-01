"""Phase 19 durable storage for deterministic audit checkpoints.

Checkpoints are stored in the same local SQLite trust domain as the audit
ledger. This detects malformed records and ordinary rollback/order conflicts;
it is not an independently anchored or tamper-proof store.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime
import hashlib
import json
import re
import sqlite3
from pathlib import Path

from backend.audit_anchor import AuditCheckpoint

_HASH = re.compile(r"^[a-f0-9]{64}$")


class AuditCheckpointStoreError(RuntimeError):
    """Raised when checkpoint persistence or verification fails."""


def _canonical(payload: dict) -> bytes:
    return json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True
    ).encode("utf-8")


def _checkpoint_payload(checkpoint: AuditCheckpoint) -> dict:
    return {
        "schema_version": checkpoint.schema_version,
        "event_count": checkpoint.event_count,
        "head_hash": checkpoint.head_hash,
        "created_at": checkpoint.created_at,
    }


def _valid_checkpoint(checkpoint: AuditCheckpoint) -> bool:
    if not isinstance(checkpoint, AuditCheckpoint):
        return False
    if checkpoint.schema_version != 1 or not isinstance(checkpoint.event_count, int):
        return False
    if checkpoint.event_count < 0:
        return False
    if not isinstance(checkpoint.head_hash, str) or not _HASH.fullmatch(checkpoint.head_hash):
        return False
    if not isinstance(checkpoint.checkpoint_hash, str) or not _HASH.fullmatch(checkpoint.checkpoint_hash):
        return False
    try:
        created = datetime.fromisoformat(checkpoint.created_at.replace("Z", "+00:00"))
        if created.tzinfo is None or created.utcoffset() is None:
            return False
    except (AttributeError, TypeError, ValueError):
        return False
    return hashlib.sha256(_canonical(_checkpoint_payload(checkpoint))).hexdigest() == checkpoint.checkpoint_hash


class SQLiteAuditCheckpointStore:
    """Transactional append-only-by-contract storage for audit checkpoints."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = str(database_path)
        if not self.database_path or self.database_path == ":memory:":
            raise ValueError("file_backed_database_required")

    @staticmethod
    def _connect(path: str) -> sqlite3.Connection:
        connection = sqlite3.connect(path, timeout=10.0, isolation_level=None)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        try:
            with closing(self._connect(self.database_path)) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS audit_checkpoints (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        checkpoint_hash TEXT NOT NULL UNIQUE,
                        checkpoint_json TEXT NOT NULL
                    )"""
                )
                connection.execute(
                    """CREATE TRIGGER IF NOT EXISTS audit_checkpoints_no_update
                    BEFORE UPDATE ON audit_checkpoints
                    BEGIN SELECT RAISE(ABORT, 'audit_checkpoints_are_append_only'); END"""
                )
                connection.execute(
                    """CREATE TRIGGER IF NOT EXISTS audit_checkpoints_no_delete
                    BEFORE DELETE ON audit_checkpoints
                    BEGIN SELECT RAISE(ABORT, 'audit_checkpoints_are_append_only'); END"""
                )
        except sqlite3.Error as exc:
            raise AuditCheckpointStoreError("checkpoint_store_initialization_failed") from exc

    @staticmethod
    def _read(connection: sqlite3.Connection) -> tuple[AuditCheckpoint, ...]:
        rows = connection.execute(
            "SELECT checkpoint_json FROM audit_checkpoints ORDER BY sequence"
        ).fetchall()
        checkpoints: list[AuditCheckpoint] = []
        try:
            for row in rows:
                value = json.loads(row["checkpoint_json"])
                checkpoint = AuditCheckpoint(**value)
                if not _valid_checkpoint(checkpoint):
                    raise AuditCheckpointStoreError("checkpoint_record_invalid")
                if checkpoints:
                    previous = checkpoints[-1]
                    if checkpoint.event_count < previous.event_count:
                        raise AuditCheckpointStoreError("checkpoint_event_count_regressed")
                    if checkpoint.created_at < previous.created_at:
                        raise AuditCheckpointStoreError("checkpoint_timestamp_regressed")
                    if (
                        checkpoint.event_count == previous.event_count
                        and checkpoint.head_hash != previous.head_hash
                    ):
                        raise AuditCheckpointStoreError("checkpoint_head_conflict")
                checkpoints.append(checkpoint)
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise AuditCheckpointStoreError("checkpoint_record_malformed") from exc
        return tuple(checkpoints)

    def load(self) -> tuple[AuditCheckpoint, ...]:
        try:
            with closing(self._connect(self.database_path)) as connection:
                return self._read(connection)
        except sqlite3.Error as exc:
            raise AuditCheckpointStoreError("checkpoint_store_read_failed") from exc

    def append(self, checkpoint: AuditCheckpoint) -> tuple[AuditCheckpoint, ...]:
        """Append a valid checkpoint; exact retries are idempotent."""
        if not _valid_checkpoint(checkpoint):
            raise AuditCheckpointStoreError("checkpoint_integrity_failed")
        connection = None
        try:
            connection = self._connect(self.database_path)
            connection.execute("BEGIN IMMEDIATE")
            existing = self._read(connection)
            if checkpoint in existing:
                connection.execute("COMMIT")
                return existing
            if existing:
                previous = existing[-1]
                if checkpoint.event_count < previous.event_count:
                    raise AuditCheckpointStoreError("checkpoint_event_count_regressed")
                if checkpoint.created_at < previous.created_at:
                    raise AuditCheckpointStoreError("checkpoint_timestamp_regressed")
                if (
                    checkpoint.event_count == previous.event_count
                    and checkpoint.head_hash != previous.head_hash
                ):
                    raise AuditCheckpointStoreError("checkpoint_head_conflict")
            connection.execute(
                "INSERT INTO audit_checkpoints(checkpoint_hash, checkpoint_json) VALUES (?, ?)",
                (
                    checkpoint.checkpoint_hash,
                    json.dumps(
                        {
                            **_checkpoint_payload(checkpoint),
                            "checkpoint_hash": checkpoint.checkpoint_hash,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                ),
            )
            connection.execute("COMMIT")
            return self._read(connection)
        except (sqlite3.Error, AuditCheckpointStoreError) as exc:
            if connection is not None:
                try:
                    connection.execute("ROLLBACK")
                except sqlite3.Error:
                    pass
            if isinstance(exc, AuditCheckpointStoreError):
                raise
            raise AuditCheckpointStoreError("checkpoint_store_append_failed") from exc
        finally:
            if connection is not None:
                connection.close()
