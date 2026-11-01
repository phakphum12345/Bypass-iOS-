import unittest
from datetime import datetime, timedelta, timezone

from backend.identity import (
    IdentityEvidence,
    UnavailableIdentityProvider,
    resolve_identity,
)

NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)


class FakeProvider:
    def __init__(self, evidence=None, error=None):
        self.evidence = evidence
        self.error = error
        self.received_token = None

    def resolve_bearer_session(self, bearer_token, *, now):
        self.received_token = bearer_token
        if self.error:
            raise self.error
        return self.evidence


def verified(**overrides):
    values = {
        "status": "VERIFIED",
        "issuer": "https://identity.example.test",
        "subject_ref": "usr_opaque_123",
        "session_ref": "ses_opaque_123",
        "issued_at": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(minutes=10),
        "auth_time": NOW - timedelta(minutes=5),
        "assurance": "mfa",
        "source": "test_trusted_provider",
    }
    values.update(overrides)
    return IdentityEvidence(**values)


class IdentityResolutionTests(unittest.TestCase):
    def test_default_provider_never_verifies_identity(self):
        result = resolve_identity(
            UnavailableIdentityProvider(), "Bearer secret-token", now=NOW
        )
        self.assertEqual(result.status, "UNKNOWN")
        self.assertEqual(result.source, "no_trusted_identity_provider")

    def test_missing_or_malformed_bearer_header_fails_closed(self):
        for header in (None, "", "Basic abc", "Bearer", "Bearer a b"):
            with self.subTest(header=header):
                self.assertEqual(resolve_identity(FakeProvider(verified()), header, now=NOW).status, "UNKNOWN")

    def test_verified_identity_requires_trusted_provider_evidence(self):
        provider = FakeProvider(verified())
        result = resolve_identity(provider, "Bearer session-secret", now=NOW)
        self.assertEqual(result.status, "VERIFIED")
        self.assertEqual(result.subject_ref, "usr_opaque_123")
        self.assertEqual(provider.received_token, "session-secret")
        self.assertNotIn("session-secret", repr(result))

    def test_revoked_session_is_never_verified(self):
        result = resolve_identity(
            FakeProvider(IdentityEvidence(status="REVOKED", source="trusted")),
            "Bearer token",
            now=NOW,
        )
        self.assertEqual(result.status, "REVOKED")
        self.assertIsNone(result.subject_ref)

    def test_expired_session_is_never_verified(self):
        result = resolve_identity(
            FakeProvider(verified(expires_at=NOW - timedelta(seconds=1))),
            "Bearer token",
            now=NOW,
        )
        self.assertEqual(result.status, "EXPIRED")

    def test_missing_subject_or_session_reference_fails_closed(self):
        for field in ("issuer", "subject_ref", "session_ref"):
            with self.subTest(field=field):
                result = resolve_identity(
                    FakeProvider(verified(**{field: None})),
                    "Bearer token",
                    now=NOW,
                )
                self.assertEqual(result.status, "UNKNOWN")

    def test_missing_or_naive_timestamps_fail_closed(self):
        result = resolve_identity(
            FakeProvider(verified(expires_at=None)), "Bearer token", now=NOW
        )
        self.assertEqual(result.status, "UNKNOWN")
        result = resolve_identity(
            FakeProvider(verified(auth_time=NOW.replace(tzinfo=None))),
            "Bearer token",
            now=NOW,
        )
        self.assertEqual(result.status, "UNKNOWN")

    def test_future_and_inconsistent_timestamps_fail_closed(self):
        for evidence in (
            verified(issued_at=NOW + timedelta(seconds=1)),
            verified(auth_time=NOW + timedelta(seconds=1)),
            verified(expires_at=NOW - timedelta(seconds=1)),
            verified(auth_time=NOW - timedelta(days=2)),
        ):
            result = resolve_identity(FakeProvider(evidence), "Bearer token", now=NOW)
            self.assertIn(result.status, {"UNKNOWN", "EXPIRED"})

    def test_provider_exception_or_unexpected_response_fails_closed(self):
        for provider in (FakeProvider(error=RuntimeError("secret")), FakeProvider(object())):
            result = resolve_identity(provider, "Bearer token", now=NOW)
            self.assertEqual(result.status, "UNKNOWN")
            self.assertNotIn("secret", repr(result))

    def test_client_claims_are_not_an_identity_input(self):
        # The resolver accepts only a provider and Authorization header; it has
        # no parameter for client-supplied roles, ownership, or org membership.
        self.assertEqual(
            resolve_identity(None, "Bearer token", now=NOW).status,
            "UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
