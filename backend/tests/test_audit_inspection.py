import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from backend.audit_anchor import create_audit_checkpoint
from backend.audit_evidence import AuditLedger, append_event
from backend.audit_inspection import inspect_audit_database
from backend.audit_inspection_cli import main
from backend.audit_checkpoint_store import SQLiteAuditCheckpointStore
from backend.audit_store import SQLiteAuditStore

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class AuditInspectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "audit.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def populated_database(self):
        ledger_store = SQLiteAuditStore(self.database)
        checkpoint_store = SQLiteAuditCheckpointStore(self.database)
        ledger_store.initialize()
        checkpoint_store.initialize()
        ledger = append_event(
            AuditLedger(),
            event_id="evt_inspect_000001",
            actor_ref="actor_opaque",
            device_ref="not_applicable",
            service_id="local_ipc",
            action="read_host_health",
            decision="UNKNOWN",
            result="SUCCEEDED",
            occurred_at=NOW,
            correlation_ref="req_inspect_000001",
        )
        ledger_store.append(ledger)
        checkpoint_store.append(create_audit_checkpoint(ledger, created_at=NOW))
        return ledger_store, checkpoint_store

    def test_existing_consistent_database_passes_and_is_report_only(self):
        self.populated_database()
        before = self.database.read_bytes()
        report = inspect_audit_database(self.database)
        after = self.database.read_bytes()
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.ledger_event_count, 1)
        self.assertEqual(report.checkpoint_count, 1)
        self.assertEqual(report.external_anchor_status, "UNKNOWN")
        self.assertEqual(before, after)

    def test_missing_database_is_unknown_and_not_created(self):
        missing = Path(self.temp.name) / "missing.sqlite3"
        report = inspect_audit_database(missing)
        self.assertEqual(report.status, "UNKNOWN")
        self.assertFalse(missing.exists())
        self.assertEqual(report.reason, "database_file_missing")

    def test_database_with_missing_checkpoint_table_is_unknown(self):
        import sqlite3
        with sqlite3.connect(self.database) as connection:
            connection.execute("CREATE TABLE unrelated(value TEXT)")
        report = inspect_audit_database(self.database)
        self.assertEqual(report.status, "UNKNOWN")
        self.assertEqual(report.reason, "audit_database_unreadable_or_invalid")

    def test_cli_outputs_json_and_returns_pass(self):
        self.populated_database()
        with patch("builtins.print") as output:
            code = main(["--database", str(self.database)])
        self.assertEqual(code, 0)
        payload = json.loads(output.call_args.args[0])
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["storage_trust"], "UNVERIFIED_LOCAL_DATABASE")

    def test_cli_returns_unknown_exit_code_for_missing_database(self):
        missing = Path(self.temp.name) / "absent.sqlite3"
        with patch("builtins.print"):
            code = main(["--database", str(missing)])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
