#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools/codegen/generate.py"


def inspect_generator() -> dict[str, Any]:
    return {
        "available": GENERATOR.is_file(),
        "path": str(GENERATOR.relative_to(ROOT)),
        "supported_phase": 5,
        "mutating": True,
        "supports_dry_run": True,
        "supports_file_scoping": True,
        "supports_phase_selection": True,
    }


def run_generator(
    phase_id: int,
    dry_run: bool = True,
    files: list[str] | None = None,
) -> dict[str, Any]:
    if phase_id != 5:
        return {
            "passed": False,
            "error": (
                "Generator adapter only permits the existing "
                "deterministic Phase 5 generator."
            ),
            "command": [],
            "output": "",
        }

    if not GENERATOR.is_file():
        return {
            "passed": False,
            "error": "Generator not found.",
            "command": [],
            "output": "",
        }

    command = [
        "python3",
        str(GENERATOR.relative_to(ROOT)),
        "--phase",
        str(phase_id),
    ]

    if dry_run:
        command.append("--dry-run")

    if files:
        command.append("--files")
        command.extend(files)

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return {
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "command": command,
        "output": result.stdout,
        "dry_run": dry_run,
        "phase": phase_id,
        "files": files or [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded generator adapter"
    )
    parser.add_argument(
        "--inspect",
        action="store_true",
    )
    parser.add_argument(
        "--phase",
        type=int,
        default=5,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
    )
    parser.add_argument(
        "--files",
        nargs="*",
        default=None,
    )
    args = parser.parse_args()

    if args.inspect:
        print(inspect_generator())
        return 0

    result = run_generator(
        phase_id=args.phase,
        dry_run=args.dry_run,
        files=args.files,
    )

    print(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
