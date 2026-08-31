#!/usr/bin/env python3

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools/codegen/generate.py"


def run_generator() -> dict[str, Any]:
    result = subprocess.run(
        ["python3", str(GENERATOR)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    return {
        "command": ["python3", str(GENERATOR.relative_to(ROOT))],
        "returncode": result.returncode,
        "passed": result.returncode == 0,
        "output": result.stdout,
    }


def inspect_generator() -> dict[str, Any]:
    if not GENERATOR.is_file():
        return {
            "available": False,
            "reason": "generator_missing",
        }

    return {
        "available": True,
        "path": str(GENERATOR.relative_to(ROOT)),
        "mutating": True,
        "supports_dry_run": False,
        "supports_phase_selection": False,
        "writes_manifest": True,
        "writes_templates": True,
    }


if __name__ == "__main__":
    print(inspect_generator())
