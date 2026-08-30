#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SPEC_DIR = ROOT / "tools" / "orchestrator" / "specs"


def spec_path_for_phase(phase_id: int) -> Path:
    matches = sorted(
        SPEC_DIR.glob(f"phase_{phase_id}_*.json")
    )

    if not matches:
        raise RuntimeError(
            f"No specification found for phase {phase_id}"
        )

    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple specifications found for phase {phase_id}: "
            + ", ".join(str(path.relative_to(ROOT)) for path in matches)
        )

    return matches[0]


def load_phase_spec(phase_id: int) -> dict[str, Any]:
    path = spec_path_for_phase(phase_id)

    try:
        import json

        data = json.loads(path.read_text())
    except Exception as exc:
        raise RuntimeError(
            f"Unable to load phase {phase_id} specification: {exc}"
        ) from exc

    if data.get("phase") != phase_id:
        raise RuntimeError(
            f"Specification phase mismatch: expected {phase_id}, "
            f"got {data.get('phase')}"
        )

    return data
