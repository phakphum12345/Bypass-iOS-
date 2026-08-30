#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator.lifecycle import (
    all_phases_completed,
    is_terminal_state,
    resolve_next_phase,
)


REGISTRY = {
    "phases": [
        {"id": 6},
        {"id": 7},
        {"id": 8},
        {"id": 9},
    ]
}


def test_all_phases_completed():
    state = {
        "completed_phases": [3, 4, 5, 6, 7, 8, 9],
    }

    assert all_phases_completed(REGISTRY, state)


def test_terminal_state_with_current_phase():
    state = {
        "current_phase": 9,
        "completed_phases": [3, 4, 5, 6, 7, 8, 9],
        "status": "completed",
    }

    assert is_terminal_state(REGISTRY, state)


def test_incomplete_state_is_not_terminal():
    state = {
        "current_phase": 8,
        "completed_phases": [6, 7, 8],
        "status": "running",
    }

    assert not is_terminal_state(REGISTRY, state)


def test_next_phase_is_resolved():
    state = {
        "completed_phases": [6, 7],
    }

    phase = resolve_next_phase(REGISTRY, state)

    assert phase is not None
    assert phase["id"] == 8


def test_no_next_phase_after_completion():
    state = {
        "completed_phases": [6, 7, 8, 9],
    }

    assert resolve_next_phase(REGISTRY, state) is None


def main():
    tests = [
        test_all_phases_completed,
        test_terminal_state_with_current_phase,
        test_incomplete_state_is_not_terminal,
        test_next_phase_is_resolved,
        test_no_next_phase_after_completion,
    ]

    for test in tests:
        test()
        print(f"PASS: {test.__name__}")

    print("LIFECYCLE UNIT TEST: PASS")


if __name__ == "__main__":
    main()
