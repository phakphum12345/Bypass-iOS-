import sqlite3
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from backend.audit_evidence import AuditLedger, append_event, verify_ledger
from backend.audit_store import AuditStoreError, SQLiteAuditStore

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class SQLiteAuditStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "audit.sqlite3"
        self.store = SQLiteAuditStore(self.path)
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
                occurred_at=NOW,
                correlation_ref=f"req_{index:016d}",
            )
        return ledger

    def test_empty_store_loads_as_empty_verified_ledger(self):
        loaded = self.store.load()
        self.assertEqual(loaded, AuditLedger())
        self.assertTrue(verify_ledger(loaded))

    def test_append_and_reload_preserves_hash_chain(self):
        ledger = self.make_ledger(2)
        saved = self.store.append(ledger)
        self.assertEqual(saved, ledger)
        self.assertEqual(self.store.load(), ledger)
        self.assertTrue(verify_ledger(self.store.load()))

    def test_append_accepts_only_a_strict_extension_of_persisted_prefix(self):
        first = self.make_ledger(1)
        self.store.append(first)
        extended = self.make_ledger(2)
        self.assertEqual(self.store.append(extended), extended)
        conflicting = self.make_ledger(1)
        with self.assertRaises(AuditStoreError):
            self.store.append(conflicting)

    def test_duplicate_append_is_idempotent_for_same_ledger(self):
        ledger = self.make_ledger(1)
        self.store.append(ledger)
        self.assertEqual(self.store.append(ledger), ledger)

    def test_sql_update_and_delete_are_rejected(self):
        self.store.append(self.make_ledger(1))
        with sqlite3.connect(self.path) as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE audit_events SET event_json='{}'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("DELETE FROM audit_events")

    def test_modified_database_fails_hash_chain_verification(self):
        self.store.append(self.make_ledger(1))
        with sqlite3.connect(self.path) as connection:
            connection.execute("DROP TRIGGER audit_events_no_update")
            connection.execute(
                "UPDATE audit_events SET event_json='{}' WHERE sequence=1"
            )
        with self.assertRaises(AuditStoreError):
            self.store.load()

    def test_incomplete_or_invalid_ledger_is_not_persisted(self):
        with self.assertRaises(Exception):
            self.store.append(object())
        self.assertEqual(self.store.load(), AuditLedger())


if __name__ == "__main__":
    unittest.main()
