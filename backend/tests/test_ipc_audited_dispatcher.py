import json
import unittest
from datetime import datetime, timedelta, timezone

from backend.audit_evidence import AuditLedger, verify_ledger
from backend.ipc_dispatcher import dispatch_local_ipc_request_with_audit
from backend.ipc_peer_auth import PeerEvidence

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
REQUEST_ID = "req_1234567890abcdef"


class VerifiedAuthenticator:
    def __init__(self, status="VERIFIED"):
        self.status = status
        self.calls = 0

    def verify_peer(self, connection_context, *, audience, now):
        self.calls += 1
        return PeerEvidence(
            status=self.status,
            transport="unix_domain_socket",
            principal_ref="principal_ref_opaque",
            audience=audience,
            channel_binding_ref="channel_ref_opaque",
            authenticated_at=now - timedelta(seconds=5),
            expires_at=now + timedelta(minutes=1),
            source="test_verifier",
        )


class BrokenAuthenticator:
    def verify_peer(self, connection_context, *, audience, now):
        raise RuntimeError("private provider detail")


def request(method="host.health.read"):
    return json.dumps({
        "schema_version": "1.0",
        "request_id": REQUEST_ID,
        "method": method,
        "params": {},
    }).encode()


class AuditedIPCDispatcherTests(unittest.TestCase):
    def dispatch(self, raw, authenticator, **kwargs):
        return dispatch_local_ipc_request_with_audit(
            raw,
            authenticator=authenticator,
            connection_context=object(),
            ledger=kwargs.pop("ledger", AuditLedger()),
            event_id=kwargs.pop("event_id", "evt_0000000000000001"),
            occurred_at=NOW,
            now=NOW,
            **kwargs,
        )

    def test_success_is_dispatched_and_audited_once(self):
        authenticator = VerifiedAuthenticator()
        response, ledger = self.dispatch(request(), authenticator)
        self.assertEqual(response["status"], "OK")
        self.assertEqual(authenticator.calls, 1)
        self.assertEqual(len(ledger.events), 1)
        event = ledger.events[0]
        self.assertEqual(event.actor_ref, "principal_ref_opaque")
        self.assertEqual(event.action, "read_host_health")
        self.assertEqual(event.result, "SUCCEEDED")
        self.assertEqual(event.decision, "UNKNOWN")
        self.assertEqual(event.correlation_ref, REQUEST_ID)
        self.assertTrue(verify_ledger(ledger))

    def test_unknown_peer_is_denied_and_audited_without_provider_call(self):
        authenticator = VerifiedAuthenticator(status="UNKNOWN")
        calls = []
        response, ledger = self.dispatch(
            request("host.diagnostics.read"),
            authenticator,
            diagnostics_provider=lambda: calls.append(True) or {},
        )
        self.assertEqual(response["status"], "DENIED")
        self.assertEqual(authenticator.calls, 1)
        self.assertEqual(calls, [])
        self.assertEqual(ledger.events[0].actor_ref, "peer_unknown")
        self.assertEqual(ledger.events[0].result, "NOT_RUN")

    def test_invalid_envelope_is_audited_without_authentication(self):
        authenticator = VerifiedAuthenticator()
        response, ledger = self.dispatch(b"{", authenticator)
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(authenticator.calls, 0)
        self.assertEqual(ledger.events[0].action, "request_rejected")
        self.assertEqual(ledger.events[0].correlation_ref, "evt_0000000000000001")

    def test_provider_failure_is_audited_without_exception_details(self):
        response, ledger = self.dispatch(
            request("host.diagnostics.read"),
            VerifiedAuthenticator(),
            diagnostics_provider=lambda: (_ for _ in ()).throw(
                RuntimeError("private path secret")
            ),
        )
        self.assertEqual(response["status"], "ERROR")
        self.assertEqual(ledger.events[0].result, "FAILED")
        self.assertNotIn("private path", str(ledger.events[0]))

    def test_authenticator_exception_is_denied_and_audited(self):
        response, ledger = self.dispatch(request(), BrokenAuthenticator())
        self.assertEqual(response["status"], "DENIED")
        self.assertEqual(ledger.events[0].actor_ref, "peer_unknown")
        self.assertEqual(ledger.events[0].result, "NOT_RUN")

    def test_existing_ledger_is_preserved_immutably(self):
        original = AuditLedger()
        _, updated = self.dispatch(request(), VerifiedAuthenticator(), ledger=original)
        self.assertEqual(original.events, ())
        self.assertEqual(len(updated.events), 1)


if __name__ == "__main__":
    unittest.main()
