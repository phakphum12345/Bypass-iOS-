"""Phase 22 read-only inspection of a local SQLite audit database.

The inspector opens an existing database using SQLite read-only mode. It
never initializes schemas, writes, repairs, deletes, or exports event details.
"""
from __future__ import annotations

from contextlib import closing
from dataclasses import asdict, dataclass
from pathlib import Path
import sqlite3

from backend.audit_consistency import verify_checkpointed_audit
from backend.audit_checkpoint_store import SQLiteAuditCheckpointStore
from backend.audit_store import SQLiteAuditStore


@dataclass(frozen=True, slots=True)
class AuditInspectionReport:
    status: str
    ledger_event_count: int
    checkpoint_count: int
    verified_checkpoint_count: int
    latest_checkpoint_hash: str | None
    reason: str
    external_anchor_status: str = "UNKNOWN"
    storage_trust: str = "UNVERIFIED_LOCAL_DATABASE"


def inspect_audit_database(
    database_path: str | Path,
    *,
    require_current_head: bool = True,
) -> AuditInspectionReport:
    """Inspect an existing SQLite audit database without opening it for writes."""
    path = Path(database_path).expanduser()
    if not path.is_file():
        return AuditInspectionReport(
            "UNKNOWN", 0, 0, 0, None, "database_file_missing"
        )

    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, timeout=5.0)) as connection:
            connection.row_factory = sqlite3.Row
            ledger = SQLiteAuditStore._read(connection)
            checkpoints = SQLiteAuditCheckpointStore._read(connection)
        result = verify_checkpointed_audit(
            ledger, checkpoints, require_current_head=require_current_head
        )
        return AuditInspectionReport(
            status=result.status,
            ledger_event_count=result.ledger_event_count,
            checkpoint_count=result.checkpoint_count,
            verified_checkpoint_count=result.verified_checkpoint_count,
            latest_checkpoint_hash=result.latest_checkpoint_hash,
            reason=result.reason,
        )
    except (sqlite3.Error, OSError, ValueError, TypeError, RuntimeError):
        return AuditInspectionReport(
            "UNKNOWN", 0, 0, 0, None, "audit_database_unreadable_or_invalid"
        )


def report_as_dict(report: AuditInspectionReport) -> dict[str, object]:
    """Return a stable, non-sensitive summary suitable for JSON output."""
    return asdict(report)
