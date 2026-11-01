import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from backend.authorization import (
    ConsentEvidence,
    EntitlementEvidence,
    OwnershipEvidence,
    PolicyEvidence,
    evaluate_authorization,
)
from backend.identity import IdentityEvidence

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
SUBJECT = "usr_opaque_123"
DEVICE = "dev_opaque_123"
ACTION = "read_diagnostics"
SERVICE = "device_diagnostics"


def evidence_set():
    return {
        "identity": IdentityEvidence(
            status="VERIFIED",
            issuer="https://identity.example.test",
            subject_ref=SUBJECT,
            session_ref="ses_opaque_123",
            issued_at=NOW - timedelta(minutes=5),
            expires_at=NOW + timedelta(minutes=10),
            auth_time=NOW - timedelta(minutes=5),
            source="trusted_test_provider",
        ),
        "ownership": OwnershipEvidence(
            status="VERIFIED",
            ownership_ref="own_opaque_123",
            subject_ref=SUBJECT,
            device_ref=DEVICE,
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
        "consent": ConsentEvidence(
            status="GRANTED",
            consent_ref="con_opaque_123",
            subject_ref=SUBJECT,
            device_ref=DEVICE,
            action=ACTION,
            granted_at=NOW - timedelta(minutes=2),
            expires_at=NOW + timedelta(minutes=5),
        ),
        "policy": PolicyEvidence(
            status="ACTIVE",
            policy_ref="pol_opaque_123",
            device_ref=DEVICE,
            permitted_actions=(ACTION,),
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
        "entitlement": EntitlementEvidence(
            status="ACTIVE",
            entitlement_ref="ent_opaque_123",
            subject_ref=SUBJECT,
            service_id=SERVICE,
            valid_from=NOW - timedelta(days=1),
            valid_until=NOW + timedelta(days=1),
        ),
    }


def evaluate(**overrides):
    values = evidence_set()
    values.update(overrides)
    return evaluate_authorization(
        **values, device_ref=DEVICE, action=ACTION, service_id=SERVICE, now=NOW
    )


class AuthorizationEvidenceTests(unittest.TestCase):
    def test_all_current_scope_matched_server_evidence_is_eligible(self):
        result = evaluate()
        self.assertEqual(result.status, "ALLOW")
        self.assertFalse(result.operation_performed)

    def test_missing_provider_evidence_is_unknown(self):
        for key in ("identity", "ownership", "consent", "policy", "entitlement"):
            with self.subTest(key=key):
                self.assertEqual(evaluate(**{key: None}).status, "UNKNOWN")

    def test_identity_must_be_verified_and_current(self):
        values = evidence_set()
        self.assertEqual(
            evaluate(identity=replace(values["identity"], status="UNKNOWN")).status,
            "UNKNOWN",
        )
        self.assertEqual(
            evaluate(identity=replace(values["identity"], status="REVOKED")).status,
            "DENY",
        )
        self.assertEqual(
            evaluate(identity=replace(
                values["identity"], expires_at=NOW - timedelta(seconds=1)
            )).status,
            "UNKNOWN",
        )

    def test_ownership_must_match_subject_device_and_time(self):
        values = evidence_set()
        cases = (
            replace(values["ownership"], subject_ref="another_user"),
            replace(values["ownership"], device_ref="another_device"),
            replace(values["ownership"], valid_until=NOW),
            replace(values["ownership"], status="UNKNOWN"),
        )
        for ownership in cases:
            with self.subTest(ownership=ownership):
                self.assertEqual(evaluate(ownership=ownership).status, "UNKNOWN")

    def test_consent_is_action_specific_time_bounded_and_revocable(self):
        values = evidence_set()
        cases = (
            replace(values["consent"], action="erase_device"),
            replace(values["consent"], device_ref="another_device"),
            replace(values["consent"], expires_at=NOW),
            replace(values["consent"], revoked_at=NOW - timedelta(seconds=1)),
            replace(values["consent"], status="REVOKED"),
        )
        for consent in cases:
            with self.subTest(consent=consent):
                self.assertEqual(evaluate(consent=consent).status, "DENY")

    def test_policy_must_allow_exact_action_and_device(self):
        values = evidence_set()
        cases = (
            replace(values["policy"], permitted_actions=("other_action",)),
            replace(values["policy"], device_ref="another_device"),
            replace(values["policy"], valid_until=NOW),
            replace(values["policy"], status="DENY"),
        )
        for policy in cases:
            with self.subTest(policy=policy):
                self.assertEqual(evaluate(policy=policy).status, "DENY")

    def test_entitlement_must_match_subject_service_and_time(self):
        values = evidence_set()
        cases = (
            replace(values["entitlement"], subject_ref="another_user"),
            replace(values["entitlement"], service_id="other_service"),
            replace(values["entitlement"], valid_until=NOW),
            replace(values["entitlement"], status="EXPIRED"),
        )
        for entitlement in cases:
            with self.subTest(entitlement=entitlement):
                self.assertEqual(evaluate(entitlement=entitlement).status, "DENY")

    def test_naive_evaluation_time_fails_closed(self):
        values = evidence_set()
        result = evaluate_authorization(
            **values,
            device_ref=DEVICE,
            action=ACTION,
            service_id=SERVICE,
            now=NOW.replace(tzinfo=None),
        )
        self.assertEqual(result.status, "UNKNOWN")

    def test_invalid_request_scope_fails_closed(self):
        values = evidence_set()
        result = evaluate_authorization(
            **values, device_ref=" ", action=ACTION, service_id=SERVICE, now=NOW
        )
        self.assertEqual(result.status, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
