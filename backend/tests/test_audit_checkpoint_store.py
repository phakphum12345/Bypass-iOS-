import json
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.audit_anchor import AuditCheckpoint, create_audit_checkpoint
from backend.audit_evidence import AuditLedger, append_event
from backend.audit_checkpoint_store import (
    AuditCheckpointStoreError,
    SQLiteAuditCheckpointStore,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class SQLiteAuditCheckpointStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "audit.sqlite3"
        self.store = SQLiteAuditCheckpointStore(self.path)
        self.store.initialize()

    def make_ledger(self, count):
        ledger = AuditLedger()
        for index in range(count):
            ledger = append_event(
                ledger,
                event_id=f"evt_{index:016d}",
                actor_ref="actor_opaque",
                device_ref="not_applicable",
                service_id="local_ipc",
                action="read_host_health",
                decision="UNKNOWN",
                result="SUCCEEDED",
                occurred_at=NOW + timedelta(seconds=index),
                correlation_ref=f"req_{index:016d}",
            )
        return ledger

    def checkpoint(self, count, offset=0):
        return create_audit_checkpoint(
            self.make_ledger(count), created_at=NOW + timedelta(minutes=offset)
        )

    def test_empty_store_loads_empty_history(self):
        self.assertEqual(self.store.load(), ())

    def test_append_and_reload_preserves_checkpoint(self):
        checkpoint = self.checkpoint(1)
        self.assertEqual(self.store.append(checkpoint), (checkpoint,))
        self.assertEqual(self.store.load(), (checkpoint,))

    def test_exact_retry_is_idempotent(self):
        checkpoint = self.checkpoint(1)
        self.store.append(checkpoint)
        self.assertEqual(self.store.append(checkpoint), (checkpoint,))

    def test_monotonic_event_count_and_timestamp_are_required(self):
        self.store.append(self.checkpoint(2, offset=2))
        with self.assertRaises(AuditCheckpointStoreError):
            self.store.append(self.checkpoint(1, offset=3))
        with self.assertRaises(AuditCheckpointStoreError):
            self.store.append(self.checkpoint(3, offset=1))

    def test_same_event_count_cannot_change_chain_head(self):
        self.store.append(self.checkpoint(1))
        different_ledger = append_event(
            AuditLedger(),
            event_id="evt_different_0001",
            actor_ref="actor_opaque",
            device_ref="not_applicable",
            service_id="local_ipc",
            action="read_host_health",
            decision="UNKNOWN",
            result="SUCCEEDED",
            occurred_at=NOW,
            correlation_ref="req_different_0001",
        )
        conflict = create_audit_checkpoint(
            different_ledger, created_at=NOW + timedelta(minutes=1)
        )
        with self.assertRaises(AuditCheckpointStoreError):
            self.store.append(conflict)

    def test_invalid_digest_is_rejected_without_write(self):
        valid = self.checkpoint(1)
        invalid = AuditCheckpoint(
            schema_version=valid.schema_version,
            event_count=valid.event_count,
            head_hash=valid.head_hash,
            created_at=valid.created_at,
            checkpoint_hash="f" * 64,
        )
        with self.assertRaises(AuditCheckpointStoreError):
            self.store.append(invalid)
        self.assertEqual(self.store.load(), ())

    def test_sql_update_and_delete_are_rejected(self):
        self.store.append(self.checkpoint(1))
        with sqlite3.connect(self.path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE audit_checkpoints SET checkpoint_json='{}'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM audit_checkpoints")

    def test_modified_record_fails_on_reload(self):
        self.store.append(self.checkpoint(1))
        with sqlite3.connect(self.path) as connection:
            connection.execute("DROP TRIGGER audit_checkpoints_no_update")
            connection.execute(
                "UPDATE audit_checkpoints SET checkpoint_json=? WHERE sequence=1",
                (json.dumps({"schema_version": 1}),),
            )
        with self.assertRaises(AuditCheckpointStoreError):
            self.store.load()


if __name__ == "__main__":
    unittest.main()
