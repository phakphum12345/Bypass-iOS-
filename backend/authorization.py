"""Phase 4 server-side consent, policy and entitlement evaluation contracts.

Pure evaluator only: no HTTP route, provider integration, or device execution.
Evidence must come from trusted server-side providers, never client claims.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.identity import IdentityEvidence


@dataclass(frozen=True)
class OwnershipEvidence:
    status: str
    ownership_ref: str | None = None
    subject_ref: str | None = None
    device_ref: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class ConsentEvidence:
    status: str
    consent_ref: str | None = None
    subject_ref: str | None = None
    device_ref: str | None = None
    action: str | None = None
    granted_at: datetime | None = None
    expires_at: datetime | None = None
    revoked_at: datetime | None = None


@dataclass(frozen=True)
class PolicyEvidence:
    status: str
    policy_ref: str | None = None
    device_ref: str | None = None
    permitted_actions: tuple[str, ...] = ()
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class EntitlementEvidence:
    status: str
    entitlement_ref: str | None = None
    subject_ref: str | None = None
    service_id: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class AuthorizationDecision:
    status: str
    reason: str
    operation_performed: bool = False


def _aware(value: datetime | None) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _window_state(
    starts_at: datetime | None, ends_at: datetime | None, now: datetime
) -> str:
    if not _aware(starts_at) or not _aware(ends_at) or ends_at <= starts_at:
        return "UNKNOWN"
    if ends_at <= now:
        return "EXPIRED"
    if starts_at > now:
        return "NOT_YET_VALID"
    return "CURRENT"


def _unknown(reason: str) -> AuthorizationDecision:
    return AuthorizationDecision(status="UNKNOWN", reason=reason)


def _deny(reason: str) -> AuthorizationDecision:
    return AuthorizationDecision(status="DENY", reason=reason)


def evaluate_authorization(
    *,
    identity: IdentityEvidence | None,
    ownership: OwnershipEvidence | None,
    consent: ConsentEvidence | None,
    policy: PolicyEvidence | None,
    entitlement: EntitlementEvidence | None,
    device_ref: str,
    action: str,
    service_id: str,
    now: datetime | None = None,
) -> AuthorizationDecision:
    """Evaluate independent server-side evidence for one exact scoped request.

    ALLOW means eligible for a separate human-review/confirmation stage only.
    The live Decision API intentionally remains deny-only and never calls this.
    """
    current = now if now is not None else datetime.now(timezone.utc)
    if not _aware(current):
        return _unknown("invalid_evaluation_time")
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (device_ref, action, service_id)
    ):
        return _unknown("invalid_request_scope")

    if not isinstance(identity, IdentityEvidence):
        return _unknown("identity_not_verified")
    if identity.status in {"REVOKED", "EXPIRED"}:
        return _deny("identity_not_active")
    if identity.status != "VERIFIED":
        return _unknown("identity_not_verified")
    subject_ref = identity.subject_ref
    if any(
        not isinstance(value, str) or not value.strip()
        for value in (identity.issuer, subject_ref, identity.session_ref)
    ):
        return _unknown("identity_evidence_incomplete")
    identity_window = _window_state(identity.issued_at, identity.expires_at, current)
    if identity_window == "EXPIRED":
        return _deny("identity_session_expired")
    if identity_window != "CURRENT":
        return _unknown("identity_session_not_current")
    if (
        not _aware(identity.auth_time)
        or identity.auth_time > current
        or identity.auth_time < identity.issued_at
    ):
        return _unknown("identity_authentication_time_invalid")

    if not isinstance(ownership, OwnershipEvidence):
        return _unknown("device_ownership_unknown")
    if ownership.status in {"DENIED", "REVOKED", "EXPIRED"}:
        return _deny("device_ownership_not_verified")
    if ownership.status != "VERIFIED":
        return _unknown("device_ownership_unknown")
    ownership_window = _window_state(
        ownership.valid_from, ownership.valid_until, current
    )
    if ownership_window == "EXPIRED":
        return _deny("device_ownership_expired")
    if ownership_window != "CURRENT":
        return _unknown("device_ownership_not_current")
    if (
        ownership.subject_ref != subject_ref
        or ownership.device_ref != device_ref
        or not isinstance(ownership.ownership_ref, str)
        or not ownership.ownership_ref.strip()
    ):
        return _unknown("device_ownership_scope_mismatch")

    if not isinstance(consent, ConsentEvidence):
        return _unknown("consent_not_verified")
    if consent.status in {"REVOKED", "EXPIRED", "DENIED"}:
        return _deny("consent_not_active")
    if consent.status != "GRANTED":
        return _unknown("consent_not_verified")
    if consent.revoked_at is not None:
        return _deny("consent_revoked")
    consent_window = _window_state(consent.granted_at, consent.expires_at, current)
    if consent_window == "EXPIRED":
        return _deny("consent_expired")
    if consent_window != "CURRENT":
        return _unknown("consent_not_current")
    if (
        consent.subject_ref != subject_ref
        or consent.device_ref != device_ref
        or consent.action != action
        or not isinstance(consent.consent_ref, str)
        or not consent.consent_ref.strip()
    ):
        return _deny("consent_scope_mismatch")

    if not isinstance(policy, PolicyEvidence):
        return _unknown("policy_not_verified")
    if policy.status in {"DENY", "REVOKED", "EXPIRED"}:
        return _deny("policy_denies_request")
    if policy.status != "ACTIVE":
        return _unknown("policy_not_verified")
    policy_window = _window_state(policy.valid_from, policy.valid_until, current)
    if policy_window in {"EXPIRED", "NOT_YET_VALID"}:
        return _deny("policy_not_active")
    if policy_window != "CURRENT":
        return _unknown("policy_validity_unknown")
    if (
        policy.device_ref != device_ref
        or not isinstance(policy.permitted_actions, tuple)
        or any(not isinstance(item, str) for item in policy.permitted_actions)
        or action not in policy.permitted_actions
        or not isinstance(policy.policy_ref, str)
        or not policy.policy_ref.strip()
    ):
        return _deny("policy_scope_or_action_denied")

    if not isinstance(entitlement, EntitlementEvidence):
        return _unknown("entitlement_not_verified")
    if entitlement.status in {"INACTIVE", "EXPIRED", "REVOKED", "DENIED"}:
        return _deny("entitlement_not_active")
    if entitlement.status != "ACTIVE":
        return _unknown("entitlement_not_verified")
    entitlement_window = _window_state(
        entitlement.valid_from, entitlement.valid_until, current
    )
    if entitlement_window in {"EXPIRED", "NOT_YET_VALID"}:
        return _deny("entitlement_not_active")
    if entitlement_window != "CURRENT":
        return _unknown("entitlement_validity_unknown")
    if (
        entitlement.subject_ref != subject_ref
        or entitlement.service_id != service_id
        or not isinstance(entitlement.entitlement_ref, str)
        or not entitlement.entitlement_ref.strip()
    ):
        return _deny("entitlement_scope_mismatch")

    return AuthorizationDecision(
        status="ALLOW",
        reason=(
            "All required server-side evidence is current and scope-matched; "
            "eligible for separate review only. No operation was executed."
        ),
    )
