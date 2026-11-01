import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.audit_evidence import AuditLedger, verify_ledger
from backend.audit_store import AuditStoreError, SQLiteAuditStore
from backend.ipc_dispatcher import dispatch_local_ipc_request_with_durable_audit
from backend.ipc_peer_auth import PeerEvidence

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
REQUEST_ID = "req_1234567890abcdef"


class VerifiedAuthenticator:
    def __init__(self, status="VERIFIED"):
        self.status, self.calls = status, 0

    def verify_peer(self, connection_context, *, audience, now):
        self.calls += 1
        return PeerEvidence(
            status=self.status, transport="unix_domain_socket",
            principal_ref="principal_ref_opaque", audience=audience,
            channel_binding_ref="channel_ref_opaque",
            authenticated_at=now - timedelta(seconds=5),
            expires_at=now + timedelta(minutes=1), source="test_verifier",
        )


class BrokenStore:
    def load(self):
        return AuditLedger()

    def append(self, ledger):
        raise AuditStoreError("simulated_persistence_failure")


class DurableAuditedDispatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.path = Path(self.temp_dir.name) / "audit.sqlite3"
        self.store = SQLiteAuditStore(self.path)
        self.store.initialize()

    def request(self, method="host.health.read"):
        return json.dumps({
            "schema_version": "1.0", "request_id": REQUEST_ID,
            "method": method, "params": {},
        }).encode()

    def dispatch(self, raw=None, *, store=None, authenticator=None, **kwargs):
        return dispatch_local_ipc_request_with_durable_audit(
            self.request() if raw is None else raw,
            authenticator=authenticator or VerifiedAuthenticator(),
            connection_context=object(),
            store=self.store if store is None else store,
            event_id=kwargs.pop("event_id", "evt_0000000000000001"),
            occurred_at=NOW, now=NOW, **kwargs,
        )

    def test_success_is_persisted_and_survives_new_store_instance(self):
        response, ledger = self.dispatch()
        self.assertEqual(response["status"], "OK")
        self.assertTrue(response["audit_recorded"])
        self.assertEqual(len(ledger.events), 1)
        self.assertTrue(verify_ledger(ledger))
        self.assertEqual(SQLiteAuditStore(self.path).load(), ledger)

    def test_second_dispatch_loads_and_extends_persisted_ledger(self):
        _, first = self.dispatch()
        response, second = self.dispatch(event_id="evt_0000000000000002")
        self.assertEqual(response["status"], "OK")
        self.assertEqual(len(first.events), 1)
        self.assertEqual(len(second.events), 2)
        self.assertEqual(self.store.load(), second)

    def test_denied_peer_is_still_durably_audited(self):
        response, ledger = self.dispatch(
            authenticator=VerifiedAuthenticator(status="UNKNOWN"))
        self.assertEqual(response["status"], "DENIED")
        self.assertTrue(response["audit_recorded"])
        self.assertEqual(ledger.events[0].actor_ref, "peer_unknown")
        self.assertEqual(ledger.events[0].result, "NOT_RUN")

    def test_invalid_envelope_is_durably_audited_without_peer_call(self):
        auth = VerifiedAuthenticator()
        response, ledger = self.dispatch(raw=b"{", authenticator=auth)
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertTrue(response["audit_recorded"])
        self.assertEqual(auth.calls, 0)
        self.assertEqual(ledger.events[0].action, "request_rejected")

    def test_unreadable_store_prevents_dispatch(self):
        uninitialized = SQLiteAuditStore(
            Path(self.temp_dir.name) / "not_initialized.sqlite3")
        auth, calls = VerifiedAuthenticator(), []
        response, ledger = self.dispatch(
            store=uninitialized, authenticator=auth,
            diagnostics_provider=lambda: calls.append(True) or {})
        self.assertEqual(response["status"], "AUDIT_UNAVAILABLE")
        self.assertFalse(response["audit_recorded"])
        self.assertIsNone(ledger)
        self.assertEqual(auth.calls, 0)
        self.assertEqual(calls, [])

    def test_persistence_failure_suppresses_read_result(self):
        response, ledger = self.dispatch(store=BrokenStore())
        self.assertEqual(response["status"], "AUDIT_PERSISTENCE_FAILED")
        self.assertFalse(response["audit_recorded"])
        self.assertNotIn("result", response)
        self.assertEqual(ledger, AuditLedger())

    def test_failed_append_of_invalid_envelope_is_not_claimed(self):
        response, _ = self.dispatch(store=BrokenStore(), raw=b"{")
        self.assertEqual(response["status"], "AUDIT_PERSISTENCE_FAILED")
        self.assertFalse(response["audit_recorded"])


if __name__ == "__main__":
    unittest.main()
