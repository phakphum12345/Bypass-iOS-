import unittest
from datetime import datetime, timezone

from backend.audit_evidence import AuditLedger, export_ledger, verify_ledger
from backend.ipc_audit import append_ipc_audit_event
from backend.ipc_peer_auth import PeerEvidence

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
REQUEST_ID = "req_1234567890abcdef"


class IPCAuditEvidenceTests(unittest.TestCase):
    def verified_peer(self):
        return PeerEvidence(
            status="VERIFIED",
            transport="unix_domain_socket",
            principal_ref="principal_opaque_123",
            audience="host-agent-local-ipc",
            channel_binding_ref="channel_opaque_123",
            authenticated_at=NOW,
            expires_at=datetime(2026, 11, 1, 13, 0, tzinfo=timezone.utc),
            source="test",
        )

    def append(self, ledger, **overrides):
        values = {
            "event_id": "evt_0000000000000001",
            "peer": self.verified_peer(),
            "request_id": REQUEST_ID,
            "method": "host.health.read",
            "response_status": "OK",
            "occurred_at": NOW,
        }
        values.update(overrides)
        return append_ipc_audit_event(ledger, **values)

    def test_verified_peer_maps_to_opaque_actor_and_success(self):
        ledger = self.append(AuditLedger())
        event = ledger.events[0]
        self.assertEqual(event.actor_ref, "principal_opaque_123")
        self.assertEqual(event.device_ref, "not_applicable")
        self.assertEqual(event.service_id, "local_ipc")
        self.assertEqual(event.action, "read_host_health")
        self.assertEqual(event.decision, "UNKNOWN")
        self.assertEqual(event.result, "SUCCEEDED")
        self.assertEqual(event.correlation_ref, REQUEST_ID)
        self.assertTrue(verify_ledger(ledger))

    def test_unverified_peer_is_recorded_as_unknown_actor(self):
        peer = PeerEvidence(status="UNKNOWN", source="not_configured")
        ledger = self.append(AuditLedger(), peer=peer, response_status="DENIED")
        event = ledger.events[0]
        self.assertEqual(event.actor_ref, "peer_unknown")
        self.assertEqual(event.decision, "UNKNOWN")
        self.assertEqual(event.result, "NOT_RUN")

    def test_provider_error_is_recorded_without_exception_details(self):
        ledger = self.append(
            AuditLedger(),
            response_status="ERROR",
            method="host.diagnostics.read",
        )
        event = ledger.events[0]
        self.assertEqual(event.action, "read_host_diagnostics")
        self.assertEqual(event.result, "FAILED")
        self.assertNotIn("exception", str(event))

    def test_invalid_request_uses_server_generated_correlation_reference(self):
        ledger = self.append(
            AuditLedger(),
            peer=None,
            request_id=None,
            method=None,
            response_status="INVALID_REQUEST",
        )
        event = ledger.events[0]
        self.assertEqual(event.action, "request_rejected")
        self.assertEqual(event.correlation_ref, "evt_0000000000000001")
        self.assertEqual(event.result, "NOT_RUN")

    def test_audit_decision_never_grants_device_authority(self):
        for status in ("OK", "ERROR", "DENIED", "INVALID_REQUEST"):
            with self.subTest(status=status):
                ledger = self.append(AuditLedger(), response_status=status)
                self.assertEqual(ledger.events[0].decision, "UNKNOWN")

    def test_audit_record_has_no_request_or_diagnostic_payload(self):
        ledger = self.append(AuditLedger())
        exported = export_ledger(ledger, include_opaque_references=True)
        self.assertNotIn("request_body", exported)
        self.assertNotIn("diagnostic_report", exported)
        self.assertNotIn("serial", exported)

    def test_invalid_status_is_rejected(self):
        with self.assertRaises(ValueError):
            self.append(AuditLedger(), response_status="AUTHORIZED")

    def test_original_ledger_is_immutable(self):
        original = AuditLedger()
        updated = self.append(original)
        self.assertEqual(original.events, ())
        self.assertEqual(len(updated.events), 1)


if __name__ == "__main__":
    unittest.main()
