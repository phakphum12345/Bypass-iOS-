"""Phase 16 local SQLite persistence for the immutable audit ledger.

The store provides transactional append and hash-chain verification. SQLite
triggers prevent ordinary UPDATE/DELETE statements; this is not protection
against an administrator or attacker who can replace or rewrite the database.
"""
from __future__ import annotations

from dataclasses import asdict
import json
import sqlite3
from pathlib import Path

from backend.audit_evidence import AuditEvent, AuditLedger, AuditValidationError, verify_ledger


class AuditStoreError(RuntimeError):
    """Raised when durable audit evidence cannot be safely read or appended."""


class SQLiteAuditStore:
    """A local append-only-by-contract SQLite adapter for AuditLedger."""

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
            with self._connect(self.database_path) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute(
                    """CREATE TABLE IF NOT EXISTS audit_events (
                        sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_id TEXT NOT NULL UNIQUE,
                        event_json TEXT NOT NULL
                    )"""
                )
                connection.execute(
                    """CREATE TRIGGER IF NOT EXISTS audit_events_no_update
                    BEFORE UPDATE ON audit_events
                    BEGIN SELECT RAISE(ABORT, 'audit_events_are_append_only'); END"""
                )
                connection.execute(
                    """CREATE TRIGGER IF NOT EXISTS audit_events_no_delete
                    BEFORE DELETE ON audit_events
                    BEGIN SELECT RAISE(ABORT, 'audit_events_are_append_only'); END"""
                )
        except sqlite3.Error as exc:
            raise AuditStoreError("audit_store_initialization_failed") from exc

    @staticmethod
    def _read(connection: sqlite3.Connection) -> AuditLedger:
        rows = connection.execute(
            "SELECT event_json FROM audit_events ORDER BY sequence"
        ).fetchall()
        events: list[AuditEvent] = []
        try:
            for row in rows:
                value = json.loads(row["event_json"])
                events.append(AuditEvent(**value))
        except (TypeError, ValueError, KeyError, json.JSONDecodeError) as exc:
            raise AuditStoreError("audit_store_record_malformed") from exc
        ledger = AuditLedger(events=tuple(events))
        if not verify_ledger(ledger):
            raise AuditStoreError("audit_store_integrity_failed")
        return ledger

    def load(self) -> AuditLedger:
        try:
            with self._connect(self.database_path) as connection:
                return self._read(connection)
        except sqlite3.Error as exc:
            raise AuditStoreError("audit_store_read_failed") from exc

    def append(self, ledger: AuditLedger) -> AuditLedger:
        """Persist a ledger extension; never replace or truncate existing rows."""
        if not verify_ledger(ledger):
            raise AuditValidationError("ledger_integrity_failed")
        try:
            with self._connect(self.database_path) as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = self._read(connection)
                current = existing.events
                proposed = ledger.events
                if len(proposed) < len(current) or proposed[:len(current)] != current:
                    raise AuditStoreError("audit_store_append_conflict")
                for event in proposed[len(current):]:
                    connection.execute(
                        "INSERT INTO audit_events(event_id, event_json) VALUES (?, ?)",
                        (
                            event.event_id,
                            json.dumps(asdict(event), sort_keys=True, separators=(",", ":")),
                        ),
                    )
                connection.execute("COMMIT")
                return self._read(connection)
        except (sqlite3.Error, AuditStoreError) as exc:
            try:
                connection.execute("ROLLBACK")
            except (sqlite3.Error, UnboundLocalError):
                pass
            if isinstance(exc, AuditStoreError):
                raise
            raise AuditStoreError("audit_store_append_failed") from exc
