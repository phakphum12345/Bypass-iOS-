from datetime import datetime, timedelta, timezone
import unittest

from backend.ipc_peer_auth import (
    PeerEvidence,
    UnavailablePeerAuthenticator,
    resolve_peer,
)


NOW = datetime(2026, 11, 1, 12, 0, tzinfo=timezone.utc)
AUDIENCE = "host-agent-local-ipc"


class VerifiedAuthenticator:
    def __init__(self, evidence):
        self.evidence = evidence

    def verify_peer(self, connection_context, *, audience, now):
        self.connection_context = connection_context
        self.audience = audience
        self.now = now
        return self.evidence


def verified(**overrides):
    values = {
        "status": "VERIFIED",
        "transport": "unix_domain_socket",
        "principal_ref": "principal_opaque_123",
        "audience": AUDIENCE,
        "channel_binding_ref": "channel_opaque_456",
        "authenticated_at": NOW - timedelta(minutes=1),
        "expires_at": NOW + timedelta(minutes=5),
        "source": "test_os_adapter",
    }
    values.update(overrides)
    return PeerEvidence(**values)


class PeerAuthContractTests(unittest.TestCase):
    def test_unavailable_default_is_unknown(self):
        result = resolve_peer(
            UnavailablePeerAuthenticator(), object(), audience=AUDIENCE, now=NOW
        )
        self.assertEqual(result.status, "UNKNOWN")
        self.assertEqual(result.source, "no_peer_authenticator")

    def test_valid_evidence_is_returned_and_bound_to_context(self):
        context = object()
        provider = VerifiedAuthenticator(verified())
        result = resolve_peer(provider, context, audience=AUDIENCE, now=NOW)
        self.assertEqual(result.status, "VERIFIED")
        self.assertIs(provider.connection_context, context)
        self.assertEqual(provider.audience, AUDIENCE)

    def test_missing_provider_or_context_fails_closed(self):
        self.assertEqual(
            resolve_peer(None, object(), audience=AUDIENCE, now=NOW).status,
            "UNKNOWN",
        )
        self.assertEqual(
            resolve_peer(VerifiedAuthenticator(verified()), None,
                         audience=AUDIENCE, now=NOW).status,
            "UNKNOWN",
        )

    def test_provider_exception_and_malformed_result_fail_closed(self):
        class Broken:
            def verify_peer(self, *args, **kwargs):
                raise RuntimeError("secret detail must not escape")

        class Malformed:
            def verify_peer(self, *args, **kwargs):
                return {"status": "VERIFIED"}

        for provider in (Broken(), Malformed()):
            self.assertEqual(
                resolve_peer(provider, object(), audience=AUDIENCE, now=NOW).status,
                "UNKNOWN",
            )

    def test_revoked_and_expired_statuses_are_not_verified(self):
        for status in ("REVOKED", "EXPIRED"):
            result = resolve_peer(
                VerifiedAuthenticator(PeerEvidence(status=status)),
                object(), audience=AUDIENCE, now=NOW,
            )
            self.assertEqual(result.status, status)

    def test_wrong_transport_audience_or_missing_binding_fails_closed(self):
        cases = (
            {"transport": "tcp"},
            {"audience": "other-service"},
            {"channel_binding_ref": None},
            {"principal_ref": " "},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                result = resolve_peer(
                    VerifiedAuthenticator(verified(**changes)),
                    object(), audience=AUDIENCE, now=NOW,
                )
                self.assertEqual(result.status, "UNKNOWN")

    def test_future_naive_and_expired_timestamps_fail_closed(self):
        cases = (
            {"authenticated_at": NOW + timedelta(seconds=1)},
            {"authenticated_at": datetime(2026, 11, 1, 11, 0)},
            {"expires_at": NOW},
            {"expires_at": NOW - timedelta(seconds=1)},
        )
        for changes in cases:
            with self.subTest(changes=changes):
                result = resolve_peer(
                    VerifiedAuthenticator(verified(**changes)),
                    object(), audience=AUDIENCE, now=NOW,
                )
                self.assertIn(result.status, {"UNKNOWN", "EXPIRED"})

    def test_invalid_expected_audience_and_evaluation_time(self):
        provider = VerifiedAuthenticator(verified())
        self.assertEqual(
            resolve_peer(provider, object(), audience=" ", now=NOW).status,
            "UNKNOWN",
        )
        self.assertEqual(
            resolve_peer(provider, object(), audience=AUDIENCE,
                         now=datetime(2026, 11, 1, 12, 0)).status,
            "UNKNOWN",
        )


if __name__ == "__main__":
    unittest.main()
