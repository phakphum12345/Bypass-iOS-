import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from backend.audit_anchor import create_audit_checkpoint
from backend.audit_evidence import AuditLedger, append_event
from backend.audit_checkpoint_store import SQLiteAuditCheckpointStore
from backend.audit_store import SQLiteAuditStore
from backend.decision_api.server import DecisionHandler

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class AuditInspectionApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DecisionHandler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.database = Path(self.temp.name) / "audit.sqlite3"

    def tearDown(self):
        self.temp.cleanup()

    def request(self):
        connection = HTTPConnection("127.0.0.1", self.port, timeout=2)
        connection.request("GET", "/v1/audit/inspection")
        response = connection.getresponse()
        payload = response.read()
        connection.close()
        return response.status, json.loads(payload)

    def populate_database(self):
        ledger_store = SQLiteAuditStore(self.database)
        checkpoint_store = SQLiteAuditCheckpointStore(self.database)
        ledger_store.initialize()
        checkpoint_store.initialize()
        ledger = append_event(
            AuditLedger(),
            event_id="evt_api_inspect_0001",
            actor_ref="actor_private_ref",
            device_ref="not_applicable",
            service_id="local_ipc",
            action="read_host_health",
            decision="UNKNOWN",
            result="SUCCEEDED",
            occurred_at=NOW,
            correlation_ref="req_api_inspect_0001",
        )
        ledger_store.append(ledger)
        checkpoint_store.append(create_audit_checkpoint(ledger, created_at=NOW))

    def test_unconfigured_database_returns_unknown_without_path_disclosure(self):
        with patch.dict(os.environ, {}, clear=True):
            status, body = self.request()
        self.assertEqual(status, 503)
        self.assertEqual(body["status"], "UNKNOWN")
        self.assertEqual(body["reason"], "audit_inspection_not_configured")
        self.assertNotIn("database_path", body)

    def test_existing_consistent_database_returns_redacted_pass_summary(self):
        self.populate_database()
        before = self.database.read_bytes()
        with patch.dict(os.environ, {"DECISION_API_AUDIT_DATABASE": str(self.database)}):
            status, body = self.request()
        after = self.database.read_bytes()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "PASS")
        self.assertEqual(body["ledger_event_count"], 1)
        self.assertEqual(body["checkpoint_count"], 1)
        self.assertEqual(body["external_anchor_status"], "UNKNOWN")
        self.assertEqual(body["storage_trust"], "UNVERIFIED_LOCAL_DATABASE")
        self.assertEqual(before, after)
        self.assertNotIn("actor_private_ref", json.dumps(body))
        self.assertNotIn("evt_api_inspect_0001", json.dumps(body))

    def test_missing_database_returns_unknown_and_is_not_created(self):
        missing = self.database
        with patch.dict(os.environ, {"DECISION_API_AUDIT_DATABASE": str(missing)}):
            status, body = self.request()
        self.assertEqual(status, 200)
        self.assertEqual(body["status"], "UNKNOWN")
        self.assertEqual(body["reason"], "database_file_missing")
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
