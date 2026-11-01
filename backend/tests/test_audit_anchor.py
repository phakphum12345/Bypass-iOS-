import unittest
from datetime import datetime, timedelta, timezone

from backend.audit_evidence import AuditLedger, append_event
from backend.audit_anchor import (
    AnchorEvidence,
    create_audit_checkpoint,
    resolve_audit_anchor,
    verify_anchor_evidence,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class StaticProvider:
    def __init__(self, evidence=None, error=None):
        self.evidence, self.error = evidence, error
        self.calls = 0

    def verify_checkpoint(self, checkpoint, *, now):
        self.calls += 1
        if self.error:
            raise self.error
        return self.evidence


class AuditCheckpointAnchorTests(unittest.TestCase):
    def setUp(self):
        self.ledger = append_event(
            AuditLedger(),
            event_id="evt_0000000000000001",
            actor_ref="actor_opaque",
            device_ref="not_applicable",
            service_id="local_ipc",
            action="read_host_health",
            decision="UNKNOWN",
            result="SUCCEEDED",
            occurred_at=NOW,
            correlation_ref="req_0000000000000001",
        )
        self.checkpoint = create_audit_checkpoint(self.ledger, created_at=NOW)

    def evidence(self, **changes):
        values = {
            "status": "VERIFIED",
            "provider_ref": "provider_external",
            "anchor_ref": "anchor_opaque_001",
            "checkpoint_hash": self.checkpoint.checkpoint_hash,
            "verified_at": NOW.isoformat().replace("+00:00", "Z"),
            "expires_at": (NOW + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
        }
        values.update(changes)
        return AnchorEvidence(**values)

    def test_checkpoint_binds_event_count_and_head_hash(self):
        self.assertEqual(self.checkpoint.event_count, 1)
        self.assertEqual(self.checkpoint.head_hash, self.ledger.events[-1].event_hash)
        self.assertEqual(len(self.checkpoint.checkpoint_hash), 64)

    def test_empty_ledger_uses_genesis_hash(self):
        checkpoint = create_audit_checkpoint(AuditLedger(), created_at=NOW)
        self.assertEqual(checkpoint.event_count, 0)
        self.assertEqual(checkpoint.head_hash, "0" * 64)

    def test_default_missing_provider_is_unknown(self):
        result = resolve_audit_anchor(self.checkpoint, provider=None, now=NOW)
        self.assertEqual(result.status, "UNKNOWN")

    def test_valid_external_evidence_is_verified(self):
        result = resolve_audit_anchor(
            self.checkpoint, provider=StaticProvider(self.evidence()), now=NOW
        )
        self.assertEqual(result.status, "VERIFIED")
        self.assertEqual(result.checkpoint_hash, self.checkpoint.checkpoint_hash)

    def test_provider_exception_is_unknown(self):
        result = resolve_audit_anchor(
            self.checkpoint, provider=StaticProvider(error=RuntimeError()), now=NOW
        )
        self.assertEqual(result.status, "UNKNOWN")

    def test_mismatched_checkpoint_is_unknown(self):
        evidence = self.evidence(checkpoint_hash="f" * 64)
        result = verify_anchor_evidence(self.checkpoint, evidence, now=NOW)
        self.assertEqual(result.status, "UNKNOWN")

    def test_expired_evidence_is_unknown(self):
        evidence = self.evidence(
            expires_at=(NOW - timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        )
        self.assertEqual(verify_anchor_evidence(self.checkpoint, evidence, now=NOW).status, "UNKNOWN")

    def test_future_verification_is_unknown(self):
        evidence = self.evidence(
            verified_at=(NOW + timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        )
        self.assertEqual(verify_anchor_evidence(self.checkpoint, evidence, now=NOW).status, "UNKNOWN")

    def test_tampered_checkpoint_digest_is_unknown(self):
        tampered = type(self.checkpoint)(
            schema_version=1, event_count=99, head_hash=self.checkpoint.head_hash,
            created_at=self.checkpoint.created_at,
            checkpoint_hash=self.checkpoint.checkpoint_hash,
        )
        self.assertEqual(
            verify_anchor_evidence(tampered, self.evidence(), now=NOW).status,
            "UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
