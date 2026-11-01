import json
from datetime import datetime, timedelta, timezone
import unittest

from backend.agent_lifecycle import AgentLifecycle, AgentState
from backend.ipc_dispatcher import dispatch_local_ipc_request
from backend.ipc_peer_auth import PeerEvidence, UnavailablePeerAuthenticator

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
AUDIENCE = "host-agent-local-ipc"


class VerifiedAuthenticator:
    def __init__(self, status="VERIFIED"):
        self.status = status
        self.context = None
        self.calls = 0

    def verify_peer(self, connection_context, *, audience, now):
        self.calls += 1
        self.context = connection_context
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
        raise RuntimeError("sensitive provider detail")


class LocalIPCDispatcherTests(unittest.TestCase):
    def request(self, method="host.health.read"):
        return json.dumps({
            "schema_version": "1.0",
            "request_id": "req_1234567890abcdef",
            "method": method,
            "params": {},
        }).encode()

    def test_unavailable_default_denies_before_any_read(self):
        calls = []
        response = dispatch_local_ipc_request(
            self.request("host.diagnostics.read"),
            authenticator=UnavailablePeerAuthenticator(),
            connection_context=object(),
            diagnostics_provider=lambda: calls.append("called") or {"safe": True},
            now=NOW,
        )
        self.assertEqual(response["status"], "DENIED")
        self.assertEqual(response["peer_status"], "UNKNOWN")
        self.assertEqual(calls, [])
        self.assertFalse(response["authorization_granted"])
        self.assertFalse(response["device_operation_performed"])

    def test_verified_peer_can_read_health_only(self):
        authenticator = VerifiedAuthenticator()
        lifecycle = AgentLifecycle()
        lifecycle.transition(AgentState.STARTING)
        lifecycle.transition(AgentState.RUNNING)
        context = object()
        response = dispatch_local_ipc_request(
            self.request(),
            authenticator=authenticator,
            connection_context=context,
            lifecycle=lifecycle,
            now=NOW,
        )
        self.assertEqual(response["status"], "OK")
        self.assertEqual(response["request_id"], "req_1234567890abcdef")
        self.assertEqual(response["result"]["state"], "RUNNING")
        self.assertIs(authenticator.context, context)
        self.assertEqual(authenticator.calls, 1)
        self.assertFalse(response["authorization_granted"])
        self.assertFalse(response["device_operation_performed"])

    def test_verified_peer_can_read_diagnostics(self):
        authenticator = VerifiedAuthenticator()
        calls = []
        response = dispatch_local_ipc_request(
            self.request("host.diagnostics.read"),
            authenticator=authenticator,
            connection_context=object(),
            diagnostics_provider=lambda: calls.append(True) or {
                "capabilities": {"attached_device_inspection": "NOT_CONFIGURED"}
            },
            now=NOW,
        )
        self.assertEqual(response["status"], "OK")
        self.assertEqual(len(calls), 1)
        self.assertEqual(
            response["result"]["capabilities"]["attached_device_inspection"],
            "NOT_CONFIGURED",
        )

    def test_unknown_revoked_and_expired_peers_never_reach_provider(self):
        for status in ("UNKNOWN", "REVOKED", "EXPIRED"):
            with self.subTest(status=status):
                calls = []
                response = dispatch_local_ipc_request(
                    self.request("host.diagnostics.read"),
                    authenticator=VerifiedAuthenticator(status=status),
                    connection_context=object(),
                    diagnostics_provider=lambda: calls.append(True) or {},
                    now=NOW,
                )
                self.assertEqual(response["status"], "DENIED")
                self.assertEqual(response["peer_status"], status)
                self.assertEqual(calls, [])

    def test_authenticator_exception_is_redacted_and_denied(self):
        response = dispatch_local_ipc_request(
            self.request(),
            authenticator=BrokenAuthenticator(),
            connection_context=object(),
            now=NOW,
        )
        self.assertEqual(response["status"], "DENIED")
        self.assertEqual(response["error"], "peer_not_verified")
        self.assertNotIn("sensitive", str(response))

    def test_invalid_request_is_rejected_before_authentication(self):
        authenticator = VerifiedAuthenticator()
        response = dispatch_local_ipc_request(
            b"{",
            authenticator=authenticator,
            connection_context=object(),
            now=NOW,
        )
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(authenticator.calls, 0)

    def test_provider_failure_is_redacted(self):
        def broken():
            raise RuntimeError("private path and secret")

        response = dispatch_local_ipc_request(
            self.request("host.diagnostics.read"),
            authenticator=VerifiedAuthenticator(),
            connection_context=object(),
            diagnostics_provider=broken,
            now=NOW,
        )
        self.assertEqual(response["status"], "ERROR")
        self.assertEqual(response["error"], "read_provider_unavailable")
        self.assertNotIn("private path", str(response))

    def test_dispatcher_does_not_accept_unlisted_methods(self):
        authenticator = VerifiedAuthenticator()
        response = dispatch_local_ipc_request(
            self.request("device.unlock"),
            authenticator=authenticator,
            connection_context=object(),
            now=NOW,
        )
        self.assertEqual(response["status"], "INVALID_REQUEST")
        self.assertEqual(authenticator.calls, 0)


if __name__ == "__main__":
    unittest.main()
