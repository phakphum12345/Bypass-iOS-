"""Map local IPC outcomes to the existing immutable audit evidence ledger.

This adapter records metadata only. It never stores request bodies, diagnostic
reports, credentials, raw device identifiers, or exception details. The
underlying AuditLedger remains in-memory and is not a durable audit service.
"""
from __future__ import annotations

from datetime import datetime

from backend.audit_evidence import AuditLedger, append_event
from backend.ipc_peer_auth import PeerEvidence

_SERVICE_ID = "local_ipc"
_HOST_SCOPE_REF = "not_applicable"
_UNKNOWN_ACTOR_REF = "peer_unknown"
_ALLOWED_METHODS = {
    "host.health.read": "read_host_health",
    "host.diagnostics.read": "read_host_diagnostics",
}
_ALLOWED_RESPONSE_RESULTS = {
    "OK": "SUCCEEDED",
    "ERROR": "FAILED",
    "DENIED": "NOT_RUN",
    "INVALID_REQUEST": "NOT_RUN",
}


def append_ipc_audit_event(
    ledger: AuditLedger,
    *,
    event_id: str,
    peer: PeerEvidence | None,
    request_id: str | None,
    method: str | None,
    response_status: str,
    occurred_at: datetime,
) -> AuditLedger:
    """Return a new ledger with one metadata-only IPC outcome event.

    peer must be the result of the server-side resolve_peer call, never
    a value reconstructed from the request envelope. The audit decision is
    always UNKNOWN: local peer verification is not device-operation authority.
    """
    if response_status not in _ALLOWED_RESPONSE_RESULTS:
        raise ValueError("unsupported_ipc_response_status")

    actor_ref = _UNKNOWN_ACTOR_REF
    if (
        isinstance(peer, PeerEvidence)
        and peer.status == "VERIFIED"
        and isinstance(peer.principal_ref, str)
    ):
        actor_ref = peer.principal_ref

    correlation_ref = (
        request_id
        if isinstance(request_id, str)
        and 16 <= len(request_id) <= 80
        and all(char.isalnum() or char in "_-" for char in request_id)
        else event_id
    )
    action = _ALLOWED_METHODS.get(method, "request_rejected")

    return append_event(
        ledger,
        event_id=event_id,
        actor_ref=actor_ref,
        device_ref=_HOST_SCOPE_REF,
        service_id=_SERVICE_ID,
        action=action,
        decision="UNKNOWN",
        result=_ALLOWED_RESPONSE_RESULTS[response_status],
        occurred_at=occurred_at,
        correlation_ref=correlation_ref,
    )
