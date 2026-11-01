import unittest
from datetime import datetime, timedelta, timezone

from backend.audit_anchor import create_audit_checkpoint
from backend.audit_consistency import verify_checkpointed_audit
from backend.audit_evidence import AuditLedger, append_event

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class AuditConsistencyTests(unittest.TestCase):
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

    def checkpoint(self, ledger, offset=0):
        return create_audit_checkpoint(
            ledger, created_at=NOW + timedelta(minutes=offset)
        )

    def test_matching_checkpoint_at_current_head_passes(self):
        ledger = self.make_ledger(2)
        checkpoint = self.checkpoint(ledger)
        report = verify_checkpointed_audit(ledger, (checkpoint,))
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.verified_checkpoint_count, 1)
        self.assertEqual(report.latest_checkpoint_hash, checkpoint.checkpoint_hash)

    def test_historical_prefixes_pass_without_current_head_requirement(self):
        first_ledger = self.make_ledger(1)
        full_ledger = self.make_ledger(2)
        first = self.checkpoint(first_ledger)
        second = self.checkpoint(full_ledger, offset=1)
        report = verify_checkpointed_audit(
            full_ledger, (first, second), require_current_head=True
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.verified_checkpoint_count, 2)

    def test_stale_latest_checkpoint_is_unknown_when_current_head_required(self):
        ledger = self.make_ledger(2)
        stale = self.checkpoint(self.make_ledger(1))
        report = verify_checkpointed_audit(ledger, (stale,))
        self.assertEqual(report.status, "UNKNOWN")
        self.assertEqual(report.reason, "latest_checkpoint_not_at_current_head")

    def test_checkpoint_prefix_mismatch_fails(self):
        ledger = self.make_ledger(2)
        foreign = self.checkpoint(self.make_ledger(1))
        # Same count, different event-chain head.
        different = append_event(
            AuditLedger(),
            event_id="evt_foreign_0000001",
            actor_ref="actor_opaque",
            device_ref="not_applicable",
            service_id="local_ipc",
            action="read_host_health",
            decision="UNKNOWN",
            result="SUCCEEDED",
            occurred_at=NOW,
            correlation_ref="req_foreign_000001",
        )
        wrong = self.checkpoint(different)
        report = verify_checkpointed_audit(ledger, (wrong,))
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.reason, "checkpoint_prefix_mismatch")

    def test_checkpoint_digest_tampering_fails(self):
        ledger = self.make_ledger(1)
        valid = self.checkpoint(ledger)
        from backend.audit_anchor import AuditCheckpoint
        tampered = AuditCheckpoint(
            schema_version=valid.schema_version,
            event_count=valid.event_count,
            head_hash=valid.head_hash,
            created_at=valid.created_at,
            checkpoint_hash="f" * 64,
        )
        report = verify_checkpointed_audit(ledger, (tampered,))
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(report.reason, "checkpoint_integrity_failed")

    def test_missing_checkpoint_is_unknown_for_full_verification(self):
        report = verify_checkpointed_audit(self.make_ledger(0), ())
        self.assertEqual(report.status, "UNKNOWN")
        self.assertEqual(report.reason, "checkpoint_evidence_missing")

    def test_empty_history_is_accepted_only_as_pre_append_state(self):
        report = verify_checkpointed_audit(
            self.make_ledger(1), (), require_current_head=False
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(report.reason, "no_prior_checkpoints")


if __name__ == "__main__":
    unittest.main()
