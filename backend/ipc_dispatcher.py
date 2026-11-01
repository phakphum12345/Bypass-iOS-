"""In-process dispatcher for the narrow, authenticated local IPC contract.

This is not a transport server. Callers must supply an opaque, server-owned
connection context from a future OS-native IPC adapter. The default peer
authenticator is unavailable, so requests are denied until a trusted adapter
is explicitly provided.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping

from backend.agent_lifecycle import AgentLifecycle
from backend.host_diagnostics import collect_host_diagnostics
from backend.audit_evidence import AuditLedger
from backend.ipc_audit import append_ipc_audit_event
from backend.ipc_peer_auth import PeerAuthenticator, PeerEvidence, resolve_peer
from backend.local_ipc_contract import IPCContractError, validate_request_bytes

SERVICE_AUDIENCE = "host-agent-local-ipc"


def _response(
    request_id: str | None,
    *,
    status: str,
    peer_status: str,
    result: Mapping[str, Any] | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    response: dict[str, Any] = {
        "schema_version": "1.0",
        "request_id": request_id,
        "status": status,
        "peer_status": peer_status,
        "authorization_granted": False,
        "device_operation_performed": False,
    }
    if result is not None:
        response["result"] = dict(result)
    if error is not None:
        response["error"] = error
    return response


def dispatch_local_ipc_request(
    raw: bytes,
    *,
    authenticator: PeerAuthenticator | None,
    connection_context: object,
    lifecycle: AgentLifecycle | None = None,
    diagnostics_provider: Callable[[], Mapping[str, Any]] = collect_host_diagnostics,
    audience: str = SERVICE_AUDIENCE,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Validate, authenticate, then dispatch one allowlisted read-only request.

    The function intentionally does not create a connection context, infer
    identity, or accept identity/authority data from the JSON envelope.
    """
    try:
        request = validate_request_bytes(raw)
    except IPCContractError as exc:
        return _response(
            None,
            status="INVALID_REQUEST",
            peer_status="NOT_CHECKED",
            error=str(exc),
        )

    peer = resolve_peer(
        authenticator,
        connection_context,
        audience=audience,
        now=now,
    )
    if peer.status != "VERIFIED":
        return _response(
            request["request_id"],
            status="DENIED",
            peer_status=peer.status,
            error="peer_not_verified",
        )

    try:
        if request["method"] == "host.health.read":
            report = (lifecycle or AgentLifecycle()).health()
        elif request["method"] == "host.diagnostics.read":
            report = diagnostics_provider()
            if not isinstance(report, Mapping):
                raise TypeError("diagnostics_provider_must_return_mapping")
        else:
            # The request validator should make this unreachable. Keep a
            # second server-side allowlist at the dispatch boundary.
            return _response(
                request["request_id"],
                status="DENIED",
                peer_status=peer.status,
                error="method_not_allowed",
            )
    except Exception:
        return _response(
            request["request_id"],
            status="ERROR",
            peer_status=peer.status,
            error="read_provider_unavailable",
        )

    return _response(
        request["request_id"],
        status="OK",
        peer_status=peer.status,
        result=report,
    )



class _CapturingAuthenticator:
    """Capture the resolver's validated peer result without re-verifying a peer."""

    def __init__(self, authenticator: PeerAuthenticator | None) -> None:
        self._authenticator = authenticator
        self.evidence: PeerEvidence | None = None

    def verify_peer(
        self, connection_context: object, *, audience: str, now: datetime
    ) -> PeerEvidence:
        self.evidence = resolve_peer(
            self._authenticator,
            connection_context,
            audience=audience,
            now=now,
        )
        return self.evidence


def dispatch_local_ipc_request_with_audit(
    raw: bytes,
    *,
    authenticator: PeerAuthenticator | None,
    connection_context: object,
    ledger: AuditLedger,
    event_id: str,
    occurred_at: datetime,
    lifecycle: AgentLifecycle | None = None,
    diagnostics_provider: Callable[[], Mapping[str, Any]] = collect_host_diagnostics,
    audience: str = SERVICE_AUDIENCE,
    now: datetime | None = None,
) -> tuple[dict[str, Any], AuditLedger]:
    """Dispatch once and return the corresponding metadata-only audit ledger.

    The wrapper captures the validated server-side peer evidence through a
    proxy, so the underlying OS/provider verifier is called at most once.
    Invalid envelopes are still audited with an unknown actor and no request
    correlation data. The caller owns the returned immutable ledger.
    """
    capturing = _CapturingAuthenticator(authenticator)
    response = dispatch_local_ipc_request(
        raw,
        authenticator=capturing,
        connection_context=connection_context,
        lifecycle=lifecycle,
        diagnostics_provider=diagnostics_provider,
        audience=audience,
        now=now,
    )
    try:
        request = validate_request_bytes(raw)
        request_id = request["request_id"]
        method = request["method"]
    except IPCContractError:
        request_id = None
        method = None

    updated_ledger = append_ipc_audit_event(
        ledger,
        event_id=event_id,
        peer=capturing.evidence,
        request_id=request_id,
        method=method,
        response_status=response["status"],
        occurred_at=occurred_at,
    )
    return response, updated_ledger
