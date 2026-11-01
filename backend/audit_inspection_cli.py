"""Command-line entry point for read-only audit database inspection."""
from __future__ import annotations

import argparse
import json
import sys

from backend.audit_inspection import inspect_audit_database, report_as_dict


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify local audit ledger/checkpoint consistency (read-only)."
    )
    parser.add_argument("--database", required=True, help="Existing SQLite audit database")
    parser.add_argument(
        "--allow-stale-checkpoint",
        action="store_true",
        help="Verify stored checkpoint prefixes without requiring the latest to cover the current ledger head",
    )
    args = parser.parse_args(argv)
    report = inspect_audit_database(
        args.database,
        require_current_head=not args.allow_stale_checkpoint,
    )
    print(json.dumps(report_as_dict(report), sort_keys=True, separators=(",", ":")))
    if report.status == "PASS":
        return 0
    if report.status == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
