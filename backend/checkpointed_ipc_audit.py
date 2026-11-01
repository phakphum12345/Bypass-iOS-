"""Phase 20 checkpointed durable local IPC audit orchestration.

This is an in-process wrapper only. It adds no transport listener and grants
no authority to perform device operations. A read result is withheld unless
both the durable event ledger and its corresponding checkpoint are persisted.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Mapping

from backend.audit_anchor import GENESIS_HASH, AuditCheckpoint, create_audit_checkpoint
from backend.audit_checkpoint_store import (
    AuditCheckpointStoreError,
    SQLiteAuditCheckpointStore,
)
from backend.audit_evidence import AuditLedger
from backend.audit_store import SQLiteAuditStore
from backend.agent_lifecycle import AgentLifecycle
from backend.host_diagnostics import collect_host_diagnostics
from backend.ipc_dispatcher import (
    SERVICE_AUDIENCE,
    dispatch_local_ipc_request_with_durable_audit,
)
from backend.ipc_peer_auth import PeerAuthenticator


def _checkpoint_history_matches_ledger(
    checkpoints: tuple[AuditCheckpoint, ...], ledger: AuditLedger
) -> bool:
    """Require every stored checkpoint to identify the exact ledger prefix."""
    for checkpoint in checkpoints:
        if checkpoint.event_count > len(ledger.events):
            return False
        expected_head = (
            ledger.events[checkpoint.event_count - 1].event_hash
            if checkpoint.event_count
            else GENESIS_HASH
        )
        if checkpoint.head_hash != expected_head:
            return False
    return True


def dispatch_local_ipc_request_with_checkpointed_audit(
    raw: bytes,
    *,
    authenticator: PeerAuthenticator | None,
    connection_context: object,
    audit_store: SQLiteAuditStore,
    checkpoint_store: SQLiteAuditCheckpointStore,
    event_id: str,
    occurred_at: datetime,
    lifecycle: AgentLifecycle | None = None,
    diagnostics_provider: Callable[[], Mapping[str, Any]] = collect_host_diagnostics,
    audience: str = SERVICE_AUDIENCE,
    now: datetime | None = None,
) -> tuple[dict[str, Any], AuditLedger | None, AuditCheckpoint | None]:
    """Persist an IPC outcome and matching checkpoint before returning a read.

    The caller initializes both stores and owns their lifecycle. If event audit
    fails, no result is returned. If checkpoint persistence or reconciliation
    fails after the event is persisted, the response explicitly reports that
    the event is recorded but the checkpoint is not, and suppresses read data.
    """
    response, ledger = dispatch_local_ipc_request_with_durable_audit(
        raw,
        authenticator=authenticator,
        connection_context=connection_context,
        store=audit_store,
        event_id=event_id,
        occurred_at=occurred_at,
        lifecycle=lifecycle,
        diagnostics_provider=diagnostics_provider,
        audience=audience,
        now=now,
    )
    if not response.get("audit_recorded") or ledger is None:
        response["checkpoint_recorded"] = False
        return response, ledger, None

    try:
        history = checkpoint_store.load()
        if not _checkpoint_history_matches_ledger(history, ledger):
            raise AuditCheckpointStoreError("checkpoint_ledger_mismatch")
        checkpoint = create_audit_checkpoint(ledger, created_at=occurred_at)
        checkpoint_store.append(checkpoint)
        response["checkpoint_recorded"] = True
        response["checkpoint_hash"] = checkpoint.checkpoint_hash
        return response, ledger, checkpoint
    except Exception:
        # The event is durable, but the checkpoint guarantee is not met.
        # Do not return potentially sensitive host-read data in this state.
        response.pop("result", None)
        response["status"] = "AUDIT_CHECKPOINT_FAILED"
        response["audit_recorded"] = True
        response["checkpoint_recorded"] = False
        response["error"] = "audit_checkpoint_unavailable"
        return response, ledger, None
