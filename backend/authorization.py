"""Phase 4 server-side consent, policy and entitlement evaluation contracts.

This module is a pure evaluator, not an HTTP endpoint or execution engine.
Evidence objects must be produced by trusted server-side providers; callers
must never construct them from client-submitted claims. Missing providers,
untrusted/incomplete evidence, stale timestamps, and scope mismatches fail
closed. A successful result means only that the request is eligible for a
separate authorization/confirmation workflow; it never performs an operation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from backend.identity import IdentityEvidence


@dataclass(frozen=True)
class OwnershipEvidence:
    """Trusted ownership-provider result; references are opaque and non-secret."""

    status: str
    ownership_ref: str | None = None
    subject_ref: str | None = None
    device_ref: str | None = None
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class ConsentEvidence:
    """Explicit, action-specific, revocable device-owner consent."""

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
    """Organization/device policy snapshot returned by a trusted policy source."""

    status: str
    policy_ref: str | None = None
    device_ref: str | None = None
    permitted_actions: tuple[str, ...] = ()
    valid_from: datetime | None = None
    valid_until: datetime | None = None


@dataclass(frozen=True)
class EntitlementEvidence:
    """Server-verified product/service entitlement; never a client plan flag."""

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


def _window_is_current(
    starts_at: datetime | None, ends_at: datetime | None, now: datetime
) -> bool:
    return (
        _aware(starts_at)
        and _aware(ends_at)
        and starts_at <= now < ends_at
        and ends_at > starts_at
    )


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

    No request-body roles, ownership flags, consent booleans, policy overrides,
    or entitlement claims are accepted. The existing Decision API intentionally
    remains deny-only and does not call this evaluator.
    """
    current = now or datetime.now(timezone.utc)
    if not _aware(current):
        return _unknown("invalid_evaluation_time")
    if any(not isinstance(value, str) or not value.strip()
           for value in (device_ref, action, service_id)):
        return _unknown("invalid_request_scope")

    if identity is None or identity.status != "VERIFIED":
        if identity is not None and identity.status in {"REVOKED", "EXPIRED"}:
            return _deny("identity_not_active")
        return _unknown("identity_not_verified")
    subject_ref = identity.subject_ref
    if not isinstance(subject_ref, str) or not subject_ref.strip():
        return _unknown("identity_subject_missing")
    if not _window_is_current(identity.issued_at, identity.expires_at, current):
        return _unknown("identity_session_not_current")
    if not _aware(identity.auth_time) or identity.auth_time > current:
        return _unknown("identity_authentication_time_invalid")

    if ownership is None or ownership.status != "VERIFIED":
        if ownership is not None and ownership.status in {"DENIED", "REVOKED", "EXPIRED"}:
            return _deny("device_ownership_not_verified")
        return _unknown("device_ownership_unknown")
    if (
        ownership.subject_ref != subject_ref
        or ownership.device_ref != device_ref
        or not ownership.ownership_ref
        or not _window_is_current(ownership.valid_from, ownership.valid_until, current)
    ):
        return _unknown("device_ownership_scope_or_validity_mismatch")

    if consent is None or consent.status != "GRANTED":
        if consent is not None and consent.status in {"REVOKED", "EXPIRED", "DENIED"}:
            return _deny("consent_not_active")
        return _unknown("consent_not_verified")
    if consent.revoked_at is not None:
        return _deny("consent_revoked")
    if (
        consent.subject_ref != subject_ref
        or consent.device_ref != device_ref
        or consent.action != action
        or not consent.consent_ref
        or not _window_is_current(consent.granted_at, consent.expires_at, current)
    ):
        return _unknown("consent_scope_or_validity_mismatch")

    if policy is None or policy.status != "ACTIVE":
        if policy is not None and policy.status in {"DENY", "REVOKED", "EXPIRED"}:
            return _deny("policy_denies_request")
        return _unknown("policy_not_verified")
    if (
        policy.device_ref != device_ref
        or action not in policy.permitted_actions
        or not policy.policy_ref
        or not _window_is_current(policy.valid_from, policy.valid_until, current)
    ):
        return _deny("policy_scope_or_action_denied")

    if entitlement is None or entitlement.status != "ACTIVE":
        if entitlement is not None and entitlement.status in {
            "INACTIVE", "EXPIRED", "REVOKED", "DENIED"
        }:
            return _deny("entitlement_not_active")
        return _unknown("entitlement_not_verified")
    if (
        entitlement.subject_ref != subject_ref
        or entitlement.service_id != service_id
        or not entitlement.entitlement_ref
        or not _window_is_current(
            entitlement.valid_from, entitlement.valid_until, current
        )
    ):
        return _deny("entitlement_scope_or_validity_mismatch")

    return AuthorizationDecision(
        status="ALLOW",
        reason="All required server-side evidence is current and scope-matched; no operation was executed.",
    )
