import json
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from backend.audit_evidence import (
    AuditEvent,
    AuditLedger,
    AuditValidationError,
    append_event,
    export_ledger,
    retention_candidates,
    verify_ledger,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


def append(ledger, event_id="evt_001", at=NOW):
    return append_event(
        ledger,
        event_id=event_id,
        actor_ref="actor_opaque_1",
        device_ref="device_opaque_1",
        service_id="diagnostics",
        action="read_report",
        decision="DENY",
        result="NOT_RUN",
        occurred_at=at,
        correlation_ref="corr_opaque_1",
    )


class AuditEvidenceTests(unittest.TestCase):
    def test_append_returns_new_ledger_and_preserves_original(self):
        original = AuditLedger()
        updated = append(original)
        self.assertEqual(original.events, ())
        self.assertEqual(len(updated.events), 1)
        self.assertTrue(verify_ledger(updated))

    def test_chain_links_multiple_events(self):
        ledger = append(append(AuditLedger()), "evt_002", NOW + timedelta(seconds=1))
        self.assertTrue(verify_ledger(ledger))
        self.assertEqual(ledger.events[1].previous_hash, ledger.events[0].event_hash)

    def test_tampered_payload_or_link_fails_verification(self):
        ledger = append(AuditLedger())
        event = ledger.events[0]
        tampered_payload = replace(event, result="SUCCEEDED")
        tampered_link = replace(event, previous_hash="f" * 64)
        self.assertFalse(verify_ledger(AuditLedger((tampered_payload,))))
        self.assertFalse(verify_ledger(AuditLedger((tampered_link,))))

    def test_duplicate_event_id_is_rejected(self):
        ledger = append(AuditLedger())
        with self.assertRaises(AuditValidationError):
            append(ledger)

    def test_malformed_and_sensitive_identifier_shaped_refs_are_rejected(self):
        kwargs = dict(
            event_id="evt_002", actor_ref="actor_1", device_ref="device_1",
            service_id="diagnostics", action="read_report", decision="DENY",
            result="NOT_RUN", occurred_at=NOW, correlation_ref="corr_1",
        )
        for field, value in (("actor_ref", " "), ("device_ref", "UDID/serial raw")):
            with self.subTest(field=field):
                with self.assertRaises(AuditValidationError):
                    append_event(AuditLedger(), **{**kwargs, field: value})

    def test_naive_timestamp_and_unknown_enums_fail_closed(self):
        kwargs = dict(
            event_id="evt_001", actor_ref="actor_1", device_ref="device_1",
            service_id="diagnostics", action="read_report", decision="ALLOW",
            result="NOT_RUN", occurred_at=NOW.replace(tzinfo=None),
            correlation_ref="corr_1",
        )
        with self.assertRaises(AuditValidationError):
            append_event(AuditLedger(), **kwargs)
        kwargs["occurred_at"] = NOW
        kwargs["decision"] = "MAYBE"
        with self.assertRaises(AuditValidationError):
            append_event(AuditLedger(), **kwargs)

    def test_retention_only_reports_candidates_and_never_deletes(self):
        ledger = append(append(AuditLedger(), "evt_old", NOW - timedelta(days=30)),
                        "evt_new", NOW)
        candidates = retention_candidates(ledger, before=NOW - timedelta(days=7))
        self.assertEqual(candidates, ("evt_old",))
        self.assertEqual(len(ledger.events), 2)
        self.assertTrue(verify_ledger(ledger))

    def test_export_redacts_opaque_refs_by_default(self):
        ledger = append(AuditLedger())
        payload = json.loads(export_ledger(ledger))
        record = payload["events"][0]
        self.assertEqual(record["actor_ref"], "[REDACTED]")
        self.assertEqual(record["device_ref"], "[REDACTED]")
        self.assertNotIn("device_opaque_1", export_ledger(ledger))
        explicit = json.loads(export_ledger(ledger, include_opaque_references=True))
        self.assertEqual(explicit["events"][0]["device_ref"], "device_opaque_1")

    def test_corrupt_ledger_cannot_be_exported_or_extended(self):
        ledger = append(AuditLedger())
        corrupted = AuditLedger((replace(ledger.events[0], event_hash="0" * 64),))
        self.assertFalse(verify_ledger(corrupted))
        with self.assertRaises(AuditValidationError):
            export_ledger(corrupted)
        with self.assertRaises(AuditValidationError):
            append(corrupted, "evt_002")


if __name__ == "__main__":
    unittest.main()
