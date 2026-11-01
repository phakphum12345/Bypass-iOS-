import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.audit_checkpoint_store import SQLiteAuditCheckpointStore
from backend.audit_store import SQLiteAuditStore
from backend.checkpointed_ipc_audit import (
    dispatch_local_ipc_request_with_checkpointed_audit,
)
from backend.ipc_peer_auth import PeerEvidence, UnavailablePeerAuthenticator

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
AUDIENCE = "host-agent-local-ipc"


class VerifiedAuthenticator:
    def verify_peer(self, connection_context, *, audience, now):
        return PeerEvidence(
            status="VERIFIED",
            transport="unix_domain_socket",
            principal_ref="principal_ref_opaque",
            audience=audience,
            channel_binding_ref="channel_ref_opaque",
            authenticated_at=now - timedelta(seconds=5),
            expires_at=now + timedelta(minutes=1),
            source="test_verifier",
        )


class FailingCheckpointStore:
    def load(self):
        raise RuntimeError("private storage detail")

    def append(self, checkpoint):
        raise AssertionError("append must not run after load failure")


class CheckpointedIPCAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        database = Path(self.temp_dir.name) / "audit.sqlite3"
        self.audit_store = SQLiteAuditStore(database)
        self.checkpoint_store = SQLiteAuditCheckpointStore(database)
        self.audit_store.initialize()
        self.checkpoint_store.initialize()

    @staticmethod
    def request():
        return json.dumps({
            "schema_version": "1.0",
            "request_id": "req_1234567890abcdef",
            "method": "host.diagnostics.read",
            "params": {},
        }).encode()

    def dispatch(self, *, event_id, authenticator=None, checkpoint_store=None, at=NOW):
        return dispatch_local_ipc_request_with_checkpointed_audit(
            self.request(),
            authenticator=authenticator or VerifiedAuthenticator(),
            connection_context=object(),
            audit_store=self.audit_store,
            checkpoint_store=checkpoint_store or self.checkpoint_store,
            event_id=event_id,
            occurred_at=at,
            diagnostics_provider=lambda: {"safe": True},
            now=at,
        )

    def test_success_requires_both_durable_event_and_checkpoint(self):
        response, ledger, checkpoint = self.dispatch(event_id="evt_0000000000000001")
        self.assertEqual(response["status"], "OK")
        self.assertTrue(response["audit_recorded"])
        self.assertTrue(response["checkpoint_recorded"])
        self.assertEqual(response["result"], {"safe": True})
        self.assertIsNotNone(ledger)
        self.assertIsNotNone(checkpoint)
        self.assertEqual(self.checkpoint_store.load(), (checkpoint,))

    def test_each_dispatch_advances_checkpoint_to_ledger_head(self):
        first = self.dispatch(event_id="evt_0000000000000001")
        second = self.dispatch(
            event_id="evt_0000000000000002",
            at=NOW + timedelta(seconds=1),
        )
        self.assertEqual(first[2].event_count, 1)
        self.assertEqual(second[2].event_count, 2)
        self.assertEqual(len(self.checkpoint_store.load()), 2)

    def test_checkpoint_failure_suppresses_read_result(self):
        response, ledger, checkpoint = self.dispatch(
            event_id="evt_0000000000000001",
            checkpoint_store=FailingCheckpointStore(),
        )
        self.assertEqual(response["status"], "AUDIT_CHECKPOINT_FAILED")
        self.assertTrue(response["audit_recorded"])
        self.assertFalse(response["checkpoint_recorded"])
        self.assertNotIn("result", response)
        self.assertIsNotNone(ledger)
        self.assertIsNone(checkpoint)

    def test_denied_request_is_still_durably_audited_and_checkpointed(self):
        response, ledger, checkpoint = self.dispatch(
            event_id="evt_0000000000000001",
            authenticator=UnavailablePeerAuthenticator(),
        )
        self.assertEqual(response["status"], "DENIED")
        self.assertTrue(response["audit_recorded"])
        self.assertTrue(response["checkpoint_recorded"])
        self.assertIsNotNone(ledger)
        self.assertIsNotNone(checkpoint)
        self.assertNotIn("result", response)


if __name__ == "__main__":
    unittest.main()
