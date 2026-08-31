#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


STAGES = [
    "queued",
    "planned",
    "generated",
    "mutated",
    "validating",
    "repairing",
    "final_validated",
    "committed",
    "pushed",
    "pr_open",
    "ci_running",
    "ci_passed",
    "completed",
    "failed",
]


ALLOWED_TRANSITIONS = {
    "queued": {"planned", "failed"},
    "planned": {
        "generated",
        "validating",
        "failed",
    },
    "generated": {"mutated", "failed"},
    "mutated": {"validating", "failed"},
    "validating": {
        "repairing",
        "final_validated",
        "failed",
    },
    "repairing": {"validating", "failed"},
    "final_validated": {
        "committed",
        "pushed",
        "completed",
        "failed",
    },
    "committed": {
        "pushed",
        "completed",
        "failed",
    },
    "pushed": {
        "pr_open",
        "completed",
        "failed",
    },
    "pr_open": {
        "ci_running",
        "failed",
    },
    "ci_running": {
        "ci_passed",
        "failed",
    },
    "ci_passed": {
        "completed",
        "failed",
    },
    "completed": set(),
    "failed": set(),
}


def transition(
    state: dict[str, Any],
    stage: str,
) -> dict[str, Any]:
    current = state.get("stage")

    if current is not None:
        allowed = ALLOWED_TRANSITIONS.get(
            current,
            set(),
        )

        if stage not in allowed:
            raise RuntimeError(
                f"Invalid state transition: "
                f"{current} -> {stage}"
            )

    state["stage"] = stage
    state.setdefault("history", []).append({
        "stage": stage,
    })

    return state


def load_state(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def save_state(
    path: Path,
    state: dict[str, Any],
) -> None:
    path.write_text(
        json.dumps(
            state,
            indent=2,
        )
        + "\n"
    )
